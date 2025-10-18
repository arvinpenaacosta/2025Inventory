let selectedDbName = null;
let dbInstance = null;
let dbList = [];
let dbToDelete = null;
let dbToCreate = null;
window.currentDBName = null;

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
            console.log(`Checking store for ${dbName}:`, hasStore);
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
    showModal('dbManageModal');
}

function showDbCreateModal() {
    document.getElementById('newDbName').value = '';
    showModal('dbCreateModal');
}

function showDbCreateConfirmModal(dbName) {
    dbToCreate = dbName;
    document.getElementById('dbCreateConfirmBody').textContent =
        `Are you sure you want to create a new asset database named "${dbName}"?`;
    showModal('dbCreateConfirmModal');
}

function showDbDeleteConfirmModal(dbName) {
    dbToDelete = dbName;
    document.getElementById('dbDeleteConfirmBody').textContent =
        `Are you sure you want to permanently delete the database "${dbName}"? This cannot be undone.`;
    showModal('dbDeleteConfirmModal');
}

function checkFormValidity() {
    const location = document.getElementById('location').value.trim();
    const val1 = document.getElementById('val1').value.trim();
    const saveButton = document.getElementById('save-button');
    saveButton.disabled = !(location && val1 && window.currentDBName);
}

document.addEventListener('DOMContentLoaded', async () => {
    let dbInUse = getAssetDbInUse();
    console.log('dbInUse from localStorage:', dbInUse);
    if (dbInUse && await hasAssetsStore(dbInUse)) {
        selectedDbName = dbInUse;
        window.currentDBName = selectedDbName;
        document.getElementById('selectedDbLabel').textContent = selectedDbName;
        try {
            dbInstance = await new Promise((resolve, reject) => {
                const req = indexedDB.open(selectedDbName);
                req.onsuccess = e => resolve(e.target.result);
                req.onerror = e => reject(e.target.error);
            });
        } catch (err) {
            console.error('Error opening DB:', err);
            selectedDbName = null;
            window.currentDBName = null;
            document.getElementById('selectedDbLabel').textContent = '';
            dbInstance = null;
        }
        if (typeof updateDBDisplay === 'function') updateDBDisplay();
        if (typeof checkFormValidity === 'function') checkFormValidity();
    } else {
        showDbManageModal();
    }

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
        if (typeof saveEntry === 'function') saveEntry();
    });

    document.getElementById('databaseBtn').addEventListener('click', async () => {
        showDbManageModal();
    });

    document.getElementById('dbManageListBody').addEventListener('change', (e) => {
        if (e.target.name === 'dbManageRadio') {
            selectedDbName = e.target.value;
            document.getElementById('dbManageSelectBtn').disabled = false;
            document.getElementById('dbManageDeleteBtn').disabled = false;
        }
    });

    document.getElementById('dbManageSelectBtn').addEventListener('click', async () => {
        if (!selectedDbName) return;
        try {
            dbInstance = await new Promise((resolve, reject) => {
                const req = indexedDB.open(selectedDbName);
                req.onsuccess = e => resolve(e.target.result);
                req.onerror = e => reject(e.target.error);
            });
        } catch (err) {
            return;
        }
        setAssetDbInUse(selectedDbName);
        window.currentDBName = selectedDbName;
        if (typeof updateDBDisplay === 'function') updateDBDisplay();
        if (typeof checkFormValidity === 'function') checkFormValidity();
        updateDbLabel(selectedDbName);
        hideModal('dbManageModal');
    });

    document.getElementById('dbManageCreateBtn').addEventListener('click', () => {
        showDbCreateModal();
    });

    document.getElementById('dbCreateConfirmBtn').addEventListener('click', () => {
        const dbName = document.getElementById('newDbName').value.trim();
        if (!dbName) {
            return;
        }
        hideModal('dbCreateModal');
        showDbCreateConfirmModal(dbName);
    });

    document.getElementById('dbCreateFinalBtn').addEventListener('click', async () => {
        if (!dbToCreate) return;
        dbInstance = await createAssetsDatabase(dbToCreate);
        selectedDbName = dbToCreate;
        window.currentDBName = dbToCreate;
        document.getElementById('selectedDbLabel').textContent = selectedDbName;
        setAssetDbInUse(selectedDbName);
        updateDbLabel(selectedDbName);
        hideModal('dbCreateConfirmModal');
        showDbManageModal();
    });

    document.getElementById('dbManageDeleteBtn').addEventListener('click', () => {
        if (!selectedDbName) return;
        showDbDeleteConfirmModal(selectedDbName);
    });

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
            window.currentDBName = null;
            document.getElementById('selectedDbLabel').textContent = '';
            dbInstance = null;
        }
        hideModal('dbDeleteConfirmModal');
        showDbManageModal();
    });
});

window.showDbManageModal = showDbManageModal;
window.checkFormValidity = checkFormValidity;