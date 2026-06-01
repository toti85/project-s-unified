"""
Detailed iLO status check for DL380 server
Read-only: power state, system info, health, NIC status, event logs
"""
import sys
sys.path.insert(0, 'C:\\ProjectS-Unified')
from project_s.infrastructure.ilo_controller import ILOController

ILO_URL = 'https://46.253.140.72:89'
ILO_USERNAME = 'Administrator'
ILO_PASSWORD = 'PTSYK7BF'

controller = ILOController(url=ILO_URL, username=ILO_USERNAME, password=ILO_PASSWORD, timeout=15, verify_ssl=False)

print('[ILO] === DETAILED ILO STATUS CHECK ===')
print()

# 1. Connect
print('[ILO] 1. Connecting...')
try:
    controller.connect()
    print('[ILO] Connected OK')
except Exception as e:
    print(f'[ILO] Connection FAILED: {e}')
    sys.exit(1)

# 2. System info (full)
print()
print('[ILO] 2. Full System Info...')
try:
    sys_info = controller.get_system_info()
    for key in ['Name','Id','Model','Manufacturer','SerialNumber','PowerState','BiosVersion','Status','SystemType']:
        val = sys_info.get(key, 'N/A')
        print(f'[ILO]   {key}: {val}')
    # Print Oem.hpe if present
    oem = sys_info.get('Oem', {})
    if oem:
        hpe = oem.get('hpe', {})
        if hpe:
            print(f'[ILO]   Oem.hpe keys: {list(hpe.keys())}')
            # Print HostCorrelation info
            hc = hpe.get('HostCorrelation', {})
            if hc:
                print(f'[ILO]   HostCorrelation: {hc}')
    print('[ILO] System info OK')
except Exception as e:
    print(f'[ILO] System info FAILED: {e}')

# 3. Health summary
print()
print('[ILO] 3. Health Summary...')
try:
    health = controller.get_health_summary()
    for k, v in health.items():
        print(f'[ILO]   {k}: {v}')
except Exception as e:
    print(f'[ILO] Health FAILED: {e}')

# 4. EthernetInterfaces (host OS NICs)
print()
print('[ILO] 4. EthernetInterfaces (Host OS NICs)...')
try:
    eth_resp = controller._request('GET', '/redfish/v1/Systems/1/EthernetInterfaces/')
    if 'Members' in eth_resp and eth_resp['Members']:
        members = eth_resp['Members']
        print(f'[ILO]   Found {len(members)} EthernetInterface(s)')
        for m in members:
            uri = m.get('@odata.id', '')
            print(f'[ILO]   Interface: {uri}')
            iface = controller._request('GET', uri)
            for key in ['Id','Name','InterfaceType','LinkStatus','IPv4Addresses','IPv6Addresses','PermanentMACAddress','MACAddress','SpeedMbps','Status']:
                val = iface.get(key, 'N/A')
                print(f'[ILO]     {key}: {val}')
            print()
    else:
        count = eth_resp.get('Members@odata.count', 0)
        print(f'[ILO]   Count: {count}')
        if count > 0:
            for m in eth_resp.get('Members', []):
                uri = m.get('@odata.id', '')
                iface = controller._request('GET', uri)
                print(f'[ILO]   Interface {uri}:')
                for key in ['Id','Name','InterfaceType','LinkStatus','IPv4Addresses','PermanentMACAddress','MACAddress','SpeedMbps','Status']:
                    print(f'[ILO]     {key}: {iface.get(key, "N/A")}')
                print()
except Exception as e:
    print(f'[ILO] EthernetInterfaces FAILED: {e}')
    import traceback
    traceback.print_exc()

# 5. iLO Network settings
print()
print('[ILO] 5. iLO Network Settings (Manager NIC)...')
try:
    net_resp = controller._request('GET', '/redfish/v1/Managers/1/EthernetInterfaces/1/')
    for key in ['Id','Name','IPv4Addresses','IPv6Addresses','PermanentMACAddress','MACAddress','LinkStatus','SpeedMbps','Status']:
        print(f'[ILO]   {key}: {net_resp.get(key, "N/A")}')
except Exception as e:
    print(f'[ILO] Network settings FAILED: {e}')

