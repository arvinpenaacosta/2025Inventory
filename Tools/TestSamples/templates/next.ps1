# Load required assemblies

# Get the current working directory
$currentDirectory = Get-Location

# Concatenate the current working directory with \.env
$firstBat = Join-Path -Path $currentDirectory -ChildPath "test1.bat"
$firstBat


Start-Process -FilePath "$firstBat" -NoNewWindow -Wait


Cls
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing


# HTML content

$htmlContent = @"
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">

<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Centered Table</title>
<style>
    body {
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        min-height: 100vh;
    }

    /* Container with glass effect */
    .container {
        background: rgba(255, 255, 255, 0.2); /* Transparent white */
        border-radius: 30px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3); /* Shadow effect */
        backdrop-filter: blur(10px); /* Glass effect */
        -webkit-backdrop-filter: blur(10px); /* Safari support */
        max-width: 800px; /* Increase container width */
        margin: auto; /* Center the container horizontally */
        margin-top: 20px; /* Add margin to the top */
        margin-bottom: 20px; /* Add margin to the bottom */
    }

    /* Table styles */
    table {
        border-collapse: collapse;
        width: 100%;
        font-size: smaller; /* Set font size to smaller */
    }

    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
        font-size: .9em;
    }

    th:first-child, td:first-child {
        width: 35%; /* First column width */
    }

    th:last-child, td:last-child {
        width: 85%; /* Second column width */
    }

    th {
        background-color: #f2f2f2;
    }

    /* Hover effect for table rows */
    tr:hover {
        background-color: #f5f5f5; /* Change the background color on hover */
    }

    .footer {
        background-color: #f0f0f0;
        padding: 10px;
        text-align: center;
        /* Positioning */
        position: fixed;
        bottom: 0;
        width: 100%;
    }

</style>


</head>
<body>

<div class="container">
    <h2 class="inline-elements" style="margin-bottom: 10px;">$CompName System Info</h2>
 
    <table>
        <thead>
            <tr>
                <th>Fields</th>
                <th>Informations</th>
            </tr>
        </thead>
        <tbody>
            <!-- 15 rows and 2 columns -->
	 		<tr>
	            <td>Floor</td>
	            <td>$PODFloor</td>
	        </tr>
	        <tr>
	            <td>Location</td>
	            <td>$Location</td>
	        </tr>
	        <tr>
	            <td>UpdateBy</td>
	            <td>$Updateby </td>
	        </tr>
	        <tr>
	            <td>Computer Name</td>
	            <td>$CompName</td>
	        </tr>
	        <tr>
	            <td>Serial Number</td>
	            <td>$SerNum</td>
	        </tr>
	        <tr>
	            <td>PC Model</td>
	            <td>$PCModel</td>
	        </tr>
	        <tr>
	            <td>CPU Type</td>
	            <td>$CPUName</td>
	        </tr>
	        <tr>
	            <td>Memory</td>
	            <td>$Ram</td>
	        </tr>
	        <tr>
	            <td>IPAddress</td>
	            <td>$ipAddress</td>
	        </tr>
	        <tr>
	            <td>Mac Address</td>
	            <td>$macVal</td>
	        </tr>

	        <tr>
	            <td>Window Edition</td>
	            <td>$WinEdition</td>
	        </tr>
	        <tr>
	            <td>Window Version</td>
	            <td>$displayVersion</td>
	        </tr>
	        <tr>
	            <td>Window OS Num</td>
	            <td>$OSVer</td>
	        </tr>
	        <tr>
	            <td>Citrix Name</td>
	            <td>$CitrixDisplayName</td>
	        </tr>
	        <tr>
	            <td>Citrix Ver</td>
	            <td>$CitrixDisplayVersion</td>
	        </tr>
	        <tr>
	            <td>Inventory Date</td>
	            <td>$formattedDate</td>
	        </tr>
        </tbody>
    </table>
        
</div>

<div class="footer">
    &copy; 2024 VinTools. All rights reserved.
</div>

</body>
</html>
"@

# Define a function to execute Restart-Computer -Force
function Restart-ComputerForce {
    #Restart-Computer -Force
    Write-Host "+   REBOOT PROCESS HERE...   +" 
}

# Function to display HTML content and open Thank You form after submission
function Show-HtmlPageAndThankYouForm {
    param (
        [string]$HtmlContent
    )

    # Create a temporary HTML file
    $htmlFilePath = [System.IO.Path]::GetTempFileName() + ".html"
    $HtmlContent | Set-Content -Path $htmlFilePath -Encoding UTF8

    # Create a form to display HTML content
    $htmlForm = New-Object System.Windows.Forms.Form
    $htmlForm.Text = "VinTools Sys Info Collector"
    $htmlForm.Size = New-Object System.Drawing.Size(600,750)
    $htmlForm.MaximizeBox = $false  # Disable maximize button
    $htmlForm.MinimizeBox = $false  # Disable minimize button
    $htmlForm.StartPosition = "CenterScreen"  # Center the form on the screen

    # Create a web browser control
    $webBrowser = New-Object System.Windows.Forms.WebBrowser
    $webBrowser.Location = New-Object System.Drawing.Point(0, -20)
    $webBrowser.Size = New-Object System.Drawing.Size(600, 700)
    $webBrowser.Navigate($htmlFilePath)

    # Variable to track if the submit button was clicked
    $submitClicked = $false




    # Add FormClosing event handler to clean up resources
    $htmlForm.Add_FormClosing({
        if (-not $submitClicked) {
            $result = [System.Windows.Forms.MessageBox]::Show("Do you want to Reboot or No.?", "Warning", [System.Windows.Forms.MessageBoxButtons]::YesNo)
            if ($result -eq "Yes") {
                # Add code here to perform reboot
                Restart-ComputerForce
            } else {
                # Add code here to close the script or perform any other action
            }
        }
        if ($_.Cancel -ne $true) {
            $htmlForm.Dispose()
            $htmlForm.Close()
        }
    })

    # Add web browser control to the form
    $htmlForm.Controls.Add($webBrowser)

    # Show HTML form
    $htmlForm.ShowDialog() | Out-Null

    # Clean up - delete temporary HTML file
    Remove-Item -Path $htmlFilePath
}

# Show HTML page and open Thank You form after submission
Show-HtmlPageAndThankYouForm -HtmlContent $htmlContent


