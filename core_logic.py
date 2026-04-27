import adsk.core, adsk.fusion, traceback
import json
import re
import datetime
import tempfile
import webbrowser
import time
import os
import sys
import platform
import importlib.util

# ==============================================================================
# CONSTANTS (From Config & Changelog)
# ==============================================================================
CONFIG_ATTR_GROUP = "EdJ_Data"
CONFIG_ATTR_NAME = "Config_Snapshots"
ACTIVE_CONFIG_ATTR = "Last_Active_Config"
PLUGIN_REGISTRY_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources', 'plugins.json')

# ==============================================================================
# PLUGIN / MACRO MANAGER
# ==============================================================================
def get_fusion_api_paths():
    """Dynamically resolves Fusion's hidden and hashed script directories."""
    paths = {}
    is_mac = platform.system() == 'Darwin'
    
    # 1. User's Personal Scripts
    if is_mac:
        user_base = os.path.expanduser("~/Library/Application Support/Autodesk/Autodesk Fusion 360/API")
    else:
        user_base = os.path.expandvars(r"%APPDATA%\Autodesk\Autodesk Fusion 360\API")
        
    paths['scripts'] = os.path.join(user_base, "Scripts")
    
    # 2. Native Fusion Samples (Dynamic Production Hash Folder)
    prod_dir = os.path.dirname(sys.executable)
    if is_mac:
        samples_path = ""
        for p in sys.path:
            clean_path = p.replace('\\', '/')
            if "Api/Python/packages" in clean_path:
                samples_path = os.path.abspath(os.path.join(p, "../../Samples"))
                break
        paths['samples'] = samples_path
    else:
        paths['samples'] = os.path.join(prod_dir, "Python", "Samples")
        
    return paths

def get_plugins():
    if os.path.exists(PLUGIN_REGISTRY_PATH):
        try:
            with open(PLUGIN_REGISTRY_PATH, 'r') as f:
                return json.load(f)
        except: return []
    return []

def save_plugins(plugins):
    try:
        with open(PLUGIN_REGISTRY_PATH, 'w') as f:
            json.dump(plugins, f, indent=4)
    except: pass

def add_plugin(path):
    plugins = get_plugins()
    name = os.path.basename(path).replace('.py', '')
    if not any(p.get('path') == path for p in plugins):
        plugins.append({'name': name, 'path': path})
        save_plugins(plugins)

def remove_plugin(path):
    plugins = get_plugins()
    plugins = [p for p in plugins if p.get('path') != path]
    save_plugins(plugins)

def execute_external_script(script_path):
    try:
        if not os.path.exists(script_path):
            return json.dumps({"message": "Script file not found.", "type": "error"})

        folder = os.path.dirname(script_path)
        module_name = os.path.splitext(os.path.basename(script_path))[0]

        # --- THE SANDBOX FIX: NEUTRALIZE adsk.terminate ---
        # Standalone scripts call adsk.terminate() when their dialogs close.
        # If they do that inside our Add-in, it kills LiveUtilities!
        # We intercept and disable that specific command globally.
        if not hasattr(adsk, '_edj_terminate_patched'):
            try:
                adsk._original_terminate = adsk.terminate
                adsk.terminate = lambda: None
                adsk._edj_terminate_patched = True
            except:
                pass

        # 1. Add the folder to the system path so standard imports work
        if folder not in sys.path:
            sys.path.insert(0, folder)

        # 2. Build the module spec
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        script_module = importlib.util.module_from_spec(spec)
        
        # 3. Fake the Package Namespace (Fixes relative imports like 'from . import')
        script_module.__package__ = module_name
        script_module.__path__ = [folder] 
        sys.modules[module_name] = script_module

        # 4. Execute the module code
        spec.loader.exec_module(script_module)

        # 5. Trigger Fusion's standard run() function
        if hasattr(script_module, 'run'):
            context = {'isApplicationStartup': False}
            script_module.run(context)
            
            # Clean up sys.path
            if folder in sys.path:
                sys.path.remove(folder)
            
            return json.dumps({"message": f"Ran {module_name}", "type": "success"})
        else:
            if folder in sys.path:
                sys.path.remove(folder)
            return json.dumps({"message": "No run() function found in script.", "type": "error"})

    except Exception as e:
        # Failsafe cleanup
        try:
            folder = os.path.dirname(script_path)
            if folder in sys.path:
                sys.path.remove(folder)
        except: pass
        
        return json.dumps({"message": f"Error executing script:\n{str(e)}", "type": "error"})

