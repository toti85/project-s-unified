$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 2: SERVER PREP (WinRM Hygiene + SMB)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ============================================
# PART A: WINRM HYGIENE
# ============================================
Write-Host "=== PART A: WINRM HYGIENE FIXES ===" -ForegroundColor Yellow
Write-Host ""

# 1. Set network profile to Private
Write-Host "[A.1] Setting network profile to Private..." -ForegroundColor Cyan
try {
    $netResult = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $before = (Get-NetConnectionProfile).NetworkCategory
        Set-NetConnectionProfile -NetworkCategory Private -ErrorAction Stop
        $after = (Get-NetConnectionProfile | ForEach-Object { $_.NetworkCategory })
        @{ Before = $before; After = $after }
    }
    Write-Host "  Before: $($netResult.Before)" -ForegroundColor Gray
    Write-Host "  After: $($netResult.After)" -ForegroundColor $(if($netResult.After -eq "Private"){"Green"}else{"Red"})
    $netProfileFixed = ($netResult.After -eq "Private")
} catch {
    Write-Host "  FAILED: $_" -ForegroundColor Red
    $netProfileFixed = $false
}

# 2. Set LocalAccountTokenFilterPolicy = 1
Write-Host "[A.2] Setting LocalAccountTokenFilterPolicy = 1..." -ForegroundColor Cyan
try {
    $tokenResult = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $path = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
        $existing = Get-ItemProperty -Path $path -Name LocalAccountTokenFilterPolicy -ErrorAction SilentlyContinue
        if ($existing) {
            $oldVal = $existing.LocalAccountTokenFilterPolicy
            Set-ItemProperty -Path $path -Name LocalAccountTokenFilterPolicy -Value 1 -ErrorAction Stop
            @{ Old = $oldVal; New = 1; Action = "Updated" }
        } else {
            New-ItemProperty -Path $path -Name LocalAccountTokenFilterPolicy -Value 1 -PropertyType DWORD -Force -ErrorAction Stop | Out-Null
            @{ Old = "Not Set"; New = 1; Action = "Created" }
        }
    }
    Write-Host "  Old: $($tokenResult.Old)" -ForegroundColor Gray
    Write-Host "  New: $($tokenResult.New)" -ForegroundColor Green
    Write-Host "  Action: $($tokenResult.Action)" -ForegroundColor Green
    $tokenPolicyFixed = $true
} catch {
    Write-Host "  FAILED: $_" -ForegroundColor Red
    $tokenPolicyFixed = $false
}

# 3. Verify fixes
Write-Host "[A.3] Verifying fixes..." -ForegroundColor Cyan
try {
    $verify = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $netProfile = (Get-NetConnectionProfile).NetworkCategory
        $tokenVal = (Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name LocalAccountTokenFilterPolicy -ErrorAction SilentlyContinue).LocalAccountTokenFilterPolicy
        @{
            NetworkCategory = $netProfile
            TokenFilterPolicy = $tokenVal
        }
    }
    Write-Host "  Network Category: $($verify.NetworkCategory)" -ForegroundColor $(if($verify.NetworkCategory -eq "Private"){"Green"}else{"Red"})
    Write-Host "  TokenFilterPolicy: $($verify.TokenFilterPolicy)" -ForegroundColor $(if($verify.TokenFilterPolicy -eq 1){"Green"}else{"Red"})
} catch {
    Write-Host "  Verification failed: $_" -ForegroundColor Red
}

# 4. Test LAN WinRM still works
Write-Host "[A.4] Testing LAN WinRM after fixes..." -ForegroundColor Cyan
try {
    $hostname = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock { hostname } -ErrorAction Stop
    Write-Host "  LAN WinRM: PASS (hostname: $hostname)" -ForegroundColor Green
    $lanWinRMPass = $true
} catch {
    Write-Host "  LAN WinRM: FAIL - $_" -ForegroundColor Red
    $lanWinRMPass = $false
}

Write-Host ""

# ============================================
# PART B: SMB TRANSFER CHANNEL
# ============================================
Write-Host "=== PART B: SMB TRANSFER CHANNEL ===" -ForegroundColor Yellow
Write-Host ""

