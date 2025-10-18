
    // --- VALIDATION FUNCTION ---
    /**
     * Enables the Save button if the Location and Asset ID1 (val1) fields are filled.
     */
    function checkFormValidity() {
        const location = document.getElementById('location').value.trim();
        const val1 = document.getElementById('val1').value.trim();
        const saveButton = document.getElementById('save-button');

        // REQUIRED: Location AND Asset ID1 (val1)
        const requiredFieldsFilled = location && val1;

        // Enable or disable the save button based on the check
        saveButton.disabled = !requiredFieldsFilled;
    }


    // --- BATCH SCAN CONFIGURATION ---
    const MAX_SCANS = 4;
    const PAUSE_DURATION_MS = 1000; // 1 seconds pause
    const DUPLICATE_MESSAGE_DURATION_MS = 2000; // 2 seconds for duplicate error

    // --- GLOBAL STATE ---
    let html5QrCode = null;
    let currentScanCount = 0;
    let isScanning = false;
    let isProcessing = false; // Flag to prevent rapid multi-scan during pause/process

    // --- ELEMENT REFERENCES ---
    const appContainer = document.getElementById("appContainer");
    const searchBtn = document.getElementById("searchBtn");
    const scannerModalEl = document.getElementById("scannerModal");
    const scanModalTitle = document.getElementById("scanModalTitle");
    const closeScannerBtn = document.getElementById("closeScannerBtn");
    const pauseOverlay = document.getElementById("pauseOverlay");
    const stopScanBtn = document.getElementById("stopScanBtn"); 
    const duplicateMessageBox = document.getElementById("duplicateMessageBox");
    const duplicateSerialText = document.getElementById("duplicateSerialText");

    // Array to hold references to the four new input elements
    const tempOutputs = [
        document.getElementById("location"),
        document.getElementById("val1"),
        document.getElementById("val2"),
        document.getElementById("val3"),
    ];

    // --- AUDIO HELPER FUNCTION ---
    function playSound(audioId) {
        const audio = document.getElementById(audioId);
        if (audio) {
            audio.pause();
            audio.currentTime = 0;
            audio.play().catch(e => console.error("Error playing sound:", e));
        }
    }

    // --- UI UPDATES ---
    function updateScanStatus(isFinal = false) { 
        appContainer.classList.toggle('scanning-active', !isFinal);
        appContainer.classList.toggle('scanning-complete', isFinal);
    }

    function updateModalStatus(step) {
        if (duplicateMessageBox.style.display === 'none') {
            scanModalTitle.textContent = `Scanning Serial (${step} of ${MAX_SCANS})`;
        }
    }

    function showDuplicateError(serial) {
        playSound('cancel-sound');
        duplicateSerialText.textContent = `Value: ${serial}`;
        duplicateMessageBox.style.display = 'block';
        
        // Set a timeout to clear the error message
        setTimeout(() => {
            duplicateMessageBox.style.display = 'none';
            if(isScanning && !isProcessing) { 
                updateModalStatus(currentScanCount + 1);
            }
        }, DUPLICATE_MESSAGE_DURATION_MS);
    }

    /**
     * Stops the scanning process, closes the modal, and returns to the main UI.
     * @param {boolean} isCancelled - True if manually cancelled via modal close button.
     */
    function stopBatchScan(isCancelled = false) {
        stopScanner().finally(() => { 
            const scanModal = bootstrap.Modal.getInstance(scannerModalEl);
            if (scanModal) scanModal.hide(); // Close scanner modal
            
            isScanning = false;
            isProcessing = false;

            // Fill remaining empty fields with N/A
            if (currentScanCount < MAX_SCANS) {
                for (let i = currentScanCount; i < MAX_SCANS; i++) {
                    if (tempOutputs[i].value === '') { 
                        tempOutputs[i].value = 'N/A';
                    }
                }
            }
            
            if (isCancelled) {
                    playSound('cancel-sound'); 
            } 
            
            // Ensure the stop button is hidden upon return
            stopScanBtn.style.display = 'none';
            updateScanStatus(true); // Final state
            
            // >> IMPORTANT: Check validity after inputs are finalized/N/A'd
            checkFormValidity();
        });
    }

    // --- CORE LOGIC: Handle Scanned Serial ---
    function handleScanSuccess(serial) {
        if (isProcessing) return; // Ignore subsequent scans while processing
        isProcessing = true;
        
        const trimmedSerial = serial.trim().replace(/[\r\n]+/g, "").replace(/^"|"$/g, "");

        // --- DUPLICATE CHECK LOGIC ---
        const existingValues = tempOutputs.slice(0, currentScanCount).map(input => input.value);
        if (existingValues.includes(trimmedSerial)) {
            isProcessing = false; // Allow next scan immediately
            showDuplicateError(trimmedSerial);
            
            // Resume scanning immediately
            if (html5QrCode && html5QrCode.getState() !== 1) { 
                    html5QrCode.resume();
            }
            return; // EXIT: Do not proceed with capture or pause logic
        }
        // --- END DUPLICATE CHECK ---

        currentScanCount++;
        
        console.log(`Captured Serial #${currentScanCount} (Temp${currentScanCount}): ${trimmedSerial}`);
        
        // Place scanned value into the correct individual input field
        if (currentScanCount > 0 && currentScanCount <= MAX_SCANS) {
            tempOutputs[currentScanCount - 1].value = trimmedSerial;
        }

        // 1. Play sound
        playSound('beep-sound');

        // 2. Check if batch is complete
        if (currentScanCount >= MAX_SCANS) {
            // Batch complete (Final logic)
            stopScanner().finally(() => { 
                const scanModal = bootstrap.Modal.getInstance(scannerModalEl);
                if (scanModal) scanModal.hide(); // Close scanner modal
                
                isScanning = false;
                isProcessing = false;

                // Reset UI to final state (all 4 inputs are filled)
                updateScanStatus(true); // Final state
                // >> IMPORTANT: Check validity after inputs are finalized
                checkFormValidity();
            });
            
        } else {
            // Check for mid-batch stop condition (After 2nd scan)
            if (currentScanCount >= 2) {
                stopScanBtn.style.display = 'block'; // Show the stop button
                updateModalStatus(currentScanCount + 1);
            } else {
                updateModalStatus(currentScanCount + 1);
            }

            // Show pause feedback overlay
            pauseOverlay.style.display = 'flex';
            
            // Temporarily disable detection
            if (html5QrCode) {
                    html5QrCode.pause(true); 
            }
            
            // Pause duration is still 1.5 seconds
            setTimeout(() => {
                pauseOverlay.style.display = 'none'; // Hide pause feedback

                // Re-enable detection process after the pause
                if (html5QrCode) {
                    html5QrCode.resume();
                }

                // Update modal title for the next scan.
                updateModalStatus(currentScanCount + 1);
                
                updateScanStatus(false); // Scanning state (simplified)
                
                isProcessing = false; // Allow the next scan to be captured
            }, PAUSE_DURATION_MS);
        }
    }

    /* ---- QR SCANNER LOGIC ---- */

    function startScanner() {
        if (isScanning) {
            updateModalStatus(currentScanCount + 1);
            return;
        }

        const scanModal = new bootstrap.Modal(scannerModalEl);
        scanModal.show();
        
        isScanning = true;
        
        if (!html5QrCode) {
            html5QrCode = new Html5Qrcode("qr-reader");
        }
        
        // Initial title update
        updateModalStatus(currentScanCount + 1);

        html5QrCode
            .start(
                { facingMode: "environment" },
                { fps: 10, qrbox: 250 },
                (txt) => handleScanSuccess(txt),
                (err) => console.log("scan error:", err)
            )
            .catch((err) => {
                console.error("QR start error", err);
                const modal = bootstrap.Modal.getInstance(scannerModalEl);
                if (modal) modal.hide();
                resetState(); // Simplified reset
            });
    }

    function stopScanner() {
        if (html5QrCode) {
            return html5QrCode
                .stop()
                .then(() => {
                    html5QrCode = null;
                })
                .catch((err) => console.error("stop error:", err));
        }
        return Promise.resolve();
    }

    function resetState() { 
        currentScanCount = 0;
        isScanning = false;
        isProcessing = false;
        
        // Clear all four input fields on reset
        tempOutputs.forEach(input => input.value = '');
        
        updateScanStatus(true);
        appContainer.classList.remove('scanning-active');
        appContainer.classList.add('scanning-complete');
        pauseOverlay.style.display = 'none';
        stopScanBtn.style.display = 'none'; // Ensure stop button is hidden
        duplicateMessageBox.style.display = 'none'; // Ensure duplicate message is hidden
        
        // >> IMPORTANT: Check validity after reset (should disable the button)
        checkFormValidity();
    }

    // --- EVENT LISTENERS ---

    // 1. Initial Setup on Load
    document.addEventListener('DOMContentLoaded', () => {
        
        // Attach listeners to all four fields so typing/scanning in any field triggers the check
        const inputIds = ['location', 'val1', 'val2', 'val3'];
        const saveButton = document.getElementById('save-button');
        const databaseButton = document.getElementById('databaseBtn'); // New button reference

        inputIds.forEach(id => {
            const inputElement = document.getElementById(id);
            if (inputElement) {
                // The 'input' event fires whenever the value of the element changes (typing, scanning, pasting)
                inputElement.addEventListener('input', checkFormValidity);
            }
        });

        resetState(); // Clear fields and perform initial check (which disables the button)

        // Set up the form submit handler
        document.getElementById('asset-form').addEventListener('submit', function(e) {
            e.preventDefault();
            // In a real application, you would call a saveEntry() function here
        });

        // Save button click handler (remains the same)
        saveButton.addEventListener('click', () => {
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

        // Placeholder listener for the new database button
        databaseButton.addEventListener('click', () => {
            alert('Database button clicked! Ready for your instruction.');
        });
    });

    // 2. Start Batch Scan Button
    searchBtn.addEventListener("click", () => {
        // Reset state for a new batch
        resetState(); 
        document.getElementById("resultsOutput").style.display = 'block';
        
        // Transition to scanning state
        updateScanStatus(false);
        startScanner();
    });

    // 3. Stop Batch Scan Button (Manual Completion/Early Exit)
    stopScanBtn.addEventListener("click", () => {
        stopBatchScan(false); // Manually stop and accept captured scans
    });

    // 4. Close Scanner Button (Manual Cancellation)
    closeScannerBtn.addEventListener("click", () => {
        // Treat closing the modal using the X button as a cancellation
        stopBatchScan(true); 
    });

