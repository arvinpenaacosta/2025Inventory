let pendingRecord = null;
const OBJECT_STORE_NAME = "assets";

// Utility: Format timestamp in local time (UTC+8)
function formatLocalTimestamp(date) {
    return date.toLocaleString('en-US', {
        timeZone: 'Asia/Hong_Kong',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        fractionalSecondDigits: 3,
        hour12: false
    });
}

// Utility: Show/hide modal
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

// Utility: Show status message (simple toast)
function showStatusMessage(message, isError = false) {
    const openModals = document.querySelectorAll('.modal.show');
    openModals.forEach(modal => {
        bootstrap.Modal.getInstance(modal)?.hide();
    });
    
    let box = document.getElementById('message-box');
    if (!box) {
        box = document.createElement('div');
        box.id = 'message-box';
        box.style.position = 'fixed';
        box.style.top = '80px';
        box.style.left = '50%';
        box.style.transform = 'translateX(-50%)';
        box.style.zIndex = '9999';
        box.style.padding = '12px 24px';
        box.style.borderRadius = '8px';
        box.style.color = '#fff';
        box.style.fontWeight = 'bold';
        box.style.display = 'none';
        document.body.appendChild(box);
    }
    box.textContent = message;
    box.style.backgroundColor = isError ? '#dc3545' : '#28a745';
    box.style.display = 'block';
    setTimeout(() => { box.style.display = 'none'; }, 2000);
}

// Reset UI to initial state
function resetUIToInitialState() {
    document.getElementById('resultsOutput').style.display = 'none';
    document.getElementById('save-button-container').style.display = 'none';
    document.getElementById('button-container').style.display = 'flex';
    document.getElementById('asset-form').reset();
    if (window.checkFormValidity) window.checkFormValidity();
}

// Update database label
function updateDBDisplay() {
    document.getElementById('selectedDbLabel').textContent = window.currentDBName || '';
}

// Main save process
function saveEntry(callback) {
    if (!window.currentDBName) {
        showStatusMessage("Please select or create a database first.", true);
        if (typeof window.showDbManageModal === 'function') window.showDbManageModal();
        if (typeof callback === 'function') callback();
        return;
    }
    const form = document.getElementById('asset-form');
    const currentValues = {
        location: form.location.value.trim(),
        device1: form.val1.value.trim(),
        device2: form.val2.value.trim(),
        device3: form.val3.value.trim()
    };
    if (!currentValues.location || !currentValues.device1) {
        showStatusMessage("Location and Asset ID1 are required.", true);
        if (typeof callback === 'function') callback();
        return;
    }
    searchAndValidate(currentValues, callback);
}

// Search for previous record and validate
function searchAndValidate(currentValues, callback) {
    const request = indexedDB.open(window.currentDBName);
    request.onsuccess = function(event) {
        const db = event.target.result;
        if (!db.objectStoreNames.contains(OBJECT_STORE_NAME)) {
            db.close();
            showStatusMessage(`Error: Store '${OBJECT_STORE_NAME}' not found.`, true);
            if (typeof callback === 'function') callback();
            return;
        }
        const transaction = db.transaction(OBJECT_STORE_NAME, 'readonly');
        const store = transaction.objectStore(OBJECT_STORE_NAME);
        const index = store.index && store.index('locationIndex') ? store.index('locationIndex') : store;
        const getAllReq = index.getAll(IDBKeyRange.only(currentValues.location));
        getAllReq.onsuccess = function(e) {
            const results = e.target.result;
            console.log("Search results:", results);
            if (!results || results.length === 0) {
                db.close();
                saveRecordDirectly(currentValues, "As Is", callback);
            } else {
                const latestRecord = results.reduce((max, record) =>
                    (record.timestamp > max.timestamp ? record : max), results[0]);
                db.close();
                compareAndConfirm(latestRecord, currentValues, callback);
            }
        };
        getAllReq.onerror = function(e) {
            db.close();
            showStatusMessage("Error searching for existing records.", true);
            if (typeof callback === 'function') callback();
        };
    };
    request.onerror = function(event) {
        showStatusMessage("Failed to connect to the selected database.", true);
        if (typeof callback === 'function') callback();
    };
}

