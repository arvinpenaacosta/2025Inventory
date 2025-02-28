
    //<!-- EVENT SUBMIT BUTTON - SAVE SCANNED INPUT TO LOCALSTORAGE -->

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

          return `${year}${month}${day} ${hours}:${minutes}:${seconds}`;
        }


        // SAVE FUNCTION SCANNED INPUT TO LOCALSTORAGE


        function handleFormSubmission() {
            if (document.getElementById('scaninput4').value === '') document.getElementById('scaninput4').value = 'na';
            if (document.getElementById('scaninput5').value === '') document.getElementById('scaninput5').value = 'na';

            const input1Val = document.getElementById('scaninput1').value;
            const input2Val = document.getElementById('scaninput2').value;
            const input3Val = document.getElementById('scaninput3').value;
            const input4Val = document.getElementById('scaninput4').value;
            const input5Val = document.getElementById('scaninput5').value;



            // Call the function to get the formatted date
            const formattedDate = formatCurrentDate();

            let inputString = input2Val;
            let parts = inputString.split('.');

            // Define newSubmission objects for each submission
            const newSubmission1 = {
                'NOC ID/User': input1Val,
                'Floor':  parts[0],
                'Location1': parts[1],
                'Location2': parts[2],
                'Serial Number': input3Val,
                'Type' : 'CPU',
                'Date Scanned': formattedDate
            };

            const newSubmission2 = {
                'NOC ID/User': input1Val,
                'Floor':  parts[0],
                'Location1': parts[1],
                'Location2': parts[2],
                'Serial Number': input5Val,
                'Type' : 'Monitor1',
                'Date Scanned': formattedDate
            };

            const newSubmission3 = {
                'NOC ID/User': input1Val,
                'Floor':  parts[0],
                'Location1': parts[1],
                'Location2': parts[2],
                'Serial Number': input6Val,
                'Type' : 'Monitor2',
                'Date Scanned': formattedDate
            };

            // Append each newSubmission object to the CSV individually
            appendToCSV(newSubmission1, filename);
            appendToCSV(newSubmission2, filename);
            appendToCSV(newSubmission3, filename);


            //appendToCSV(newSubmission, filename);
            displaySuccessModal();

            const formData = new FormData();
            formData.append('scaninput1', input1Val);
            formData.append('scaninput2', input2Val);
            formData.append('scaninput3', input3Val);
            formData.append('scaninput4', input4Val);
            formData.append('scaninput5', input5Val);


            // Append keyboard and mouse values to formData
            formData.append('keyboard', keyboardVal);
            formData.append('mouse', mouseVal);

            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/upload', true);
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

            xhr.onload = function () {
                if (xhr.status === 200) {
                    console.log(xhr.responseText);
                } else {
                    console.error('Error:', xhr.status, xhr.statusText);
                }
            };

            xhr.send(formData);

            document.querySelector('form').reset();

            updateInputsFromQRCode();
        }




    //<!-- SCANNER SCRIPT -->
    
        let html5QrcodeScanner;
        let activeInput;

        const scaninput1Var = document.getElementById('scaninput1');
        const scaninput2Var = document.getElementById('scaninput2');

        const scaninput3Var = document.getElementById('scaninput3');
        const scaninput4Var = document.getElementById('scaninput4');
        const scaninput5Var = document.getElementById('scaninput5');


        
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

        function toggleScanner(inputId) {
            if (!html5QrcodeScanner) {
                openScanner(inputId);
            } else {
                closeScanner();
            }
        }

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
            qrInput.value = decodedText;

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
        addClickListenerToScanInput(scaninput4Var, 4);
        addClickListenerToScanInput(scaninput5Var, 5);



        // Add a click event listener to the "OK" button in the "No Scanned Records" modal
        closeNoRecordsModalButton.addEventListener('click', closeNoRecordsModal);

        // Add a click event listener to the "Revert Scanning" button
        revertScanButton.addEventListener('click', function () {
            closeScanner();
            updateInputsFromQRCode();
            //alert('Closing Camera....'); // For example, display an alert
        });
 
    //<!-- VALIDATION for SUBMIT BUTTON if Valid for Submission -->
    
        function updateInputsFromQRCode() {
          const inputchk3 = scaninput3Var.value.trim();
          const inputchk4 = scaninput4Var.value.trim();
          const inputchk5 = scaninput5Var.value.trim();


          const submitButton = document.getElementById('submitButton');

          if (inputchk3 !== '' && inputchk4 !== '' && inputchk5 !== '') {
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

        // Function to remove the CSV data from local storage
        function removeCSVData() {
            localStorage.removeItem(filename);
            // alert('CSV data removed. You can start with a fresh CSV.');
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

        // Function to append data to the CSV file
        function appendToCSV(data) {
            const csvData = localStorage.getItem(filename) ? JSON.parse(localStorage.getItem(filename)) : [];
            csvData.push(data);
            localStorage.setItem(filename, JSON.stringify(csvData));
        }



        // Function to convert an array of objects to a CSV string
        function convertArrayOfObjectsToCSV(data) {
            const header = Object.keys(data[0]).join(',');
            const rows = data.map(obj => Object.values(obj).join(','));
            return header + '\n' + rows.join('\n');
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

