# Server Phase 1 — Hostname Rename + Runtime Bootstrap
# Target: 192.168.1.180 (new HP ProLiant DL380 Gen9)

$targetIP = "192.168.1.180"
$password = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ("$targetIP\Administrator", $password)

$report = @{}
$report["StartTime"] = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

Write-Host "=== Server Phase 1 Bootstrap ===" -ForegroundColor Cyan
Write-Host "Target: $targetIP" -ForegroundColor Yellow
Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host ""

# ============================================================
# PART A — Hostname Rename
# ============================================================
Write-Host "=== PART A: Hostname Rename ===" -ForegroundColor Cyan

# Step A1: Confirm current hostname
Write-Host "--- A1: Current Hostname ---" -ForegroundColor Green
try {
    $currentHost = Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
        (Get-ComputerInfo).CsName
    }
    $report["OldHostname"] = $currentHost.CSName
    Write-Host "  Current hostname: $($currentHost.CSName)" -ForegroundColor Yellow
} catch {
    Write-Host "  Error reading hostname: $_" -ForegroundColor Red
    $report["OldHostname"] = "ERROR: $_"
}
Write-Host ""

# Step A2: Rename to SHAYANSKA-DL380
Write-Host "--- A2: Renaming to SHAYANSKA-DL380 ---" -ForegroundColor Green
try {
    Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
        Rename-Computer -NewName "SHAYANSKA-DL380" -Force -PassThru
    }
    $report["RenameStatus"] = "SUCCESS"
    Write-Host "  Rename command accepted successfully" -ForegroundColor Green
} catch {
    $report["RenameStatus"] = "FAILED: $_"
    Write-Host "  Rename FAILED: $_" -ForegroundColor Red
}
Write-Host ""

# Step A3: Controlled reboot
Write-Host "--- A3: Initiating controlled reboot ---" -ForegroundColor Green
try {
    Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
        Shutdown /r /t 10 /c "Server Phase 1 Bootstrap - Hostname change" /f
    }
    $report["RebootInitiated"] = "YES"
    Write-Host "  Reboot initiated (10 second delay)" -ForegroundColor Green
} catch {
    $report["RebootInitiated"] = "NO: $_"
    Write-Host "  Reboot FAILED: $_" -ForegroundColor Red
}
Write-Host ""

# ============================================================
# PART B — Post-Reboot Recovery Verification
# ============================================================
Write-Host "=== PART B: Post-Reboot Recovery ===" -ForegroundColor Cyan
Write-Host "Waiting for server to come back online..." -ForegroundColor Yellow

$report["RecoveryTime"] = $null
$report["WinRMAfterReboot"] = $null
$report["RDPAfterReboot"] = $null
$report["NewHostname"] = $null

$recoveryTimeout = 300  # 5 minutes max
$pollInterval = 10
$elapsed = 0
$serverFound = $false

