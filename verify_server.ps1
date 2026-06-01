$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    Write-Host "=== Server State Check ===" -ForegroundColor Cyan
    
    # Check C:\ProjectS
    if (Test-Path "C:\ProjectS") {
        Write-Host "C:\ProjectS exists" -ForegroundColor Green
        $projectSItems = Get-ChildItem "C:\ProjectS" -Force
        foreach ($item in $projectSItems) {
            Write-Host "  - $($item.Name) ($($item.Mode))" -ForegroundColor Yellow
        }
        
        # Check project-s-code
        $codeDir = "C:\ProjectS\project-s-code"
        if (Test-Path $codeDir) {
            Write-Host "`nC:\ProjectS\project-s-code exists" -ForegroundColor Green
            $fileCount = (Get-ChildItem $codeDir -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object).Count
            $dirCount = (Get-ChildItem $codeDir -Recurse -Force -Directory -ErrorAction SilentlyContinue | Measure-Object).Count
            Write-Host "  Files: $fileCount" -ForegroundColor Green
            Write-Host "  Dirs: $dirCount" -ForegroundColor Green
            
            # List top-level items
            Write-Host "`nTop-level items in project-s-code:" -ForegroundColor Yellow
            Get-ChildItem $codeDir -Force | Select-Object Name, Mode | Format-Table -AutoSize
        } else {
            Write-Host "C:\ProjectS\project-s-code does NOT exist" -ForegroundColor Red
        }
        
        # Check if robocopy created files at a different location
        Write-Host "`nAll items in C:\ProjectS (recursive count):" -ForegroundColor Yellow
        $allInProjectS = Get-ChildItem "C:\ProjectS" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  Total items: $($allInProjectS.Count)" -ForegroundColor Gray
    } else {
        Write-Host "C:\ProjectS does NOT exist" -ForegroundColor Red
    }
    
    # Check C:\ProjectS-Unified (should not exist on server)
    if (Test-Path "C:\ProjectS-Unified") {
        Write-Host "`nC:\ProjectS-Unified exists (unexpected)" -ForegroundColor Red
    } else {
        Write-Host "`nC:\ProjectS-Unified does not exist (expected)" -ForegroundColor Green
    }
}