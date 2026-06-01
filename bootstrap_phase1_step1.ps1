# SHAYANSKA-DL380 Bootstrap Phase 1 - Step 1: Connectivity Verification
# This script tests WinRM connectivity to the target server

$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force

# Try multiple credential formats
$credFormats = @(
    ("192.168.1.180\Administrator", "IP\Admin format"),
    ("Administrator", "Local Admin format"),
    ("SHAYANSKA-DL380\Administrator", "Hostname\Admin format")
)

$remoteHostname = $null
$winrmWorked = $false

Write-Host "=== Step 1: Connectivity Verification ===" -ForegroundColor Cyan

# Test TCP port 5985
Write-Host "`n[1.1] Testing TCP connection to $targetIP:5985 ..." -ForegroundColor Yellow
$tcpTest = Test-NetConnection -ComputerName $targetIP -Port 5985 -WarningAction SilentlyContinue
Write-Host "  TCP Test Result: $($tcpTest.TcpTestSucceeded)" -ForegroundColor $(if($tcpTest.TcpTestSucceeded){"Green"}else{"Red"})

if (-not $tcpTest.TcpTestSucceeded) {
    Write-Host "FAIL: TCP connection to WinRM port failed." -ForegroundColor Red
    exit 1
}

# Test WinRM remote command with each credential format
Write-Host "`n[1.2] Testing WinRM remote command (hostname) ..." -ForegroundColor Yellow

foreach ($credInfo in $credFormats) {
    $credStr = $credInfo[0]
    $credLabel = $credInfo[1]
    Write-Host "  Trying credential format: $credLabel ($credStr)" -ForegroundColor Gray
    
    try {
        $cred = New-Object System.Management.Automation.PSCredential($credStr, $securePass)
        $result = Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock { hostname } -ErrorAction Stop
        $remoteHostname = $result
        $winrmWorked = $true
        Write-Host "  SUCCESS with format: $credLabel" -ForegroundColor Green
        Write-Host "  Remote Hostname: $remoteHostname" -ForegroundColor Green
        break
    } catch {
        Write-Host "  FAILED: $_" -ForegroundColor Gray
    }
}

if (-not $winrmWorked) {
    Write-Host "`nFAIL: All credential formats failed." -ForegroundColor Red
    Write-Host "The password may be incorrect or WinRM may require different configuration." -ForegroundColor Red
    
    # Try without credentials (may work if PSRemoting is configured for trusted hosts)
    Write-Host "`n  Trying without credentials (TrustedHosts)..." -ForegroundColor Gray
    try {
        $result = Invoke-Command -ComputerName $targetIP -ScriptBlock { hostname } -ErrorAction Stop
        $remoteHostname = $result
        $winrmWorked = $true
        Write-Host "  SUCCESS without credentials" -ForegroundColor Green
        Write-Host "  Remote Hostname: $remoteHostname" -ForegroundColor Green
    } catch {
        Write-Host "  Also failed without credentials: $_" -ForegroundColor Red
    }
}

if ($winrmWorked) {
    if ($remoteHostname -eq "SHAYANSKA-DL380") {
        Write-Host "  Hostname MATCH: Confirmed SHAYANSKA-DL380" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: Hostname is '$remoteHostname', expected 'SHAYANSKA-DL380'" -ForegroundColor Yellow
    }
    
    Write-Host "`n[1.3] WinRM connectivity: VERIFIED" -ForegroundColor Green
} else {
    Write-Host "`n[1.3] WinRM connectivity: FAILED" -ForegroundColor Red
    Write-Host "Cannot proceed without WinRM access. Check credentials and WinRM config on target." -ForegroundColor Red
    exit 1
}

# Save results for later use
$step1Results = @{
    TcpTestSucceeded = $tcpTest.TcpTestSucceeded
    RemoteHostname = $remoteHostname
    HostnameConfirmed = ($remoteHostname -eq "SHAYANSKA-DL380")
    WinRMVerified = $winrmWorked
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

# Export step 1 results
$step1Results | ConvertTo-Json | Out-File -FilePath "step1_results.json" -Encoding UTF8

Write-Host "`nStep 1 results saved to step1_results.json" -ForegroundColor Green