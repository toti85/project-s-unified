$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Invoke-Command -Session $s -ScriptBlock {
    $envPath = "C:\ProjectS\project-s-code\.env"
    if (Test-Path $envPath) {
        $content = Get-Content $envPath -Raw
        if ($content -match 'OPENROUTER_API_KEY') {
            $match = $matches[0]
            $keyPart = $match.Substring($match.IndexOf('=') + 1)
            if ($keyPart.Length -gt 10) {
                Write-Host "OPENROUTER_API_KEY: PRESENT (length=$($keyPart.Length))"
            } else {
                Write-Host "OPENROUTER_API_KEY: EMPTY"
            }
        } else {
            Write-Host "OPENROUTER_API_KEY: MISSING"
        }
    } else {
        Write-Host ".env file: NOT FOUND"
    }

    # Verify dotenv loads it
    try {
        $loadTest = python -c "import os; from dotenv import load_dotenv; load_dotenv(); v=os.getenv('OPENROUTER_API_KEY',''); print('dotenv loaded: ' + ('YES' if v else 'NO') + ' (present=' + ('YES' if v else 'NO') + ')')" 2>&1 | Out-String
        Write-Host $loadTest
    } catch {
        Write-Host "dotenv load test failed: $_"
    }
} -ErrorAction Stop

Remove-PSSession $s