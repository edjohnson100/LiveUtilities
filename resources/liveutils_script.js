// --- GLOBAL STATE ---
let lastReceivedData = null;
let searchQuery = "";
let statusTimeout;

document.addEventListener('DOMContentLoaded', function() {
    // 1. Theme Initialization
    const toggleSwitch = document.getElementById('theme-checkbox');
    const savedTheme = localStorage.getItem('edj_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    toggleSwitch.checked = (savedTheme === 'dark');
    toggleSwitch.addEventListener('change', e => {
        const newTheme = e.target.checked ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('edj_theme', newTheme);
    });

    // 2. Tab Memory
    const savedTab = localStorage.getItem('edj_active_tab') || 'tab-params';
    switchTab(savedTab);

    // 3. Listeners
    document.getElementById('favFilterCheck').addEventListener('change', e => {
        if (lastReceivedData) renderUI(lastReceivedData);
    });
    document.getElementById('searchInput').addEventListener('input', e => {
        searchQuery = e.target.value.toLowerCase();
        if (lastReceivedData) renderUI(lastReceivedData);
    });

    waitForFusion();
});

// --- UI NAVIGATION ---
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
    
    // Find matching button
    const btns = document.querySelectorAll('.tab-btn');
    for(let btn of btns) {
        if(btn.getAttribute('onclick').includes(tabId)) {
            btn.classList.add('active');
            break;
        }
    }

    // --- NEW DYNAMIC TITLE LOGIC ---
    const titleEl = document.getElementById('appTitle');
    if (titleEl) {
        if (tabId === 'tab-params') titleEl.innerText = 'LIVE PARAMETERS';
        else if (tabId === 'tab-config') titleEl.innerText = 'LIVE CONFIG';
        else if (tabId === 'tab-changelog') titleEl.innerText = 'CHANGELOG SIDECAR';
    }
    
    localStorage.setItem('edj_active_tab', tabId);
}

function toggleSection(id) {
    document.getElementById(id).classList.toggle('collapsed');
}

// --- FUSION BRIDGE ---

// 1. Declare the handler globally FIRST so Python never hits a ReferenceError
window.fusionJavaScriptHandler = {
    handle: function(action, data) {
        try {
            const parsed = typeof data === 'string' ? JSON.parse(data) : data;
            if (action === 'update_ui') renderUI(parsed);
            else if (action === 'notification') showStatus(parsed);
        } catch (e) { console.error(e); }
        return "OK";
    }
};

// 2. Then wait for the adsk object to initialize to send the refresh command
function waitForFusion() {
    if (window.adsk) {
        // Optional modern event listener binding
        if (window.adsk.fusion && window.adsk.fusion.on) {
            window.adsk.fusion.on('update_ui', (jsonStr) => renderUI(JSON.parse(jsonStr)));
        }
        // Ask Python for the initial data payload
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

// --- STATUS NOTIFICATIONS ---
function showStatus(data) {
    const box = document.getElementById('statusMessage');
    box.innerText = data.message;
    box.className = 'status-box ' + (data.type || 'info');
    
    // Clear the inline style from the previous timeout so the CSS class takes over
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

    renderParameters(data.parameters || []);
    renderConfigs(data.configs || {}, data.active_config, data.is_dirty); // Added data.is_dirty here
    renderFeatures(data.features || []);
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

    // Split into our two categories using the flag from Python
    const userParams = visible.filter(p => p.is_user_param);
    const modelParams = visible.filter(p => !p.is_user_param);

    // Render User Params
    if (userParams.length === 0) {
        userContainer.innerHTML = `<div class="empty-state">No matching user parameters.</div>`;
    } else {
        userParams.forEach(p => userContainer.innerHTML += createParamRow(p));
    }

    // Render Model Params
    if (modelParams.length === 0) {
        modelContainer.innerHTML = `<div class="empty-state">No matching model parameters.</div>`;
    } else {
        modelParams.forEach(p => modelContainer.innerHTML += createParamRow(p));
    }
}

// Helper function to build the HTML string for a single parameter row
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
    const names = Object.keys(configs);
    container.innerHTML = '';

    if (names.length === 0) {
        container.innerHTML = '<div class="empty-state">No snapshots saved.</div>';
        return;
    }

    names.forEach(name => {
        // Start with the base layout styling
        let combinedStyle = 'flex-grow:1; text-align:left; margin-right:5px;';
        let dirtyIndicator = '';
        
        // Append the Green/Red styling based on the dirty flag
        if (name === activeConfig) {
            if (isDirty) {
                combinedStyle += ' border-color: #dc3545; color: #dc3545;'; // Red for dirty
                dirtyIndicator = '<span style="font-size: 10px; opacity: 0.8; margin-left: 5px;">(Modified)</span>';
            } else {
                combinedStyle += ' border-color: #28a745; color: #28a745;'; // Green for clean
            }
        }
        
        const safeNameDisplay = name.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        const encodedName = encodeURIComponent(name);

        container.innerHTML += `
            <div class="data-row">
                <button class="btn-secondary" style="${combinedStyle}" onclick="sendToFusion('load_snapshot', {config_name: decodeURIComponent('${encodedName}')})">
                    ${safeNameDisplay}${dirtyIndicator}
                </button>
                <div class="row-controls">
                    <button class="action-btn" title="Rename" onclick="renameSnapshot(decodeURIComponent('${encodedName}'))">✎</button>
                    <button class="action-btn" title="Update" onclick="if(confirm('Update ' + decodeURIComponent('${encodedName}') + '?')) sendToFusion('save_snapshot', {config_name: decodeURIComponent('${encodedName}')})">💾</button>
                    <button class="action-btn del-btn" title="Delete" onclick="if(confirm('Delete ' + decodeURIComponent('${encodedName}') + '?')) sendToFusion('delete_snapshot', {config_name: decodeURIComponent('${encodedName}')})">×</button>
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

// --- ACTION DISPATCHERS ---

// Parameters
function createParam() {
    const nameField = document.getElementById('new_name').value.trim();
    const exprField = document.getElementById('new_expr').value.trim();

    // Prevent submission if required fields are empty
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

function deleteParam(name) { if(confirm(`Delete parameter '${name}'?`)) sendToFusion('delete_param', {name: name}); }
function toggleCustomUnit(sel) { document.getElementById('custom_unit').style.display = (sel.value === 'OTHER') ? 'block' : 'none'; }

// Modal Logic
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

// Config
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

// Changelog
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

function openDashboard() { sendToFusion('refresh_dashboard'); }