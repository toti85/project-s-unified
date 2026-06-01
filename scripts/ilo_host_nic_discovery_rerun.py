"""
Server Phase 1 Host LAN Reachability Discovery — Rerun.
Re-query iLO Redfish host EthernetInterfaces after LAN cable connection.
"""
import requests
import json
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

ILO_URL = "https://46.253.140.72:89"
ILO_USER = "Administrator"
ILO_PASS = "PTSYK7BF"

def fetch_nic(idx):
    auth = (ILO_USER, ILO_PASS)
    ep = f"/redfish/v1/Systems/1/EthernetInterfaces/{idx}/"
    try:
        r = requests.get(ILO_URL + ep, auth=auth, verify=False, timeout=10, allow_redirects=False)
        if r.status_code == 200:
            data = r.json()
            print(f"=== NIC {idx} ===")
            print(json.dumps(data, indent=2))
            print()
        else:
            loc = r.headers.get("Location", "none")
            print(f"NIC {idx}: status={r.status_code}, redirect={loc}")
            if loc and "192.168" in loc:
                r2 = requests.get(ILO_URL + loc, auth=auth, verify=False, timeout=10, allow_redirects=False)
                if r2.status_code == 200:
                    data = r2.json()
                    print(f"=== NIC {idx} (after rewrite) ===")
                    print(json.dumps(data, indent=2))
                    print()
    except Exception as e:
        print(f"NIC {idx} error: {e}")

def main():
    print("=== Server Phase 1 Host LAN Reachability Discovery — RERUN ===")
    print(f"Time: 2026-05-15 ~13:50 UTC+3")
    print(f"Context: Host LAN cable now confirmed physically connected")
    print()
    
    for i in range(1, 5):
        fetch_nic(i)

if __name__ == "__main__":
    main()