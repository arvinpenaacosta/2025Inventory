
    let currentDBName = null; // Set this when a DB is selected
    const OBJECT_STORE_NAME = "assets";
    let pendingRecord = null;

    // Utility: Show/hide modal
    function showModal(id) {
        document.getElementById(id).style.display = 'flex';
    }
    function hideModal(id) {
        document.getElementById(id).style.display = 'none';
    }

    // Utility: Show status message (simple toast)
    function showStatusMessage(message, isError = false) {
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
        setTimeout(() => { box.style.display = 'none'; }, 3000);
    }

    // Enable/disable save button based on DB selection
    function updateDBDisplay() {
        document.getElementById('save-button').disabled = !currentDBName;
        document.getElementById('selectedDbLabel').textContent = currentDBName || '';
    }

    // Main save process
    function saveEntry() {
        if (!currentDBName) {
            showStatusMessage("Please select or create a database first.", true);
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
            return;
        }
        searchAndValidate(currentValues);
    }

    // Search for previous record and validate
    function searchAndValidate(currentValues) {
        const request = indexedDB.open(currentDBName);
        request.onsuccess = function(event) {
            const db = event.target.result;
            if (!db.objectStoreNames.contains(OBJECT_STORE_NAME)) {
                db.close();
                showStatusMessage(`Error: Store '${OBJECT_STORE_NAME}' not found.`, true);
                return;
            }
            const transaction = db.transaction(OBJECT_STORE_NAME, 'readonly');
            const store = transaction.objectStore(OBJECT_STORE_NAME);
            // Find latest record for this location
            const index = store.index && store.index('locationIndex') ? store.index('locationIndex') : store;
            const getAllReq = index.getAll(IDBKeyRange.only(currentValues.location));
            getAllReq.onsuccess = function(e) {
                const results = e.target.result;
                if (!results || results.length === 0) {
                    db.close();
                    saveRecordDirectly(currentValues, "As Is");
                } else {
                    // Use latest record (by timestamp or id)
                    const latestRecord = results.reduce((max, record) =>
                        (record.timestamp > max.timestamp ? record : max), results[0]);
                    db.close();
                    compareAndConfirm(latestRecord, currentValues);
                }
            };
            getAllReq.onerror = function(e) {
                db.close();
                showStatusMessage("Error searching for existing records.", true);
            };
        };
        request.onerror = function(event) {
            showStatusMessage("Failed to connect to the selected database.", true);
        };
    }

    // Compare previous and current values, set status, show confirmation
    function compareAndConfirm(previousRecord, currentValues) {
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
        const additions = currValues.filter(v => !prevValues.includes(v));
        const removals = prevValues.filter(v => !currValues.includes(v));
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
            timestamp: new Date().toISOString()
        };
        document.getElementById('confirm-location').textContent = currentValues.location;
        document.getElementById('confirm-previous').textContent =
            `${previousRecord.device1 || '(empty)'}, ${previousRecord.device2 || '(empty)'}, ${previousRecord.device3 || '(empty)'}`;
        document.getElementById('confirm-current').textContent =
            `${currentValues.device1 || '(empty)'}, ${currentValues.device2 || '(empty)'}, ${currentValues.device3 || '(empty)'}`;
        document.getElementById('confirm-status').textContent = detectedStatus;
        showModal('confirm-modal');
    }

    // Save after confirmation
    function confirmAndSave() {
        if (!pendingRecord) {
            showStatusMessage("No pending record to save.", true);
            return;
        }
        const request = indexedDB.open(currentDBName);
        request.onsuccess = function(event) {
            const db = event.target.result;
            const transaction = db.transaction(OBJECT_STORE_NAME, 'readwrite');
            const store = transaction.objectStore(OBJECT_STORE_NAME);
            const addRequest = store.add(pendingRecord);
            addRequest.onsuccess = function(e) {
                showStatusMessage(`Asset entry saved for ${pendingRecord.location}.`);
                document.getElementById('asset-form').reset();
                hideModal('confirm-modal');
                pendingRecord = null;
            };
            addRequest.onerror = function(e) {
                showStatusMessage("Error saving data.", true);
            };
            transaction.oncomplete = () => db.close();
            transaction.onerror = () => db.close();
        };
        request.onerror = function(event) {
            showStatusMessage("Failed to connect to the selected database.", true);
        };
    }

    // Cancel confirmation
    function cancelSave() {
        hideModal('confirm-modal');
        pendingRecord = null;
        showStatusMessage("Save operation cancelled.");
    }

    // Save directly if no previous record
    function saveRecordDirectly(currentValues, status) {
        const record = {
            location: currentValues.location,
            device1: currentValues.device1,
            device2: currentValues.device2,
            device3: currentValues.device3,
            status: status,
            timestamp: new Date().toISOString()
        };
        const request = indexedDB.open(currentDBName);
        request.onsuccess = function(event) {
            const db = event.target.result;
            const transaction = db.transaction(OBJECT_STORE_NAME, 'readwrite');
            const store = transaction.objectStore(OBJECT_STORE_NAME);
            const addRequest = store.add(record);
            addRequest.onsuccess = function(e) {
                showStatusMessage(`Asset entry saved for ${record.location}.`);
                document.getElementById('asset-form').reset();
            };
            addRequest.onerror = function(e) {
                showStatusMessage("Error saving data.", true);
            };
            transaction.oncomplete = () => db.close();
            transaction.onerror = () => db.close();
        };
        request.onerror = function(event) {
            showStatusMessage("Failed to connect to the selected database.", true);
        };
    }

    // Attach save button handler
    document.getElementById('save-button').addEventListener('click', saveEntry);

    // Disable Create New button when dbCreateModal is shown
    const dbManageModal = document.getElementById('dbManageModal');
    const dbCreateModal = document.getElementById('dbCreateModal');
    const dbManageCreateBtn = document.getElementById('dbManageCreateBtn');

    dbCreateModal.addEventListener('shown.bs.modal', function () {
        dbManageCreateBtn.disabled = true;
    });

    // Re-enable Create New button when dbCreateModal is hidden
    dbCreateModal.addEventListener('hidden.bs.modal', function () {
        dbManageCreateBtn.disabled = false;
    });

    // Call updateDBDisplay() after DB selection elsewhere in your code