# ==============================================================================
# MASTER SCANNER
# ==============================================================================
def scan_all():
    """Scans parameters, timeline features, saved configs, and plugins in one pass."""
    app = adsk.core.Application.get()
    design = app.activeProduct
    
    # Grab plugins right away as they are global
    global_plugins = get_plugins()
    
    if not design: 
        return json.dumps({"error": "No design active", "plugins": global_plugins})

    clean_name = re.sub(r'\s+v\d+$', '', app.activeDocument.name)

    # 1. PARAMETERS (Merged from live_logic and config_logic)
    param_data = []
    for param in design.allParameters:
        is_user = design.userParameters.itemByName(param.name) is not None
        is_fav = getattr(param, "isFavorite", False)
        is_renamed = not re.match(r'^d\d+$', param.name) if not is_user else False
        
        if is_user or is_fav or is_renamed:
            safe_val = 0
            try: safe_val = param.value
            except: pass

            param_data.append({
                "name": param.name,
                "expression": param.expression,
                "value": safe_val, 
                "unit": param.unit,
                "comment": param.comment, 
                "isFavorite": is_fav,
                "is_user_param": is_user 
            })

    # 2. TIMELINE FEATURES & GROUPS (CFG_)
    feature_data = []
    root = design.rootComponent
    
    for feature in root.features:
        if feature.name.startswith("CFG_"):
            feature_data.append({
                "name": feature.name,
                "isSuppressed": feature.isSuppressed
            })
            
    timeline = design.timeline
    for group in timeline.timelineGroups:
        if group.name.startswith("CFG_"):
            feature_data.append({
                "name": group.name,
                "isSuppressed": group.isSuppressed
            })

    # 3. SAVED CONFIG SNAPSHOTS
    saved_configs = {}
    attr = root.attributes.itemByName(CONFIG_ATTR_GROUP, CONFIG_ATTR_NAME)
    if attr:
        try: saved_configs = json.loads(attr.value)
        except: saved_configs = {}

    last_active = ""
    active_attr = root.attributes.itemByName(CONFIG_ATTR_GROUP, ACTIVE_CONFIG_ATTR)
    if active_attr:
        last_active = active_attr.value

    # --- DIRTY STATE EVALUATION ---
    current_feats = {}
    for f in root.features:
        if f.name.startswith("CFG_"): current_feats[f.name] = f.isSuppressed
    for g in design.timeline.timelineGroups:
        if g.name.startswith("CFG_"): current_feats[g.name] = g.isSuppressed

    current_params = {}
    for p in design.allParameters:
        is_user = design.userParameters.itemByName(p.name) is not None
        is_fav = getattr(p, "isFavorite", False)
        is_renamed = not re.match(r'^d\d+$', p.name) if not is_user else False
        if is_user or is_fav or is_renamed:
            current_params[p.name] = p

    um = design.unitsManager
    
    def check_match(snapshot):
        snap_params = snapshot.get("params", {})
        snap_feats = snapshot.get("features", {})
        
        if snap_feats != current_feats: return False
        if len(snap_params) != len(current_params): return False
        
        for p_name, saved_expr in snap_params.items():
            p = current_params.get(p_name)
            if not p: return False
            try:
                saved_val = um.evaluateExpression(saved_expr, p.unit)
                if round(saved_val, 5) != round(p.value, 5): return False
            except:
                if p.expression != saved_expr: return False
        return True

    is_dirty = True
    matched_name = ""

    if last_active and last_active in saved_configs and check_match(saved_configs[last_active]):
        is_dirty = False
        matched_name = last_active
    else:
        for c_name, c_snap in saved_configs.items():
            if check_match(c_snap):
                is_dirty = False
                matched_name = c_name
                root.attributes.add(CONFIG_ATTR_GROUP, ACTIVE_CONFIG_ATTR, matched_name)
                break

    final_active_config = matched_name if matched_name else last_active

    return json.dumps({
        "doc_name": clean_name,
        "parameters": param_data,
        "features": feature_data,
        "configs": saved_configs,
        "active_config": final_active_config,
        "is_dirty": is_dirty,
        "plugins": global_plugins
    })

# ==============================================================================
# CONFIGURATOR LOGIC
# ==============================================================================
def toggle_feature(name, should_suppress):
    app = adsk.core.Application.get()
    design = app.activeProduct
    root = design.rootComponent
    
    item = root.features.itemByName(name)
    if not item:
        timeline = design.timeline
        for group in timeline.timelineGroups:
            if group.name == name:
                item = group
                break
        
    if item:
        item.isSuppressed = should_suppress
        adsk.doEvents() 
        
    return scan_all()

