// --- QR SCANNER LOGIC & BATCH SCAN HANDLING ---
const MAX_SCANS = 4;
const PAUSE_DURATION_MS = 1000;
const DUPLICATE_MESSAGE_DURATION_MS = 2000;

let html5QrCode = null;
let currentScanCount = 0;
let isScanning = false;
let isProcessing = false;

const scannerModalEl = document.getElementById("scannerModal");
const scanModalTitle = document.getElementById("scanModalTitle");
const pauseOverlay = document.getElementById("pauseOverlay");
const stopScanBtn = document.getElementById("stopScanBtn");
const duplicateMessageBox = document.getElementById("duplicateMessageBox");
const duplicateSerialText = document.getElementById("duplicateSerialText");
const appContainer = document.getElementById("appContainer");
const tempOutputs = [
    document.getElementById("location"),
    document.getElementById("val1"),
    document.getElementById("val2"),
    document.getElementById("val3"),
];

function playSound(audioId) {
    const audio = document.getElementById(audioId);
    if (audio) {
        audio.pause();
        audio.currentTime = 0;
        audio.play().catch(e => console.error("Error playing sound:", e));
    }
}

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
    setTimeout(() => {
        duplicateMessageBox.style.display = 'none';
        if(isScanning && !isProcessing) { 
            updateModalStatus(currentScanCount + 1);
        }
    }, DUPLICATE_MESSAGE_DURATION_MS);
}

function stopBatchScan(isCancelled = false) {
    stopScanner().finally(() => { 
        const scanModal = bootstrap.Modal.getInstance(scannerModalEl);
        if (scanModal) scanModal.hide();
        isScanning = false;
        isProcessing = false;
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
        stopScanBtn.style.display = 'none';
        updateScanStatus(true);
        if (window.checkFormValidity) checkFormValidity();
    });
}

function handleScanSuccess(serial) {
    if (isProcessing) return;
    isProcessing = true;
    const trimmedSerial = serial.trim().replace(/[\r\n]+/g, "").replace(/^"|"$/g, "");
    const existingValues = tempOutputs.slice(0, currentScanCount).map(input => input.value);
    if (existingValues.includes(trimmedSerial)) {
        isProcessing = false;
        showDuplicateError(trimmedSerial);
        if (html5QrCode && html5QrCode.getState() !== 1) { 
            html5QrCode.resume();
        }
        return;
    }
    currentScanCount++;
    if (currentScanCount > 0 && currentScanCount <= MAX_SCANS) {
        tempOutputs[currentScanCount - 1].value = trimmedSerial;
    }
    playSound('beep-sound');
    if (currentScanCount >= MAX_SCANS) {
        stopScanner().finally(() => { 
            const scanModal = bootstrap.Modal.getInstance(scannerModalEl);
            if (scanModal) scanModal.hide();
            isScanning = false;
            isProcessing = false;
            updateScanStatus(true);
            if (window.checkFormValidity) checkFormValidity();
        });
    } else {
        if (currentScanCount >= 2) {
            stopScanBtn.style.display = 'block';
            updateModalStatus(currentScanCount + 1);
        } else {
            updateModalStatus(currentScanCount + 1);
        }
        pauseOverlay.style.display = 'flex';
        if (html5QrCode) {
            html5QrCode.pause(true); 
        }
        setTimeout(() => {
            pauseOverlay.style.display = 'none';
            if (html5QrCode) {
                html5QrCode.resume();
            }
            updateModalStatus(currentScanCount + 1);
            updateScanStatus(false);
            isProcessing = false;
        }, PAUSE_DURATION_MS);
    }
}

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
            resetState();
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
    tempOutputs.forEach(input => input.value = '');
    updateScanStatus(true);
    appContainer.classList.remove('scanning-active');
    appContainer.classList.add('scanning-complete');
    pauseOverlay.style.display = 'none';
    stopScanBtn.style.display = 'none';
    duplicateMessageBox.style.display = 'none';
    if (window.checkFormValidity) checkFormValidity();
}

// --- QR Scan Event Listeners ---
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById("searchBtn").addEventListener("click", () => {
        resetState(); 
        document.getElementById("resultsOutput").style.display = 'block';
        updateScanStatus(false);
        startScanner();
    });
    stopScanBtn.addEventListener("click", () => {
        stopBatchScan(false);
    });
    document.getElementById("closeScannerBtn").addEventListener("click", () => {
        stopBatchScan(true); 
    });
});