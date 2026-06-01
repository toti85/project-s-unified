# SHAYANSKA-DL380 Bootstrap Phase 1 - Step 2: Remote Inventory Snapshot
# Collects system info from the target server

$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

Write-Host "=== Step 2: Remote Inventory Snapshot ===" -ForegroundColor Cyan

# Collect all inventory data remotely
$inventory = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    $os = Get-CimInstance -ClassName Win32_OperatingSystem
    $cpu = Get-CimInstance -ClassName Win32_Processor
    $ram = Get-CimInstance -ClassName Win32_ComputerSystem
    $disks = Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DriveType=3"
    $envPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    
    # Check for Git
    $gitCheck = Get-Command git -ErrorAction SilentlyContinue
    $gitExists = $null -ne $gitCheck
    
    # Check for Python
    $pythonCheck = Get-Command python -ErrorAction SilentlyContinue
    $pythonExists = $null -ne $pythonCheck
    
    # Check for winget
    $wingetCheck = Get-Command winget -ErrorAction SilentlyContinue
    $wingetExists = $null -ne $wingetCheck
    
    # Check for Chocolatey
    $chocoCheck = Get-Command choco -ErrorAction SilentlyContinue
    $chocoExists = $null -ne $chocoCheck
    
    # Check for PowerShell Core
    $pwshCheck = Get-Command pwsh -ErrorAction SilentlyContinue
    $pwshExists = $null -ne $pwshCheck
    
    # Get Windows build info
    $buildInfo = Get-CimInstance -ClassName Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber, OSArchitecture
    
    [PSCustomObject]@{
        Hostname        = $env:COMPUTERNAME
        OS_Caption      = $os.Caption
        OS_Version      = $os.Version
        OS_Build        = $os.BuildNumber
        OS_Architecture = $os.OSArchitecture
        CPU_Description = ($cpu | ForEach-Object { $_.Description }) -join ", "
        CPU_Count       = $cpu.Count
        CPU_MaxClock    = ($cpu | ForEach-Object { $_.MaxClockSpeed }) -join " / "
        TotalRAM_GB     = [math]::Round($ram.TotalPhysicalMemory / 1GB, 2)
        LogicalDisks    = ($disks | ForEach-Object {
            "$($_.DeviceID): $([math]::Round($_.FreeSpace/1GB, 2)) GB free"
        }) -join " | "
        PATH            = $envPath
        Git_Exists      = $gitExists
        Python_Exists   = $pythonExists
        winget_Exists   = $wingetExists
        Chocolatey_Exists = $chocoExists
        PowerShellCore_Exists = $pwshExists
    }
} -ErrorAction Stop

# Display inventory
Write-Host "`n--- System Information ---" -ForegroundColor Yellow
$inventory | Format-List | Out-String | Write-Host

# Save inventory to file
$inventory | ConvertTo-Json | Out-File -FilePath "step2_inventory.json" -Encoding UTF8
Write-Host "`n[2.1] Inventory saved to step2_inventory.json" -ForegroundColor Green

# Save as markdown for report
$md = @"
# Remote Inventory - SHAYANSKA-DL380
**Collected:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

| Property | Value |
|----------|-------|
| Hostname | $($inventory.Hostname) |
| OS Caption | $($inventory.OS_Caption) |
| OS Version | $($inventory.OS_Version) |
| OS Build | $($inventory.OS_Build) |
| OS Architecture | $($inventory.OS_Architecture) |
| CPU | $($inventory.CPU_Description) |
| CPU Count | $($inventory.CPU_Count) |
| Max Clock Speed | $($inventory.CPU_MaxClock) MHz |
| Total RAM | $($inventory.TotalRAM_GB) GB |
| Free Disk Space | $($inventory.LogicalDisks) |
| Git Installed | $($inventory.Git_Exists) |
| Python Installed | $($inventory.Python_Exists) |
| winget Available | $($inventory.winget_Exists) |
| Chocolatey Available | $($inventory.Chocolatey_Exists) |
| PowerShell Core | $($inventory.PowerShellCore_Exists) |
"@

$md | Out-File -FilePath "step2_inventory.md" -Encoding UTF8
Write-Host "[2.2] Inventory saved to step2_inventory.md" -ForegroundColor Green

Write-Host "`nStep 2 complete." -ForegroundColor Green