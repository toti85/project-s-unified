$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

$dirs = @('C:\ProjectS', 'C:\ProjectS\bootstrap', 'C:\ProjectS\logs', 'C:\ProjectS\reports')

Write-Host "=== Creating Project-S subdirectories ===" -ForegroundColor Cyan

Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    param($dirs)
    foreach ($d in $dirs) {
        if (-not (Test-Path $d)) {
            New-Item -Path $d -ItemType Directory -Force | Out-Null
            Write-Host "CREATED: $d" -ForegroundColor Green
        } else {
            Write-Host "EXISTS: $d" -ForegroundColor Yellow
        }
    }
} -ArgumentList $dirs

Write-Host "`n=== Verifying all directories ===" -ForegroundColor Cyan

Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    param($dirs)
    foreach ($d in $dirs) {
        $exists = Test-Path $d
        if ($exists) {
            Write-Host "[OK] $d" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] $d" -ForegroundColor Red
        }
    }
} -ArgumentList $dirs