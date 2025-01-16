[Important Files Needed]
.env
<app>.bat

============================================
[.env]


ENABLE_CSV = true   --> Enable Saving to CSV File. If not Available then, false.
ENABLE_SQL = true   --> Enable Saving to SQLite Database. Server must be Started. If not Available then, false.

# For CSV File Saving
CSV_FOLDER = TMOB_CSV               --> specify CSV folder name
CSV_FILE = TMOB_inv1.csv            --> specify CSV filename
NET_CONN = ETHERNET                 --> specify NIC (ETHERNET for LAN / WIFI* for Wifi)

# For SQLITE Database Connection and Saving
INVENTORY_SVR_HOST = 192.168.1.18   --> Specify Server Host IP
INVENTORY_SVR_PORT = 8892           --> Specify Server Port


NOTES:
============================================
# Add below line ## to running batch file to run

@echo off
net use X: /delete /y
net use X: <path where the running app is located> /PERSISTENT:NO
X:

sample:
X		is the specified Drive Letter to Map
net use		Command for mapping drive folder
net use X: \\ltop8672\devshared\REMOTE /PERSISTENT:NO


if any of ENABLE_SQL and ENABLE_CSV is missing. Default is False
	ENABLE_SQL = true
	ENABLE_CSV = true




@echo off
net use V: /delete /y 
net use V: \\LTOP8672\devshared\INVENTORY /PERSISTENT:NO
V:

