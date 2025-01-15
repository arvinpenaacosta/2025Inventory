


# Dummy data values for DataObject
$DataObject = [PSCustomObject]@{
    Floor            = "1ST"
    Location1        = "POD01"
    Location2        = "RoomA"
    CiscoExt         = "12345"
    Updateby         = "USER1"
    ComputerName     = "COMPUTER-01"
    SerialNumber     = "SN123456789"
    PCModel          = "Dell Latitude 7490"
    Processor        = "Intel(R) Core(TM) i7-8665U CPU @ 1.90GHz"
    RAMSlot          = "2"  # Convert to string
    RAMCapGB         = "8"  # Convert to string
    RAMTotalGB       = "16" # Convert to string
    RAMType          = "DDR4"
    SpeedMHz         = "2400"  # Convert to string
    Mfr              = "Corsair"
    RAMSerNum        = "ABC12345XYZ"
    IPAddress        = "192.168.1.100"
    MACAddress       = "12:34:56:78:9A:BC"
    WindowsEdition   = "Windows 10 Pro"
    DisplayVersion   = "22H2"
    OSVersion        = "10.0.19045"
    CitrixName       = "Citrix Workspace"
    CitrixVersion    = "22.12.0"
    
    NOCItem          = "Desktop"
}



$Data = $DataObject | ConvertTo-Json -Depth 2

$tcpClient = New-Object System.Net.Sockets.TcpClient

$env_HOST = "192.168.1.18"
$env_PORT = "8892"

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
    $DataObject
} catch {
    Write-Host "An error occurred while sending data: $_"
}
