$(document).ready(function () {
  const table = new DataTable('#daTable', {
    ajax: {
      url: '/items', // Fetch data from /items endpoint
      dataSrc: '' // Use a flat array directly
    },
    columns: [
      {
        className: 'dt-control',
        orderable: false,
        data: null,
        defaultContent: ''
      },
      { data: 'id' },
      { data: 'serial_number' },
      { data: 'description' },
      { data: 'location' },
      { data: 'itypes' },
      { data: 'brand' },
      { data: 'model' },
      { data: 'stampTime' }
    ],
    paging: false,
    scrollCollapse: true,
    scrollY: '400px',
    order: [[1, 'asc']]
  });

  // Add event listener for clicking on the child row control
  $('#daTable tbody').on('click', 'td.dt-control', function () {
    const tr = $(this).closest('tr');
    const row = table.row(tr);


    // Update the modal title dynamically
    $('#dynamicModalLabel').text(`Details for ID :  ${row.data().id}`);

    // Generate table content and inject it into the modal body
    const modalContent = format(row.data());
    $('#dynamicModal .modal-body').html(modalContent);
    $('#dynamicModal').modal('show'); // Show the modal
  });
});


// Function to handle modal actions
function handleModalAction(id, action) {
  // Close the dynamicModal
  $('#dynamicModal').modal('hide');

  // Small delay to ensure the modal closes completely
  setTimeout(() => {
    if (action === 'delete') {
      openDelModal(id, 'delete'); // Call the delete modal action
    } else {
      openModal(id, action); // Call the desired modal action (new, modify, clone)
    }
  }, 300); // Adjust delay as needed
}

// Function to generate table content
function format(d) {
  return `
  <div class="container ">
      <div class="card" style="width:400px ; border: 1px solid #1610bc74; border-radius: 18px; padding: 15px; margin-bottom:0px; font-size: 0.875rem;">
          <div class="card-header d-flex justify-content-between align-items-center" 
          style="background-color: #1610bc74; color: rgb(15, 1, 1); font-weight: bold;">
          <span id="dynamicModalLabel">Todo @ ID : ${d.id}</span> <!-- Title aligned to the left -->

              <div style="display: flex; gap: 15px;" class="ms-auto"> <!-- Icons aligned to the right -->
                  <i class="bi bi-file-earmark-plus icon-large" style="font-size: 1.2rem;" 
                      onclick="handleModalAction(null, 'new')" data-bs-toggle="tooltip" title="Create New"></i>
                  <i class="bi bi-pencil-square icon-large" style="font-size: 1.2rem;" 
                      onclick="handleModalAction(${d.id}, 'modify')" data-bs-toggle="tooltip" title="Modify"></i>
                  <i class="bi bi-copy icon-large" style="font-size: 1.2rem;" 
                      onclick="handleModalAction(${d.id}, 'clone')" data-bs-toggle="tooltip" title="Clone"></i>
                  <i class="bi bi-trash3 icon-large" style="font-size: 1.2rem;" 
                      onclick="handleModalAction(${d.id}, 'delete')" data-bs-toggle="tooltip" title="Delete"></i>
              </div>

          </div> 
          <p style="margin-top:20px ; margin-bottom: 0;"><strong>Other Informations</strong></p>   
          <div class="card-body">
          <div style="display: grid; grid-template-columns: 1fr 1.5fr; gap: 5px; align-items: center;">
              <p style="margin-bottom: 0;"><strong>Status:</strong></p> <p style="margin-bottom: 0;">${d.status || 'N/A'}</p>
              <p style="margin-bottom: 0;"><strong>MAC Address:</strong></p> <p style="margin-bottom: 0;">${d.macadd || 'N/A'}</p>
              <p style="margin-bottom: 0;"><strong>Remarks:</strong></p> <p style="margin-bottom: 0;">${d.remarks || 'N/A'}</p>
              <p style="margin-bottom: 0;"><strong>Switch:</strong></p> <p style="margin-bottom: 0;">${d.swtich || 'N/A'}</p>
              <p style="margin-bottom: 0;"><strong>Timestamp:</strong></p> <p style="margin-bottom: 0;">${d.stampTime || 'N/A'}</p>
          </div>
          </div>
      </div>
  </div>`

}

// Add Bootstrap modal structure to the HTML
$(document.body).append(`
  <div class="modal fade"  id="dynamicModal" tabindex="-1" aria-labelledby="dynamicModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered " style="max-width: 480px; "> 
     <div class="modal-content" style="border-radius: 30px;">

        <div class="modal-body p-4">
          <!-- Table content will be injected here -->
        </div>

      </div>
    </div>
  </div>
`);