@echo off
--> remove existing mapped drive
--> Mapped the network drive to X: with no Persistent (\\LTOP8672\devshared\Inventory --> Specify the correct shared folder location
--> go to mapped drive letter (Where X is the assigned Drive Letter to Map)


SOURCE CODE
============================================
[source code] Note: Batch File should be =< 32KB when converted

# THIS IS WORKING 2025
function Show-InventoryBanner {
cls
Write-Host ""
Write-Host "++++++++++++++++++++++++++++++++++++++" -ForegroundColor Green
Write-Host "+              2 0 2 5               +" -ForegroundColor Green
Write-Host "+           V I N T O O L S          +" -ForegroundColor Green
Write-Host "+                                    +" -ForegroundColor Green
Write-Host "+      INVENTORY RECORDER Rev.1      +" -ForegroundColor Green
Write-Host "++++++++++++++++++++++++++++++++++++++" -ForegroundColor Green
Write-Host ""
}
function Read-EnvFile {
    param (
        [string]$FilePath
    )
    $envContent = Get-Content -Path $FilePath
    $envVariables = @{}

    foreach ($line in $envContent) {
        if (-not ($line -match '^\s*#') -and -not [string]::IsNullOrWhiteSpace($line)) {
            $key, $value = $line -split '=', 2
            $key = $key.Trim()
            $value = $value.Trim()
            $envVariables[$key] = $value
        }
    }
    return $envVariables
}
function Prompt-ValidInput {
    param (
        [string]$message,
        [string[]]$validInputs
    )
    do {
        $response = Read-Host $message
        $response = $response.ToUpper() # Convert input to uppercase

        if (-not ($validInputs -contains $response)) {
            [System.Windows.Forms.MessageBox]::Show("Invalid input. Please enter a valid value: P, A, C, B, E, T, O", "Error", "OK", "Error")
        }
    } while (-not ($validInputs -contains $response))
    return $response
}
function Prompt-MacMoa {
    param (
        [string]$message,
        [string[]]$MacMoa
    )
    do {
        $response = Read-Host $message
        $response = $response.ToUpper() # Convert input to uppercase

        if (-not ($MacMoa -contains $response)) {
            [System.Windows.Forms.MessageBox]::Show("Invalid input. Please enter a valid value: Mac / MOA", "Error", "OK", "Error")
        }
    } while (-not ($MacMoa -contains $response))
    return $response
}
function Show-RebootPrompt {
    Add-Type -AssemblyName System.Windows.Forms
    $result = [System.Windows.Forms.MessageBox]::Show(
        "Do you want to reboot?",   # Message text
        "Warning",                  # MessageBox title
        [System.Windows.Forms.MessageBoxButtons]::YesNo
    )
    if ($result -eq [System.Windows.Forms.DialogResult]::Yes) { 
        Restart-Computer -Force
    } 
}
Show-InventoryBanner
$currentDirectory = Get-Location
$envFilePath = Join-Path -Path $currentDirectory -ChildPath ".env"
$envVariables = Read-EnvFile -FilePath $envFilePath

$env_enaSQL = [bool]($envVariables["ENABLE_SQL"])
$env_enaCSV = [bool]($envVariables["ENABLE_CSV"])
$env_HOST = $envVariables["INVENTORY_SVR_HOST"]
$env_PORT = $envVariables["INVENTORY_SVR_PORT"]
$env_CSVFolder = $envVariables["CSV_FOLDER"]
$env_CSVFile = $envVariables["CSV_FILE"]
$env_Net = $envVariables["NET_CONN"]

# Check if the folder exists
if (-not (Test-Path -Path $env_CSVFolder)) {
    # Create the folder if it doesn't exist
    New-Item -ItemType Directory -Path $env_CSVFolder
    Write-Host "Folder created at: $env_CSVFolder"
}
#===========================
$Updateby = Read-Host "Enter your Name or EID "
Write-Host "--------------------------------------"
$Floor = Read-Host "Enter Floor "
Write-Host "======================================"
Write-Host "**         Select Location          **"
Write-Host "======================================"
Write-Host "   [" -NoNewline; Write-Host "P" -NoNewline -ForegroundColor Green; Write-Host "]OD Production"
Write-Host "  P[" -NoNewline; Write-Host "A" -NoNewline -ForegroundColor Green; Write-Host "] Production "; 
Write-Host "   [" -NoNewline; Write-Host "C" -NoNewline -ForegroundColor Green; Write-Host "]R Coaching Room "; 
Write-Host "   [" -NoNewline; Write-Host "B" -NoNewline -ForegroundColor Green; Write-Host "]oard Room "; 
Write-Host "   [" -NoNewline; Write-Host "E" -NoNewline -ForegroundColor Green; Write-Host "]nterprise "; 
Write-Host "   [" -NoNewline; Write-Host "T" -NoNewline -ForegroundColor Green; Write-Host "]raining Room "; 
Write-Host "   [" -NoNewline; Write-Host "O" -NoNewline -ForegroundColor Green; Write-Host "]ther Location"
Write-Host "======================================"
Write-Host "Enter you Selection  " -NoNewline
$selectedLocation = Prompt-ValidInput " " @('P', 'A', 'C', 'B', 'E', 'T', 'O', '~')
Write-Host "======================================"
# Based on selected environment, prompt for additional information
switch ($selectedLocation) {
    'P' {        Write-Host "** PRODUCTION POD **"
        $location1 = Read-Host "Enter Pod Number"
        try { $location1 = "POD{0:D2}" -f [int]$location1 } catch {}
        $location2 = Read-Host "Enter Station Letter"
    }
    'A' {        Write-Host "** PRODUCTION PA **"
        $location1 = Read-Host "Enter PA Number"
        try { $location1 = "PA{0:D2}" -f [int]$location1 } catch {}
        $location2 = Read-Host "Enter Station Letter"
    }
    'C' {        Write-Host "** PRODUCTION COACHING ROOM **"
        $selectedLocation1 = Prompt-MacMoa "Select [MAC/MOA]" @('MAC', 'MOA')
        $location1 = "CR_" + $selectedLocation1
        $location2 = Read-Host "Enter Seat Number"
        try { $location2 = "Seat-{0:D2}" -f [int]$location2 } catch {}
    }
    'B' {        Write-Host "** PRODUCTION BOARD ROOM **"
        $selectedLocation1 = Prompt-MacMoa "Select [MAC/MOA]" @('MAC', 'MOA')
        $location1 = "BR_" + $selectedLocation1
        $location2 = Read-Host "Enter Seat Number"
        try { $location2 = "Seat-{0:D2}" -f [int]$location2 } catch {}
    }
    'E' {        Write-Host "** ENTERPRISE AREA **"
        $selectedLocation1 = Prompt-MacMoa "Select [MAC/MOA]" @('MAC', 'MOA')
        $location1 = "Ent_" + $selectedLocation1
        $location2 = Read-Host "Enter Seat Number"
        try { $location2 = "Seat-{0:D2}" -f [int]$location2 } catch {}
    }
    'T' {        Write-Host "** TRAINING ROOM **"
        $location1 = Read-Host "Enter Location Name"
        $location1 = "TR_"+$location1
        $location2 = Read-Host "Enter Seat Number"
        try { $location2 = "Seat-{0:D2}" -f [int]$location2 } catch {}
    }
    'O' {        Write-Host "** OTHER LOCATION **"
        Write-Host "Note: use '_' as Space"
        Write-Host "--------------------------------------"
        $location1 = Read-Host "Enter Location Name"
        $location2 = Read-Host "Enter Seat Number"
        try { $location2 = "Seat-{0:D2}" -f [int]$location2 } catch {}
    }
    '~' {
        $location1 = "N_A"
        $location2 = "N_A"
        $CiscoExt  = "N_A"
    }
}
$CiscoExt = if ($CiscoExt -ne "N_A") { Read-Host "Cisco Ext." } else { $CiscoExt }

if ([string]::IsNullOrWhiteSpace($Floor)) { $Floor = "N/A"}
if ([string]::IsNullOrWhiteSpace($CiscoExt)) { $CiscoExt = "N/A"}
if ([string]::IsNullOrWhiteSpace($Updateby)) { $Updateby = "NOC"}
#===========================
# Get system information
$Computer = hostname
$RecordedDT = Get-Date -UFormat "%Y%m%d_%H%M%S"
$date = [DateTime]::ParseExact($RecordedDT, "yyyyMMdd_HHmmss", $null)
$formattedDate = $date.ToString("yyyyMMdd HH:mm:ss")
$ComputerInfo = Get-ComputerInfo
$PC = Get-WmiObject Win32_ComputerSystem -Computer $Computer
$CPU = Get-WmiObject Win32_Processor -Computer $Computer
$DateInstalled = (Get-WmiObject Win32_OperatingSystem).InstallDate
$BIOS = Get-WmiObject Win32_BIOS -Computer $Computer
#===========================
# Retrieve information about RAM modules
$ramModules = Get-CimInstance -ClassName Win32_PhysicalMemory
$RAMSlot = ($ramModules | ForEach-Object { $_.BankLabel }) -join ', '
$CapGB = ($ramModules | ForEach-Object { [math]::Round($_.Capacity / 1GB, 2) }) -join ', '  # Convert capacity to GB
$TotalMemoryGB = ([math]::Round(($ramModules | Measure-Object -Property Capacity -Sum).Sum / 1GB, 2)).ToString() + " GB"
$MemType = ($ramModules | ForEach-Object {
    Switch ($_.SMBIOSMemoryType) {
        20 { "DDR" }
        21 { "DDR2" }
        24 { "DDR3" }
        26 { "DDR4" }
        Default { "Unknown" }
    }
}) -join ', '
$Speedz = ($ramModules | ForEach-Object { $_.Speed }) -join ', '
$Mfr = ($ramModules | ForEach-Object { $_.Manufacturer }) -join ', '
$RAMSerNum = ($ramModules | ForEach-Object { $_.SerialNumber }) -join ', '
#===========================
$adapterName = $env_Net
$macVal = (Get-NetAdapter -Name $adapterName).MacAddress -replace "-", "" | ForEach-Object { $_.Insert(4, ".").Insert(9, ".") }
$ipAddress = (Get-NetIPAddress -InterfaceAlias $adapterName -AddressFamily IPv4).IPAddress
$OS = Get-WmiObject Win32_OperatingSystem -Computer $Computer
$displayVersion = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').DisplayVersion
$OSVer = (Get-ComputerInfo).OsVersion 
$WinEdition = (Get-CimInstance -class Win32_OperatingSystem).Caption
#===========================
$installed_citrix = Get-ItemProperty HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* | 
                    Where-Object { $_.DisplayName -like "Citrix Workspace 2*" } |
                    Select-Object DisplayName, DisplayVersion
$CitrixDisplayName = if ($installed_citrix) { $installed_citrix.DisplayName } else { "Citrix N/A" }
$CitrixDisplayVersion = if ($installed_citrix) { $installed_citrix.DisplayVersion } else { "Citrix N/A" }
#+++++++++++++++++++++++++++++++
$DataObject = [PSCustomObject]@{
   Floor            = $Floor.ToUpper()
    Location1        = $Location1.ToUpper()
    Location2        = $Location2.ToUpper()
    CiscoExt         = $CiscoExt
   Updateby         = $UpdateBy.ToUpper()
    ComputerName     = $PC.Name
    SerialNumber     = $BIOS.SerialNumber
    PCModel          = $PC.Model
    Processor        = $CPU.Name
   RAMTotalGB       = $TotalMemoryGB
    RAMSlot          = $RAMSlot
    RAMCapGB         = $CapGB
    RAMType          = $MemType
    SpeedMHz         = $Speedz
    Mfr              = $Mfr
    RAMSerNum        = $RAMSerNum
   IPAddress        = $IPAddress
    MACAddress       = $macVal
    WindowsEdition   = $WinEdition
    DisplayVersion   = $DisplayVersion
    OSVersion        = $OSVer
   CitrixName       = $CitrixDisplayName
    CitrixVersion    = $CitrixDisplayVersion
   RecordedDateTime = $formattedDate
    NOCItem          = "Desktop"
}
Show-InventoryBanner
Write-Host "======================================"
$DataObject
Write-Host "======================================"
# SAVE to CSV
if ($env_enaCSV) { 
    $csvPath = "$PSScriptRoot\$env_CSVFolder\$env_CSVFile"  # Specify the desired file path
    #$DataObject | Export-Csv -Path $csvPath -NoTypeInformation -Append
    try {
        $DataObject | Export-Csv -Path $csvPath -NoTypeInformation -Append
        Write-Host "CSV Data appended successfully to $csvPath"
    } catch {
        Write-Host "Failed to append data to $csvPath. Error: $($_.Exception.Message)" -ForegroundColor Red
    }
 }
# SAVE to SQLITE
if ($env_enaSQL) { 
    $Data = $DataObject | ConvertTo-Json -Depth 2
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    try {
        # Attempt to connect to the server
        $tcpClient.Connect($env_HOST, $env_PORT)
        $connected = $true
        Write-Host "Connected to server: $env_HOST on port $env_PORT"
    } catch {
        # Handle connection failure
        Write-Host "Sorry... Information Not Saved. Could not connect to Server"
        return  # Exit the script
    }
    $Url = "https://$($env_HOST):$($env_PORT)/api_save_data/"
    # Disable SSL certificate validation (for self-signed certificates)
    [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }

    # Send the POST request
    try {
        $response = Invoke-RestMethod -Uri $Url -Method POST -Body $Data -ContentType "application/json"
        Write-Host "Response from server:" $response
        #$DataObject
    } catch {
        Write-Host "An error occurred while sending data: $_"
    }
}
Show-RebootPrompt