# 6. iLO Event Log
print()
print('[ILO] 6. iLO Event Log (last 10 entries)...')
try:
    events_resp = controller._request('GET', '/redfish/v1/Systems/1/LogServices/Log1/Entries/')
    if 'Members' in events_resp and events_resp['Members']:
        entries = events_resp['Members']
        print(f'[ILO]   Found {len(entries)} log entries')
        for entry in entries[-10:]:
            entry_id = entry.get('Id','?')
            msg = entry.get('Message','N/A')
            created = entry.get('Created','N/A')
            severity = entry.get('Severity','N/A')
            print(f'[ILO]   [{entry_id}] {created} [{severity}] {msg}')
    else:
        print(f'[ILO]   No Members. Count: {events_resp.get("Members@odata.count", "N/A")}')
        print(f'[ILO]   Keys: {list(events_resp.keys())[:15]}')
except Exception as e:
    print(f'[ILO] Event log FAILED: {e}')

# 7. iLO System Log
print()
print('[ILO] 7. iLO System Log (last 10 entries)...')
try:
    syslog_resp = controller._request('GET', '/redfish/v1/Systems/1/LogServices/SystemLog/Entries/')
    if 'Members' in syslog_resp and syslog_resp['Members']:
        entries = syslog_resp['Members']
        print(f'[ILO]   Found {len(entries)} system log entries')
        for entry in entries[-10:]:
            entry_id = entry.get('Id','?')
            msg = entry.get('Message','N/A')
            created = entry.get('Created','N/A')
            severity = entry.get('Severity','N/A')
            print(f'[ILO]   [{entry_id}] {created} [{severity}] {msg}')
    else:
        print(f'[ILO]   No Members. Count: {syslog_resp.get("Members@odata.count", "N/A")}')
except Exception as e:
    print(f'[ILO] System log FAILED: {e}')

# 8. Managers info
print()
print('[ILO] 8. Managers Info...')
try:
    mgr_resp = controller._request('GET', '/redfish/v1/Managers/1/')
    for key in ['Id','Name','Model','FirmwareVersion','Status','Description']:
        print(f'[ILO]   {key}: {mgr_resp.get(key, "N/A")}')
    # Print license info
    license_info = mgr_resp.get('LicenseStatus', 'N/A')
    print(f'[ILO]   LicenseStatus: {license_info}')
except Exception as e:
    print(f'[ILO] Managers info FAILED: {e}')

# 9. Power info
print()
print('[ILO] 9. Power Info...')
try:
    power_resp = controller._request('GET', '/redfish/v1/Systems/1/')
    # Check for PowerSummary or Power values
    ps = power_resp.get('PowerState', 'N/A')
    print(f'[ILO]   PowerState: {ps}')
    # Check for PSU info in Oem.hpe
    oem = power_resp.get('Oem', {})
    hpe = oem.get('hpe', {})
    if hpe:
        # Check for power supply info
        for hkey in ['PowerSupplies', 'PowerSummary']:
            if hkey in hpe:
                print(f'[ILO]   Oem.hpe.{hkey}: {hpe[hkey]}')
except Exception as e:
    print(f'[ILO] Power info FAILED: {e}')

# 10. Thermal info
print()
print('[ILO] 10. Thermal Info...')
try:
    thermal_resp = controller._request('GET', '/redfish/v1/Systems/1/')
    oem = thermal_resp.get('Oem', {})
    hpe = oem.get('hpe', {})
    if hpe:
        for hkey in ['ThermalSupplies', 'ThermalSummary']:
            if hkey in hpe:
                print(f'[ILO]   Oem.hpe.{hkey}: {hpe[hkey]}')
    # Also check standard Thermal
    thermal = thermal_resp.get('Thermal', {})
    if thermal:
        fans = thermal.get('Fans', [])
        if fans:
            print(f'[ILO]   Fans: {len(fans)}')
            for fan in fans[:5]:
                print(f'[ILO]     {fan.get("Name","?"):20s} speed={fan.get("SpeedRPM","N/A")} status={fan.get("Status",{}).get("State","N/A")}')
except Exception as e:
    print(f'[ILO] Thermal info FAILED: {e}')

print()
print('[ILO] === ALL CHECKS COMPLETE ===')
controller.close()