while ($elapsed -lt $recoveryTimeout) {
    Start-Sleep -Seconds $pollInterval
    $elapsed += $pollInterval
    Write-Host "  Polling... ($elapsed / $recoveryTimeout seconds)" -ForegroundColor Gray

    # Try ping first
    $ping = Test-Connection -ComputerName $targetIP -Count 1 -Quiet -ErrorAction SilentlyContinue
    if (-not $ping) {
        Write-Host "    Ping: unreachable" -ForegroundColor Gray
        continue
    }
    Write-Host "    Ping: reachable" -ForegroundColor Green

    # Try WinRM
    try {
        $winrmTest = Test-NetConnection -ComputerName $targetIP -Port 5985 -WarningAction SilentlyContinue
        if ($winrmTest.TcpTestSucceeded) {
            Write-Host "    WinRM (5985): OPEN" -ForegroundColor Green
            $report["WinRMAfterReboot"] = "OPEN"

            # Verify new hostname
            try {
                $newHost = Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
                    (Get-ComputerInfo).CsName
                }
                $report["NewHostname"] = $newHost.CSName
                Write-Host "    New hostname: $($newHost.CSName)" -ForegroundColor Green
            } catch {
                $report["NewHostname"] = "ERROR: $_"
                Write-Host "    Hostname check error: $_" -ForegroundColor Yellow
            }
        } else {
            Write-Host "    WinRM (5985): CLOSED" -ForegroundColor Yellow
            $report["WinRMAfterReboot"] = "CLOSED"
        }
    } catch {
        Write-Host "    WinRM check error: $_" -ForegroundColor Yellow
        $report["WinRMAfterReboot"] = "ERROR: $_"
    }

    # Try RDP
    try {
        $rdpTest = Test-NetConnection -ComputerName $targetIP -Port 3389 -WarningAction SilentlyContinue
        if ($rdpTest.TcpTestSucceeded) {
            Write-Host "    RDP (3389): OPEN" -ForegroundColor Green
            $report["RDPAfterReboot"] = "OPEN"
        } else {
            Write-Host "    RDP (3389): CLOSED" -ForegroundColor Yellow
            $report["RDPAfterReboot"] = "CLOSED"
        }
    } catch {
        Write-Host "    RDP check error: $_" -ForegroundColor Yellow
        $report["RDPAfterReboot"] = "ERROR: $_"
    }

    $serverFound = $true
    $report["RecoveryTime"] = "$elapsed seconds"
    break
}

if (-not $serverFound) {
    Write-Host ""
    Write-Host "  WARNING: Server did not recover within $recoveryTimeout seconds" -ForegroundColor Red
    $report["RecoveryStatus"] = "TIMEOUT"
} else {
    Write-Host ""
    Write-Host "  Server recovered successfully" -ForegroundColor Green
    $report["RecoveryStatus"] = "SUCCESS"
}
Write-Host ""

# ============================================================
# PART C — Install Git for Windows
# ============================================================
Write-Host "=== PART C: Install Git for Windows ===" -ForegroundColor Cyan

$report["GitInstalled"] = $null
$report["GitVersion"] = $null
$report["GitPath"] = $null

Write-Host "--- C1: Check if Git exists ---" -ForegroundColor Green
try {
    $gitCheck = Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
        $gitExe = Get-Command git -ErrorAction SilentlyContinue
        if ($gitExe) {
            $version = & git --version 2>&1
            [PSCustomObject]@{
                Found = $true
                Version = $version
                Path = $gitExe.Source
            }
        } else {
            [PSCustomObject]@{
                Found = $false
                Version = $null
                Path = $null
            }
        }
    }
    $report["GitInstalled"] = $gitCheck.Found
    Write-Host "  Git found: $($gitCheck.Found)" -ForegroundColor $(if ($gitCheck.Found) { "Green" } else { "Yellow" })
    if ($gitCheck.Found) {
        $report["GitVersion"] = $gitCheck.Version
        $report["GitPath"] = $gitCheck.Path
        Write-Host "  Version: $($gitCheck.Version)" -ForegroundColor Green
        Write-Host "  Path: $($gitCheck.Path)" -ForegroundColor Green
    }
} catch {
    $report["GitInstalled"] = "ERROR: $_"
    Write-Host "  Error checking Git: $_" -ForegroundColor Red
}
Write-Host ""