def save_snapshot(config_name):
    app = adsk.core.Application.get()
    design = app.activeProduct
    if not design: return False
    
    root = design.rootComponent 

    params = {}
    for p in design.allParameters:
        is_user = design.userParameters.itemByName(p.name) is not None
        is_fav = getattr(p, "isFavorite", False)
        is_renamed = not re.match(r'^d\d+$', p.name) if not is_user else False
        
        if is_user or is_fav or is_renamed:
            params[p.name] = p.expression

    feats = {}
    for f in root.features:
        if f.name.startswith("CFG_"):
            feats[f.name] = f.isSuppressed
            
    timeline = design.timeline
    for g in timeline.timelineGroups:
        if g.name.startswith("CFG_"):
            feats[g.name] = g.isSuppressed

    current_data = {}
    attr = root.attributes.itemByName(CONFIG_ATTR_GROUP, CONFIG_ATTR_NAME)
    if attr:
        try: current_data = json.loads(attr.value)
        except: pass
    
    current_data[config_name] = {
        "params": params,
        "features": feats
    }

    root.attributes.add(CONFIG_ATTR_GROUP, CONFIG_ATTR_NAME, json.dumps(current_data))
    root.attributes.add(CONFIG_ATTR_GROUP, ACTIVE_CONFIG_ATTR, config_name)
    return True

def delete_snapshot(config_name):
    app = adsk.core.Application.get()
    design = app.activeProduct
    if not design: return False
    
    root = design.rootComponent 
    attr = root.attributes.itemByName(CONFIG_ATTR_GROUP, CONFIG_ATTR_NAME)
    if not attr: return False
    
    try:
        current_data = json.loads(attr.value)
        if config_name in current_data:
            del current_data[config_name]
            root.attributes.add(CONFIG_ATTR_GROUP, CONFIG_ATTR_NAME, json.dumps(current_data))
            
            active_attr = root.attributes.itemByName(CONFIG_ATTR_GROUP, ACTIVE_CONFIG_ATTR)
            if active_attr and active_attr.value == config_name:
                root.attributes.add(CONFIG_ATTR_GROUP, ACTIVE_CONFIG_ATTR, "")
            return True
    except: pass
    return False

def rename_snapshot(old_name, new_name):
    app = adsk.core.Application.get()
    design = app.activeProduct
    if not design: return False
    
    root = design.rootComponent 
    attr = root.attributes.itemByName(CONFIG_ATTR_GROUP, CONFIG_ATTR_NAME)
    if not attr: return False
    
    try:
        current_data = json.loads(attr.value)
        if old_name in current_data:
            if new_name in current_data and old_name != new_name:
                return False 
            
            current_data[new_name] = current_data.pop(old_name)
            root.attributes.add(CONFIG_ATTR_GROUP, CONFIG_ATTR_NAME, json.dumps(current_data))
            
            active_attr = root.attributes.itemByName(CONFIG_ATTR_GROUP, ACTIVE_CONFIG_ATTR)
            if active_attr and active_attr.value == old_name:
                root.attributes.add(CONFIG_ATTR_GROUP, ACTIVE_CONFIG_ATTR, new_name)
                
            return True
    except: pass
    return False

def apply_snapshot(config_name):
    app = adsk.core.Application.get()
    design = app.activeProduct
    root = design.rootComponent 
    
    attr = root.attributes.itemByName(CONFIG_ATTR_GROUP, CONFIG_ATTR_NAME)
    if not attr: return
    
    data = json.loads(attr.value)
    if config_name not in data: return
    
    snapshot = data[config_name]
    
    design.isComputeDeferred = True
    try:
        saved_params = snapshot.get("params", {})
        for name, expr in saved_params.items():
            p = design.allParameters.itemByName(name)
            if p: p.expression = expr
            
        saved_feats = snapshot.get("features", {})
        timeline = design.timeline
        for name, is_suppressed in saved_feats.items():
            item = root.features.itemByName(name)
            if not item:
                for group in timeline.timelineGroups:
                    if group.name == name:
                        item = group
                        break
            if item: 
                item.isSuppressed = is_suppressed

        root.attributes.add(CONFIG_ATTR_GROUP, ACTIVE_CONFIG_ATTR, config_name)
    except:
        pass
    finally:
        design.isComputeDeferred = False
        app.activeViewport.refresh()

