# AO5_T5 — Camera Firmware Inventory via DL380 WinRM
# DL380: 192.168.1.180, WinRM port 15985

$cred = Get-Credential -Message "DL380 admin credentials"

# Ensure C:\temp exists on DL380
Invoke-Command -ComputerName 192.168.1.180 -Credential $cred -Port 15985 -ScriptBlock {
    if (!(Test-Path C:\temp)) { New-Item -ItemType Directory -Path C:\temp | Out-Null }
}

# Copy script to DL380
Copy-Item -Path "C:\ProjectS-Unified\orchestrator_runtime\sandbox\ao5_t5_camera_fw_check.py" `
          -Destination "\\192.168.1.180\C$\temp\ao5_t5_camera_fw_check.py" `
          -Credential $cred -Force

# Run on DL380
$result = Invoke-Command -ComputerName 192.168.1.180 -Credential $cred -Port 15985 -ScriptBlock {
    cd C:\temp
    python ao5_t5_camera_fw_check.py
}

Write-Output $result