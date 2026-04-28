// --- GLOBAL STATE ---
let lastReceivedData = null;
let searchQuery = "";
let statusTimeout;

let currentSelectedGroups = 0; // Tracks timeline group selection count
// --- THEME MANAGER STATE ---
const cssVariables = [
    '--font-family', '--font-size-base', 
    '--bg-body', '--text-main', '--text-sub', '--border-color',
    '--row-bg', '--row-border', '--row-hover',
    '--input-bg', '--input-border', '--input-text', '--input-placeholder', '--toggle-bg',
    '--header-hover', '--tab-bg', '--tab-active-bg', '--tab-text', '--tab-active-text',
    '--btn-primary', '--btn-primary-hover', '--btn-success', '--btn-success-hover',
    '--btn-secondary', '--btn-secondary-hover', '--btn-secondary-text',
    '--status-success-bg', '--status-success-text',
    '--status-error-bg', '--status-error-text',
    '--status-info-bg', '--status-info-text'
];
let themes = {};
let baseCSS = "";
let customThemes = JSON.parse(localStorage.getItem('LU_custom_themes') || '{}');

document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('LU_theme') || 'Default Light';
    initThemes(savedTheme);

    const savedTab = localStorage.getItem('LU_activeTab') || 'tab-params';
    switchTab(savedTab);

    document.getElementById('favFilterCheck').addEventListener('change', e => {
        if (lastReceivedData) renderUI(lastReceivedData);
    });
    document.getElementById('searchInput').addEventListener('input', e => {
        searchQuery = e.target.value.toLowerCase();
        if (lastReceivedData) renderUI(lastReceivedData);
    });

    document.getElementById('newMergedGroupName').addEventListener('input', e => {
        validateRegroupState();
    });

    waitForFusion();
});

function initThemes(savedTheme) {
    fetch('style.css')
    .then(r => {
        if (!r.ok) throw new Error('Not found');
        return r.text().then(text => {
            let style = document.getElementById('imported-style-css');
            if (!style) {
                style = document.createElement('style');
                style.id = 'imported-style-css';
            }
            document.head.appendChild(style);
            style.innerHTML = text;
            return text;
        });
    })
    .catch(() => fetch('liveutils_style.css').then(res => res.text()))
    .then(css => {
        const parsed = parseStyleCSS(css);
        themes = parsed.themes;
        baseCSS = parsed.baseCSS;
        
        for (let id in customThemes) {
            if (!themes[id]) themes[id] = {};
            Object.assign(themes[id], customThemes[id]);
        }
        updateThemeDropdown();
        updateStyleTag();
        
        const themeSelector = document.getElementById('themeSelector');
        if (themeSelector && (themes[savedTheme] || savedTheme === 'Default Light')) {
            themeSelector.value = savedTheme;
        }
        changeTheme();
    }).catch(e => console.log('Theme CSS fetch failed:', e));
}

function parseStyleCSS(cssText) {
    const themeRegex = /(?:\/\*[\s\S]*?\*\/\s*)?(?:(:root)|\[data-theme=["']?([^"']+)["']?\])\s*\{([^}]+)\}/g;
    let match;
    let parsedThemes = {};
    while ((match = themeRegex.exec(cssText)) !== null) {
        let themeId = match[1] ? "Default Light" : match[2];
        let content = match[3];
        let vars = {};
        // Safely extract variables even if a trailing semicolon is missing
        const varRegex = /(--[\w-]+)\s*:\s*([^;]+?)(?=\s*;|\s*$)/g;
        let vMatch;
        while ((vMatch = varRegex.exec(content)) !== null) {
            vars[vMatch[1].trim()] = vMatch[2].trim();
        }
        parsedThemes[themeId] = vars;
    }
    let cleanCSS = cssText.replace(themeRegex, '').trim();
    return { themes: parsedThemes, baseCSS: cleanCSS };
}

function generateFullCSS() {
    let out = "";
    let i = 1;
    for (let id in themes) {
        let comment = id === "Default Light" ? "Default Light" : id;
        let sel = id === "Default Light" ? ":root" : `[data-theme="${id}"]`;
        out += `/* ${i}. ${comment} */\n${sel} {\n`;
        for (let v of cssVariables) {
            if (themes[id][v]) out += `    ${v}: ${themes[id][v]};\n`;
        }
        out += `}\n\n`;
        i++;
    }
    return out + baseCSS;
}

