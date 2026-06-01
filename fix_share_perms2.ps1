$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

Write-Host "=== Fixing SMB Share Permissions v2 ===" -ForegroundColor Cyan

# Use net share to delete and recreate with Everyone full control
Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    $shareName = "ProjectSStage"
    $sharePath = "C:\ProjectS\project-s-code"
    
    Write-Host "[1] Deleting existing share..." -ForegroundColor Gray
    net share $shareName /delete /y
    Start-Sleep -Seconds 2
    
    Write-Host "[2] Recreating share with Everyone full control..." -ForegroundColor Gray
    # NET SHARE sharename=path /grant:Everyone,FULL
    net share $shareName=$sharePath /grant:Everyone,FULL /remark:"ProjectS staging"
    
    Write-Host "[3] Verifying share..." -ForegroundColor Gray
    net share $shareName
    
    Write-Host "[4] Checking share permissions..." -ForegroundColor Gray
    $shareInfo = net share $shareName
    Write-Host $shareInfo -ForegroundColor Gray
}

Write-Host ""
Write-Host "Share recreated. Testing UNC access..." -ForegroundColor Cyan

# Test UNC
$destUNC = "\\192.168.1.180\ProjectSStage"
net use $destUNC Qwe123 /user:192.168.1.180\Administrator 2>$null
Start-Sleep -Seconds 3

$uncTest = Test-Path $destUNC
Write-Host "  UNC path reachable: $uncTest" -ForegroundColor $(if($uncTest){"Green"}else{"Red"})

if ($uncTest) {
    Write-Host "  Testing write access..." -ForegroundColor Gray
    $testFile = Join-Path $destUNC ".write_test"
    try {
        Set-Content -Path $testFile -Value "test" -ErrorAction Stop
        Write-Host "  Write access: OK" -ForegroundColor Green
        Remove-Item $testFile -ErrorAction SilentlyContinue
        Write-Host "  Test file removed" -ForegroundColor Gray
    } catch {
        Write-Host "  Write access: FAIL - $_" -ForegroundColor Red
    }
}

# Cleanup
$delShare = $destUNC
net use $delShare /delete /y 2>$null