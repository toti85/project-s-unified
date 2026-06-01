$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Invoke-Command -Session $s -ScriptBlock {
    $codePath = "C:\ProjectS\project-s-code"

    # Check how interactive_layer loads .env
    Write-Host "=== interactive_layer/__init__.py ==="
    $initPath = Join-Path $codePath "interactive_layer\__init__.py"
    if (Test-Path $initPath) {
        Get-Content $initPath
    } else {
        Write-Host "__init__.py not found"
    }

    Write-Host ""
    Write-Host "=== interactive_layer/main.py (first 50 lines) ==="
    $mainPath = Join-Path $codePath "interactive_layer\main.py"
    if (Test-Path $mainPath) {
        Get-Content $mainPath -TotalCount 50
    }

    Write-Host ""
    Write-Host "=== Checking dotenv import in main.py ==="
    $mainContent = Get-Content $mainPath -Raw
    if ($mainContent -match 'dotenv') {
        Write-Host "dotenv found in main.py"
        $lines = $mainContent -split "`n"
        for ($i = 0; $i -lt $lines.Length; $i++) {
            if ($lines[$i] -match 'dotenv|load_dotenv|\.env') {
                Write-Host "  Line $($i+1): $($lines[$i])"
            }
        }
    } else {
        Write-Host "dotenv NOT found in main.py"
    }

    # Test loading directly
    Write-Host ""
    Write-Host "=== Python dotenv test from code path ==="
    $test = python -c "
import sys
sys.path.insert(0, r'$codePath')
from dotenv import load_dotenv
import os
load_dotenv()
v = os.getenv('OPENROUTER_API_KEY', '')
print('Key loaded: ' + ('YES' if v else 'NO'))
print('Key length: ' + str(len(v)))
print('Key starts with: ' + v[:20] if v else 'N/A')
" 2>&1 | Out-String
    Write-Host $test
} -ErrorAction Stop

Remove-PSSession $s