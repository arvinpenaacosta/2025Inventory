
        // Function to format the child row data with headers
        function formatChildRow(data) {
            return '<table class="child-table table table-bordered">' +
                '<thead>' +
                    '<tr>' +
                        '<th>Log User</th>' +
                        '<th>Model</th>' +
                        '<th>Processor</th>' +
                        '<th>RAM Speed</th>' +
                        '<th>IP Address</th>' +
                        '<th>MAC Address</th>' +
                        '<th>Timestamp</th>' +
                    '</tr>' +
                '</thead>' +
                '<tbody>' +
                    '<tr>' +
                        '<td>' + (data.log_user || '') + '</td>' +
                        '<td>' + (data.model || '') + '</td>' +
                        '<td>' + (data.processor || '') + '</td>' +
                        '<td>' + (data.ram_speed || '') + '</td>' +
                        '<td>' + (data.ip_address || '') + '</td>' +
                        '<td>' + (data.mac_address || '') + '</td>' +
                        '<td>' + (data.timestamp || '') + '</td>' +
                    '</tr>' +
                '</tbody>' +
                '</table>';
        }

        $(document).ready(function() {
            const table = $('#example').DataTable({
                data: tableData,
                columns: [
                    {
                        className: 'details-control',
                        orderable: false,
                        data: null,
                        defaultContent: `
                            <svg class="expand-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path d="M12 4V20M4 12H20" stroke="#333" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            <svg class="collapse-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path d="M4 12H20" stroke="#333" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        `
                    },
                    { data: 'id' },
                    { data: 'floor' },
                    { data: 'loc1' },
                    { data: 'loc2' },
                    { data: 'hostname' },
                    { data: 'serial_number' },
                    { data: 'windows_version' },
                    { data: 'windows_display_version' },
                    { data: 'total_ram' },
                    { data: 'ram_per_slot' },
                    { data: 'ram_type' },
                    { data: 'citrix_name' },
                    { data: 'citrix_version' }
                ],
                scrollX: true,
                scrollY: '400px',
                scrollCollapse: true,
                paging: false,
                responsive: true,
                initComplete: function () {
                    this.api()
                        .columns([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
                        .every(function () {
                            let column = this;
                            let title = column.footer().textContent;

                            // Create input element with Bootstrap classes
                            let input = document.createElement('input');
                            input.placeholder = title;
                            input.className = 'form-control form-control-sm';
                            column.footer().replaceChildren(input);

                            // Event listener for user input
                            input.addEventListener('keyup', () => {
                                if (column.search() !== input.value) {
                                    column.search(input.value).draw();
                                }
                            });
                        });
                }
            });

            // Add event listener for opening and closing child rows
            $('#example tbody').on('click', 'td.details-control', function () {
                let tr = $(this).closest('tr');
                let row = table.row(tr);

                if (row.child.isShown()) {
                    row.child.hide();
                    tr.removeClass('shown');
                } else {
                    row.child(formatChildRow(row.data())).show();
                    tr.addClass('shown');
                }
            });

            // Dark/Light mode toggle
            $('#modeToggle').on('click', function() {
                $('body').toggleClass('dark-mode');
                const isDarkMode = $('body').hasClass('dark-mode');
                $(this).find('.sun-icon').toggleClass('d-none', isDarkMode);
                $(this).find('.moon-icon').toggleClass('d-none', !isDarkMode);
                $(this).find('span').text(isDarkMode ? 'Light Mode' : 'Dark Mode');
            });

            // Export button functionality (export to CSV)
            $('#exportBtn').on('click', function() {
                let csvContent = "ID,Floor,Location 1,Location 2,Hostname,Serial Number,Windows Version,Windows Display Version,Model,Processor,Total RAM,RAM Type,Log User,RAM per Slot,RAM Speed,IP Address,MAC Address,Citrix Name,Citrix Version,Timestamp\n";
                tableData.forEach(row => {
                    csvContent += `"${row.id}","${row.floor}","${row.loc1}","${row.loc2}","${row.hostname}","${row.serial_number}","${row.windows_version}","${row.windows_display_version}","${row.model}","${row.processor}","${row.total_ram}","${row.ram_type}","${row.log_user}","${row.ram_per_slot}","${row.ram_speed}","${row.ip_address}","${row.mac_address}","${row.citrix_name}","${row.citrix_version}","${row.timestamp}"\n`;
                });
                const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                const link = document.createElement('a');
                const url = URL.createObjectURL(blob);
                link.setAttribute('href', url);
                link.setAttribute('download', 'system_inventory.csv');
                link.style.visibility = 'hidden';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            });
        });
