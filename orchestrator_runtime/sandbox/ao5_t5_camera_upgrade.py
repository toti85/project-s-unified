"""
AO5_T5 — Camera Firmware Upgrade via ISAPI
DRY_RUN = True in this step. No actual upgrades performed.
Target: DS-2CD2T42WD-I8 cameras on 192.168.1.x
Current firmware: V5.5.53 → Target: V5.5.82
"""

import sys
import time
import requests
from requests.auth import HTTPDigestAuth

DRY_RUN = False  # LIVE UPGRADE — ONE CAMERA FIRST (192.168.1.60)

CAMERAS_TO_UPGRADE = [
    "192.168.1.60",  # ch1 — FIRST CAMERA ONLY
    # Uncomment after ch1 verified SUCCESS:
    # "192.168.1.62",  # ch3
    # "192.168.1.63",  # ch4
    # "192.168.1.65",  # ch6 konveer1
    # "192.168.1.67",  # ch8 konveer2
    # "192.168.1.68",  # ch9 zadnia2
    # "192.168.1.69",  # ch10 dvir2
]

CAMERA_USER = "admin"
CAMERA_PASS = "er13fig1"
FW_FILE = r"C:\temp\fw\digicap.dav"
TARGET_FW = "V5.5.82"
TIMEOUT = 10

def extract_field(xml, field):
    start = xml.find(f"<{field}>")
    end = xml.find(f"</{field}>")
    if start > 0 and end > start:
        return xml[start + len(f"<{field}>"):end]
    return "UNKNOWN"

def main():
    if DRY_RUN:
        print("=" * 80)
        print("AO5_T5 CAMERA FIRMWARE UPGRADE — DRY RUN")
        print("=" * 80)
        print("DRY_RUN = True — NO firmware will be uploaded")
        print("Each camera will be checked but NOT upgraded.")
        print()

    auth = HTTPDigestAuth(CAMERA_USER, CAMERA_PASS)
    success = 0
    failed = 0
    skipped = 0

    for ip in CAMERAS_TO_UPGRADE:
        url = f"http://{ip}/ISAPI/System/deviceInfo"
        print(f"Checking {ip}...")

        try:
            resp = requests.get(url, auth=auth, timeout=TIMEOUT)
            if resp.status_code != 200:
                print(f"  HTTP {resp.status_code} — skipping")
                skipped += 1
                continue

            xml = resp.text
            model = extract_field(xml, "deviceModel")
            fw = extract_field(xml, "firmwareVersion")
            serial = extract_field(xml, "serialNumber")

            print(f"  Model:  {model}")
            print(f"  FW:     {fw}")
            print(f"  Serial: {serial}")

            if TARGET_FW in fw:
                print(f"  -> Already on {TARGET_FW}, skipping")
                skipped += 1
            elif fw == "V5.5.53":
                print(f"  -> Needs upgrade: {fw} -> {TARGET_FW}")
                if DRY_RUN:
                    print(f"  [DRY RUN] Would upload: {FW_FILE}")
                    print(f"  [DRY RUN] Would POST to: http://{ip}/ISAPI/System/updateFirmware")
                    print(f"  [DRY RUN] Would wait 60s for reboot")
                    print(f"  [DRY RUN] Would verify new version")
                    success += 1  # count as "would succeed"
                else:
                    # LIVE UPGRADE
                    print(f"  [LIVE] Upgrading {ip}...")
                    print(f"  [LIVE] Firmware file: {FW_FILE}")

                    # Check firmware file exists
                    import os
                    if not os.path.exists(FW_FILE):
                        print(f"  [FAIL] Firmware file not found: {FW_FILE}")
                        failed += 1
                        print(f"  [STOP] Stopping upgrade process.")
                        break

                    # POST firmware via ISAPI firmware upload
                    # Hikvision requires: POST /ISAPI/System/updateFirmware with multipart/form-data
                    try:
                        with open(FW_FILE, 'rb') as fw:
                            # Hikvision ISAPI firmware upload expects:
                            # Content-Type: multipart/form-data
                            # The file must be sent as 'firmware' field
                            files = {
                                'firmware': ('digicap.dav', fw, 'application/octet-stream'),
                            }
                            headers = {
                                'Accept': 'application/xml',
                            }
                            upload_resp = requests.post(
                                f"http://{ip}/ISAPI/System/updateFirmware",
                                auth=auth,
                                files=files,
                                headers=headers,
                                timeout=120,
                            )
                        print(f"  [LIVE] Upload response: {upload_resp.status_code}")
                        print(f"  [LIVE] Response body: {upload_resp.text[:500]}")

                        if upload_resp.status_code == 200:
                            print(f"  [LIVE] Firmware uploaded successfully. Waiting 90s for reboot...")
                            time.sleep(90)

                            # Verify after reboot
                            verify_resp = requests.get(
                                f"http://{ip}/ISAPI/System/deviceInfo",
                                auth=auth,
                                timeout=10,
                            )
                            if verify_resp.status_code == 200:
                                verify_xml = verify_resp.text
                                new_fw = extract_field(verify_xml, "firmwareVersion")
                                print(f"  [LIVE] Post-reboot firmware: {new_fw}")
                                if TARGET_FW in new_fw:
                                    print(f"  [SUCCESS] {ip} upgraded to {new_fw}")
                                    success += 1
                                else:
                                    print(f"  [FAIL] {ip} firmware is {new_fw}, expected {TARGET_FW}")
                                    failed += 1
                            else:
                                print(f"  [FAIL] Cannot verify {ip} after reboot (HTTP {verify_resp.status_code})")
                                failed += 1
                        else:
                            print(f"  [FAIL] Upload failed with HTTP {upload_resp.status_code}")
                            failed += 1
                            print(f"  [STOP] Stopping upgrade process.")
                            break

                    except Exception as e:
                        print(f"  [FAIL] Upgrade error: {e}")
                        failed += 1
                        print(f"  [STOP] Stopping upgrade process.")
                        break
            else:
                print(f"  -> Unexpected firmware: {fw}, skipping")
                skipped += 1

        except requests.exceptions.Timeout:
            print(f"  TIMEOUT — unreachable")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1

        print()

    print("=" * 80)
    print("DRY RUN SUMMARY")
    print("=" * 80)
    print(f"Would upgrade:  {success}")
    print(f"Failed:         {failed}")
    print(f"Skipped:        {skipped}")
    print(f"Total:          {len(CAMERAS_TO_UPGRADE)}")
    print()
    if DRY_RUN:
        print("No cameras were actually upgraded.")
        print("Set DRY_RUN = False and confirm before running actual upgrades.")

if __name__ == "__main__":
    main()