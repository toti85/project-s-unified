"""Probe 192.168.1.88 management ports."""
import socket
import time

def probe(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex((ip, port))
        s.close()
        return "OPEN" if result == 0 else "closed"
    except:
        return "error"

ports = [(3389, "RDP"), (22, "SSH"), (5985, "WinRM"), (5986, "WinRM-HTTPS"), (445, "SMB"), (80, "HTTP"), (443, "HTTPS")]
for p, n in ports:
    print(f"192.168.1.88:{p:5d} ({n:10s}) = {probe('192.168.1.88', p)}")