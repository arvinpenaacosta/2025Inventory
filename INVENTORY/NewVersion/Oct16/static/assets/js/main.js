let selectedDbName = null;
let dbInstance = null;
let dbList = [];
let dbToDelete = null;
let dbToCreate = null;


// Utility: List all IndexedDB databases (Chrome/Edge/Firefox only)
function listAllDatabases() {
    if (indexedDB.databases) {
        return indexedDB.databases().then(dbs => dbs.map(db => db.name).filter(Boolean));
    }
    return Promise.resolve([]);
}

function hasAssetsStore(dbName) {
    return new Promise(resolve => {
        const req = indexedDB.open(dbName);
        req.onsuccess = function(e) {
            const db = e.target.result;
            const hasStore = db.objectStoreNames.contains('assets');
            console.log(`Checking store for ${dbName}:`, hasStore); // <--- Add this
            db.close();
            resolve(hasStore);
        };
        req.onerror = function() { resolve(false); };
        req.onupgradeneeded = function(e) {
            e.target.transaction.abort();
            resolve(false);
        };
    });
}

function createAssetsDatabase(dbName) {
    return new Promise((resolve, reject) => {
        const req = indexedDB.open(dbName, 1);
        req.onupgradeneeded = function(e) {
            const db = e.target.result;
            const store = db.createObjectStore('assets', { keyPath: 'id', autoIncrement: true });
            store.createIndex('locationIndex', 'location', { unique: false });
        };
        req.onsuccess = function(e) {
            resolve(e.target.result);
        };
        req.onerror = function(e) {
            reject(e.target.error);
        };
    });
}

function deleteDatabase(dbName) {
    return new Promise((resolve, reject) => {
        const req = indexedDB.deleteDatabase(dbName);
        req.onsuccess = () => resolve(true);
        req.onerror = () => reject(false);
        req.onblocked = () => reject(false);
    });
}

function setAssetDbInUse(dbName) {
    localStorage.setItem('assetDBInUse', dbName);
}

function getAssetDbInUse() {
    return localStorage.getItem('assetDBInUse');
}

function updateDbLabel(name) {
    document.getElementById('selectedDbLabel').textContent = name || '';
}


function showModal(id) {
    const modalEl = document.getElementById(id);
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
}
function hideModal(id) {
    const modalEl = document.getElementById(id);
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.hide();
}



// ----------- Modal Logic -----------

// Show database selection modal (onload or manage)
async function showDbManageModal() {
    dbList = [];
    let dbNames = await listAllDatabases();
    for (const name of dbNames) {
        if (await hasAssetsStore(name)) dbList.push(name);
    }
    const dbManageListBody = document.getElementById('dbManageListBody');
    if (dbList.length === 0) {
        dbManageListBody.innerHTML = `<div class="text-center text-muted">No asset databases found.</div>`;
    } else {
        dbManageListBody.innerHTML = dbList.map((name, idx) =>
            `<div class="form-check">
                <input class="form-check-input" type="radio" name="dbManageRadio" id="dbManageRadio${idx}" value="${name}">
                <label class="form-check-label db-list-name" for="dbManageRadio${idx}">${name}</label>
            </div>`
        ).join('');
    }
    document.getElementById('dbManageSelectBtn').disabled = true;
    document.getElementById('dbManageDeleteBtn').disabled = true;
    new bootstrap.Modal(document.getElementById('dbManageModal')).show();
}

// Show create database modal
function showDbCreateModal() {
    document.getElementById('newDbName').value = '';
    new bootstrap.Modal(document.getElementById('dbCreateModal')).show();
}

// Show confirm create modal - dbCreateConfirmModal
function showDbCreateConfirmModal(dbName) {
    dbToCreate = dbName;
    document.getElementById('dbCreateConfirmBody').textContent =
        `Are you sure you want to create a new asset database named "${dbName}"?`;
    new bootstrap.Modal(document.getElementById('dbCreateConfirmModal')).show();
}

// Show confirm delete modal - dbDeleteConfirmModal
function showDbDeleteConfirmModal(dbName) {
    dbToDelete = dbName;
    document.getElementById('dbDeleteConfirmBody').textContent =
        `Are you sure you want to permanently delete the database "${dbName}"? This cannot be undone.`;
    new bootstrap.Modal(document.getElementById('dbDeleteConfirmModal')).show();
}

// ----------- Event Listeners -----------