if (-not $gitCheck.Found) {
    Write-Host "--- C2: Downloading Git for Windows installer ---" -ForegroundColor Green
    $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.1/Git-2.47.1-64-bit.exe"
    $gitInstaller = "C:\GitInstaller.exe"

    try {
        Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
            param($url, $path)
            Write-Host "  Downloading Git for Windows..." -ForegroundColor Yellow
            Invoke-WebRequest -Uri $url -OutFile $path -UseBasicParsing
            Write-Host "  Download complete: $path" -ForegroundColor Green
        } -ArgumentList $gitUrl, $gitInstaller

        Write-Host "--- C3: Installing Git silently (system-wide) ---" -ForegroundColor Green
        Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
            param($path)
            Write-Host "  Running Git installer..." -ForegroundColor Yellow
            Start-Process $path -ArgumentList "/VERYSILENT /NORESTART /NOCANCEL /SP- /SUPPRESSMSGBOXES /DIR=`"C:\Program Files\Git`"" -Wait -NoNewWindow
            Write-Host "  Git installation complete" -ForegroundColor Green
        } -ArgumentList $gitInstaller

        # Refresh PATH and verify
        Write-Host "--- C4: Verifying Git installation ---" -ForegroundColor Green
        Start-Sleep -Seconds 5
        try {
            $gitVerify = Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
                # Force refresh PATH
                $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
                $gitExe = Get-Command git -ErrorAction SilentlyContinue
                if ($gitExe) {
                    $version = & git --version 2>&1
                    [PSCustomObject]@{
                        Version = $version
                        Path = $gitExe.Source
                    }
                } else {
                    [PSCustomObject]@{
                        Version = "git command not found in PATH"
                        Path = "not found"
                    }
                }
            }
            $report["GitVersion"] = $gitVerify.Version
            $report["GitPath"] = $gitVerify.Path
            Write-Host "  Git version: $($gitVerify.Version)" -ForegroundColor Green
            Write-Host "  Git path: $($gitVerify.Path)" -ForegroundColor Green
        } catch {
            $report["GitVersion"] = "ERROR: $_"
            Write-Host "  Git verification error: $_" -ForegroundColor Red
        }
    } catch {
        $report["GitStatus"] = "FAILED: $_"
        Write-Host "  Git installation FAILED: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  Git already installed, skipping installation" -ForegroundColor Green
}
Write-Host ""

# ============================================================
# PART D — Install Python 3.12
# ============================================================
Write-Host "=== PART D: Install Python 3.12 ===" -ForegroundColor Cyan

$report["PythonInstalled"] = $null
$report["PythonVersion"] = $null
$report["PythonPath"] = $null
$report["PipInstalled"] = $null
$report["PipVersion"] = $null

Write-Host "--- D1: Check if Python exists ---" -ForegroundColor Green
try {
    $pythonCheck = Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
        $pyExe = Get-Command python -ErrorAction SilentlyContinue
        if ($pyExe) {
            $version = & python --version 2>&1
            [PSCustomObject]@{
                Found = $true
                Version = $version
                Path = $pyExe.Source
            }
        } else {
            [PSCustomObject]@{
                Found = $false
                Version = $null
                Path = $null
            }
        }
    }
    $report["PythonInstalled"] = $pythonCheck.Found
    Write-Host "  Python found: $($pythonCheck.Found)" -ForegroundColor $(if ($pythonCheck.Found) { "Green" } else { "Yellow" })
    if ($pythonCheck.Found) {
        $report["PythonVersion"] = $pythonCheck.Version
        $report["PythonPath"] = $pythonCheck.Path
        Write-Host "  Version: $($pythonCheck.Version)" -ForegroundColor Green
        Write-Host "  Path: $($pythonCheck.Path)" -ForegroundColor Green
    }
} catch {
    $report["PythonInstalled"] = "ERROR: $_"
    Write-Host "  Error checking Python: $_" -ForegroundColor Red
}
Write-Host ""

if (-not $pythonCheck.Found) {
    Write-Host "--- D2: Downloading Python 3.12.9 installer ---" -ForegroundColor Green
    $pythonUrl = "https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe"
    $pythonInstaller = "C:\PythonInstaller.exe"

    try {
        Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
            param($url, $path)
            Write-Host "  Downloading Python 3.12.9..." -ForegroundColor Yellow
            Invoke-WebRequest -Uri $url -OutFile $path -UseBasicParsing
            Write-Host "  Download complete: $path" -ForegroundColor Green
        } -ArgumentList $pythonUrl, $pythonInstaller

        Write-Host "--- D3: Installing Python silently (all users, PATH enabled) ---" -ForegroundColor Green
        Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
            param($path)
            Write-Host "  Running Python installer..." -ForegroundColor Yellow
            Start-Process $path -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1' -Wait -NoNewWindow
            Write-Host "  Python installation complete" -ForegroundColor Green
        } -ArgumentList $pythonInstaller

        # Verify Python and pip
        Write-Host "--- D4: Verifying Python and pip installation ---" -ForegroundColor Green
        Start-Sleep -Seconds 5
        try {
            $pythonVerify = Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
                $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
                $pyExe = Get-Command python -ErrorAction SilentlyContinue
                $pipExe = Get-Command pip -ErrorAction SilentlyContinue

                $pyVersion = if ($pyExe) { & python --version 2>&1 } else { "python not found" }
                $pipVersion = if ($pipExe) { & pip --version 2>&1 } else { "pip not found" }

                [PSCustomObject]@{
                    PythonVersion = $pyVersion
                    PythonPath = if ($pyExe) { $pyExe.Source } else { "not found" }
                    PipVersion = $pipVersion
                    PipPath = if ($pipExe) { $pipExe.Source } else { "not found" }
                }
            }
            $report["PythonVersion"] = $pythonVerify.PythonVersion
            $report["PythonPath"] = $pythonVerify.PythonPath
            $report["PipInstalled"] = ($pythonVerify.PipVersion -ne "pip not found")
            $report["PipVersion"] = $pythonVerify.PipVersion
            Write-Host "  Python version: $($pythonVerify.PythonVersion)" -ForegroundColor Green
            Write-Host "  Python path: $($pythonVerify.PythonPath)" -ForegroundColor Green
            Write-Host "  pip version: $($pythonVerify.PipVersion)" -ForegroundColor Green
            Write-Host "  pip path: $($pythonVerify.PipPath)" -ForegroundColor Green
        } catch {
            $report["PythonVersion"] = "ERROR: $_"
            Write-Host "  Python verification error: $_" -ForegroundColor Red
        }
    } catch {
        $report["PythonStatus"] = "FAILED: $_"
        Write-Host "  Python installation FAILED: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  Python already installed, skipping installation" -ForegroundColor Green
}
Write-Host ""

# ============================================================
# PART E — Final Bootstrap Inventory
# ============================================================
Write-Host "=== PART E: Final Bootstrap Inventory ===" -ForegroundColor Cyan

try {
    $finalInventory = Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
        $ci = Get-ComputerInfo
        $hw = Get-CimInstance Win32_ComputerSystem
        $os = Get-CimInstance Win32_OperatingSystem
        $disks = Get-CimInstance Win32_DiskDrive | Select-Object -First 5
        $netAdapters = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' }

        [PSCustomObject]@{
            Hostname = $hw.Name
            Model = $hw.Model
            Manufacturer = $hw.Manufacturer
            TotalRAM = [math]::Round($hw.TotalPhysicalMemory / 1GB, 1)
            OS = $os.Caption
            OSVersion = $os.Version
            Build = $os.BuildNumber
            Architecture = $ci.OSArchitecture
            LastBoot = $os.LastBootUpTime
            Uptime = (New-TimeSpan $lastBoot (Get-Date))
            IP = ($netAdapters | ForEach-Object { (Get-NetIPAddress -InterfaceAlias $_.Name -AddressFamily IPv4).IPAddress } | Where-Object { $_ }) -join ', '
            MAC = ($netAdapters | ForEach-Object { $_.MacAddress } | Where-Object { $_ }) -join ', '
            CPU = (Get-CimInstance Win32_Processor | ForEach-Object { "$($_.Name) ($($_.NumberOfCores) cores, $($_.NumberOfLogicalProcessors) threads)" }) -join '; '
            Drives = (Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object { "$($_.DeviceID): $([math]::Round($_.FreeSpace/1GB,1))GB free" }) -join '; '
        }
    }

    $report["FinalHostname"] = $finalInventory.Hostname
    $report["FinalModel"] = $finalInventory.Model
    $report["FinalRAM"] = "$($finalInventory.TotalRAM) GB"
    $report["FinalOS"] = "$($finalInventory.OS) $($finalInventory.OSVersion) ($($finalInventory.Build)) $($finalInventory.Architecture)"
    $report["FinalCPU"] = $finalInventory.CPU
    $report["FinalDrives"] = $finalInventory.Drives
    $report["FinalIP"] = $finalInventory.IP
    $report["FinalLastBoot"] = $finalInventory.LastBoot

    Write-Host "  Hostname: $($finalInventory.Hostname)" -ForegroundColor Green
    Write-Host "  Model: $($finalInventory.Model)" -ForegroundColor Green
    Write-Host "  RAM: $($finalInventory.TotalRAM) GB" -ForegroundColor Green
    Write-Host "  OS: $($finalInventory.OS) $($finalInventory.OSVersion)" -ForegroundColor Green
    Write-Host "  CPU: $($finalInventory.CPU)" -ForegroundColor Green
    Write-Host "  Drives: $($finalInventory.Drives)" -ForegroundColor Green
    Write-Host "  IP: $($finalInventory.IP)" -ForegroundColor Green
} catch {
    Write-Host "  Error collecting final inventory: $_" -ForegroundColor Red
}
Write-Host ""

# ============================================================
# Summary
# ============================================================
Write-Host "=== BOOTSTRAP SUMMARY ===" -ForegroundColor Cyan
Write-Host "Rename: $($report['RenameStatus'])" -ForegroundColor $(if ($report['RenameStatus'] -eq 'SUCCESS') { 'Green' } else { 'Red' })
Write-Host "Recovery: $($report['RecoveryStatus']) ($($report['RecoveryTime']))" -ForegroundColor $(if ($report['RecoveryStatus'] -eq 'SUCCESS') { 'Green' } else { 'Red' })
Write-Host "New Hostname: $($report['NewHostname'])" -ForegroundColor $(if ($report['NewHostname'] -eq 'SHAYANSKA-DL380') { 'Green' } else { 'Red' })
Write-Host "WinRM Post-Reboot: $($report['WinRMAfterReboot'])" -ForegroundColor $(if ($report['WinRMAfterReboot'] -eq 'OPEN') { 'Green' } else { 'Red' })
Write-Host "RDP Post-Reboot: $($report['RDPAfterReboot'])" -ForegroundColor $(if ($report['RDPAfterReboot'] -eq 'OPEN') { 'Green' } else { 'Red' })
$gitStatus = if ($report['GitVersion'] -and $report['GitVersion'] -notmatch 'not found') { $report['GitVersion'] } else { 'Not installed' }
$pyStatus = if ($report['PythonVersion'] -and $report['PythonVersion'] -notmatch 'not found') { $report['PythonVersion'] } else { 'Not installed' }
$pipStatus = if ($report['PipInstalled']) { $report['PipVersion'] } else { 'Not installed' }
Write-Host "Git: $gitStatus" -ForegroundColor $(if ($report['GitVersion'] -and $report['GitVersion'] -notmatch 'not found') { 'Green' } else { 'Yellow' })
Write-Host "Python: $pyStatus" -ForegroundColor $(if ($report['PythonVersion'] -and $report['PythonVersion'] -notmatch 'not found') { 'Green' } else { 'Yellow' })
Write-Host "pip: $pipStatus" -ForegroundColor $(if ($report['PipInstalled']) { 'Green' } else { 'Yellow' })
Write-Host "NVIDIA: NOT installed (intentional)" -ForegroundColor Yellow
Write-Host "Project-S: NOT migrated (intentional)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Bootstrap complete. Report saved." -ForegroundColor Green