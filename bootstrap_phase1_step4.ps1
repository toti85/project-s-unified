$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

Write-Host "=== Step 4: Post-Install Verification (Fresh Process Test) ===" -ForegroundColor Cyan

# Test in a fresh remote PowerShell process
$freshTest = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    # Simulate a fresh process by not relying on session state
    $gitVer = & git --version 2>&1
    $pythonVer = & python --version 2>&1
    $pipVer = & pip --version 2>&1
    $pyLauncherExists = Test-Path "C:\Users\*\AppData\Local\py Launcher" -ErrorAction SilentlyContinue
    
    # Check PATH for Python and Git
    $pathEntries = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    $pythonInPath = $pathEntries -split ';' | Where-Object { $_ -like '*Python*' }
    $gitInPath = $pathEntries -split ';' | Where-Object { $_ -like '*Git*' }
    
    # Check Python installation location
    $pythonExe = Get-Command python -ErrorAction SilentlyContinue
    $gitExe = Get-Command git -ErrorAction SilentlyContinue
    
    [PSCustomObject]@{
        Git_Version = $gitVer
        Python_Version = $pythonVer
        Pip_Version = $pipVer
        Python_Exe_Path = if($pythonExe){$pythonExe.Source} else {"NOT FOUND"}
        Git_Exe_Path = if($gitExe){$gitExe.Source} else {"NOT FOUND"}
        PythonInPath = if($pythonInPath){($pythonInPath -join ';')} else {"NOT IN PATH"}
        GitInPath = if($gitInPath){($gitInPath -join ';')} else {"NOT IN PATH"}
        Python312Dir = Test-Path "C:\Program Files\Python312"
        GitInstallDir = if($gitInPath){$true} else {$false}
    }
}

Write-Host "`n--- Fresh Process Results ---" -ForegroundColor Yellow
$freshTest | Format-List | Out-String | Write-Host

# Save results
$freshTest | ConvertTo-Json | Out-File -FilePath "step4_verification.json" -Encoding UTF8
Write-Host "`nStep 4 results saved to step4_verification.json" -ForegroundColor Green
Write-Host "`nStep 4 complete." -ForegroundColor Green