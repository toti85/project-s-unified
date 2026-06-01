"""
HPE iLO 4 Redfish API Controller Module

This module provides a Python interface to interact with HPE iLO 4 servers
using the Redfish API specification. It supports server power management,
system information retrieval, and health monitoring.

Handles NAT/port-forward scenarios where iLO redirects to internal private IPs
by rewriting redirects back to the original public endpoint.
"""

import requests
import urllib3
from urllib.parse import urlparse, urljoin
from typing import Dict, Any, Optional
from requests.exceptions import RequestException, Timeout, ConnectionError

# Suppress SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Private IP ranges for redirect detection
PRIVATE_IP_RANGES = [
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
]


class ILOController:
    """
    Controller for HPE iLO 4 server management via Redfish API.
    
    Supports remote public access through NAT/port-forwarding by detecting
    and rewriting internal redirects back to the original public endpoint.
    
    Attributes:
        url: Base URL of the iLO 4 server
        username: Authentication username
        password: Authentication password
        session: Requests session for API communication
    """
    
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        timeout: int = 10,
        verify_ssl: bool = False
    ):
        """
        Initialize ILOController instance.
        
        Args:
            url: Base URL of iLO 4 (e.g., https://46.253.140.72:89)
            username: iLO username
            password: iLO password
            timeout: Request timeout in seconds (default: 10)
            verify_ssl: Whether to verify SSL certificate (default: False for self-signed)
        """
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._connected = False
    
    def _is_private_ip(self, hostname: str) -> bool:
        """
        Check if hostname is a private IP or reserved hostname.
        
        Args:
            hostname: Hostname or IP address to check
            
        Returns:
            True if hostname appears to be private/internal
        """
        if not hostname:
            return False
        
        # Check for localhost
        if hostname.lower() in ("localhost", "127.0.0.1", "::1"):
            return True
        
        # Check for private IP patterns
        if hostname.startswith("192.168.") or hostname.startswith("10.") or hostname.startswith("172."):
            return True
        
        # Check for internal hostnames
        if hostname.lower().endswith(".local") or hostname.lower().endswith(".internal"):
            return True
        
        return False
    
    def _handle_redirect(
        self,
        response: requests.Response,
        original_base_url: str
    ) -> Optional[str]:
        """
        Handle HTTP redirects for NAT/port-forward scenarios.
        
        Detects redirects to internal private IPs and rewrites them back to
        the original public endpoint while preserving the redirected path.
        
        Args:
            response: HTTP response with redirect status
            original_base_url: Original request base URL
            
        Returns:
            Rewritten URL if redirect should be followed, None otherwise
        """
        if response.status_code not in (301, 302, 303, 307, 308):
            return None
        
        location = response.headers.get("Location")
        if not location:
            return None
        
        print(f"[ILO] redirect detected: {location}")
        
        # Parse the redirect location
        parsed_location = urlparse(location)
        
        # If it's a relative redirect, construct full URL
        if not parsed_location.scheme:
            # Relative redirect - append to original URL
            target_url = urljoin(response.url, location)
        else:
            target_url = location
        
        # Check if redirect target is an internal/private address
        parsed_target = urlparse(target_url)
        
        if self._is_private_ip(parsed_target.hostname):
            # Rewrite redirect to use original public endpoint
            parsed_base = urlparse(original_base_url)
            
            # Preserve path and query from the redirected location
            path = parsed_target.path or "/"
            query = f"?{parsed_target.query}" if parsed_target.query else ""
            
            rewritten_url = f"{parsed_base.scheme}://{parsed_base.netloc}{path}{query}"
            print(f"[ILO] rewritten redirect target: {rewritten_url}")
            
            return rewritten_url
        
        # Redirect is to external address, use as-is
        return target_url
    
    def _request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to iLO API with manual redirect handling.
        
        Creates a fresh connection for each request to avoid HPE iLO 4 session
        closure issues. Always closes connection after response.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            payload: Request payload for POST/PATCH operations
            
        Returns:
            Response JSON as dictionary
            
        Raises:
            ConnectionError: Connection failed or timeout
            requests.exceptions.HTTPError: HTTP error response
            Exception: Authentication or server errors
        """
        full_url = f"{self.url}{endpoint}"
        
        # Request headers
        headers = {
            "Connection": "close",
            "Accept": "application/json"
        }
        
        try:
            print(f"[ILO] new connection created")
            print(f"[ILO] request {method.upper()} {endpoint}")
            
            # Make request without automatic redirects
            if method.upper() == "GET":
                response = requests.get(
                    full_url,
                    auth=(self.username, self.password),
                    headers=headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                    allow_redirects=False
                )
            elif method.upper() == "POST":
                response = requests.post(
                    full_url,
                    auth=(self.username, self.password),
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                    allow_redirects=False
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Handle redirects manually
            if response.status_code in (301, 302, 303, 307, 308):
                redirect_url = self._handle_redirect(response, self.url)
                
                if redirect_url:
                    print(f"[ILO] retrying via public endpoint...")
                    
                    # Parse redirected endpoint from URL for logging
                    parsed_redirect = urlparse(redirect_url)
                    redirect_path = parsed_redirect.path
                    if parsed_redirect.query:
                        redirect_path += f"?{parsed_redirect.query}"
                    
                    # Follow the rewritten redirect with fresh connection
                    if method.upper() == "GET":
                        response = requests.get(
                            redirect_url,
                            auth=(self.username, self.password),
                            headers=headers,
                            timeout=self.timeout,
                            verify=self.verify_ssl,
                            allow_redirects=False
                        )
                    else:
                        response = requests.post(
                            redirect_url,
                            auth=(self.username, self.password),
                            json=payload,
                            headers=headers,
                            timeout=self.timeout,
                            verify=self.verify_ssl,
                            allow_redirects=False
                        )
            
            # Check for HTTP errors after redirect handling
            if response.status_code == 401:
                print(f"[ILO] authentication failed")
                raise requests.exceptions.HTTPError("Authentication failed (401)")
            elif response.status_code == 404:
                raise requests.exceptions.HTTPError(f"Endpoint not found (404): {endpoint}")
            elif response.status_code >= 400:
                print(f"[ILO] HTTP error {response.status_code}")
                raise requests.exceptions.HTTPError(f"HTTP {response.status_code}: {response.text}")
            
            return response.json()
            
        except Timeout:
            print(f"[ILO] connection timeout")
            raise ConnectionError("Request timeout - server unavailable")
        except ConnectionError as e:
            print(f"[ILO] connection failed")
            raise ConnectionError(f"Connection failed: {str(e)}")
        except RequestException as e:
            print(f"[ILO] request error: {str(e)}")
            raise
    
    def connect(self) -> bool:
        """
        Test connection to iLO Redfish API.
        
        Returns:
            True if connection successful
            
        Raises:
            ConnectionError: If connection fails
            Exception: If authentication fails
        """
        print(f"[ILO] connecting to {self.url}/redfish/v1")
        
        try:
            response = self._request("GET", "/redfish/v1")
            
            if "RedfishVersion" in response:
                print(f"[ILO] connection OK")
                self._connected = True
                return True
            else:
                raise Exception("Invalid Redfish API response")
                
        except Exception as e:
            print(f"[ILO] connection failed: {str(e)}")
            raise
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Retrieve system information from iLO.
        
        Returns:
            Dictionary containing system details
            
        Raises:
            ConnectionError: If request fails
        """
        print(f"[ILO] fetching system info")
        
        try:
            response = self._request("GET", "/redfish/v1/Systems/1")
            print(f"[ILO] system info retrieved")
            return response
            
        except Exception as e:
            print(f"[ILO] failed to get system info: {str(e)}")
            raise
    
    def get_power_state(self) -> Optional[str]:
        """
        Get current power state of the system.
        
        Returns:
            Power state string (e.g., "On", "Off")
            
        Raises:
            ConnectionError: If request fails
        """
        try:
            system_info = self.get_system_info()
            power_state = system_info.get("PowerState")
            
            if power_state:
                print(f"[ILO] power state: {power_state}")
                return power_state
            else:
                print(f"[ILO] power state unavailable")
                return None
                
        except Exception as e:
            print(f"[ILO] failed to get power state: {str(e)}")
            raise
    
    def restart_server(self) -> bool:
        """
        Force restart the server.
        
        Returns:
            True if restart command sent successfully
            
        Raises:
            ConnectionError: If request fails
        """
        print(f"[ILO] sending restart command")
        
        try:
            payload = {"ResetType": "ForceRestart"}
            self._request(
                "POST",
                "/redfish/v1/Systems/1/Actions/ComputerSystem.Reset",
                payload=payload
            )
            print(f"[ILO] restart command sent")
            return True
            
        except Exception as e:
            print(f"[ILO] restart command failed: {str(e)}")
            raise
    
    def power_on(self) -> bool:
        """
        Power on the server.
        
        Returns:
            True if power-on command sent successfully
            
        Raises:
            ConnectionError: If request fails
        """
        print(f"[ILO] sending power on command")
        
        try:
            payload = {"ResetType": "On"}
            self._request(
                "POST",
                "/redfish/v1/Systems/1/Actions/ComputerSystem.Reset",
                payload=payload
            )
            print(f"[ILO] power on command sent")
            return True
            
        except Exception as e:
            print(f"[ILO] power on command failed: {str(e)}")
            raise
    
    def power_off(self) -> bool:
        """
        Force power off the server.
        
        Returns:
            True if power-off command sent successfully
            
        Raises:
            ConnectionError: If request fails
        """
        print(f"[ILO] sending power off command")
        
        try:
            payload = {"ResetType": "ForceOff"}
            self._request(
                "POST",
                "/redfish/v1/Systems/1/Actions/ComputerSystem.Reset",
                payload=payload
            )
            print(f"[ILO] power off command sent")
            return True
            
        except Exception as e:
            print(f"[ILO] power off command failed: {str(e)}")
            raise
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get a compact health summary of the server.
        
        Returns:
            Dictionary with model, manufacturer, power_state, serial_number,
            bios_version, and health information. Handles missing fields gracefully.
            
        Raises:
            ConnectionError: If request fails
        """
        print(f"[ILO] fetching health summary")
        
        try:
            system_info = self.get_system_info()
            
            # Safely extract fields with fallback values
            summary = {
                "model": system_info.get("Model", "Unknown"),
                "manufacturer": system_info.get("Manufacturer", "Unknown"),
                "power_state": system_info.get("PowerState", "Unknown"),
                "serial_number": system_info.get("SerialNumber", "Unknown"),
            }
            
            # Optional fields
            if "BiosVersion" in system_info:
                summary["bios_version"] = system_info["BiosVersion"]
            
            if "Status" in system_info:
                status = system_info["Status"]
                if isinstance(status, dict):
                    summary["health"] = status.get("Health", "Unknown")
            
            print(f"[ILO] health summary retrieved")
            return summary
            
        except Exception as e:
            print(f"[ILO] failed to get health summary: {str(e)}")
            raise
    
    def close(self) -> None:
        """Close the session connection."""
        if self.session:
            self.session.close()
            print(f"[ILO] session closed")
    
    def connect(self) -> bool:
        """
        Test connection to iLO Redfish API.
        
        Returns:
            True if connection successful
            
        Raises:
            ConnectionError: If connection fails
            Exception: If authentication fails
        """
        print(f"[ILO] connecting to {self.url}/redfish/v1")
        
        try:
            response = self._request("GET", "/redfish/v1")
            
            if "RedfishVersion" in response:
                print(f"[ILO] connection OK")
                self._connected = True
                return True
            else:
                raise Exception("Invalid Redfish API response")
                
        except Exception as e:
            print(f"[ILO] connection failed: {str(e)}")
            raise
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Retrieve system information from iLO.
        
        Returns:
            Dictionary containing system details
            
        Raises:
            ConnectionError: If request fails
        """
        print(f"[ILO] fetching system info")
        
        try:
            response = self._request("GET", "/redfish/v1/Systems/1")
            print(f"[ILO] system info retrieved")
            return response
            
        except Exception as e:
            print(f"[ILO] failed to get system info: {str(e)}")
            raise
    
    def get_power_state(self) -> Optional[str]:
        """
        Get current power state of the system.
        
        Returns:
            Power state string (e.g., "On", "Off")
            
        Raises:
            ConnectionError: If request fails
        """
        try:
            system_info = self.get_system_info()
            power_state = system_info.get("PowerState")
            
            if power_state:
                print(f"[ILO] power state: {power_state}")
                return power_state
            else:
                print(f"[ILO] power state unavailable")
                return None
                
        except Exception as e:
            print(f"[ILO] failed to get power state: {str(e)}")
            raise
    
    def restart_server(self) -> bool:
        """
        Force restart the server.
        
        Returns:
            True if restart command sent successfully
            
        Raises:
            ConnectionError: If request fails
        """
        print(f"[ILO] sending restart command")
        
        try:
            payload = {"ResetType": "ForceRestart"}
            self._request(
                "POST",
                "/redfish/v1/Systems/1/Actions/ComputerSystem.Reset",
                payload=payload
            )
            print(f"[ILO] restart command sent")
            return True
            
        except Exception as e:
            print(f"[ILO] restart command failed: {str(e)}")
            raise
    
    def power_on(self) -> bool:
        """
        Power on the server.
        
        Returns:
            True if power-on command sent successfully
            
        Raises:
            ConnectionError: If request fails
        """
        print(f"[ILO] sending power on command")
        
        try:
            payload = {"ResetType": "On"}
            self._request(
                "POST",
                "/redfish/v1/Systems/1/Actions/ComputerSystem.Reset",
                payload=payload
            )
            print(f"[ILO] power on command sent")
            return True
            
        except Exception as e:
            print(f"[ILO] power on command failed: {str(e)}")
            raise
    
    def power_off(self) -> bool:
        """
        Force power off the server.
        
        Returns:
            True if power-off command sent successfully
            
        Raises:
            ConnectionError: If request fails
        """
        print(f"[ILO] sending power off command")
        
        try:
            payload = {"ResetType": "ForceOff"}
            self._request(
                "POST",
                "/redfish/v1/Systems/1/Actions/ComputerSystem.Reset",
                payload=payload
            )
            print(f"[ILO] power off command sent")
            return True
            
        except Exception as e:
            print(f"[ILO] power off command failed: {str(e)}")
            raise
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get a compact health summary of the server.
        
        Returns:
            Dictionary with model, manufacturer, power_state, serial_number,
            bios_version, and health information. Handles missing fields gracefully.
            
        Raises:
            ConnectionError: If request fails
        """
        print(f"[ILO] fetching health summary")
        
        try:
            system_info = self.get_system_info()
            
            # Safely extract fields with fallback values
            summary = {
                "model": system_info.get("Model", "Unknown"),
                "manufacturer": system_info.get("Manufacturer", "Unknown"),
                "power_state": system_info.get("PowerState", "Unknown"),
                "serial_number": system_info.get("SerialNumber", "Unknown"),
            }
            
            # Optional fields
            if "BiosVersion" in system_info:
                summary["bios_version"] = system_info["BiosVersion"]
            
            if "Status" in system_info:
                status = system_info["Status"]
                if isinstance(status, dict):
                    summary["health"] = status.get("Health", "Unknown")
            
            print(f"[ILO] health summary retrieved")
            return summary
            
        except Exception as e:
            print(f"[ILO] failed to get health summary: {str(e)}")
            raise
    
    def close(self) -> None:
        """
        Cleanup method for compatibility.
        
        No longer needed since each request uses a fresh connection,
        but kept for API compatibility.
        """
        print(f"[ILO] session closed")


if __name__ == "__main__":
    try:
        # Initialize controller
        controller = ILOController(
            url="https://46.253.140.72:89",
            username="Administrator",
            password="PASSWORD"
        )
        
        # Test connection
        controller.connect()
        
        # Get system info
        system_info = controller.get_system_info()
        print(system_info)
        
        # Get power state
        power_state = controller.get_power_state()
        print(f"Current power state: {power_state}")
        
        # Close session
        controller.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")