function updateThemeDropdown() {
    const select = document.getElementById('themeSelector');
    if (!select) return;
    const current = select.value;
    select.innerHTML = '<option value="Default Light">Default Light</option>';
    for (let id in themes) {
        if (id === "Default Light") continue;
        let opt = document.createElement('option');
        opt.value = id; opt.text = id;
        select.appendChild(opt);
    }
    if (current && [...select.options].some(o => o.value === current)) select.value = current;
}

function updateStyleTag() {
    let out = "";
    for (let id in customThemes) {
        let sel = id === "Default Light" ? ":root" : `[data-theme="${id}"]`;
        out += `${sel} {\n`;
        for (let v of cssVariables) {
            if (customThemes[id][v]) out += `    ${v}: ${customThemes[id][v]};\n`;
        }
        out += `}\n`;
    }
    let styleTag = document.getElementById('dynamic-theme-overrides');
    if (!styleTag) {
        styleTag = document.createElement('style');
        styleTag.id = 'dynamic-theme-overrides';
    }
    // Force append to end of head to ensure highest CSS specificity
    document.head.appendChild(styleTag);
    styleTag.innerHTML = out;
}

function updateActiveThemeProperty(prop, value) {
    const themeSelector = document.getElementById('themeSelector');
    const themeId = themeSelector ? themeSelector.value : 'Default Light';
    
    if (!customThemes[themeId]) customThemes[themeId] = {};
    if (!themes[themeId]) themes[themeId] = {};
    
    customThemes[themeId][prop] = value;
    themes[themeId][prop] = value;
    localStorage.setItem('LU_custom_themes', JSON.stringify(customThemes));
    updateStyleTag();
}

function requestImport(type) { sendToFusion('import_theme', { file_type: type }); }
function requestExport(type) {
    const themeSelector = document.getElementById('themeSelector');
    if (!themeSelector) return;
    const id = themeSelector.value;
    if (type === 'json' && id === 'Default Light') return showStatus({message: "Select a custom theme to export as JSON.", type: "error"});
    const content = type === 'json' ? JSON.stringify({ id: id, vars: themes[id] }, null, 2) : generateFullCSS();
    const defaultName = type === 'json' ? `${id}.theme.json` : 'style.css';
    sendToFusion('export_theme', { file_type: type, content: content, default_name: defaultName });
}

// --- CUSTOM CONFIRM MODAL ---
let pendingConfirmAction = null;
function showConfirmModal(title, message, actionCallback) {
    document.getElementById('confirmModalTitle').innerText = title;
    document.getElementById('confirmModalMessage').innerText = message;
    pendingConfirmAction = actionCallback;
    document.getElementById('confirmModal').style.display = 'flex';
}
function closeConfirmModal() {
    document.getElementById('confirmModal').style.display = 'none';
    pendingConfirmAction = null;
}
function executeConfirmModal() {
    if (pendingConfirmAction) pendingConfirmAction();
    closeConfirmModal();
}

function resetThemeCache() {
    showConfirmModal('Factory Reset', "This will permanently delete all custom imported themes and font overrides. Continue?", function() {
        localStorage.removeItem('LU_custom_themes');
        localStorage.removeItem('LU_theme');
        customThemes = {};
        
        let styleTag = document.getElementById('dynamic-theme-overrides');
        if (styleTag) styleTag.remove();
        
        let importedTag = document.getElementById('imported-style-css');
        if (importedTag) importedTag.remove();
        
        showStatus({message: "Theme cache wiped. Reloading defaults...", type: "success"});
        initThemes('Default Light');
    });
}

