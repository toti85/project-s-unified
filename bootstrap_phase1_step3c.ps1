$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

Write-Host "=== Creating Project-S subdirectories ===" -ForegroundColor Cyan

$scriptBlock = {
    $dirList = @(
        "C:\ProjectS",
        "C:\ProjectS\bootstrap",
        "C:\ProjectS\logs",
        "C:\ProjectS\reports"
    )
    foreach ($d in $dirList) {
        if (Test-Path $d) {
            Write-Host "EXISTS: $d"
        } else {
            New-Item -Path $d -ItemType Directory -Force | Out-Null
            Write-Host "CREATED: $d"
        }
    }
}

Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock $scriptBlock

Write-Host "`n=== Final verification ===" -ForegroundColor Cyan

$verifyBlock = {
    $dirList = @(
        "C:\ProjectS",
        "C:\ProjectS\bootstrap",
        "C:\ProjectS\logs",
        "C:\ProjectS\reports"
    )
    foreach ($d in $dirList) {
        if (Test-Path $d) {
            Write-Host "[OK] $d"
        } else {
            Write-Host "[FAIL] $d"
        }
    }
}

Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock $verifyBlock