// On page load: check localStorage, then scan for asset DBs if needed
document.addEventListener('DOMContentLoaded', async () => {
    let dbInUse = getAssetDbInUse();
    console.log('dbInUse from localStorage:', dbInUse); // <--- Add this line
    if (dbInUse && await hasAssetsStore(dbInUse)) {
        selectedDbName = dbInUse;
        document.getElementById('selectedDbLabel').textContent = selectedDbName;
        currentDBName = selectedDbName;
        //window.currentDBName = selectedDbName; // <-- ADD THIS LINE
        try {
            dbInstance = await new Promise((resolve, reject) => {
                const req = indexedDB.open(selectedDbName);
                req.onsuccess = e => resolve(e.target.result);
                req.onerror = e => reject(e.target.error);
            });
        } catch (err) {
            console.error('Error opening DB:', err); // <--- Add this line
            selectedDbName = null;
            document.getElementById('selectedDbLabel').textContent = selectedDbName;
            dbInstance = null;
        }
        console.log('Setting selectedDbName:138', selectedDbName);
        updateDbLabel(selectedDbName);
        if (typeof updateDBDisplay === 'function') updateDBDisplay(); // <-- Optionally add this
    } else {
        showDbManageModal();
    }

    // --- Form validation and UI logic ---
    ['location', 'val1', 'val2', 'val3'].forEach(id => {
        const inputElement = document.getElementById(id);
        if (inputElement) {
            inputElement.addEventListener('input', checkFormValidity);
        }
    });
    checkFormValidity();

    document.getElementById('asset-form').addEventListener('submit', function(e) {
        e.preventDefault();
    });

    document.getElementById('save-button').addEventListener('click', () => {
        const locationValue = document.getElementById('location').value.trim();
        const val1Value = document.getElementById('val1').value.trim();
        const val2Value = document.getElementById('val2').value.trim();
        const val3Value = document.getElementById('val3').value.trim();
        const message = `Inventory Entry Saved!\n\n` + 
                        `Location: ${locationValue}\n` +
                        `Asset ID1 (Scan 1): ${val1Value}\n` +
                        `Asset ID2 (Scan 2): ${val2Value}\n` +
                        `Asset ID3 (Scan 3): ${val3Value}`;
        alert(message);
    });

});

// Database icon click: open manage modal
document.getElementById('databaseBtn').addEventListener('click', async () => {
    showDbManageModal();
});

// Select radio in manage modal
document.getElementById('dbManageListBody').addEventListener('change', (e) => {
    if (e.target.name === 'dbManageRadio') {
        selectedDbName = e.target.value;
        document.getElementById('dbManageSelectBtn').disabled = false;
        document.getElementById('dbManageDeleteBtn').disabled = false;
    }
});

// Select database button
document.getElementById('dbManageSelectBtn').addEventListener('click', async () => {
    if (!selectedDbName) return;
    try {
        dbInstance = await new Promise((resolve, reject) => {
            const req = indexedDB.open(selectedDbName);
            req.onsuccess = e => resolve(e.target.result);
            req.onerror = e => reject(e.target.error);
        });
    } catch (err) {
        // alert("Error opening database: " + err);
        return;
    }
    setAssetDbInUse(selectedDbName);
    currentDBName = selectedDbName; // <-- Place here

    // --- ADD THESE LINES ---
    //window.currentDBName = selectedDbName; // Make sure this matches your global usage
    if (typeof updateDBDisplay === 'function') updateDBDisplay();
    // -----------------------

    console.log('Setting selectedDbName 207:', selectedDbName);
    updateDbLabel(selectedDbName);
    bootstrap.Modal.getInstance(document.getElementById('dbManageModal')).hide();
    // alert(`Selected database: ${selectedDbName}`);
});

// Create new database button
document.getElementById('dbManageCreateBtn').addEventListener('click', () => {
    showDbCreateModal();
});

// Confirm create button in create modal
document.getElementById('dbCreateConfirmBtn').addEventListener('click', () => {
    const dbName = document.getElementById('newDbName').value.trim();
    if (!dbName) {
        // alert('Please enter a database name.');
        return;
    }
    bootstrap.Modal.getInstance(document.getElementById('dbCreateModal')).hide();
    showDbCreateConfirmModal(dbName);
});

// Final create confirmation
document.getElementById('dbCreateFinalBtn').addEventListener('click', async () => {
    if (!dbToCreate) return;
    dbInstance = await createAssetsDatabase(dbToCreate);
    selectedDbName = dbToCreate;
    document.getElementById('selectedDbLabel').textContent = selectedDbName;
    setAssetDbInUse(selectedDbName);
    console.log('Setting selectedDbName:235', selectedDbName);
    updateDbLabel(selectedDbName);
    bootstrap.Modal.getInstance(document.getElementById('dbCreateConfirmModal')).hide();
    // alert(`Created and selected database: ${selectedDbName}`);
    showDbManageModal();
});

// Delete database button
document.getElementById('dbManageDeleteBtn').addEventListener('click', () => {
    if (!selectedDbName) return;
    showDbDeleteConfirmModal(selectedDbName);
});

// Final delete confirmation
document.getElementById('dbDeleteFinalBtn').addEventListener('click', async () => {
    if (!dbToDelete) return;
    if (dbInstance && selectedDbName === dbToDelete) {
        dbInstance.close();
    }
    await deleteDatabase(dbToDelete);
    if (getAssetDbInUse() === dbToDelete) {
        localStorage.removeItem('assetDBInUse');
        updateDbLabel('');
        selectedDbName = null;
        document.getElementById('selectedDbLabel').textContent = selectedDbName;
        dbInstance = null;
    }
    bootstrap.Modal.getInstance(document.getElementById('dbDeleteConfirmModal')).hide();
    // alert(`Deleted database: ${dbToDelete}`);
    showDbManageModal();
});

// --- Existing form validation & UI logic below ---
function checkFormValidity() {
    const location = document.getElementById('location').value.trim();
    const val1 = document.getElementById('val1').value.trim();
    const saveButton = document.getElementById('save-button');
    saveButton.disabled = !(location && val1);
}