function changeTheme() {
    const themeSelector = document.getElementById('themeSelector');
    if (!themeSelector) return;
    const theme = themeSelector.value;
    if (theme === 'Default Light') {
        document.documentElement.removeAttribute('data-theme');
    } else {
        document.documentElement.setAttribute('data-theme', theme);
    }
    localStorage.setItem('LU_theme', theme);

    const currentVars = themes[theme] || {};
    const fontFam = document.getElementById('fontFamilySelector');
    const fontSize = document.getElementById('fontSizeSelector');
    if (fontFam && currentVars['--font-family']) {
        let fam = currentVars['--font-family'].replace(/"/g, "'");
        let match = Array.from(fontFam.options).find(o => o.value === fam);
        if (match) fontFam.value = match.value;
    }
    if (fontSize && currentVars['--font-size-base']) {
        let match = Array.from(fontSize.options).find(o => o.value === currentVars['--font-size-base']);
        if (match) fontSize.value = match.value;
    }
}

function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
    
    const btns = document.querySelectorAll('.tab-btn');
    for(let btn of btns) {
        if(btn.getAttribute('onclick').includes(tabId)) {
            btn.classList.add('active');
            if (btn.scrollIntoView) {
                btn.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
            }
            break;
        }
    }

    const titleEl = document.getElementById('appTitle');
    if (titleEl) {
        if (tabId === 'tab-params') titleEl.innerText = 'LIVE PARAMETERS';
        else if (tabId === 'tab-config') titleEl.innerText = 'LIVE CONFIG';
        else if (tabId === 'tab-changelog') titleEl.innerText = 'CHANGELOG SIDECAR';
        else if (tabId === 'tab-scripts') titleEl.innerText = 'MACRO BOARD';
        else if (tabId === 'tab-themes') titleEl.innerText = 'THEME MANAGER';
    }
    
    localStorage.setItem('LU_activeTab', tabId);
}

function toggleSection(id) {
    document.getElementById(id).classList.toggle('collapsed');
}

window.fusionJavaScriptHandler = {
    handle: function(action, data) {
        try {
            const parsed = typeof data === 'string' ? JSON.parse(data) : data;
            if (action === 'update_ui') renderUI(parsed);
            else if (action === 'notification') showStatus(parsed);
            else if (action === 'theme_imported') {
                if (parsed.file_type === 'css') {
                    const parsedCSS = parseStyleCSS(parsed.content);
                    Object.assign(themes, parsedCSS.themes);
                    Object.assign(customThemes, parsedCSS.themes);
                    localStorage.setItem('LU_custom_themes', JSON.stringify(customThemes));
                    updateThemeDropdown(); 
                    updateStyleTag();
                    
                    // Auto-select the first non-default theme from the imported file
                    const customKeys = Object.keys(parsedCSS.themes).filter(k => k !== "Default Light");
                    const themeSelector = document.getElementById('themeSelector');
                    if (themeSelector && customKeys.length > 0) {
                        themeSelector.value = customKeys[0];
                    }
                    
                    changeTheme();
                    showStatus({message: "CSS Theme(s) Imported Successfully", type: "success"});
                } else if (parsed.file_type === 'json') {
                    try {
                        const themeData = JSON.parse(parsed.content);
                        if (themeData.vars && themeData.id !== undefined) {
                            themes[themeData.id] = themeData.vars;
                            customThemes[themeData.id] = themeData.vars;
                            localStorage.setItem('LU_custom_themes', JSON.stringify(customThemes));
                            updateThemeDropdown(); updateStyleTag();
                            const themeSelector = document.getElementById('themeSelector');
                            if (themeSelector) themeSelector.value = themeData.id;
                            changeTheme();
                            showStatus({message: `Theme '${themeData.id}' Imported`, type: "success"});
                        }
                    } catch(e) { showStatus({message: "Invalid JSON theme format.", type: "error"}); }
                }
            } else if (action === 'selection_changed') {
                currentSelectedGroups = parsed.count;
                const area = document.getElementById('selectedGroupsArea');
                if (currentSelectedGroups > 0) {
                    let html = `<div style="font-size: calc(var(--font-size-base) - 2px); font-weight: bold; margin-bottom: 5px;">Selected Groups (${parsed.count}):</div>`;
                    parsed.names.forEach(name => {
                        html += `<div class="data-row" style="padding: 4px 8px; min-height: unset; margin-bottom: 4px;"><span class="row-label">${name}</span></div>`;
                    });
                    area.innerHTML = html;
                } else {
                    area.innerHTML = `<div class="empty-state" id="regroupEmptyState">Select a contiguous block of grouped features to continue.</div>`;
                }
                validateRegroupState();
            }
        } catch (e) { console.error(e); }
        return "OK";
    }
};