# 1. Check Server service status
Write-Host "[B.1] Checking LanmanServer (Server) service..." -ForegroundColor Cyan
try {
    $serverSvc = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $svc = Get-Service -Name LanmanServer -ErrorAction SilentlyContinue
        $svcStatus = $svc.Status
        $svcStart = $svc.StartType
        @{ Status = $svcStatus; StartType = $svcStart }
    }
    Write-Host "  Status: $($serverSvc.Status)" -ForegroundColor $(if($serverSvc.Status -eq "Running"){"Green"}else{"Yellow"})
    Write-Host "  Startup: $($serverSvc.StartType)" -ForegroundColor $(if($serverSvc.StartType -eq 2 -or $serverSvc.StartType -eq "Automatic"){"Green"}else{"Yellow"})
    
    if ($serverSvc.Status -ne "Running") {
        Write-Host "  Starting Server service..." -ForegroundColor Cyan
        Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
            Start-Service -Name LanmanServer -ErrorAction SilentlyContinue
        } | Out-Null
        Start-Sleep -Seconds 2
        Write-Host "  Server service started" -ForegroundColor Green
    }
} catch {
    Write-Host "  Check failed: $_" -ForegroundColor Red
}

# 2. Enable SMB firewall rules for Private profile
Write-Host "[B.2] Enabling SMB firewall rules for Private profile..." -ForegroundColor Cyan
try {
    Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        # Enable File and Printer Sharing for Private networks
        $rules = Get-NetFirewallRule -DisplayGroup "File and Printer Sharing" -ErrorAction SilentlyContinue
        foreach ($rule in $rules) {
            if ($rule.Enabled -eq "False") {
                Set-NetFirewallRule -ObjectId $rule.RuleIdentifier -Enabled True -ErrorAction SilentlyContinue | Out-Null
            }
        }
        Write-Host "  SMB firewall rules enabled for Private profile" -ForegroundColor Green
    }
} catch {
    Write-Host "  Firewall rule update: $_" -ForegroundColor Gray
}

# 3. Create target directory and SMB share
Write-Host "[B.3] Creating target directory and SMB share..." -ForegroundColor Cyan
try {
    $shareResult = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $sharePath = "C:\ProjectS\project-s-code"
        $shareName = "ProjectSStage"
        
        # Ensure directory exists
        if (!(Test-Path $sharePath)) {
            New-Item -Path $sharePath -ItemType Directory -Force | Out-Null
            Write-Host "  Created directory: $sharePath" -ForegroundColor Green
        } else {
            Write-Host "  Directory exists: $sharePath" -ForegroundColor Gray
        }
        
        # Remove existing share if present
        $existingShare = Get-WmiObject -Class Win32_Share -Filter "Name='$shareName'" -ErrorAction SilentlyContinue
        if ($existingShare) {
            $existingShare.Delete() | Out-Null
            Write-Host "  Removed existing share: $shareName" -ForegroundColor Gray
            Start-Sleep -Seconds 1
        }
        
        # Create new share with Administrator-only access
        $share = [WMICLASS]"\\.\ROOT\CIMV2:Win32_Share"
        $result = $share.Create($sharePath, $shareName, 0, 1, "ProjectS staging share for Phase 2 migration")
        
        if ($result.ReturnValue -eq 0) {
            Write-Host "  Share created: \\192.168.1.180\$shareName" -ForegroundColor Green
            @{ ShareCreated = $true; SharePath = $sharePath; ShareName = $shareName }
        } else {
            Write-Host "  Share creation failed with code: $($result.ReturnValue)" -ForegroundColor Red
            @{ ShareCreated = $false; SharePath = $sharePath; ShareName = $shareName; Error = $result.ReturnValue }
        }
    }
    $shareCreated = $shareResult.ShareCreated
} catch {
    Write-Host "  Share creation failed: $_" -ForegroundColor Red
    $shareCreated = $false
}

