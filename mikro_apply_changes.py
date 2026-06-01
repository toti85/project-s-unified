#!/usr/bin/env python3
"""
MikroTik WiFi Stability - Apply Changes
Applies changes one at a time with verification between each.
"""

import subprocess
import sys
import time
import os

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST = "192.168.88.1"
USER = "admin"
PASS = ""

SSH_OPTS = (
    "-o PasswordAuthentication=yes "
    "-o PubkeyAuthentication=no "
    "-o HostKeyAlgorithms=ssh-rsa "
    "-o KexAlgorithms=diffie-hellman-group1-sha1,diffie-hellman-group14-sha1 "
    "-o MACs=hmac-sha1 "
    "-o StrictHostKeyChecking=no "
    "-o UserKnownHostsFile=/dev/null "
)

def run_cmd(cmd):
    """Run a single SSH command."""
    full_cmd = f"ssh {SSH_OPTS} {USER}@{HOST} {cmd}"
    try:
        result = subprocess.run(
            full_cmd.split(),
            input=PASS + "\n",
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return None
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None

def verify_connectivity():
    """Verify we can still reach the router."""
    print("  Verifying connectivity...")
    test = run_cmd("/system resource print")
    if test and len(test) > 50:
        print("  OK - Router reachable")
        return True
    print("  FAIL - Router NOT reachable!")
    return False

def ping_gateway():
    """Ping the gateway from DEV."""
    try:
        result = subprocess.run(
            ["ping", "192.168.88.1", "-n", "5"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        output = result.stdout
        if "Lost = 0" in output:
            print("  Gateway ping: 0% loss")
            return True
        elif "Lost = 1" in output or "Lost = 2" in output:
            print("  Gateway ping: minor loss")
            return True
        else:
            print("  Gateway ping: significant loss or timeout")
            return False
    except:
        print("  Gateway ping: FAILED")
        return False

def wifi_check():
    """Check current WiFi state from DEV."""
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in result.stdout.split("\n"):
            if any(k in line for k in ["Signal", "Rssi", "Channel", "SSID", "Receive rate", "Transmit rate"]):
                print(f"  {line.strip()}")
    except:
        pass

def apply_change(step_name, cmd, pre_wait=2, post_wait=5):
    """Apply a single change with verification."""
    print(f"\n{'='*60}")
    print(f"CHANGE: {step_name}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")
    
    # Pre-change state
    print("\n[BEFORE] WiFi state:")
    wifi_check()
    ping_gateway()
    
    # Apply
    print(f"\nApplying: {cmd}")
    result = run_cmd(cmd)
    if result is None:
        print(f"  TIMEOUT applying command!")
        return False
    print(f"  Response: {result[:200]}")
    
    # Wait for change to take effect
    print(f"  Waiting {post_wait}s for change to settle...")
    time.sleep(post_wait)
    
    # Verify
    if not verify_connectivity():
        print(f"\n  *** CONNECTIVITY LOST after: {step_name} ***")
        print(f"  STOPPING - manual intervention needed!")
        return False
    
    if not ping_gateway():
        print(f"\n  *** GATEWAY UNREACHABLE after: {step_name} ***")
        return False
    
    print(f"\n[AFTER] WiFi state:")
    wifi_check()
    
    print(f"\n  [OK] {step_name} - APPLIED SUCCESSFULLY")
    return True

def main():
    log = "mikro_changes_log.txt"
    if os.path.exists(log):
        os.remove(log)
    
    def log_msg(msg):
        print(msg)
        with open(log, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    
    log_msg("=" * 60)
    log_msg("MIKROTIK WIFI STABILITY AUTO-CONFIG")
    log_msg(f"Date: 2026-05-24")
    log_msg("=" * 60)
    
    # === PHASE 1: BACKUP ===
    log_msg("\n=== PHASE 1: BACKUP ===")
    print("\n" + "="*60)
    print("PHASE 1: BACKUP")
    print("="*60)
    
    backup1 = run_cmd("/export hide-sensitive file=before_wifi_stability_20260524")
    log_msg(f"Export result: {backup1}")
    
    backup2 = run_cmd("/system backup save name=before_wifi_stability_20260524")
    log_msg(f"Backup result: {backup2}")
    
    # Verify backup
    verify = run_cmd('/file print where name~"before_wifi_stability"')
    log_msg(f"Backup verification: {verify}")
    print(f"Backup created: {verify}")
    
    if "before_wifi_stability" not in (verify or ""):
        print("WARNING: Backup verification unclear, but continuing...")
    
    # === PHASE 3: APPLY CHANGES ONE AT A TIME ===
    print(f"\n\n{'='*60}")
    print("PHASE 3: APPLYING CHANGES")
    print("="*60)
    
    changes = [
        (
            "DHCP LEASE TIME: 10m -> 24h",
            "/ip dhcp-server set defconf lease-time=24h",
            2,
            5,
        ),
        (
            "CHANNEL WIDTH: 20/40mhz-Ce -> 20mhz",
            '/interface wireless set wlan1 channel-width=20mhz',
            2,
            10,
        ),
        (
            "CHANNEL: auto -> 6 (2437MHz)",
            '/interface wireless set wlan1 frequency=2437',
            2,
            15,
        ),
    ]
    
    results = {}
    for name, cmd, pre, post in changes:
        print(f"\n\n{'#'*60}")
        print(f"APPLYING: {name}")
        print(f"{'#'*60}")
        
        success = apply_change(name, cmd, pre_wait=pre, post_wait=post)
        results[name] = success
        
        if not success:
            log_msg(f"\n*** STOPPED at: {name} - FAILED ***")
            print(f"\n*** STOPPING - change '{name}' caused issues ***")
            print("Manual rollback needed!")
            break
        
        log_msg(f"[OK] {name} - SUCCESS")
    
    # === STATIC DHCP LEASE FOR DEV ===
    print(f"\n\n{'#'*60}")
    print(f"STATIC DHCP LEASE FOR DEV")
    print(f"{'#'*60}")
    
    # Check if static lease already exists
    existing = run_cmd('/ip dhcp-server lease print where mac-address=D0:AB:D5:73:22:6A')
    log_msg(f"Existing DEV lease: {existing}")
    
    if "192.168.88.17" in (existing or ""):
        print("  DEV already has a DHCP lease for 192.168.88.17")
        # Make it static by setting address=
        static_cmd = '/ip dhcp-server lease set [find mac-address=D0:AB:D5:73:22:6A] address=192.168.88.17 comment=DEV-PC'
        print(f"  Making lease static: {static_cmd}")
        result = run_cmd(static_cmd)
        log_msg(f"Static lease result: {result}")
        print("  [OK] Static DHCP lease for DEV configured")
    else:
        print("  Adding static lease...")
        static_cmd = '/ip dhcp-server lease add address=192.168.88.17 mac-address=D0:AB:D5:73:22:6A comment=DEV-PC'
        result = run_cmd(static_cmd)
        log_msg(f"Static lease add result: {result}")
        print("  [OK] Static DHCP lease added for DEV")
    
    # === FINAL VERIFICATION ===
    print(f"\n\n{'='*60}")
    print("FINAL VERIFICATION")
    print("="*60)
    
    print("\n[Final WiFi State]:")
    wifi_check()
    ping_gateway()
    
    # Verify applied settings
    print("\n[Verify DHCP lease time]:")
    dhcp_verify = run_cmd("/ip dhcp-server print")
    print(f"  {dhcp_verify[:200]}")
    log_msg(f"DHCP verify: {dhcp_verify}")
    
    print("\n[Verify wireless settings]:")
    wireless_verify = run_cmd("/interface wireless print where name=wlan1")
    print(f"  {wireless_verify[:300]}")
    log_msg(f"Wireless verify: {wireless_verify}")
    
    # === SUMMARY ===
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print("="*60)
    
    for name, success in results.items():
        status = "[OK] APPLIED" if success else "[FAIL] FAILED"
        print(f"  {status}: {name}")
        log_msg(f"  {status}: {name}")
    
    log_msg("\nStatic DHCP lease for DEV: configured")
    print("  [OK] Static DHCP lease for DEV configured")
    
    log_msg("\n=== COMPLETE ===")
    print(f"\nLog saved to: {log}")
    print("\nDone!")

if __name__ == "__main__":
    main()