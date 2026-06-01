$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Invoke-Command -Session $s -ScriptBlock {
    $codePath = "C:\ProjectS\project-s-code"

    # Check if SAI module exists
    $saiPath = Join-Path $codePath "src\core\super_intelligent_ai.py"
    if (Test-Path $saiPath) {
        Write-Host "SAI module: EXISTS"
        Write-Host "Path: $saiPath"
        $content = Get-Content $saiPath -TotalCount 30
        Write-Host "First 30 lines:"
        Write-Host $content
    } else {
        Write-Host "SAI module: NOT FOUND at $saiPath"
        # Check if src directory exists
        $srcPath = Join-Path $codePath "src"
        if (Test-Path $srcPath) {
            Write-Host "src directory exists, listing contents:"
            Get-ChildItem $srcPath -Recurse -Name | Select-Object -First 20
        } else {
            Write-Host "src directory does NOT exist"
        }
    }

    # Check if SuperIntelligentAI class exists anywhere
    Write-Host ""
    Write-Host "Searching for SuperIntelligentAI class..."
    $searchResult = Select-String -Path (Join-Path $codePath "src") -Pattern "class SuperIntelligentAI" -ErrorAction SilentlyContinue
    if ($searchResult) {
        foreach ($r in $searchResult) {
            Write-Host "  Found: $($r.Path) line $($r.LineNumber): $($r.Line)"
        }
    } else {
        Write-Host "  SuperIntelligentAI class NOT FOUND in src/"
    }

    # Check what's in src/core
    $corePath = Join-Path $codePath "src\core"
    if (Test-Path $corePath) {
        Write-Host ""
        Write-Host "src/core contents:"
        Get-ChildItem $corePath -Name
    }
} -ErrorAction Stop

Remove-PSSession $s