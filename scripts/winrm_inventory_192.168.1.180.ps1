# Server Phase 1 — WinRM Remote Inventory Script
# Target: 192.168.1.180 (new DL380 Gen9)
# Read-only — no state-changing operations

$targetIP = "192.168.1.180"
$password = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ("$targetIP\Administrator", $password)

Write-Host "=== Server Phase 1 WinRM Remote Inventory ===" -ForegroundColor Cyan
Write-Host "Target: $targetIP" -ForegroundColor Yellow
Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host ""

# Step 1: Check current TrustedHosts
Write-Host "--- Step 1: Current TrustedHosts ---" -ForegroundColor Green
$th = Get-Item WSMan:\localhost\Client\TrustedHosts -ErrorAction SilentlyContinue
if ($th) {
    Write-Host "Existing TrustedHosts: $($th.Value)"
} else {
    Write-Host "No TrustedHosts configured yet."
}
Write-Host ""

# Step 2: Add target to TrustedHosts
Write-Host "--- Step 2: Adding $targetIP to TrustedHosts ---" -ForegroundColor Green
try {
    $existing = (Get-Item WSMan:\localhost\Client\TrustedHosts -ErrorAction SilentlyContinue).Value
    if ($existing -and $existing -ne "*") {
        $newList = "$existing,$targetIP"
    } else {
        $newList = $targetIP
    }
    New-Item -Path WSMan:\localhost\Client\TrustedHosts -Value $newList -Force -ErrorAction Stop | Out-Null
    Write-Host "Added $targetIP to TrustedHosts (current: $newList)" -ForegroundColor Green
} catch {
    Write-Host "Warning: Could not add to TrustedHosts: $_" -ForegroundColor Yellow
}
Write-Host ""

# Step 3: Run remote inventory
Write-Host "--- Step 3: Remote Inventory ---" -ForegroundColor Green
try {
    $result = Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
        # Host identity
        $hostname = $env:COMPUTERNAME
        $os = Get-CimInstance Win32_OperatingSystem
        $osCaption = $os.Caption
        $osVersion = $os.Version
        $osBuild = $os.BuildNumber
        $lastBoot = $os.LastBootUpTime
        $uptime = (Get-Date) - $lastBoot

        # CPU
        $cpu = Get-CimInstance Win32_Processor
        $cpuModel = ($cpu | Select-Object -First 1).Name
        $cpuCount = ($cpu | Measure-Object).Count
        $cpuCores = ($cpu | Measure-Object NumberOfCores -Sum).Sum
        $cpuThreads = ($cpu | Measure-Object NumberOfLogicalProcessors -Sum).Sum

        # RAM
        $ram = Get-CimInstance Win32_ComputerSystem
        $totalRAM_GB = [math]::Round($ram.TotalPhysicalMemory / 1GB, 1)

        # Drives
        $drives = Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3"

        # Network adapters
        $netAdapters = Get-CimInstance Win32_NetworkAdapterConfiguration -Filter "IPEnabled=True"

        # RDP status
        $rdpKey = Get-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -ErrorAction SilentlyContinue
        $rdpEnabled = if ($rdpKey) { $rdpKey.fDenyTSConnections -eq 0 } else { "unknown" }

        # PowerShell version
        $psVersion = $PSVersionTable.PSVersion.ToString()

        # Python
        $pythonPaths = @("C:\Python", "C:\Program Files\Python", "C:\Users")
        $pythonInfo = @()
        foreach ($p in $pythonPaths) {
            if (Test-Path $p) {
                $py = Get-ChildItem $p -Filter "python.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($py) { $pythonInfo += "$($py.FullName)"; continue }
                $pyv = Get-ChildItem $p -Filter "python*" -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($pyv) { $pythonInfo += "$($pyv.FullName)"; continue }
            }
        }
        # Also check PATH
        $envPython = Get-Command python -ErrorAction SilentlyContinue
        if ($envPython) { $pythonInfo += "PATH: $($envPython.Source)" }

        # Git
        $envGit = Get-Command git -ErrorAction SilentlyContinue
        $gitInfo = if ($envGit) { $envGit.Source } else { "not found in PATH" }

        # NVIDIA
        $nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
        $nvidiaInfo = if ($nvidiaSmi) { "nvidia-smi available at $($nvidiaSmi.Source)" } else { "nvidia-smi not in PATH" }

        # Output structured data
        $drivesStr = ""
        if ($drives) {
            $drivesStr = ($drives | ForEach-Object { "$($_.DeviceID): $([math]::Round($_.FreeSpace/1GB,1))GB free" }) -join "; "
        } else {
            $drivesStr = "No drives found"
        }

        $netStr = ""
        if ($netAdapters) {
            $netStr = ($netAdapters | ForEach-Object { "$($_.Description) - IP: $($_.IPAddress[0]) DNS: $($_.DNSServerSearchOrder -join ',')" }) -join "; "
        } else {
            $netStr = "No network adapters found"
        }

        $pyStr = ""
        if ($pythonInfo.Count -gt 0) {
            $pyStr = $pythonInfo -join "; "
        } else {
            $pyStr = "not found"
        }

        [PSCustomObject]@{
            Hostname = $hostname
            OSCaption = $osCaption
            OSVersion = $osVersion
            OSBuild = $osBuild
            LastBoot = $lastBoot.ToString('yyyy-MM-dd HH:mm:ss')
            UptimeDays = [math]::Round($uptime.TotalDays, 1)
            CPUModel = $cpuModel
            CPUCount = $cpuCount
            CPU_Cores = $cpuCores
            CPU_Threads = $cpuThreads
            TotalRAM_GB = $totalRAM_GB
            Drives = $drivesStr
            NetAdapters = $netStr
            RDPEnabled = $rdpEnabled
            PowerShellVersion = $psVersion
            Python = $pyStr
            Git = $gitInfo
            NVIDIA = $nvidiaInfo
        }
    }

    Write-Host ""
    Write-Host "=== INVENTORY RESULTS ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Hostname: $($result.Hostname)"
    Write-Host "OS: $($result.OSCaption) $($result.OSVersion) (Build $($result.OSBuild))"
    Write-Host "Last Boot: $($result.LastBoot) ($($result.UptimeDays) days uptime)"
    Write-Host "CPU: $($result.CPUModel) ($($result.CPUCount)x, $($result.CPU_Threads) threads)"
    Write-Host "RAM: $($result.TotalRAM_GB) GB"
    Write-Host "Drives: $($result.Drives)"
    Write-Host "Network: $($result.NetAdapters)"
    Write-Host "RDP Enabled: $($result.RDPEnabled)"
    Write-Host "PowerShell: $($result.PowerShellVersion)"
    Write-Host "Python: $($result.Python)"
    Write-Host "Git: $($result.Git)"
    Write-Host "NVIDIA: $($result.NVIDIA)"
    Write-Host ""
    Write-Host "=== WinRM Authentication: SUCCESS ===" -ForegroundColor Green

} catch {
    Write-Host ""
    Write-Host "=== WinRM Authentication: FAILED ===" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Verify the server password is correct" -ForegroundColor Yellow
    Write-Host "2. Check if WinRM is configured: winrm enumerate winrm/config/listener (via iLO console)" -ForegroundColor Yellow
    Write-Host "3. Try enabling WinRM: winrm quickconfig (via iLO console)" -ForegroundColor Yellow
}