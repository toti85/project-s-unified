@echo off
winrm set winrm/config/client "@{TrustedHosts=\"192.168.1.180\"}"
echo Exit code: %errorlevel%
pause