def batch_export_configs(export_step, export_stl, export_3mf):
    app = adsk.core.Application.get()
    ui = app.userInterface
    design = app.activeProduct
    if not design: return json.dumps({"message": "No active design", "type": "error"})
    
    root = design.rootComponent
    exportMgr = design.exportManager
    
    attr = root.attributes.itemByName(CONFIG_ATTR_GROUP, CONFIG_ATTR_NAME)
    if not attr: return json.dumps({"message": "No configs found.", "type": "error"})
    
    try: configs = json.loads(attr.value)
    except: return json.dumps({"message": "Error parsing configs.", "type": "error"})
    
    if not configs: return json.dumps({"message": "No configs to export.", "type": "info"})
    
    dlg = ui.createFolderDialog()
    dlg.title = 'Select Folder for Batch Config Export'
    if dlg.showDialog() != adsk.core.DialogResults.DialogOK:
        return json.dumps({"message": "Export cancelled.", "type": "info"})
    
    folder = dlg.folder
    
    last_active = ""
    active_attr = root.attributes.itemByName(CONFIG_ATTR_GROUP, ACTIVE_CONFIG_ATTR)
    if active_attr: last_active = active_attr.value
    
    progressDialog = ui.createProgressDialog()
    progressDialog.cancelButtonText = 'Cancel'
    progressDialog.isBackgroundTranslucent = False
    progressDialog.isCancelButtonShown = True
    
    total_configs = len(configs)
    progressDialog.show('Exporting Configs...', 'Percent Complete: %p% - Processed so far: %v of %m', 0, total_configs, 1)
    
    success_count = 0
    cancel_flag = False
    
    def sanitize_filename(name: str) -> str:
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        return name.strip().strip('.')
        
    for i, config_name in enumerate(configs.keys()):
        if progressDialog.wasCancelled:
            cancel_flag = True
            break
            
        progressDialog.progressValue = i
        
        apply_snapshot(config_name)
        app.activeViewport.refresh()
        adsk.doEvents() 
        
        safe_name = sanitize_filename(config_name)
        
        if export_step:
            path = os.path.join(folder, safe_name + '.step')
            try:
                opts = exportMgr.createSTEPExportOptions(path, root)
                exportMgr.execute(opts)
                success_count += 1
            except: pass
            
        if export_stl:
            path = os.path.join(folder, safe_name + '.stl')
            try:
                opts = exportMgr.createSTLExportOptions(root, path)
                exportMgr.execute(opts)
                success_count += 1
            except: pass
            
        if export_3mf and hasattr(exportMgr, 'createC3MFExportOptions'):
            path = os.path.join(folder, safe_name + '.3mf')
            try:
                opts = exportMgr.createC3MFExportOptions(root)
                opts.filename = path
                exportMgr.execute(opts)
                success_count += 1
            except: pass

        progressDialog.progressValue = i + 1
        app.activeViewport.refresh()
        adsk.doEvents()
            
    if last_active and last_active in configs:
        apply_snapshot(last_active)
        app.activeViewport.refresh()
        adsk.doEvents()
        
    progressDialog.hide()
    
    if cancel_flag:
        return json.dumps({"message": f"Export aborted. {success_count} files created.", "type": "info"})
        
    return json.dumps({"message": f"Exported {success_count} files successfully.", "type": "success"})

# ==============================================================================
# PARAMETER LOGIC
# ==============================================================================
def validate_expression(expression, unit):
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        if not design: return False
        return design.unitsManager.isValidExpression(expression, unit)
    except:
        return False

def update_parameter(name, expression):
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        param = design.allParameters.itemByName(name)
        
        if not param:
            return json.dumps({"message": "Parameter not found", "type": "error"})

        if not validate_expression(expression, param.unit):
            return json.dumps({
                "message": f"Invalid value for unit ({param.unit})", 
                "type": "error"
            })

        param.expression = str(expression)
        
        scan_result = json.loads(scan_all())
        scan_result["message"] = "Updated"
        scan_result["type"] = "success"
        return json.dumps(scan_result)

    except Exception as e:
        return json.dumps({"message": f"Error: {str(e)}", "type": "error"})

def toggle_favorite(name):
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        param = design.allParameters.itemByName(name)
        if param:
            param.isFavorite = not param.isFavorite
    except:
        pass
    return scan_all()

def update_parameter_attributes(old_name, new_name, comment):
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        
        param = design.allParameters.itemByName(old_name)
        if not param:
            return json.dumps({"message": "Parameter not found", "type": "error"})
            
        if old_name != new_name:
            existing = design.allParameters.itemByName(new_name)
            if existing and existing.name != old_name:
                 return json.dumps({"message": f"Name '{new_name}' already in use", "type": "error"})
            try:
                param.name = new_name
            except Exception as e:
                return json.dumps({"message": "Invalid Name (Avoid spaces/symbols)", "type": "error"})
        
        param = design.allParameters.itemByName(new_name)
        if param:
            param.comment = str(comment)

        scan_result = json.loads(scan_all())
        scan_result["message"] = "Saved"
        scan_result["type"] = "success"
        return json.dumps(scan_result)

    except Exception as e:
        return json.dumps({"message": f"Failed: {str(e)}", "type": "error"})

