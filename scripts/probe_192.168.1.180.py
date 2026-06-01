"""Probe 192.168.1.180 (new DL380 host) management ports."""
import socket
import time

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

ports = [(3389, "RDP"), (22, "SSH"), (5985, "WinRM"), (5986, "WinRM-HTTPS"), (445, "SMB"), (80, "HTTP"), (443, "HTTPS")]
print(f"=== Probing 192.168.1.180 (new DL380 host, MAC F4:03:43:3E:C6:80) ===")
for p, n in ports:
    result = probe("192.168.1.180", p)
    print(f"192.168.1.180:{p:5d} ({n:10s}) = {result}")