function waitForFusion() {
    if (window.adsk) {
        if (window.adsk.fusion && window.adsk.fusion.on) {
            window.adsk.fusion.on('update_ui', (jsonStr) => renderUI(JSON.parse(jsonStr)));
        }
        refreshData(); 
    } else {
        setTimeout(waitForFusion, 500);
    }
}

function sendToFusion(action, data = {}) {
    data.action = action;
    try {
        const json = JSON.stringify(data);
        if (window.adsk && window.adsk.fusion && window.adsk.fusion.sendCommand) {
            window.adsk.fusion.sendCommand(json);
        } else if (window.adsk && window.adsk.fusionSendData) {
            window.adsk.fusionSendData('send', json);
        }
    } catch (e) {}
}

function refreshData() { sendToFusion('refresh_data'); }

function showStatus(data) {
    const box = document.getElementById('statusMessage');
    box.innerText = data.message;
    box.className = 'status-box ' + (data.type || 'info');
    box.style.display = '';

    if (statusTimeout) clearTimeout(statusTimeout);
    
    if (data.type === 'success' && data.action === 'create_param') {
        document.getElementById('new_name').value = '';
        document.getElementById('new_expr').value = '';
        document.getElementById('new_comm').value = '';
    }

    statusTimeout = setTimeout(() => { box.style.display = 'none'; }, 3000);
}

// --- RENDER MASTER UI ---
function renderUI(data) {
    lastReceivedData = data;
    document.getElementById('docName').innerText = data.doc_name || "Unknown Design";

    // Sort parameters A-Z (case-insensitive)
    if (data.parameters) {
        data.parameters.sort((a, b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase()));
    }
    
    // --- NEW: Sort scripts/plugins A-Z (case-insensitive) ---
    if (data.plugins) {
        data.plugins.sort((a, b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase()));
    }

    renderParameters(data.parameters || []);
    renderConfigs(data.configs || {}, data.active_config, data.is_dirty);
    renderFeatures(data.features || []);
    
    // Pass the newly sorted plugins to the renderer
    renderScripts(data.plugins || []); 
}

function renderParameters(params) {
    const userContainer = document.getElementById('userParamList');
    const modelContainer = document.getElementById('modelParamList');
    const favOnly = document.getElementById('favFilterCheck').checked;
    
    userContainer.innerHTML = '';
    modelContainer.innerHTML = '';

    let visible = params;
    if (favOnly) visible = visible.filter(p => p.isFavorite);
    if (searchQuery) visible = visible.filter(p => p.name.toLowerCase().includes(searchQuery));

    const userParams = visible.filter(p => p.is_user_param);
    const modelParams = visible.filter(p => !p.is_user_param);

    if (userParams.length === 0) {
        userContainer.innerHTML = `<div class="empty-state">No matching user parameters.</div>`;
    } else {
        userParams.forEach(p => userContainer.innerHTML += createParamRow(p));
    }

    if (modelParams.length === 0) {
        modelContainer.innerHTML = `<div class="empty-state">No matching model parameters.</div>`;
    } else {
        modelParams.forEach(p => modelContainer.innerHTML += createParamRow(p));
    }
}

function createParamRow(p) {
    const star = p.isFavorite ? '#ff9e3b' : '#555';
    const safeCommHTML = p.comment ? p.comment.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;') : "";
    const encodedComm = encodeURIComponent(p.comment || "");

    const delBtnHtml = p.is_user_param 
        ? `<button class="action-btn del-btn" title="Delete" onclick="deleteParam('${p.name}')">×</button>`
        : `<button class="action-btn" title="Sketch/Feature parameters cannot be deleted here" disabled style="opacity: 0.3; cursor: not-allowed;">×</button>`;

    return `
        <div class="data-row">
            <div class="row-label" title="${p.name}\n${safeCommHTML}" style="flex: 0 1 40%; margin-right: 5px;">
                <span style="color:${star}; cursor:pointer; margin-right:4px;" onclick="sendToFusion('toggle_favorite', {name: '${p.name}'})">★</span>
                ${p.name}
            </div>
            <div class="row-controls" style="flex: 1 1 70%;">
                <input type="text" value="${p.expression}" style="flex-grow: 1; width: 50px; min-width: 60px;" onchange="sendToFusion('update_param', {name: '${p.name}', value: this.value})">
                <button class="action-btn" title="Edit" onclick="openEditModal('${p.name}', decodeURIComponent('${encodedComm}'))">✎</button>
                ${delBtnHtml}
            </div>
        </div>
    `;
}

