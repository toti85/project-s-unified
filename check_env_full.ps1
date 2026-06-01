$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Invoke-Command -Session $s -ScriptBlock {
    $envPath = "C:\ProjectS\project-s-code\.env"
    Write-Host "=== .env file contents ==="
    $content = Get-Content $envPath -Raw
    Write-Host $content
    Write-Host ""
    Write-Host "=== OPENROUTER_API_KEY line ==="
    $lines = $content -split "`n"
    foreach ($line in $lines) {
        if ($line -match 'OPENROUTER_API_KEY') {
            Write-Host $line
            Write-Host "Full line length: $($line.Length)"
        }
    }
} -ErrorAction Stop

Remove-PSSession $s