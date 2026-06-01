"""Extended probe of 192.168.1.180 and check other DL380 NICs."""
import socket
import time
import subprocess

def probe(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        start = time.time()
        result = s.connect_ex((ip, port))
        elapsed = (time.time() - start) * 1000
        s.close()
        status = "OPEN" if result == 0 else "closed"
        return f"{status} ({elapsed:.0f}ms)"
    except Exception as e:
        return f"error: {e}"

# Extended port probe
ports = [
    (3389, "RDP"), (22, "SSH"), (5985, "WinRM"), (5986, "WinRM-HTTPS"),
    (445, "SMB"), (80, "HTTP"), (443, "HTTPS"), (135, "RPC"),
    (139, "NetBIOS"), (3306, "MySQL"), (1433, "MSSQL"), (8080, "HTTP-Alt"),
    (5988, "WinRM-HTTP-alt"), (8443, "HTTPS-Alt")
]

print("=== Extended probe of 192.168.1.180 (new DL380 host) ===")
for p, n in ports:
    result = probe("192.168.1.180", p)
    print(f"192.168.1.180:{p:5d} ({n:15s}) = {result}")

print()

# Ping test
print("=== Ping test ===")
try:
    result = subprocess.run(["ping", "-n", "2", "-w", "2000", "192.168.1.180"],
                          capture_output=True, text=True, timeout=10)
    print(result.stdout)
    print(result.stderr)
except Exception as e:
    print(f"Ping error: {e}")

# Check ARP for other DL380 MACs
print("=== ARP check for other DL380 NIC MACs ===")
dl380_macs = [
    "f4-03-43-3e-c6-80",
    "f4-03-43-3e-c6-81",
    "f4-03-43-3e-c6-82",
    "f4-03-43-3e-c6-83",
]
import re
arp_output = subprocess.run(["arp", "-a"], capture_output=True, text=True).stdout
for mac in dl380_macs:
    pattern = mac.replace("-", "(:|-)") + "|" + mac
    match = re.search(pattern, arp_output, re.IGNORECASE)
    if match:
        # Find the IP near this MAC
        lines = arp_output.split("\n")
        for line in lines:
            if mac in line.lower():
                print(f"FOUND: {line.strip()}")
    else:
        print(f"NOT FOUND in ARP: {mac}")