function renderConfigs(configs, activeConfig, isDirty) {
    const container = document.getElementById('configList');
    const names = Object.keys(configs).sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
    container.innerHTML = '';

    if (names.length === 0) {
        container.innerHTML = '<div class="empty-state">No snapshots saved.</div>';
        return;
    }

    names.forEach(name => {
        let combinedStyle = 'flex-grow:1; text-align:left; margin-right:5px;';
        let dirtyIndicator = '';
        
        if (name === activeConfig) {
            if (isDirty) {
                combinedStyle += ' border-color: #dc3545; color: #dc3545;';
            dirtyIndicator = '<span style="font-size: calc(var(--font-size-base) - 3px); opacity: 0.8; margin-left: 5px;">(Modified)</span>';
            } else {
                combinedStyle += ' border-color: #28a745; color: #28a745;';
            }
        }
        
        const safeNameDisplay = name.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        const encodedName = encodeURIComponent(name);

        container.innerHTML += `
            <div class="data-row">
                <button class="btn-secondary snapshot-btn" style="${combinedStyle}" onclick="sendToFusion('load_snapshot', {config_name: decodeURIComponent('${encodedName}')})">
                    ${safeNameDisplay}${dirtyIndicator}
                </button>
                <div class="row-controls">
                    <button class="action-btn" title="Rename" onclick="renameSnapshot(decodeURIComponent('${encodedName}'))">✎</button>
                    <button class="action-btn" title="Update" onclick="showConfirmModal('Update Snapshot', 'Update ' + decodeURIComponent('${encodedName}') + '?', function(){ sendToFusion('save_snapshot', {config_name: decodeURIComponent('${encodedName}')}) })">💾</button>
                    <button class="action-btn del-btn" title="Delete" onclick="showConfirmModal('Delete Snapshot', 'Delete ' + decodeURIComponent('${encodedName}') + '?', function(){ sendToFusion('delete_snapshot', {config_name: decodeURIComponent('${encodedName}')}) })">×</button>
                </div>
            </div>
        `;
    });
}

function renderFeatures(features) {
    const container = document.getElementById('featureList');
    container.innerHTML = '';
    
    if (features.length === 0) {
         container.innerHTML = '<div class="empty-state">No CFG_ features found.</div>';
         return;
    }

    features.forEach(f => {
        const checked = !f.isSuppressed ? 'checked' : '';
        container.innerHTML += `
            <div class="data-row">
                <span class="row-label">${f.name}</span>
                <label class="theme-switch" style="transform: scale(0.8); margin-right: 5px;">
                    <input type="checkbox" ${checked} onchange="sendToFusion('toggle_feature', {name: '${f.name}', is_suppressed: !this.checked})">
                    <span class="theme-slider"></span>
                </label>
            </div>
        `;
    });
}

function renderScripts(scripts) {
    const launcherContainer = document.getElementById('scriptLauncherList');
    const managerContainer = document.getElementById('scriptManagerList');
    
    launcherContainer.innerHTML = '';
    managerContainer.innerHTML = '';

    if (!scripts || scripts.length === 0) {
        launcherContainer.innerHTML = '<div class="empty-state">No scripts linked. Open the Script Manager to add some!</div>';
        managerContainer.innerHTML = '<div class="empty-state" style="font-size: calc(var(--font-size-base) - 2px);">No scripts to manage.</div>';
        return;
    }

    scripts.forEach(script => {
        const safeName = script.name.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        const encodedPath = encodeURIComponent(script.path);

        // Updated Launcher Button: Switched to btn-success, reduced padding and font size for a sleeker profile.
        launcherContainer.innerHTML += `
            <button class="btn-success" style="padding: 9px 12px; margin-bottom: 6px; font-size: calc(var(--font-size-base) - 1px); text-align: left; display: flex; align-items: center; justify-content: flex-start; gap: 8px;" onclick="sendToFusion('launch_script', {path: decodeURIComponent('${encodedPath}')})">
                <span style="opacity: 0.8; font-size: calc(var(--font-size-base) - 3px);">▶</span> ${safeName}
            </button>
        `;

        managerContainer.innerHTML += `
            <div class="data-row" style="margin-bottom: 4px;">
                <span class="row-label" title="${script.path}">${safeName}</span>
                <div class="row-controls">
                    <button class="action-btn del-btn" title="Unlink" onclick="showConfirmModal('Unlink Script', 'Unlink ${safeName}?', function(){ sendToFusion('unlink_script', {path: decodeURIComponent('${encodedPath}')}) })">×</button>
                </div>
            </div>
        `;
    });
}

