#!/usr/bin/env python3
"""
MikroTik WiFi Stability Auto-Config — Step 0: Collect Config
Connects via SSH to RouterOS, collects router info, wireless config, DHCP config.
"""

import paramiko
import sys
import time
import os

HOST = "192.168.88.1"
USER = "admin"
PASS = "admin"

COLLECT_COMMANDS = [
    "/system resource print",
    "/system routerboard print",
    "/interface print detail",
    "/interface wireless print detail",
    "/interface wifi print detail",
    "/ip address print",
    "/ip route print",
    "/ip dhcp-server print",
    "/ip dhcp-server network print",
    "/ip dhcp-server lease print",
    "/ip dns print",
    "/ip firewall nat print",
    "/ip firewall filter print",
    "/ip service print",
    "/user print",
]

def wait_for_prompt(conn, timeout=10):
    """Wait for RouterOS prompt and return accumulated output."""
    output = b""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if conn.recv_ready():
            chunk = conn.recv(8192)
            output += chunk
            # RouterOS prompt ends with "> " or "[admin@MikroTik] > "
            if b"> " in output[-20:]:
                break
        time.sleep(0.1)
    return output

def run_cmd(conn, cmd):
    """Run a command on RouterOS and return output."""
    # Clear buffer
    wait_for_prompt(conn, timeout=2)
    
    # Send command
    conn.send(cmd + "\n")
    
    # Wait for response
    output = wait_for_prompt(conn, timeout=15)
    return output.decode('utf-8', errors='replace')

def main():
    # Clear output file
    if os.path.exists("mikro_config_output.txt"):
        os.remove("mikro_config_output.txt")
    
    print(f"Connecting to {HOST}...")
    
    transport = paramiko.Transport((HOST, 22))
    
    # Configure legacy crypto for old RouterOS
    # The router only offers ssh-dss and ssh-rsa which modern paramiko rejects
    sec_opts = transport.get_security_options()
    # For paramiko 3.x+: key_types is a set-like object
    if hasattr(sec_opts.key_types, '__or__'):
        sec_opts.key_types = sec_opts.key_types | {"ssh-rsa", "ssh-dss"}
    elif hasattr(sec_opts.key_types, 'update'):
        sec_opts.key_types.update(["ssh-rsa", "ssh-dss"])
    else:
        # Fallback: replace entirely
        sec_opts.key_types = {"ssh-rsa", "ssh-dss", "ecdsa-sha2-nistp256", 
                              "ssh-ed25519", "ecdsa-sha2-nistp384", "ecdsa-sha2-nistp521"}
    # Same for remote_host_key_types
    if hasattr(sec_opts.remote_host_key_types, '__or__'):
        sec_opts.remote_host_key_types = sec_opts.remote_host_key_types | {"ssh-rsa", "ssh-dss"}
    elif hasattr(sec_opts.remote_host_key_types, 'update'):
        sec_opts.remote_host_key_types.update(["ssh-rsa", "ssh-dss"])
    else:
        sec_opts.remote_host_key_types = {"ssh-rsa", "ssh-dss", "ecdsa-sha2-nistp256", "ssh-ed25519"}
    
    try:
        transport.connect(username=USER, password=PASS)
        print(f"Transport connected to {HOST}\n")
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)
    
    # Open session
    conn = transport.open_session()
    conn.get_pty(term='vt100')
    conn.invoke_shell()
    
    # Wait for initial prompt
    time.sleep(2)
    init = wait_for_prompt(conn, timeout=5)
    print(f"Initial: {init.decode('utf-8', errors='replace')[:200]}")
    print("=== COLLECTING CONFIG ===\n")
    
    all_output = {}
    for i, cmd in enumerate(COLLECT_COMMANDS):
        print(f"[{i+1}/{len(COLLECT_COMMANDS)}] {cmd}")
        try:
            result = run_cmd(conn, cmd)
            all_output[cmd] = result
            print(f"  -> {len(result)} chars")
            
            with open("mikro_config_output.txt", "a", encoding="utf-8") as f:
                f.write(f"\n\n{'='*60}\n{cmd}\n{'='*60}\n{result}\n")
        except Exception as e:
            print(f"  -> ERROR: {e}")
            all_output[cmd] = str(e)
    
    # Close
    conn.close()
    transport.close()
    
    print("\n=== CONFIG COLLECTION COMPLETE ===")
    print("Output saved to: mikro_config_output.txt")

if __name__ == "__main__":
    main()