# LiveUtilities.py
import adsk.core, adsk.fusion, traceback
import json
import os
import importlib 
from pathlib import Path

from . import core_logic
importlib.reload(core_logic)

app = None
ui = None
handlers = []
palette_id = 'EdJ_LiveUtilities_Palette'
command_id = 'EdJLiveUtilitiesCmd'

class MyCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            old = ui.palettes.itemById(palette_id)
            if old: old.deleteMe()

            script_folder = os.path.dirname(os.path.realpath(__file__))
            html_path = os.path.join(script_folder, 'resources', 'liveutils_index.html')
            
            if not os.path.exists(html_path):
                ui.messageBox(f'Error: HTML file not found at:\n{html_path}')
                return

            url = 'file:///' + html_path.replace('\\', '/')
            
            palette = ui.palettes.add(palette_id, 'Live Utilities', url, True, True, True, 360, 500)
            palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateRight
            
            onHtmlEvent = MyHTMLEventHandler()
            palette.incomingFromHTML.add(onHtmlEvent)
            handlers.append(onHtmlEvent)
            
            onClose = MyPaletteCloseHandler()
            palette.closed.add(onClose)
            handlers.append(onClose)
            
            palette.isVisible = True

        except:
            if ui: ui.messageBox('Execute Failed:\n{}'.format(traceback.format_exc()))

class MyHTMLEventHandler(adsk.core.HTMLEventHandler):
    def __init__(self):
        super().__init__()
    
    def is_unsafe(self, palette):
        cmd = ui.activeCommand
        if cmd != 'SelectCommand':
            if cmd == 'CommitCommand': 
                msg = "Fusion is busy.\n\nPlease try again."
            else:
                msg = f"-- ERROR --\n\nCommand '{cmd}' is active.\n\nClick the Canvas > Press ESC."
            
            if palette:
                palette.sendInfoToHTML('notification', json.dumps({
                    'message': msg,
                    'type': 'error'
                }))
            return True 
        return False 

    def notify(self, args):
        try:
            html_args = adsk.core.HTMLEventArgs.cast(args)
            data = json.loads(html_args.data)
            action = data.get('action')
            palette = ui.palettes.itemById(palette_id)
            
            # ==========================================
            # 1. READ-ONLY ACTIONS
            # ==========================================
            if action == 'refresh_data':
                payload = core_logic.scan_all()
                if palette: palette.sendInfoToHTML('update_ui', payload)
                return
            
            elif action == 'refresh_dashboard':
                core_logic.generate_and_open_report(open_browser=True)
                return
                
            elif action == 'export_log':
                core_logic.export_log_logic()
                return

            # --- MACRO ROUTING ---
            elif action == 'link_external_script':
                try:
                    target_type = data.get('target')
                    fileDialog = ui.createFileDialog()
                    fileDialog.title = 'Select Python Script to Link'
                    # The secondary wildcard is often required to prevent silent failures in Fusion's UI
                    fileDialog.filter = 'Python Files (*.py);;All Files (*.*)'
                    
                    paths = core_logic.get_fusion_api_paths()
                    
                    if target_type in paths:
                        target_dir = paths.get(target_type)
                        if target_dir and os.path.exists(target_dir):
                            # Normalize slashes just in case
                            fileDialog.initialDirectory = target_dir.replace('\\', '/')
                            
                    if fileDialog.showOpen() == adsk.core.DialogResults.DialogOK:
                        script_path = fileDialog.filename
                        core_logic.add_plugin(script_path)
                        if palette: palette.sendInfoToHTML('update_ui', core_logic.scan_all())
                except Exception as e:
                    ui.messageBox(f"Error opening file dialog:\n{str(e)}\n\n{traceback.format_exc()}")
                return

            elif action == 'launch_script':
                try:
                    payload = core_logic.execute_external_script(data.get('path'))
                    if palette: palette.sendInfoToHTML('notification', payload)
                except Exception as e:
                    ui.messageBox(f"Error launching script:\n{str(e)}\n\n{traceback.format_exc()}")
                return

            elif action == 'unlink_script':
                core_logic.remove_plugin(data.get('path'))
                if palette: palette.sendInfoToHTML('update_ui', core_logic.scan_all())
                return

            # ==========================================
            # 2. WRITE ACTIONS (Requires Safety Check)
            # ==========================================
            if self.is_unsafe(palette):
                return

            # --- PARAMETER ROUTING ---
            if action == 'update_param':
                payload = core_logic.update_parameter(data.get('name'), data.get('value'))
                if palette: 
                    palette.sendInfoToHTML('notification', payload)
                    if json.loads(payload).get('type') == 'success':
                        palette.sendInfoToHTML('update_ui', payload)
                
            elif action == 'update_attributes':
                payload = core_logic.update_parameter_attributes(data.get('old_name'), data.get('new_name'), data.get('comment'))
                if palette: 
                    palette.sendInfoToHTML('notification', payload)
                    if json.loads(payload).get('type') == 'success':
                        palette.sendInfoToHTML('update_ui', payload)
            
            elif action == 'toggle_favorite':
                payload = core_logic.toggle_favorite(data.get('name'))
                if palette: palette.sendInfoToHTML('update_ui', payload)

            elif action == 'create_param':
                payload = core_logic.create_parameter(data.get('name'), data.get('unit'), data.get('expression'), data.get('comment'))
                if palette: 
                    palette.sendInfoToHTML('notification', payload)
                    if json.loads(payload).get('type') == 'success':
                        palette.sendInfoToHTML('update_ui', payload)

            elif action == 'delete_param':
                payload = core_logic.delete_parameter(data.get('name'))
                if palette:
                    palette.sendInfoToHTML('notification', payload)
                    if json.loads(payload).get('type') == 'success':
                        palette.sendInfoToHTML('update_ui', payload)

            # --- CONFIG ROUTING ---
            elif action == 'export_configs':
                payload = core_logic.batch_export_configs(data.get('step'), data.get('stl'), data.get('3mf'))
                if palette: palette.sendInfoToHTML('notification', payload)
                
            elif action == 'rename_snapshot':
                success = core_logic.rename_snapshot(data.get('old_name'), data.get('new_name'))
                if success and palette:
                    palette.sendInfoToHTML('update_ui', core_logic.scan_all())

            elif action == 'toggle_feature':
                payload = core_logic.toggle_feature(data.get('name'), data.get('is_suppressed'))
                if palette: palette.sendInfoToHTML('update_ui', payload)

            elif action == 'save_snapshot':
                success = core_logic.save_snapshot(data.get('config_name'))
                if success and palette:
                    palette.sendInfoToHTML('update_ui', core_logic.scan_all())

            elif action == 'delete_snapshot':
                success = core_logic.delete_snapshot(data.get('config_name'))
                if success and palette:
                    palette.sendInfoToHTML('update_ui', core_logic.scan_all())
                    
            elif action == 'load_snapshot':
                core_logic.apply_snapshot(data.get('config_name'))
                if palette: palette.sendInfoToHTML('update_ui', core_logic.scan_all())

            # --- CHANGELOG ROUTING ---
            elif action == 'add_entry':
                core_logic.add_entry_logic(data.get('note'), data.get('autosave'))
                core_logic.generate_and_open_report(open_browser=False) 
                
            elif action == 'create_milestone':
                core_logic.create_milestone_logic(data.get('reason'))
                core_logic.generate_and_open_report(open_browser=False)

        except:
            if ui: ui.messageBox('HTML Event Failed:\n{}'.format(traceback.format_exc()))

