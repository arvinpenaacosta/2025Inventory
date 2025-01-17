
    //<!-- EVENT SUBMIT BUTTON - SAVE SCANNED INPUT TO LOCALSTORAGE -->

        const endpoint = 'input1a';
        const serverURL = 'https://192.168.1.3:8856';

        let filename = 'arrianoc.csv';
        
        document.getElementById('submitButton').addEventListener('click', function (event) {
            event.preventDefault();
            handleFormSubmission();
            });


        function formatCurrentDate() {
          const currentDate = new Date();
          const year = currentDate.getFullYear();
          const month = (currentDate.getMonth() + 1).toString().padStart(2, '0');
          const day = currentDate.getDate().toString().padStart(2, '0');
          const hours = currentDate.getHours().toString().padStart(2, '0');
          const minutes = currentDate.getMinutes().toString().padStart(2, '0');
          const seconds = currentDate.getSeconds().toString().padStart(2, '0');

          return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
        }


        // Function to check server status
        function checkServerStatus(serverURL) {
            return fetch(serverURL, { method: 'HEAD' })
                .then(response => {
                    return response.ok;
                })
                .catch(error => {
                    console.error('Error checking server status:', error);
                    return false;
                });
        }


        // Function to send data to server
        function sendDataToServer(newSubmission) {
            // Convert newSubmission object to JSON string
            const jsonData = JSON.stringify(newSubmission);

            // Create XMLHttpRequest object
            const xhr = new XMLHttpRequest();

            // Define endpoint URL
            const endpointURL = 'https://192.168.1.3:8856/input1b/';

            // Open connection
            xhr.open('POST', endpointURL, true);

            // Set request header
            xhr.setRequestHeader('Content-Type', 'application/json');

            // Define onload callback function
            xhr.onload = function () {
                if (xhr.status === 200) {
                    console.log('Data submitted successfully');
                } else {
                    console.error('Error submitting data:', xhr.statusText);
                }
            };

            // Define onerror callback function
            xhr.onerror = function () {
                console.error('Request failed');
            };

            // Send JSON data
            xhr.send(jsonData);
        }



        // SAVE FUNCTION SCANNED INPUT TO LOCALSTORAGE
        function handleFormSubmission() {

            if (document.getElementById('scaninput5').value === '') document.getElementById('scaninput5').value = 'na';
            if (document.getElementById('scaninput6').value === '') document.getElementById('scaninput6').value = 'na';

            const input1Val = document.getElementById('scaninput1').value;
            const input2Val = document.getElementById('scaninput2').value;
            const input3Val = document.getElementById('scaninput3').value;

            const input5Val = document.getElementById('scaninput5').value;
            const input6Val = document.getElementById('scaninput6').value;

            // Call the function to get the formatted date
            const formattedDate = formatCurrentDate();

            let inputString = input2Val;
            let parts = inputString.split('.');

            // Define newSubmission objects for each submission
            const newSubmission1 = {
                'Updateby': input1Val.toUpperCase(),
                'Floor':  parts[0].toUpperCase().toString(),
                'Location1': parts[1].toUpperCase(),
                'Location2': parts[2].toUpperCase(),
                'SerialNumber': input3Val.toUpperCase(),
                'NOCItem' : 'CPU',
                'RecordedDateTime': formattedDate
            };

            const newSubmission2 = {
                'Updateby': input1Val.toUpperCase(),
                'Floor':  parts[0].toUpperCase().toString(),
                'Location1': parts[1].toUpperCase(),
                'Location2': parts[2].toUpperCase(),
                'SerialNumber': input5Val.toUpperCase(),
                'NOCItem' : 'MONITOR1',
                'RecordedDateTime': formattedDate
            };

            const newSubmission3 = {
                'Updateby': input1Val.toUpperCase(),
                'Floor':  parts[0].toUpperCase().toString(),
                'Location1': parts[1].toUpperCase(),
                'Location2': parts[2].toUpperCase(),
                'SerialNumber': input6Val.toUpperCase(),
                'NOCItem' : 'MONITOR2',
                'RecordedDateTime': formattedDate
            };

            // Append each newSubmission object to the CSV individually
            if (newSubmission1.SerialNumber.trim() !==''){
                appendToCSV(newSubmission1, filename);
            }
            if (newSubmission2.SerialNumber.trim() !==''){
                appendToCSV(newSubmission2, filename);
            }
            if (newSubmission3.SerialNumber.trim() !==''){
                appendToCSV(newSubmission3, filename);
            } 






            // Define your data submissions
            const newSubmission11 = {
                'Floor': parts[0].toUpperCase(),
                'Location1': parts[1].toUpperCase(),
                'Location2': parts[2].toUpperCase(),
                'CiscoExt': 'N/A', // Fill in with appropriate value
                'Updateby': input1Val.toUpperCase(), // Fill in with appropriate value
                'ComputerName': 'N/A', // Fill in with appropriate value
                'SerialNumber': input3Val.toUpperCase(),
                'PCModel': 'N/A', // Fill in with appropriate value
                'CPU': 'N/A', // Fill in with appropriate value
                'RAM': 'N/A', // Fill in with appropriate value
                'IPAddress': 'N/A', // Fill in with appropriate value
                'MACAddress': 'N/A', // Fill in with appropriate value
                'WindowsEdition': 'N/A', // Fill in with appropriate value
                'DisplayVersion': 'N/A', // Fill in with appropriate value
                'OSVersion': 'N/A', // Fill in with appropriate value
                'CitrixName': 'N/A', // Fill in with appropriate value
                'CitrixVersion': 'N/A', // Fill in with appropriate value
                'NOCItem': 'CPU', // Fill in with appropriate value
            };

            // Define your data submissions
            const newSubmission22 = {
                'Floor': parts[0].toUpperCase(),
                'Location1': parts[1].toUpperCase(),
                'Location2': parts[2].toUpperCase(),
                'CiscoExt': 'N/A', // Fill in with appropriate value
                'Updateby': input1Val.toUpperCase(), // Fill in with appropriate value
                'ComputerName': 'N/A', // Fill in with appropriate value
                'SerialNumber': input5Val.toUpperCase(),
                'PCModel': 'N/A', // Fill in with appropriate value
                'CPU': 'N/A', // Fill in with appropriate value
                'RAM': 'N/A', // Fill in with appropriate value
                'IPAddress': 'N/A', // Fill in with appropriate value
                'MACAddress': 'N/A', // Fill in with appropriate value
                'WindowsEdition': 'N/A', // Fill in with appropriate value
                'DisplayVersion': 'N/A', // Fill in with appropriate value
                'OSVersion': 'N/A', // Fill in with appropriate value
                'CitrixName': 'N/A', // Fill in with appropriate value
                'CitrixVersion': 'N/A', // Fill in with appropriate value
                'NOCItem': 'MONITOR1', // Fill in with appropriate value
            };

            // Define your data submissions
            const newSubmission33 = {
                'Floor': parts[0].toUpperCase(),
                'Location1': parts[1].toUpperCase(),
                'Location2': parts[2].toUpperCase(),
                'CiscoExt': 'N/A', // Fill in with appropriate value
                'Updateby': input1Val.toUpperCase(), // Fill in with appropriate value
                'ComputerName': 'N/A', // Fill in with appropriate value
                'SerialNumber': input6Val.toUpperCase(),
                'PCModel': 'N/A', // Fill in with appropriate value
                'CPU': 'N/A', // Fill in with appropriate value
                'RAM': 'N/A', // Fill in with appropriate value
                'IPAddress': 'N/A', // Fill in with appropriate value
                'MACAddress': 'N/A', // Fill in with appropriate value
                'WindowsEdition': 'N/A', // Fill in with appropriate value
                'DisplayVersion': 'N/A', // Fill in with appropriate value
                'OSVersion': 'N/A', // Fill in with appropriate value
                'CitrixName': 'N/A', // Fill in with appropriate value
                'CitrixVersion': 'N/A', // Fill in with appropriate value
                'NOCItem': 'MONITOR2', // Fill in with appropriate value
            };


            // Send each newSubmission to the SQLITE Database
            sendDataToServer(newSubmission11);
            sendDataToServer(newSubmission22);
            sendDataToServer(newSubmission33);

            //appendToCSV(newSubmission, filename);
            displaySuccessModal();


            const formData = new FormData();
            formData.append('scaninput1', input1Val);
            formData.append('scaninput2', input2Val);
            formData.append('scaninput3', input3Val);

            formData.append('scaninput5', input5Val);
            formData.append('scaninput6', input6Val);


            document.querySelector('form').reset();

            updateInputsFromQRCode();
        }










    //<!-- SCANNER SCRIPT -->
    
        let html5QrcodeScanner;
        let activeInput;

        const scaninput1Var = document.getElementById('scaninput1');
        const scaninput2Var = document.getElementById('scaninput2');
        const scaninput3Var = document.getElementById('scaninput3');

        const scaninput5Var = document.getElementById('scaninput5');
        const scaninput6Var = document.getElementById('scaninput6');
        
        const revertScanButton = document.getElementById('revert-scan');

        // Get references to the new modal elements
        const noRecordsModal = document.getElementById('no-records-modal');
        const closeNoRecordsModalButton = document.getElementById('close-no-records-modal');



        // Function to display the "No Scanned Records" modal
        function displayNoRecordsModal() {
            noRecordsModal.style.display = 'block';
        }

        // Function to close the "No Scanned Records" modal
        function closeNoRecordsModal() {
            noRecordsModal.style.display = 'none';
        }




        // Get the textarea element
        const textarea = document.getElementById('scaninput3');

        // Attach an event listener for input changes
        textarea.addEventListener('input', function() {
            // Reset the textarea's height to auto to ensure it shrinks if needed
            textarea.style.height = 'auto';

            // Set the textarea's height to the scroll height if it's greater than the default height
            if (textarea.scrollHeight > textarea.clientHeight) {
                textarea.style.height = textarea.scrollHeight + 'px';
            }
        });



        function openScanner(inputId) {
            // Show the QR code scanner
            const qrReader = document.getElementById('qr-reader');
            qrReader.style.display = 'block';

            // Show the "Revert Scanning" button
            revertScanButton.style.display = 'block';

            const qrInput = document.getElementById(inputId);
            qrInput.focus(); // Focus on the input element

            html5QrcodeScanner = new Html5QrcodeScanner(
            "qr-reader", { fps: 20, qrbox: 250 });

            html5QrcodeScanner.render((decodedText, decodedResult) => {
            // Set the scanned data to the input element
            
            //qrInput.value = decodedText;
            //window.alert('Scanned data: ' + decodedText);

            if (inputId === "scaninput2a") {
                let parsedData = decodedText.split('.'); // Parse decodedText
                //qrInput.value = parsedData.join('\n'); // Set value with line breaks
                //window.alert('Scanned data: ' + qrInput.value);
                // Accessing individual elements of parsedData
                let floor = parsedData[0];
                let loc1 = parsedData[1];
                let loc2 = parsedData[2];
                // Continue for additional elements as needed
                qrInput.value = floor + "\n"+ loc1 + "\n"+ loc2 


            } else if  (inputId === "scaninput3a") {
                const parsedData = decodedText.split('|'); // Parse decodedText
                // Accessing individual elements of parsedData
                const hostname = parsedData[5];
                const serial = parsedData[6];
                //const serial = parsedData[6];
                const macadd = parsedData[11];

                 qrInput.value = hostname + "\n"+ serial+ "\n"+ macadd 
                // Continue for additional elements as needed
            } else {
                qrInput.value = decodedText; // Set the decodedText directly
            }


            // Close the scanner after scanning
            closeScanner();
            updateInputsFromQRCode();
            });
        }



        function closeScanner() {
            if (html5QrcodeScanner) {
                html5QrcodeScanner.clear();
                html5QrcodeScanner = null;
            }

            // Hide the QR code scanner
            const qrReader = document.getElementById('qr-reader');
            qrReader.style.display = 'none';

            // Hide the "Revert Scanning" button
            revertScanButton.style.display = 'none';
        }

      






        // Form Element Event Listener
        scaninput1.addEventListener('click', function () {
            const savedProfileModal = new bootstrap.Modal(document.getElementById('savedProfileModal'));
            savedProfileModal.show();

            document.getElementById('profileInput').focus();

        });
            

        function addClickListenerToScanInput(scaninputVar, index) {
            scaninputVar.addEventListener('click', function () {
                activeInput = scaninputVar;
                scaninputVar.value = '';
                openScanner(`scaninput${index}`);
            });
        }

        //addClickListenerToScanInput(scaninput1Var, 1);
        addClickListenerToScanInput(scaninput2Var, 2);
        addClickListenerToScanInput(scaninput3Var, 3);

        addClickListenerToScanInput(scaninput5Var, 5);
        addClickListenerToScanInput(scaninput6Var, 6);



        // Add a click event listener to the "OK" button in the "No Scanned Records" modal
        closeNoRecordsModalButton.addEventListener('click', closeNoRecordsModal);

        // Add a click event listener to the "Revert Scanning" button
        revertScanButton.addEventListener('click', function () {
            closeScanner();
            updateInputsFromQRCode();
            //alert('Closing CameraN/A.'); // For example, display an alert
        });
 

 
    //<!-- VALIDATION for SUBMIT BUTTON if Valid for Submission -->
    
        function updateInputsFromQRCode() {
          const inputchk1 = scaninput1Var.value.trim();
          const inputchk2 = scaninput2Var.value.trim();
          const inputchk3 = scaninput3Var.value.trim();


          const submitButton = document.getElementById('submitButton');

          if (inputchk1 !== '' && inputchk2 !== '' && inputchk3 !== '') {
            // All input fields are filled, enable the submit button
            submitButton.classList.remove('btn-secondary');
            submitButton.classList.add('btn-success');
            submitButton.removeAttribute('disabled');

          } else {
            // At least one input field is empty, disable the submit button and show an error message
            submitButton.classList.remove('btn-success');
            submitButton.classList.add('btn-secondary');
            submitButton.setAttribute('disabled', 'disabled');

          }
        }

    //<!-- SAVING INVENTORY TO LOCALSTORAGE -->
    


        // Get references to elements
        const successModal = document.getElementById('success-modal');
        const closeSuccessModalButton = document.getElementById('close-success-modal');

        // Get references to elements
        const removeCSVButton = document.getElementById('remove-csv-button'); //open confirmation-modal modal
        const confirmationModal = document.getElementById('confirmation-modal');
        const confirmRemoveButton = document.getElementById('confirm-remove');
        const cancelRemoveButton = document.getElementById('cancel-remove');

        const removeProfileButton = document.getElementById('remove-profile-button');


        // Function to display the success modal
        function displaySuccessModal() {
            successModal.style.display = 'block';
        }

        // Function to close the success modal
        function closeSuccessModal() {
            successModal.style.display = 'none';
        }

        // Function to display the modal
        function displayModal() {
            confirmationModal.style.display = 'block';
        }

        // Function to close the modal
        function closeModal() {
            confirmationModal.style.display = 'none';
        }





        // Function to append data to the CSV file
        function appendToCSV(data) {
            const csvData = localStorage.getItem(filename) ? JSON.parse(localStorage.getItem(filename)) : [];
            csvData.push(data);
            localStorage.setItem(filename, JSON.stringify(csvData));
        }

        // Function to remove the CSV data from local storage
        function removeCSVData() {
            localStorage.removeItem(filename);
            // alert('CSV data removed. You can start with a fresh CSV.');
        }

        // Function to convert an array of objects to a CSV string
        function convertArrayOfObjectsToCSV(data) {
            const header = Object.keys(data[0]).join(',');
            const rows = data.map(obj => Object.values(obj).join(','));
            return header + '\n' + rows.join('\n');
        }        




        function downloadAllScannedRecords() {
            const existingData = localStorage.getItem(filename);

            if (existingData) {
                const csvData = JSON.parse(existingData);
                const csvContent = convertArrayOfObjectsToCSV(csvData);

                // Create a Blob with the CSV data
                const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = filename;

                // Trigger a click event on the anchor element to initiate the download
                document.body.appendChild(a);
                a.click();

                // Clean up by removing the temporary URL and the anchor element
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                displayNoRecordsModal(); // Display the "No Scanned Records" modal
                //alert('No scanned records to download.');
            }
        }


   
    //<!-- CLEAR PROFILE TO LOCALSTORAGE -->
    
        // Add a click event listener to the "Download Scanned Records" button
        document.getElementById('download-button').addEventListener('click', function () {
            downloadAllScannedRecords();
        });


        // Add a click event listener to the "Remove CSV Data" button
        removeCSVButton.addEventListener('click', displayModal);

        // Add click event listeners to modal buttons
        confirmRemoveButton.addEventListener('click', function () {
            // Remove CSV data if confirmed
            closeModal();
            removeCSVData();
        });

        cancelRemoveButton.addEventListener('click', closeModal);

        // Add a click event listener to the "Close" button in the success modal
        closeSuccessModalButton.addEventListener('click', closeSuccessModal);

    //<!-- SCRIPT FOR INPUT MODAL ENTRY - BUTTON is Clicked -->
    
        // Set the input field when "Set Value" button is clicked
        document.querySelectorAll('[data-bs-target="#staticBackdrop"]').forEach(function (button) {
            button.addEventListener('click', function() {
                const inputTarget = this.getAttribute('data-input-target');
                const inputValue = document.getElementById(inputTarget).value;
                

                //const label = this.closest('.mb-1').querySelector('.form-label').textContent;
                const label = this.closest('.modal-label').querySelector('.form-label').textContent;

                const modalLabel = document.getElementById('staticBackdropLabel');
                modalLabel.textContent = label;



                //retrieve & set the value of input field
                document.getElementById('setValueButton').setAttribute('data-input-target', inputTarget);
                document.getElementById('modalInput').value = inputValue;

                //set cursor position -select all
                //document.getElementById('modalInput').select();
                //modalInput.select();

                //set cursor position -infront
                document.getElementById('modalInput').setSelectionRange(0, 0);
                //modalInput.setSelectionRange(0, 0);
            });
        });

        // Update the input field when "Set Value" button is clicked
        document.getElementById('setValueButton').addEventListener('click', function() {
            const inputTarget = this.getAttribute('data-input-target');
            const modalInputValue = document.getElementById('modalInput').value;
            document.getElementById(inputTarget).value = modalInputValue.toUpperCase();
            updateInputsFromQRCode()
        });

        // Add event listener to focus the input field when the modal is shown
        document.getElementById('staticBackdrop').addEventListener('shown.bs.modal', function() {
            document.getElementById('modalInput').focus();

        });



























    //<!-- SAVING & CLEARING PROFILE TO LOCALSTORAGE -->
    
        // Retrieve saved profile data from LocalStorage
        const savedProfileData = localStorage.getItem('savedprofiledata');

        if (savedProfileData) {
            // Set the value to an input field (modify 'scaninput1' to the correct ID)
            document.getElementById('scaninput1').value = savedProfileData;
        } else {
            // Open the modal for saved profile data if there's no data
            const savedProfileModal = new bootstrap.Modal(document.getElementById('savedProfileModal'));
            savedProfileModal.show();
        }

        // Add event listener to focus the input field when the modal is shown
        document.getElementById('savedProfileModal').addEventListener('shown.bs.modal', function() {
            document.getElementById('profileInput').focus();
        });

        // Set the input field and save to LocalStorage when "Set Value" button is clicked
        document.getElementById('setProfileValue').addEventListener('click', function() {
            const modalInputValue = document.getElementById('profileInput').value;
            // Save to LocalStorage
            localStorage.setItem('savedprofiledata', modalInputValue);
            // Set the value to scaninput1 (modify 'scaninput1' to the correct ID)
            // document.getElementById('scaninput1').value = modalInputValue;
            // Close the modal
            const savedProfileModal = new bootstrap.Modal(document.getElementById('savedProfileModal'));
            savedProfileModal.hide();
            window.location.reload();
        });



        // Set Profile Input1
        function clearProfileData() {
            const removeProfileModal = new bootstrap.Modal(document.getElementById('deleteProfile'));
            // Optionally, you can provide feedback to the user (e.g., an alert)
            removeProfileModal.show();            
            //alert('Profile data has been cleared.');
        }

        document.getElementById('close-deleteProfile').addEventListener('click', function() {
            localStorage.removeItem('savedprofiledata');
            localStorage.removeItem('HTML5_QRCODE_DATA');
            // Close the modal
            const removeProfileModal = new bootstrap.Modal(document.getElementById('deleteProfile'));
            //removeProfileModal.hide();
            window.location.reload();
        });

        document.getElementById('cancel-deleteProfile').addEventListener('click', function() {
          
            // Close the modal
            const removeProfileModal = new bootstrap.Modal(document.getElementById('deleteProfile'));
            //removeProfileModal.hide();
            window.location.reload();
        });

