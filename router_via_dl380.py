import winrm, sys, re, base64, hashlib
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

s = winrm.Session('http://46.253.140.72:15985/wsman',
    auth=('Administrator','Qwe123'),
    transport='ntlm')

def run(ps):
    r = s.run_ps(ps)
    out = r.std_out.decode('utf-8','replace').strip()
    err = r.std_err.decode('utf-8','replace').strip()
    if err and 'CLIXML' not in err and len(err) > 50:
        print("  [ps-err]", err[:200])
    return out

# Check if Python is available on DL380
py_check = run(r"python --version 2>&1; if (-not $?) { python3 --version 2>&1 }")
print("DL380 Python:", py_check)

# Write Python script to DL380 and run it
py_script = r"""
import sys, io, hashlib, base64, re, requests, urllib3
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
urllib3.disable_warnings()
base = 'http://192.168.1.1'

pw_md5 = hashlib.md5(b'admin').hexdigest()
b64 = base64.b64encode(('admin:' + pw_md5).encode()).decode()
cval = 'Basic%20' + b64.replace('=','%3D')

def new_session():
    s = requests.Session()
    s.headers.update({'Cookie': f'Authorization={cval}'})
    lr = s.get(base + '/userRpm/LoginRpm.htm?Save=Save', timeout=5)
    m = re.search(r'location\.href\s*=\s*"http://192\.168\.1\.1/([A-Z]+)/', lr.text)
    sess = m.group(1) if m else None
    return s, sess

# === UPnP (fresh session, first request) ===
s1, sess1 = new_session()
print('SESSION1:', sess1)
upnp_html = s1.get(f'{base}/{sess1}/userRpm/UPnPRpm.htm',
    headers={'Referer': f'http://192.168.1.1/{sess1}/userRpm/Index.htm'}, timeout=10).text
print('UPnP size:', len(upnp_html))
print('UPnP raw (first 2000):')
print(upnp_html[:2000])

# === DHCP Clients (fresh session) ===
s2, sess2 = new_session()
print('\nSESSION2:', sess2)
dhcp_html = s2.get(f'{base}/{sess2}/userRpm/AssignedIpAddrListRpm.htm',
    headers={'Referer': f'http://192.168.1.1/{sess2}/userRpm/Index.htm'}, timeout=10).text
print('DHCP size:', len(dhcp_html))
print('DHCP raw (first 3000):')
print(dhcp_html[:3000])
"""

# Write and run on DL380, save output to file, then read back
ps_run = f"""
$py = @'
{py_script}
'@
$py | Out-File -FilePath 'C:\\router_login.py' -Encoding utf8
python 'C:\\router_login.py' 2>&1 | Out-File -FilePath 'C:\\router_output.txt' -Encoding utf8
Get-Content 'C:\\router_output.txt'
"""
result = run(ps_run)
print("\n=== DL380 Python result ===")
print(result)
