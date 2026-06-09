"""
NVR Camera Firmware Inventory — AO5_T5
Inventory only — does NOT upgrade.
Target: DS-2CD2T42WD-I8 cameras on 192.168.1.x
Target firmware: V5.5.82_Build190909
Credentials: hardcoded for DL380 remote execution context only.
"""

import sys
import requests
from requests.auth import HTTPDigestAuth

# All known camera IPs (192.168.1.60-76, gaps at .61 and .66 = offline)
CAMERAS = [
    {"ip": "192.168.1.60", "channel": "ch1"},
    {"ip": "192.168.1.62", "channel": "ch3"},
    {"ip": "192.168.1.63", "channel": "ch4"},
    {"ip": "192.168.1.64", "channel": "ch5"},
    {"ip": "192.168.1.65", "channel": "ch6 (konveer1)"},
    {"ip": "192.168.1.67", "channel": "ch8 (konveer2)"},
    {"ip": "192.168.1.68", "channel": "ch9 (zadnia2)"},
    {"ip": "192.168.1.69", "channel": "ch10 (dvir2)"},
    {"ip": "192.168.1.70", "channel": "ch11"},
    {"ip": "192.168.1.71", "channel": "ch12"},
    {"ip": "192.168.1.72", "channel": "ch13"},
    {"ip": "192.168.1.73", "channel": "ch14"},
    {"ip": "192.168.1.74", "channel": "ch15"},
    {"ip": "192.168.1.75", "channel": "ch16"},
    {"ip": "192.168.1.76", "channel": "ch17"},
]

TARGET_FW = "V5.5.82"
TIMEOUT = 5
NVR_USER = "admin"
NVR_PASS = "er13fig1"

def extract_field(xml, field):
    start = xml.find(f"<{field}>")
    end = xml.find(f"</{field}>")
    if start > 0 and end > start:
        return xml[start + len(f"<{field}>"):end]
    return "UNKNOWN"

def main():
    auth = HTTPDigestAuth(NVR_USER, NVR_PASS)

    print("=" * 90)
    print("NVR Camera Firmware Inventory — AO5_T5")
    print(f"Target firmware: {TARGET_FW}")
    print(f"Cameras scanned: {len(CAMERAS)}")
    print("=" * 90)
    print(f"{'Channel':<20} {'IP':<18} {'Model':<25} {'Firmware':<25} {'Status':<12}")
    print("-" * 90)

    needs_update = []
    up_to_date = []
    unreachable = []

    for cam in CAMERAS:
        ip = cam["ip"]
        ch = cam["channel"]
        url = f"http://{ip}/ISAPI/System/deviceInfo"

        try:
            resp = requests.get(url, auth=auth, timeout=TIMEOUT)
            if resp.status_code != 200:
                print(f"{ch:<20} {ip:<18} {'HTTP ' + str(resp.status_code):<25} {'—':<25} {'SKIP':<12}")
                unreachable.append(cam)
                continue

            xml = resp.text
            model = extract_field(xml, "deviceModel")
            fw = extract_field(xml, "firmwareVersion")

            if TARGET_FW in fw:
                status = "UP_TO_DATE"
                up_to_date.append(cam)
            else:
                status = "NEEDS_UPDATE"
                needs_update.append(cam)

            print(f"{ch:<20} {ip:<18} {model:<25} {fw:<25} {status:<12}")

        except requests.exceptions.Timeout:
            print(f"{ch:<20} {ip:<18} {'TIMEOUT':<25} {'—':<25} {'UNREACHABLE':<12}")
            unreachable.append(cam)
        except Exception as e:
            err = str(e)[:25]
            print(f"{ch:<20} {ip:<18} {err:<25} {'—':<25} {'UNREACHABLE':<12}")
            unreachable.append(cam)

    # Summary
    print("=" * 90)
    print("SUMMARY")
    print("=" * 90)
    print(f"Total cameras:    {len(CAMERAS)}")
    print(f"UP_TO_DATE:       {len(up_to_date)}")
    print(f"NEEDS_UPDATE:     {len(needs_update)}")
    print(f"UNREACHABLE:      {len(unreachable)}")

    if needs_update:
        print(f"\nCameras needing update ({len(needs_update)}):")
        for c in needs_update:
            print(f"  {c['ip']} ({c['channel']})")

    if unreachable:
        print(f"\nUnreachable cameras ({len(unreachable)}):")
        for c in unreachable:
            print(f"  {c['ip']} ({c['channel']})")

if __name__ == "__main__":
    main()