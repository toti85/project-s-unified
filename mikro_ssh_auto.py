#!/usr/bin/env python3
"""
MikroTik WiFi Stability Auto-Config
Uses subprocess + expect-like pattern for SSH with password.
"""

import subprocess
import sys
import os
import time
import select

HOST = "192.168.88.1"
USER = "admin"
PASS = ""  # Default MikroTik password is empty

SSH_CMD = (
    f"ssh "
    f"-o PasswordAuthentication=yes "
    f"-o PubkeyAuthentication=no "
    f"-o HostKeyAlgorithms=ssh-rsa "
    f"-o KexAlgorithms=diffie-hellman-group1-sha1,diffie-hellman-group14-sha1 "
    f"-o MACs=hmac-sha1 "
    f"-o StrictHostKeyChecking=no "
    f"-o UserKnownHostsFile=/dev/null "
    f"{USER}@{HOST}"
)

def run_ssh_command(cmd):
    """Run a single command via SSH, return output."""
    try:
        proc = subprocess.Popen(
            SSH_CMD.split(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        
        # Wait for password prompt and send password
        time.sleep(2)
        try:
            stdout, stderr = proc.communicate(input=PASS + "\n", timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            return None
        
        # Find the command output (after the RouterOS banner and prompt)
        lines = stdout.split("\n")
        # Find the line with our command output
        result_lines = []
        capturing = False
        for line in lines:
            if cmd.strip().startswith("/") and cmd.split()[0] in line:
                capturing = True
            if capturing:
                result_lines.append(line)
        
        # If we didn't capture well, return everything after the banner
        if not result_lines or len(result_lines) < 2:
            # Find the prompt line and take everything after
            for i, line in enumerate(lines):
                if "] >" in line or line.strip().endswith(">"):
                    result_lines = lines[i+1:]
                    break
        
        return "\n".join(result_lines).strip()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return None

def run_ssh_command_simple(cmd):
    """Simpler approach - just run ssh with command directly."""
    try:
        full_cmd = SSH_CMD + " " + cmd
        result = subprocess.run(
            full_cmd.split(),
            input=PASS + "\n",
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"\n[TIMEOUT] Command: {cmd}")
        return None
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return None

def main():
    # Clear output file
    outfile = "mikro_config_output.txt"
    if os.path.exists(outfile):
        os.remove(outfile)

    print("=" * 60)
    print("MIKROTIK WIFI STABILITY AUTO-CONFIG")
    print(f"Target: {HOST}")
    print("=" * 60)

    # Test connection
    print("\n[TEST] Testing SSH connection...")
    test = run_ssh_command_simple("/system resource print")
    if test is None or len(test) < 10:
        print(f"FAILED: test output was: {test}")
        print("Trying alternative method...")
        sys.exit(1)

    print(f"Connection test OK. Got {len(test)} chars.\n")
    print(test[:500])

    # Define all commands
    commands = {
        "system_resource": "/system resource print",
        "system_routerboard": "/system routerboard print",
        "interface_print": "/interface print detail",
        "interface_wireless": "/interface wireless print detail",
        "interface_wifi": "/interface wifi print detail",
        "ip_address": "/ip address print",
        "ip_route": "/ip route print",
        "dhcp_server": "/ip dhcp-server print",
        "dhcp_network": "/ip dhcp-server network print",
        "dhcp_lease": "/ip dhcp-server lease print",
        "ip_dns": "/ip dns print",
        "firewall_nat": "/ip firewall nat print",
        "firewall_filter": "/ip firewall filter print",
        "ip_service": "/ip service print",
        "user_print": "/user print",
    }

    results = {}
    for name, cmd in commands.items():
        print(f"\n[{name}] Running: {cmd}")
        result = run_ssh_command_simple(cmd)
        if result and len(result) > 5:
            results[name] = result
            print(f"  -> Got {len(result)} chars")
            with open(outfile, "a", encoding="utf-8") as f:
                f.write(f"\n\n{'='*60}\n{name}: {cmd}\n{'='*60}\n{result}\n")
        else:
            results[name] = "FAILED"
            print(f"  -> FAILED or empty: {result}")

    print(f"\n\n{'='*60}")
    print("CONFIG COLLECTION COMPLETE")
    print(f"Output saved to: {outfile}")
    print(f"{'='*60}\n")

    # Print key findings
    print("\n=== KEY FINDINGS ===\n")

    if "system_resource" in results and results["system_resource"] != "FAILED":
        for line in results["system_resource"].split("\n"):
            if any(k in line.lower() for k in ["version", "free memory", "cpu", "platform", "board"]):
                print(f"  {line.strip()}")

    if "interface_wireless" in results and results["interface_wireless"] != "FAILED":
        print("\n--- Wireless Interfaces ---")
        for line in results["interface_wireless"].split("\n"):
            if any(k in line for k in ["name=", "frequency=", "channel=", "band=", "ssid=", "disabled=", "channel-width", "wds-bridge-ip"]):
                print(f"  {line.strip()}")

    if "interface_wifi" in results and results["interface_wifi"] != "FAILED":
        print("\n--- WiFi Interfaces ---")
        for line in results["interface_wifi"].split("\n"):
            if line.strip():
                print(f"  {line.strip()}")

    if "dhcp_network" in results and results["dhcp_network"] != "FAILED":
        print("\n--- DHCP Network ---")
        for line in results["dhcp_network"].split("\n"):
            if line.strip():
                print(f"  {line.strip()}")

    if "dhcp_lease" in results and results["dhcp_lease"] != "FAILED":
        print("\n--- DHCP Leases ---")
        for line in results["dhcp_lease"].split("\n"):
            if line.strip():
                print(f"  {line.strip()}")

    return results

if __name__ == "__main__":
    main()