"""
Read-only iLO host NIC discovery for new DL380 Gen9.
Gets EthernetInterfaces from Redfish API to identify host OS network config.
"""
import requests
import json
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

ILO_URL = "https://46.253.140.72:89"
ILO_USER = "Administrator"
ILO_PASS = "PTSYK7BF"

def main():
    auth = (ILO_USER, ILO_PASS)
    
    # Try to get host NIC info from iLO Redfish API
    endpoints = [
        "/redfish/v1/Systems/1/EthernetInterfaces/",
        "/redfish/v1/Systems/1/NetworkInterfaces/",
        "/redfish/v1/Managers/1/NetworkInterfaces/",
    ]
    
    for ep in endpoints:
        try:
            print(f"Trying: {ep}")
            r = requests.get(ILO_URL + ep, auth=auth, verify=False, timeout=10, allow_redirects=False)
            print(f"  Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                print(json.dumps(data, indent=2)[:3000])
                print("---")
            else:
                loc = r.headers.get("Location", "none")
                print(f"  Redirect: {loc}")
                if loc and "192.168" in loc:
                    # Rewrite redirect
                    r2 = requests.get(ILO_URL + loc, auth=auth, verify=False, timeout=10, allow_redirects=False)
                    print(f"  After rewrite: {r2.status_code}")
                    if r2.status_code == 200:
                        data = r2.json()
                        print(json.dumps(data, indent=2)[:3000])
                        print("---")
        except Exception as e:
            print(f"  Error: {e}")
        print()

if __name__ == "__main__":
    main()