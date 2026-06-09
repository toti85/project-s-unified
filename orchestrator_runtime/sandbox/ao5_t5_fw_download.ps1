# AO5_T5 — Download Hikvision firmware to DL380
# DL380: 192.168.1.180, WinRM port 15985

$cred = Get-Credential -Message "DL380 admin"

# Create fw directory on DL380
Invoke-Command -ComputerName 192.168.1.180 -Credential $cred -Port 15985 -ScriptBlock {
    if (!(Test-Path C:\temp\fw)) { New-Item -ItemType Directory -Path C:\temp\fw | Out-Null }
}

# List available firmware files on EU portal
Invoke-Command -ComputerName 192.168.1.180 -Credential $cred -Port 15985 -ScriptBlock {
    $url = "https://www.hikvisioneurope.com/eu/portal/?dir=portal%2FTechnical+Materials%2F00++Network+Camera%2F00++Product+Firmware%2FR6+platform+%282X22FWD%2C+2X42FWD%2C+2X52%2C64X4FWD%2C1X31%2C1X41%29%2FV5.5.82_Build190909"
    
    Write-Output "Fetching firmware page..."
    $resp = Invoke-WebRequest -Uri $url -UseBasicParsing
    
    Write-Output "`nAvailable links:"
    $resp.Links | Where-Object { $_.href -like "*.zip" -or $_.href -like "*.dav" -or $_.href -like "*.bin" } | ForEach-Object {
        Write-Output "  $($_.href) -> $($_.innerText)"
    }
    
    Write-Output "`nAll links (first 20):"
    $resp.Links | Select-Object -First 20 | ForEach-Object {
        Write-Output "  $($_.href)"
    }
}