class MyDocActivatedHandler(adsk.core.DocumentEventHandler):
    def __init__(self): super().__init__()
    def notify(self, args):
        try:
            palette = ui.palettes.itemById(palette_id)
            if palette and palette.isVisible:
                payload = core_logic.scan_all()
                palette.sendInfoToHTML('update_ui', payload)
            core_logic.generate_and_open_report(open_browser=False)
        except: pass 

class MyCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self): super().__init__()
    def notify(self, args):
        cmd = args.command
        onExec = MyCommandExecuteHandler()
        cmd.execute.add(onExec)
        handlers.append(onExec)

class MyPaletteCloseHandler(adsk.core.UserInterfaceGeneralEventHandler):
    def __init__(self): super().__init__()
    def notify(self, args): pass

def run(context):
    global ui, app
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        if ui.commandDefinitions.itemById(command_id):
            ui.commandDefinitions.itemById(command_id).deleteMe()

        script_folder = os.path.dirname(os.path.realpath(__file__))
        res_dir = os.path.join(script_folder, 'resources')
        
        cmdDef = ui.commandDefinitions.addButtonDefinition(
            command_id, 
            'Live Utilities', 
            'Persistent tools for Parameters, Configurations, Changelogs, and Macros.', 
            res_dir
        )
        
        onCreated = MyCommandCreatedHandler()
        cmdDef.commandCreated.add(onCreated)
        handlers.append(onCreated)
        
        panel = ui.allToolbarPanels.itemById('SolidModifyPanel')
        if panel:
            ctrl = panel.controls.addCommand(cmdDef)
            ctrl.isPromoted = True
            
        onDocActivated = MyDocActivatedHandler()
        app.documentActivated.add(onDocActivated)
        handlers.append(onDocActivated)
    except:
        if ui: ui.messageBox('Run Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    try:
        if ui.palettes.itemById(palette_id): ui.palettes.itemById(palette_id).deleteMe()
        if ui.commandDefinitions.itemById(command_id): ui.commandDefinitions.itemById(command_id).deleteMe()
        panel = ui.allToolbarPanels.itemById('SolidModifyPanel')
        if panel and panel.controls.itemById(command_id): panel.controls.itemById(command_id).deleteMe()
    except: pass