// Compare previous and current values, set status, show confirmation
function compareAndConfirm(previousRecord, currentValues, callback) {
    const prevValues = [
        previousRecord.device1,
        previousRecord.device2,
        previousRecord.device3
    ].filter(v => v && v.trim() !== '').map(v => v.toLowerCase());
    const currValues = [
        currentValues.device1,
        currentValues.device2,
        currentValues.device3
    ].filter(v => v && v.trim() !== '').map(v => v.toLowerCase());
    
    const additions = currValues
        .filter(v => !prevValues.includes(v))
        .filter(v => typeof v === 'string')
        .map(v => v.trim().toUpperCase());
    const removals = prevValues
        .filter(v => !currValues.includes(v))
        .map(v => String(v).trim().toUpperCase());

    let detectedStatus = "";
    if (additions.length === 0 && removals.length === 0) {
        detectedStatus = "As Is";
    } else if (additions.length > 0 && removals.length === 0) {
        detectedStatus = `Update: ${additions.join(", ")} Added to the Asset`;
    } else if (removals.length > 0 && additions.length === 0) {
        detectedStatus = `Update: ${removals.join(", ")} Removed from the Asset`;
    } else {
        detectedStatus = `Update: ${additions.join(", ")} replaced ${removals.join(", ")}`;
    }
    pendingRecord = {
        location: currentValues.location,
        device1: currentValues.device1,
        device2: currentValues.device2,
        device3: currentValues.device3,
        status: detectedStatus,
        timestamp: formatLocalTimestamp(new Date())
    };
    document.getElementById('confirm-location').textContent = currentValues.location;
    document.getElementById('confirm-previous').textContent =
        `${previousRecord.device1 || '(empty)'}, ${previousRecord.device2 || '(empty)'}, ${previousRecord.device3 || '(empty)'}`;
    document.getElementById('confirm-current').textContent =
        `${currentValues.device1 || '(empty)'}, ${currentValues.device2 || '(empty)'}, ${currentValues.device3 || '(empty)'}`;
    document.getElementById('confirm-status').textContent = detectedStatus;
    showModal('confirm-modal');
    pendingRecord.callback = callback;
}

// Save after confirmation
function confirmAndSave() {
    if (!pendingRecord) {
        showStatusMessage("No pending record to save.", true);
        return;
    }
    const callback = pendingRecord.callback;
    const request = indexedDB.open(window.currentDBName);
    request.onsuccess = function(event) {
        const db = event.target.result;
        const transaction = db.transaction(OBJECT_STORE_NAME, 'readwrite');
        const store = transaction.objectStore(OBJECT_STORE_NAME);
        const addRequest = store.add(pendingRecord);
        addRequest.onsuccess = function(e) {
            showStatusMessage(`Asset entry saved for ${pendingRecord.location}.`);
            hideModal('confirm-modal');
            pendingRecord = null;
            resetUIToInitialState();
            if (typeof callback === 'function') callback();
        };
        addRequest.onerror = function(e) {
            showStatusMessage("Error saving data.", true);
            if (typeof callback === 'function') callback();
        };
        transaction.oncomplete = () => db.close();
        transaction.onerror = () => db.close();
    };
    request.onerror = function(event) {
        showStatusMessage("Failed to connect to the selected database.", true);
        if (typeof callback === 'function') callback();
    };
}

// Cancel confirmation
function cancelSave() {
    const callback = pendingRecord?.callback;
    hideModal('confirm-modal');
    pendingRecord = null;
    showStatusMessage("Save operation cancelled.");
    if (typeof callback === 'function') callback();
}

// Save directly if no previous record
function saveRecordDirectly(currentValues, status, callback) {
    const record = {
        location: currentValues.location,
        device1: currentValues.device1,
        device2: currentValues.device2,
        device3: currentValues.device3,
        status: status,
        timestamp: formatLocalTimestamp(new Date())
    };
    const request = indexedDB.open(window.currentDBName);
    request.onsuccess = function(event) {
        const db = event.target.result;
        const transaction = db.transaction(OBJECT_STORE_NAME, 'readwrite');
        const store = transaction.objectStore(OBJECT_STORE_NAME);
        const addRequest = store.add(record);
        addRequest.onsuccess = function(e) {
            showStatusMessage(`Asset entry saved for ${record.location}.`);
            resetUIToInitialState();
            if (typeof callback === 'function') callback();
        };
        addRequest.onerror = function(e) {
            showStatusMessage("Error saving data.", true);
            if (typeof callback === 'function') callback();
        };
        transaction.oncomplete = () => db.close();
        transaction.onerror = () => db.close();
    };
    request.onerror = function(event) {
        showStatusMessage("Failed to connect to the selected database.", true);
        if (typeof callback === 'function') callback();
    };
}

// Disable Create New button when dbCreateModal is shown
const dbManageModal = document.getElementById('dbManageModal');
const dbCreateModal = document.getElementById('dbCreateModal');
const dbManageCreateBtn = document.getElementById('dbManageCreateBtn');

dbCreateModal.addEventListener('shown.bs.modal', function () {
    dbManageCreateBtn.disabled = true;
});

dbCreateModal.addEventListener('hidden.bs.modal', function () {
    dbManageCreateBtn.disabled = false;
});