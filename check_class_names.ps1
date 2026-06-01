 api key$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Invoke-Command -Session $s -ScriptBlock {
    $saiFile = "C:\ProjectS\project-s-code\src\core\super_intelligent_ai.py"
    Write-Host "=== Class definitions in super_intelligent_ai.py ==="
    $lines = Get-Content $saiFile
    foreach ($line in $lines) {
        if ($line -match '^class\s+') {
            Write-Host $line
        }
    }
} -ErrorAction Stop

Remove-PSSession $s