def create_parameter(name, unit, expression, comment):
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        if not design: return json.dumps({"message": "No design active", "type": "error"})

        if design.allParameters.itemByName(name):
            return json.dumps({"message": f"Parameter '{name}' already exists", "type": "error"})

        if not validate_expression(expression, unit):
            return json.dumps({
                "message": f"Invalid expression for unit ({unit})", 
                "type": "error"
            })

        real_val = adsk.core.ValueInput.createByString(expression)
        design.userParameters.add(name, real_val, unit, comment)
        
        scan_result = json.loads(scan_all())
        scan_result["message"] = f"Created '{name}'"
        scan_result["type"] = "success"
        scan_result["action"] = "create_param" 
        return json.dumps(scan_result)

    except Exception as e:
        return json.dumps({"message": f"Failed: {str(e)}", "type": "error"})

def delete_parameter(name):
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        if not design: return json.dumps({"message": "No design active", "type": "error"})

        param = design.userParameters.itemByName(name)
        if not param:
            return json.dumps({"message": "Parameter not found", "type": "error"})
        
        is_deleted = param.deleteMe()
        
        if is_deleted:
            scan_result = json.loads(scan_all())
            scan_result["message"] = f"Deleted '{name}'"
            scan_result["type"] = "success"
            return json.dumps(scan_result)
        else:
            return json.dumps({
                "message": f"Could not delete '{name}'. It is likely in use.", 
                "type": "error"
            })

    except Exception as e:
        return json.dumps({"message": f"Error: {str(e)}", "type": "error"})
    
# ==============================================================================
# CHANGELOG LOGIC
# ==============================================================================
CHANGELOG_GROUP_KEY = 'EdJ_ChangelogSidecar_Group'
CHANGELOG_NAME_KEY = 'EdJ_ChangelogSidecar_Data'
ARCHIVE_LOG_PREFIX = 'archive_' 

def get_timestamp_and_user():
    app = adsk.core.Application.get()
    try: username = app.currentUser.displayName
    except: username = 'Unknown'
        
    now = datetime.datetime.now().astimezone()
    tz_name = now.tzname()
    if tz_name and any(x.islower() for x in tz_name):
            tz_abbr = ''.join([word[0] for word in tz_name.split() if word])
    else:
            tz_abbr = tz_name if tz_name else ''
    return now.strftime(f'%Y-%m-%d - %H:%M:%S {tz_abbr}'), username

def add_entry_logic(note_text, autosave):
    app = adsk.core.Application.get()
    design = app.activeProduct
    if not design: return
    root = design.rootComponent
    
    timestamp, user = get_timestamp_and_user()
    current_list = []
    attr = root.attributes.itemByName(CHANGELOG_GROUP_KEY, CHANGELOG_NAME_KEY)
    if attr: 
        try: current_list = json.loads(attr.value)
        except: pass
    
    current_list.append({'timestamp': timestamp, 'user': user, 'note': note_text})
    root.attributes.add(CHANGELOG_GROUP_KEY, CHANGELOG_NAME_KEY, json.dumps(current_list, indent=4))
    
    if autosave:
        doc = app.activeDocument
        if doc.isSaved:
            try: doc.save(f'{note_text[:50]}')
            except: pass

def create_milestone_logic(reason):
    app = adsk.core.Application.get()
    design = app.activeProduct
    if not design: return
    root = design.rootComponent
    
    current_list = []
    attr = root.attributes.itemByName(CHANGELOG_GROUP_KEY, CHANGELOG_NAME_KEY)
    if attr: 
        try: current_list = json.loads(attr.value)
        except: pass
    
    timestamp, user = get_timestamp_and_user()
    milestone_entry = {'timestamp': timestamp, 'user': user, 'note': f"--- MILESTONE CREATED ---\nReason: {reason}"}
    current_list.append(milestone_entry)
    
    archive_name = f"{ARCHIVE_LOG_PREFIX}{datetime.datetime.now().strftime('%Y-%m-%dT%H%M%S')}"
    root.attributes.add(CHANGELOG_GROUP_KEY, archive_name, json.dumps(current_list, indent=4))
    
    new_log = [milestone_entry]
    root.attributes.add(CHANGELOG_GROUP_KEY, CHANGELOG_NAME_KEY, json.dumps(new_log, indent=4))
    
    doc = app.activeDocument
    if doc.isSaved:
        try: doc.save(f'🚩 {reason[:50]}')
        except: pass

