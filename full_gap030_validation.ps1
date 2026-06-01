$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GAP_030 FULL LIVE VALIDATION" -ForegroundColor Cyan
Write-Host "  Method: Start server + run test via localhost" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Deploy all files
Write-Host "`n[1/6] Deploying files..." -ForegroundColor Yellow
Copy-Item -Path "C:\ProjectS-Unified\interactive_layer\sai_runner.py" -Destination "C:\ProjectS\project-s-code\interactive_layer\sai_runner.py" -ToSession $s -Force
Copy-Item -Path "C:\ProjectS-Unified\interactive_layer\start_server.py" -Destination "C:\ProjectS\project-s-code\interactive_layer\start_server.py" -ToSession $s -Force
Copy-Item -Path "C:\ProjectS-Unified\full_gap030_validation.py" -Destination "C:\ProjectS\full_gap030_validation.py" -ToSession $s -Force
Write-Host "  Deployed: sai_runner.py, start_server.py, full_gap030_validation.py"

# Run everything on server
Write-Host "[2/6] Running full validation on server..." -ForegroundColor Yellow
$validationOutput = Invoke-Command -Session $s -ScriptBlock {
    python C:\ProjectS\full_gap030_validation.py 2>&1 | Out-String
}

Write-Host "`n=== VALIDATION OUTPUT ===" -ForegroundColor Cyan
Write-Host $validationOutput

# Save results
$validationOutput | Out-File -FilePath "C:\ProjectS-Unified\.gap030_validation_output.txt" -Encoding UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VALIDATION COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Remove-PSSession $s