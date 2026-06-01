"""
Live connectivity test for HPE iLO 4 Redfish API

Performs a real-time read-only connection test to the remote iLO endpoint.
Handles NAT/port-forward scenarios with internal redirect rewriting.

Run with: python -m project_s.infrastructure.test_ilo_controller
"""

import sys
import traceback

from .ilo_controller import ILOController


def main() -> int:
    """
    Main entry point for live iLO connectivity test.
    
    Performs real connection test against remote iLO endpoint.
    Reports actual results and exceptions.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("[ILO] HPE iLO 4 Connectivity Test")
    print("[ILO] =====================================")
    
    # Remote endpoint credentials
    ILO_URL = "https://46.253.140.72:89"
    ILO_USERNAME = "Administrator"
    ILO_PASSWORD = "PTSYK7BF"
    
    try:
        print("[ILO] trying remote endpoint...")
        
        # Initialize controller
        controller = ILOController(
            url=ILO_URL,
            username=ILO_USERNAME,
            password=ILO_PASSWORD,
            timeout=15,
            verify_ssl=False
        )
        
        # Test connection
        controller.connect()
        print("[ILO] connection OK")
        
        # Get system information
        system_info = controller.get_system_info()
        
        # Get power state
        power_state = controller.get_power_state()
        
        # Get health summary
        health = controller.get_health_summary()
        
        # Print details
        print(f"[ILO] model: {health.get('model', 'N/A')}")
        print(f"[ILO] manufacturer: {health.get('manufacturer', 'N/A')}")
        print(f"[ILO] serial: {health.get('serial_number', 'N/A')}")
        
        if "bios_version" in health:
            print(f"[ILO] bios: {health.get('bios_version', 'N/A')}")
        
        print(f"[ILO] power: {health.get('power_state', 'N/A')}")
        
        if "health" in health:
            print(f"[ILO] health: {health.get('health', 'N/A')}")
        
        # Close session
        controller.close()
        
        print("[ILO] =====================================")
        print("[ILO] test completed successfully")
        return 0
        
    except Exception as e:
        print("[ILO] =====================================")
        print("[ILO] connection failed")
        print(f"\n{type(e).__name__}: {str(e)}\n")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