def export_theme_logic(file_type, content, default_name):
    app = adsk.core.Application.get()
    ui = app.userInterface
    fileDialog = ui.createFileDialog()
    fileDialog.title = 'Export Theme'
    if file_type == 'css':
        fileDialog.filter = 'CSS Files (*.css);;All Files (*.*)'
    else:
        fileDialog.filter = 'JSON Files (*.json);;All Files (*.*)'
        
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    fileDialog.initialDirectory = resources_dir
    fileDialog.initialFilename = default_name
    if fileDialog.showSave() == adsk.core.DialogResults.DialogOK:
        try:
            with open(fileDialog.filename, 'w', encoding='utf-8') as f:
                f.write(content)
            ui.messageBox(f'Theme exported to {fileDialog.filename}')
        except Exception as e:
            ui.messageBox(f'Failed to save theme:\n{str(e)}')

def import_theme_logic(file_type):
    app = adsk.core.Application.get()
    ui = app.userInterface
    fileDialog = ui.createFileDialog()
    fileDialog.title = 'Import Theme'
    if file_type == 'css':
        fileDialog.filter = 'CSS Files (*.css);;All Files (*.*)'
    else:
        fileDialog.filter = 'JSON Files (*.json);;All Files (*.*)'
        
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    fileDialog.initialDirectory = resources_dir
    if fileDialog.showOpen() == adsk.core.DialogResults.DialogOK:
        try:
            with open(fileDialog.filename, 'r', encoding='utf-8') as f:
                content = f.read()
            return json.dumps({"file_type": file_type, "content": content})
        except Exception as e:
            ui.messageBox(f'Failed to read theme:\n{str(e)}')
    return None

def export_log_logic():
    app = adsk.core.Application.get()
    ui = app.userInterface
    design = app.activeProduct
    if not design: return
    doc = app.activeDocument
    root = design.rootComponent
    
    export_str = f"DESIGN: {doc.name}\n\n"
    all_attrs = root.attributes.itemsByGroup(CHANGELOG_GROUP_KEY)
    archive_list = [a for a in all_attrs if a.name.startswith(ARCHIVE_LOG_PREFIX)]
    archive_list.sort(key=lambda x: x.name)
    
    for attr in archive_list:
        export_str += f"--- ARCHIVE {attr.name} ---\n"
        try:
            for entry in json.loads(attr.value):
                export_str += f"[{entry['timestamp']}] {entry['user']}: {entry['note']}\n"
        except: pass
        export_str += "\n"

    attr = root.attributes.itemByName(CHANGELOG_GROUP_KEY, CHANGELOG_NAME_KEY)
    if attr:
        export_str += "--- ACTIVE LOG ---\n"
        try:
            for entry in json.loads(attr.value):
                export_str += f"[{entry['timestamp']}] {entry['user']}: {entry['note']}\n"
        except: pass

    fileDialog = ui.createFileDialog()
    fileDialog.title = 'Export Changelog'
    fileDialog.filter = 'Text Files (*.txt);;All Files (*.*)'
    fileDialog.initialFilename = f"{doc.name}_changelog.txt"
    if fileDialog.showSave() == adsk.core.DialogResults.DialogOK:
        with open(fileDialog.filename, 'w', encoding='utf-8') as f:
            f.write(export_str)
        ui.messageBox(f'Exported to {fileDialog.filename}')

