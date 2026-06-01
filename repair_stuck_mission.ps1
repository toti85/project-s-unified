$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

# Copy repair script to server
Copy-Item -Path "C:\ProjectS-Unified\repair_mission.py" -Destination "C:\ProjectS\repair_mission.py" -ToSession $s -Force

Invoke-Command -Session $s -ScriptBlock {
    python C:\ProjectS\repair_mission.py
} -ErrorAction Stop

Remove-PSSession $s