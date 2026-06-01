# SHAYANSKA-DL380 Bootstrap Phase 1 - Step 3: Version Verification + Directory Creation
# Verifies installed versions and creates Project-S directories

$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

Write-Host "=== Step 3: Version Verification + Directory Creation ===" -ForegroundColor Cyan

# Part A: Verify installed versions
Write-Host "`n[3.A] Version Verification" -ForegroundColor Yellow
$versions = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    $gitVer = git --version 2>&1
    $pythonVer = python --version 2>&1
    $pipVer = pip --version 2>&1
    
    [PSCustomObject]@{
        Git_Version = $gitVer
        Python_Version = $pythonVer
        Pip_Version = $pipVer
    }
}

Write-Host "  Git:     $($versions.Git_Version)" -ForegroundColor Green
Write-Host "  Python:  $($versions.Python_Version)" -ForegroundColor Green
Write-Host "  Pip:     $($versions.Pip_Version)" -ForegroundColor Green

# Part B: Create Project-S directories
Write-Host "`n[3.B] Creating Project-S target directories" -ForegroundColor Yellow
$dirs = @("C:\ProjectS", "C:\ProjectS\bootstrap", "C:\ProjectS\logs", "C:\ProjectS\reports")

$dirResults = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    param($dirs)
    $results = @()
    foreach ($dir in $dirs) {
        $exists = Test-Path $dir
        if (-not $exists) {
            New-Item -Path $dir -ItemType Directory -Force | Out-Null
            $results += [PSCustomObject]@{
                Directory = $dir
                Created   = $true
                Exists    = $true
            }
        } else {
            $results += [PSCustomObject]@{
                Directory = $dir
                Created   = $false
                Exists    = $true
            }
        }
    }
    $results
} -ArgumentList $dirs

foreach ($r in $dirResults) {
    $status = if ($r.Created) { "CREATED" } else { "EXISTS" }
    Write-Host "  [$status] $($r.Directory)" -ForegroundColor Green
}

# Part C: Verify directories exist
Write-Host "`n[3.C] Verification of directory creation" -ForegroundColor Yellow
$verifyDirs = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    param($dirs)
    foreach ($dir in $dirs) {
        $exists = Test-Path $dir
        $status = if($exists){"OK"}else{"FAIL"}
        $color = if($exists){"Green"}else{"Red"}
        Write-Host "  [$status] $dir" -ForegroundColor $color
    }
} -ArgumentList $dirs

# Save results
$step3Results = @{
    Git_Version = $versions.Git_Version
    Python_Version = $versions.Python_Version
    Pip_Version = $versions.Pip_Version
    Directories = $dirResults | ForEach-Object { @{ Directory = $_.Directory; Created = $_.Created; Exists = $_.Exists } }
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

$step3Results | ConvertTo-Json | Out-File -FilePath "step3_results.json" -Encoding UTF8
Write-Host "`nStep 3 results saved to step3_results.json" -ForegroundColor Green
Write-Host "`nStep 3 complete." -ForegroundColor Green