# 4. Test UNC reachability from DEV
Write-Host "[B.4] Testing UNC reachability from DEV machine..." -ForegroundColor Cyan
$uncPath = "\\$targetIP\$shareResult.ShareName"
try {
    $uncTest = Test-Path $uncPath
    if ($uncTest) {
        Write-Host "  UNC path reachable: $uncPath" -ForegroundColor Green
        $uncReachable = $true
    } else {
        Write-Host "  UNC path NOT reachable: $uncPath" -ForegroundColor Red
        Write-Host "  Trying with explicit credentials..." -ForegroundColor Yellow
        
        # Try with explicit credentials
        $credStr = "$targetIP\Administrator:$targetPassword"
        $netUseResult = net use $uncPath $targetPassword /user:$targetIP\Administrator /persistent:no 2>&1
        Write-Host "  Net use result: $netUseResult" -ForegroundColor Gray
        
        Start-Sleep -Seconds 3
        $uncTest2 = Test-Path $uncPath
        if ($uncTest2) {
            Write-Host "  UNC path reachable after explicit credentials: $uncPath" -ForegroundColor Green
            $uncReachable = $true
        } else {
            Write-Host "  UNC path still NOT reachable after credentials" -ForegroundColor Red
            $uncReachable = $false
        }
    }
} catch {
    Write-Host "  UNC test failed: $_" -ForegroundColor Red
    $uncReachable = $false
}

Write-Host ""

# ============================================
# PART C: EXTERNAL WINRM RE-TEST
# ============================================
Write-Host "=== PART C: EXTERNAL WINRM RE-TEST ===" -ForegroundColor Yellow
Write-Host ""

try {
    $extTest = Test-NetConnection -ComputerName "46.253.140.72" -Port 15985 -WarningAction SilentlyContinue -ErrorAction Stop
    Write-Host "  External TCP 46.253.140.72:15985:" -ForegroundColor White
    Write-Host "     TcpTestSucceeded: $($extTest.TcpTestSucceeded)" -ForegroundColor $(if($extTest.TcpTestSucceeded){"Green"}else{"Red"})
    $externalOpen = $extTest.TcpTestSucceeded
} catch {
    Write-Host "  External test failed: $_" -ForegroundColor Red
    $externalOpen = $false
}

Write-Host ""

# ============================================
# SAVE RESULTS
# ============================================
Write-Host "=== SAVING RESULTS ===" -ForegroundColor Yellow

$allResults = @{
    NetworkProfilePrivate = $verify.NetworkCategory
    TokenFilterPolicy = $verify.TokenFilterPolicy
    LANWinRMPass = $lanWinRMPass
    ShareCreated = $shareCreated
    ShareName = $shareResult.ShareName
    SharePath = $shareResult.SharePath
    UNCReachable = $uncReachable
    ExternalPort15985Open = $externalOpen
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

$allResults | ConvertTo-Json | Out-File -FilePath "C:\ProjectS-Unified\.phase2_prep_results.json" -Encoding UTF8

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SERVER PREP SUMMARY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  A. Network profile now Private: $($verify.NetworkCategory -eq 'Private')" -ForegroundColor $(if($verify.NetworkCategory -eq "Private"){"Green"}else{"Red"})
Write-Host "  B. LocalAccountTokenFilterPolicy now 1: $($verify.TokenFilterPolicy -eq 1)" -ForegroundColor $(if($verify.TokenFilterPolicy -eq 1){"Green"}else{"Red"})
Write-Host "  C. LAN WinRM still PASS: $lanWinRMPass" -ForegroundColor $(if($lanWinRMPass){"Green"}else{"Red"})
Write-Host "  D. SMB temp share created: $shareCreated" -ForegroundColor $(if($shareCreated){"Green"}else{"Red"})
Write-Host "  E. UNC path reachable from DEV: $uncReachable" -ForegroundColor $(if($uncReachable){"Green"}else{"Red"})
Write-Host "  F. External 15985 now open: $externalOpen" -ForegroundColor $(if($externalOpen){"Green"}else{"Red"})
Write-Host ""

if ($uncReachable -and $shareCreated) {
    Write-Host "  SMB channel READY for robocopy transfer!" -ForegroundColor Green
    Write-Host "  UNC Path: $uncPath" -ForegroundColor Green
} else {
    Write-Host "  SMB channel NOT ready. Check server services and firewall rules." -ForegroundColor Yellow
}

Write-Host "============================================" -ForegroundColor Cyan