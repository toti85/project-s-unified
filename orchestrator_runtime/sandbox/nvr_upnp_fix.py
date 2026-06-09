"""
NVR UPnP Disable — ISAPI XML Structure Mirror
Target: 192.168.1.111:85 (Hikvision DS-7632NI-I2)
Strategy: GET current config → modify enabled flags → PUT back identical structure
"""

import sys
import time
import requests
from requests.auth import HTTPDigestAuth

NVR_URL = "http://192.168.1.111:85"
NVR_USER = "admin"
NVR_PASS = "er13fig1"

def main():
    auth = HTTPDigestAuth(NVR_USER, NVR_PASS)

    # Step 1: GET current UPnP config
    print("=== GET current UPnP config ===")
    resp = requests.get(
        f"{NVR_URL}/ISAPI/System/Network/UPnP",
        auth=auth,
        timeout=10,
    )
    print(f"GET status: {resp.status_code}")
    original_xml = resp.text
    print(f"Original XML ({len(original_xml)} bytes):")
    print(original_xml)
    print()

    # Step 2: Modify — set root <enabled> to false
    modified_xml = original_xml.replace("<enabled>true</enabled>", "<enabled>false</enabled>", 1)

    # Step 3: PUT modified config back
    print("=== PUT modified UPnP config (enabled=false) ===")
    resp = requests.put(
        f"{NVR_URL}/ISAPI/System/Network/UPnP",
        data=modified_xml.encode("utf-8"),
        auth=auth,
        headers={"Content-Type": "application/xml"},
        timeout=10,
    )
    print(f"PUT status: {resp.status_code}")
    print(f"PUT response ({len(resp.text)} bytes):")
    print(resp.text)
    print()

    # Step 4: Verify
    if resp.status_code == 200:
        print("=== VERIFY ===")
        time.sleep(1)
        resp = requests.get(
            f"{NVR_URL}/ISAPI/System/Network/UPnP",
            auth=auth,
            timeout=10,
        )
        print(f"VERIFY GET status: {resp.status_code}")
        print(resp.text)

        if "<enabled>false</enabled>" in resp.text:
            print("\n[OK] UPnP successfully disabled")
        else:
            print("\n[WARN] Verification unclear — check response manually")
    else:
        print(f"\n[FAIL] PUT returned {resp.status_code}")
        print("The XML structure may need adjustment. Check the NVR ISAPI manual.")

if __name__ == "__main__":
    main()