import subprocess
import sys

# Test WinRM via PowerShell with credentials
ps_script = r"""
$secPass = ConvertTo-SecureString 'Qwe123' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential('Administrator', $secPass)

Write-Output "=== Testing LAN WinRM ==="
try {
    $s = New-PSSession -ComputerName 192.168.1.180 -Credential $cred -ErrorAction Stop
    $r = Invoke-Command -Session $s -ScriptBlock { hostname }
    Write-Output ("LAN OK: " + $r)
    Remove-PSSession $s
} catch {
    Write-Output ("LAN FAIL: " + $_.Exception.Message)
}

Write-Output "=== Testing External WinRM ==="
try {
    $opts = New-PSSessionOption -SkipCACheck -SkipCNCheck -SkipRevocationCheck
    $s2 = New-PSSession -ComputerName 46.253.140.72 -Port 15985 -UseSSL -Credential $cred -SessionOption $opts -Authentication Basic -ErrorAction Stop
    $r2 = Invoke-Command -Session $s2 -ScriptBlock { hostname }
    Write-Output ("EXT OK: " + $r2)
    Remove-PSSession $s2
} catch {
    Write-Output ("EXT FAIL: " + $_.Exception.Message)
}
"""

result = subprocess.run(
    ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
    capture_output=True, text=True, timeout=60, cwd=r'C:\ProjectS-Unified'
)

output = result.stdout + result.stderr
print(output)

with open(r'C:\ProjectS-Unified\winrm_cred_result.txt', 'w', encoding='utf-8') as f:
    f.write(output)

print("Results saved to winrm_cred_result.txt")