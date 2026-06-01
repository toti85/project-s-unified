@echo off
REM Server Phase 1 — WinRM Remote Inventory (Auto-Elevating)
REM This batch file will request Administrator privileges and run the inventory

echo === Requesting Administrator privileges... ===

net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running as Administrator
    goto :run_inventory
)

echo Not running as Administrator. Relaunching with elevated privileges...
powershell -Command "Start-Process cmd -ArgumentList '/c \"%~dpnx0\"' -Verb RunAs"
echo Please wait for the elevated window...
exit /b

:run_inventory
echo.
echo === Running TrustedHosts configuration ===
winrm set "winrm/config/client" "@{TrustedHosts=\"192.168.1.180\"}"
echo.
echo === Running WinRM inventory ===
powershell -ExecutionPolicy Bypass -File scripts\winrm_inventory_192.168.1.180.ps1
echo.
echo === Done ===
pause