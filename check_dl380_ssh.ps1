# Check OpenSSH status on DL380 via WinRM
# NOTE: Requires interactive credential prompt
# Run: powershell -ExecutionPolicy Bypass -File check_dl380_ssh.ps1

$ErrorActionPreference = 'Continue'
Write-Output "Attempting WinRM connection to DL380..."

try {
    $s = New-PSSession -ComputerName "46.253.140.72" -Port 15985 -UseSSL:$false -Authentication Basic -Credential (Get-Credential) -ErrorAction Stop
    Write-Output "CONNECTED (HTTP)"
} catch {
    Write-Output "HTTP failed, trying SSL with skips..."
    try {
        $opt = New-PSSessionOption -SkipCACheck -SkipCNCheck -SkipRevocationCheck
        $s = New-PSSession -ComputerName "46.253.140.72" -Port 15985 -SessionOption $opt -Authentication Negotiate -Credential (Get-Credential) -ErrorAction Stop
        Write-Output "CONNECTED (SSL with skips)"
    } catch {
        Write-Output "CONNECTION_FAILED: $_"
        Write-Output "Manual intervention required - run this script interactively"
        exit 1
    }
}

$result = Invoke-Command -Session $s -ScriptBlock {
    Write-Output "=== OpenSSH Capabilities ==="
    Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH*' | Format-Table Name, State -AutoSize
    Write-Output "=== sshd Service ==="
    $sshd = Get-Service sshd -ErrorAction SilentlyContinue
    if ($sshd) { $sshd | Format-Table Name, Status, StartType -AutoSize } else { Write-Output "sshd: NOT INSTALLED" }
    Write-Output "=== Firewall Rules for SSH ==="
    Get-NetFirewallRule -DisplayName "*SSH*" -ErrorAction SilentlyContinue | Format-Table DisplayName, Enabled, Direction -AutoSize
    Write-Output "=== DL380 LAN IP ==="
    (Get-NetIPAddress -InterfaceAlias '*Eth*' -AddressFamily IPv4 | Where-Object IPAddress -notlike '127.*').IPAddress
}
$result
Remove-PSSession $s