@echo off
REM Configure TrustedHosts for WinRM
winrm set "winrm/config/client" "@{TrustedHosts=\"192.168.1.180\"}"
echo Result: %errorLevel%
pause