def generate_and_open_report(open_browser=True):
    app = adsk.core.Application.get()
    design = app.activeProduct
    if not design: return
    root = design.rootComponent
    
    full_name = app.activeDocument.name
    stable_name = re.sub(r'\s+v\d+$', '', full_name)

    css = """
    <style>
        :root {
            --bg-body: #f4f6f8; --bg-container: #ffffff; --text-primary: #333333;
            --text-secondary: #6b778c; --header-border: #0052cc; --header-text: #172b4d;
            --milestone-bg: #ebecf0; --milestone-text: #172b4d; --entry-border: #ebecf0;
            --tag-bg: #e3fcef; --tag-text: #006644; --meta-text: #999999;
            --shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        html[data-theme="dark"] {
            --bg-body: #1e1e1e; --bg-container: #2d2d2d; --text-primary: #e0e0e0;
            --text-secondary: #a0a0a0; --header-border: #4cc9f0; --header-text: #ffffff;
            --milestone-bg: #3d3d3d; --milestone-text: #ffffff; --entry-border: #444444;
            --tag-bg: #0f352e; --tag-text: #4cc9f0; --meta-text: #666666;
            --shadow: 0 4px 12px rgba(0,0,0,0.4);
        }
        body { font-family: 'Segoe UI', sans-serif; padding: 20px; background-color: var(--bg-body); color: var(--text-primary); line-height: 1.6; transition: 0.3s; }
        .container { max-width: 850px; margin: 0 auto; background: var(--bg-container); padding: 30px; border-radius: 8px; box-shadow: var(--shadow); position: relative; }
        .header-row { display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 15px; border-bottom: 3px solid var(--header-border); margin-bottom: 20px; }
        .title-block h1 { margin: 0; padding: 0; color: var(--header-text); font-size: 24px; }
        .controls { display: flex; flex-direction: column; align-items: flex-end; gap: 12px; }
        h2 { background-color: var(--tag-bg); color: var(--tag-text); padding: 10px 15px; border-radius: 4px; margin-top: 30px; margin-bottom: 15px; border-left: 5px solid var(--tag-text); font-size: 18px; text-transform: uppercase; font-weight: bold; }
        .milestone-header { background-color: var(--milestone-bg); padding: 10px 15px; border-radius: 4px; margin-top: 30px; border-left: 5px solid var(--header-border); color: var(--milestone-text); font-weight: bold; }
        .entry { padding: 12px 0; border-bottom: 1px solid var(--entry-border); }
        .entry:last-child { border-bottom: none; }
        .timestamp { font-size: 0.85em; color: var(--text-secondary); font-weight: 600; margin-bottom: 4px; }
        .note { white-space: pre-wrap; color: var(--text-primary); }
        .meta-info { font-size: 12px; color: var(--meta-text); text-align: right; margin-top: 20px; border-top: 1px solid var(--entry-border); padding-top: 10px; }
        .refresh-tag { display: inline-block; background: var(--tag-bg); color: var(--tag-text); padding: 2px 6px; border-radius: 3px; font-size: 11px; font-weight: bold; vertical-align: middle; margin-left: 10px;}
        .sync-time { font-size: 12px; color: var(--text-secondary); display: block; margin-top: 4px; }
        .theme-switch-wrapper { display: flex; align-items: center; }
        .theme-switch { display: inline-block; height: 20px; position: relative; width: 40px; margin-right: 8px;}
        .theme-switch input { display:none; }
        .slider { background-color: #ccc; bottom: 0; cursor: pointer; left: 0; position: absolute; right: 0; top: 0; transition: .4s; border-radius: 34px; }
        .slider:before { background-color: #fff; bottom: 3px; content: ""; height: 14px; left: 3px; position: absolute; transition: .4s; width: 14px; border-radius: 50%; }
        input:checked + .slider { background-color: #4cc9f0; }
        input:checked + .slider:before { transform: translateX(20px); }
        .switch-label { font-size: 12px; color: var(--text-secondary); font-weight: bold; min-width: 70px; text-align: right;}
        input[type=range] { width: 100px; margin-right: 8px; cursor: pointer; }
    </style>
    """

    active_html = ""
    attr = root.attributes.itemByName(CHANGELOG_GROUP_KEY, CHANGELOG_NAME_KEY)
    if attr:
        try:
            entries = json.loads(attr.value)
            for entry in reversed(entries):
                ts = str(entry.get('timestamp',''))
                user = str(entry.get('user',''))
                note = str(entry.get('note','')).replace('\n', '<br>')
                active_html += f"<div class='entry'><div class='timestamp'>{ts} • {user}</div><div class='note'>{note}</div></div>"
        except: active_html = "<p style='color:red'>Error reading active log.</p>"
    else: active_html = "<p style='font-style:italic; color:#888'>No active entries. Add one to start tracking.</p>"

    archive_html = ""
    all_attrs = root.attributes.itemsByGroup(CHANGELOG_GROUP_KEY)
    archive_list = [a for a in all_attrs if a.name.startswith(ARCHIVE_LOG_PREFIX)]
    archive_list.sort(key=lambda x: x.name, reverse=True)
    
    for attr in archive_list:
        try:
            ts_str = attr.name.replace(ARCHIVE_LOG_PREFIX, "")
            dt = datetime.datetime.strptime(ts_str, '%Y-%m-%dT%H%M%S')
            friendly = dt.strftime('%Y-%m-%d %H:%M')
        except: friendly = attr.name
        
        archive_html += f"<div class='milestone-header'>MILESTONE: {friendly}</div>"
        try:
            entries = json.loads(attr.value)
            for entry in reversed(entries):
                 ts = str(entry.get('timestamp',''))
                 user = str(entry.get('user',''))
                 note = str(entry.get('note','')).replace('\n', '<br>')
                 archive_html += f"<div class='entry'><div class='timestamp'>{ts} • {user}</div><div class='note'>{note}</div></div>"
        except: pass

    now_str = datetime.datetime.now().strftime("%H:%M:%S")

    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Changelog: {stable_name}</title>
        <meta charset="UTF-8">
        <script>
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);

            if ('scrollRestoration' in history) {{ history.scrollRestoration = 'manual'; }}

            window.addEventListener('DOMContentLoaded', () => {{
                const contentNode = document.getElementById('log-payload');
                const currentLen = contentNode ? contentNode.innerHTML.length : 0;
                const lastLen = parseInt(sessionStorage.getItem('contentLen')) || 0;
                const scrollPos = sessionStorage.getItem('scrollPos');

                if (currentLen !== lastLen) {{
                    window.scrollTo(0, 0);
                    sessionStorage.setItem('contentLen', currentLen);
                }} else if (scrollPos) {{
                    window.scrollTo(0, parseInt(scrollPos));
                }}
            }});

            function doReload() {{
                const stored = localStorage.getItem('syncInterval');
                const interval = stored !== null ? parseInt(stored) : 2;

                if (interval > 0) {{
                    sessionStorage.setItem('scrollPos', window.scrollY);
                    var currentUrl = window.location.href.split('?')[0];
                    var newUrl = currentUrl + '?t=' + new Date().getTime();
                    window.location.replace(newUrl);
                }}
            }}
            
            window.addEventListener('load', () => {{
                const stored = localStorage.getItem('syncInterval');
                const interval = stored !== null ? parseInt(stored) : 2;
                if (interval > 0) {{ setTimeout(doReload, interval * 1000); }}
            }});
        </script>
        {css}
    </head>
    <body>
        <div class="container">
            <div class="header-row">
                <div class="title-block">
                    <h1>{stable_name} <span class="refresh-tag">LIVE SYNC</span></h1>
                    <span class="sync-time">Last Synced: {now_str}</span>
                </div>
                
                <div class="controls">
                    <div class="control-group">
                        <label class="theme-switch" for="theme-checkbox">
                            <input type="checkbox" id="theme-checkbox" />
                            <div class="slider"></div>
                        </label>
                        <span class="switch-label">Dark Mode</span>
                    </div>

                    <div class="control-group">
                        <input type="range" id="sync-slider" min="0" max="10" step="1" value="2">
                        <span id="sync-label" class="switch-label">Sync: 2s</span>
                    </div>
                </div>
            </div>
            
            <div id="log-payload">
                <h2>Active Workspace</h2>
                {active_html}
                {archive_html}
            </div>
            
            <div class="meta-info">Generated by Live Utilities • Auto-refresh active</div>
        </div>

        <script>
            const toggleSwitch = document.getElementById('theme-checkbox');
            const currentTheme = localStorage.getItem('theme');
            if (currentTheme === 'dark') {{ toggleSwitch.checked = true; }}

            toggleSwitch.addEventListener('change', function(e) {{
                const theme = e.target.checked ? 'dark' : 'light';
                document.documentElement.setAttribute('data-theme', theme);
                localStorage.setItem('theme', theme);
            }});

            const syncSlider = document.getElementById('sync-slider');
            const syncLabel = document.getElementById('sync-label');
            const savedInterval = localStorage.getItem('syncInterval');
            if (savedInterval !== null) {{
                syncSlider.value = savedInterval;
                updateLabel(savedInterval);
            }}

            function updateLabel(val) {{
                syncLabel.textContent = (val == 0) ? "Sync: Paused" : "Sync: " + val + "s";
            }}

            syncSlider.addEventListener('input', function(e) {{ updateLabel(e.target.value); }});

            syncSlider.addEventListener('change', function(e) {{
                const newVal = parseInt(e.target.value);
                localStorage.setItem('syncInterval', newVal);
                if (newVal > 0) {{ doReload(); }}
            }});
        </script>
    </body>
    </html>
    """

    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, "FusionLog_LiveUtilities_Dashboard.html")
    
    max_retries = 5
    for i in range(max_retries):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(full_html)
            break 
        except Exception as e:
            if i < max_retries - 1:
                time.sleep(0.2)
        
    if open_browser:
        webbrowser.open_new('file://' + file_path)