function createParam() {
    const nameField = document.getElementById('new_name').value.trim();
    const exprField = document.getElementById('new_expr').value.trim();

    if (!nameField || !exprField) {
        showStatus({ message: "Name and Expression are required.", type: "error" });
        return;
    }

    const unitSel = document.getElementById('new_unit').value;
    const unit = (unitSel === 'OTHER') ? document.getElementById('custom_unit').value : (unitSel === 'TEXT' ? '' : unitSel);
    
    sendToFusion('create_param', {
        name: nameField,
        unit: unit,
        expression: exprField,
        comment: document.getElementById('new_comm').value.trim()
    });
}

function deleteParam(name) { 
    showConfirmModal('Delete Parameter', `Delete parameter '${name}'?`, function() {
        sendToFusion('delete_param', {name: name});
    });
}
function toggleCustomUnit(sel) { document.getElementById('custom_unit').style.display = (sel.value === 'OTHER') ? 'block' : 'none'; }

function openEditModal(name, comm) {
    document.getElementById('editModalName').value = name;
    document.getElementById('editModalOldName').value = name;
    document.getElementById('editModalComment').value = comm === 'null' ? '' : comm;
    document.getElementById('editModal').style.display = 'flex';
}
function closeEditModal() { document.getElementById('editModal').style.display = 'none'; }
function saveEditModal() {
    sendToFusion('update_attributes', {
        old_name: document.getElementById('editModalOldName').value,
        new_name: document.getElementById('editModalName').value,
        comment: document.getElementById('editModalComment').value
    });
    closeEditModal();
}

function validateRegroupState() {
    const btn = document.getElementById('regroupBtn');
    const nameInput = document.getElementById('newMergedGroupName');
    if (btn && nameInput) {
        if (currentSelectedGroups > 0 && nameInput.value.trim().length > 0) {
            btn.disabled = false;
        } else {
            btn.disabled = true;
        }
    }
}

function mergeSelectedGroups() {
    let newName = document.getElementById('newMergedGroupName').value.trim();
    if (newName) {
        newName = newName.replace(/^CFG_/i, ''); // Strip manually typed prefix
        sendToFusion('merge_groups', { target_name: newName });
        document.getElementById('newMergedGroupName').value = '';
    }
}

function saveSnapshot() {
    const name = document.getElementById('newConfigName').value.trim();
    if(name) {
        sendToFusion('save_snapshot', {config_name: name});
        document.getElementById('newConfigName').value = '';
    }
}

function renameSnapshot(oldName) {
    const newName = prompt(`Rename snapshot '${oldName}' to:`, oldName);
    if (newName && newName.trim() !== '' && newName !== oldName) {
        sendToFusion('rename_snapshot', { old_name: oldName, new_name: newName.trim() });
    }
}

function sendLogEntry() {
    const text = document.getElementById('newEntryText').value;
    if(text) {
        sendToFusion('add_entry', { note: text, autosave: document.getElementById('autosaveCheck').checked });
        document.getElementById('newEntryText').value = '';
    }
}
function createMilestone() {
    const reason = document.getElementById('milestoneReason').value;
    if(reason) {
        sendToFusion('create_milestone', { reason: reason });
        document.getElementById('milestoneReason').value = '';
    }
}
function exportLog() { sendToFusion('export_log'); }

function exportConfigs() {
    sendToFusion('export_configs', {
        step: document.getElementById('expSTEP').checked,
        stl: document.getElementById('expSTL').checked,
        '3mf': document.getElementById('exp3MF').checked
    });
}

// --- MACRO DISPATCHER ---
function linkScript(target) {
    // Hide the modal first
    document.getElementById('linkMacroModal').style.display = 'none';
    // Send the clean event to Python
    sendToFusion('link_external_script', { target: target });
}

function openDashboard() { sendToFusion('refresh_dashboard'); }