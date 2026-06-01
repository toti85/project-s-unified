#!/usr/bin/env python3
"""
Project-S Tool: Roblox Apply Patch
Converts natural language game requests to Roblox patches
"""

import json
import requests
from pathlib import Path
from datetime import datetime
import time

class RobloxApplyPatchTool:
    """Tool for applying AI-generated patches to Roblox games"""
    
    def __init__(self, server_url="http://localhost:8001"):
        self.server_url = server_url
        self.evidence_dir = Path.home() / "Documents" / "Roblox Projects" / "evidence"
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
    
    def natural_language_to_patch(self, description):
        """
        Convert natural language description to JSON patch
        Examples:
          - "5 level neon obby"
          - "hard difficulty with 10 platforms"
          - "easy classic parkour"
        """
        
        description_lower = description.lower()
        
        # Extract difficulty
        difficulty = "medium"
        if "easy" in description_lower:
            difficulty = "easy"
        elif "hard" in description_lower:
            difficulty = "hard"
        
        # Extract levels
        levels = 5  # default
        for word in description_lower.split():
            if word.isdigit():
                num = int(word)
                if 1 <= num <= 100:
                    levels = num
                    break
        
        # Difficulty to levels mapping
        if difficulty == "easy":
            levels = min(levels, 4)
        elif difficulty == "hard":
            levels = max(levels, 8)
        
        # Extract theme
        theme = "classic"
        if "neon" in description_lower:
            theme = "neon"
        
        patch = {
            "type": "obby",
            "levels": levels,
            "theme": theme,
            "difficulty": difficulty,
            "description": description,
            "generated_at": datetime.now().isoformat()
        }
        
        return patch
    
    def validate_patch(self, patch):
        """Validate patch structure"""
        errors = []
        
        if patch.get("type") != "obby":
            errors.append("Type must be 'obby'")
        
        levels = patch.get("levels")
        if not isinstance(levels, int) or levels < 1 or levels > 100:
            errors.append("Levels must be 1-100")
        
        theme = patch.get("theme")
        if theme not in ["classic", "neon"]:
            errors.append("Theme must be classic or neon")
        
        return len(errors) == 0, errors
    
    def send_patch(self, patch, retry_count=3):
        """Send patch to Plugin Server with retry logic"""
        
        print(f"Sending patch to {self.server_url}/patch...")
        
        for attempt in range(retry_count):
            try:
                response = requests.post(
                    f"{self.server_url}/patch",
                    json=patch,
                    timeout=10
                )
                
                if response.status_code in [200, 400, 500]:
                    return response.json(), response.status_code
                
                print(f"  Attempt {attempt + 1}: HTTP {response.status_code}, retrying...")
                
            except requests.exceptions.ConnectionError:
                print(f"  Attempt {attempt + 1}: Connection error, retrying...")
            except requests.exceptions.Timeout:
                print(f"  Attempt {attempt + 1}: Timeout, retrying...")
            except Exception as e:
                print(f"  Attempt {attempt + 1}: Error - {str(e)}, retrying...")
            
            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception(f"Failed to reach server after {retry_count} attempts")
    
    def log_evidence(self, description, patch, response, status_code):
        """Log execution evidence"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        evidence_file = self.evidence_dir / f"tool_execution_{timestamp}.json"
        
        evidence = {
            "timestamp": datetime.now().isoformat(),
            "input": {
                "description": description,
                "patch": patch
            },
            "output": {
                "status_code": status_code,
                "response": response
            },
            "success": status_code == 200
        }
        
        with open(evidence_file, 'w') as f:
            json.dump(evidence, f, indent=2)
        
        return str(evidence_file)
    
    def apply_patch(self, description):
        """
        Main flow: NL → Patch → Send → Log
        
        Args:
            description: Natural language description (e.g., "10 level hard neon obby")
        
        Returns:
            dict with status, metrics, errors
        """
        
        print("\n" + "=" * 80)
        print("ROBLOX APPLY PATCH TOOL")
        print("=" * 80)
        print(f"Input: {description}\n")
        
        # Step 1: Convert NL to patch
        print("[1/4] Converting to patch...")
        patch = self.natural_language_to_patch(description)
        print(f"  Type: {patch['type']}")
        print(f"  Levels: {patch['levels']}")
        print(f"  Theme: {patch['theme']}")
        print(f"  Difficulty: {patch['difficulty']}\n")
        
        # Step 2: Validate patch
        print("[2/4] Validating patch...")
        is_valid, errors = self.validate_patch(patch)
        if not is_valid:
            print(f"  FAILED: {', '.join(errors)}\n")
            return {
                "status": "error",
                "errors": errors,
                "metrics": {}
            }
        print("  OK\n")
        
        # Step 3: Send patch to server
        print("[3/4] Sending to Roblox Plugin Server...")
        try:
            response, status_code = self.send_patch(patch)
            print(f"  Status: {response.get('status')}")
            print(f"  Metrics: {response.get('metrics')}")
            if response.get('errors'):
                print(f"  Errors: {response.get('errors')}\n")
            else:
                print()
        except Exception as e:
            print(f"  FAILED: {str(e)}\n")
            return {
                "status": "error",
                "errors": [str(e)],
                "metrics": {}
            }
        
        # Step 4: Log evidence
        print("[4/4] Logging evidence...")
        evidence_file = self.log_evidence(description, patch, response, status_code)
        print(f"  Logged to: {evidence_file}\n")
        
        # Return complete result
        result = response.copy()
        result["evidence_file"] = evidence_file
        
        print("=" * 80)
        print(f"RESULT: {result['status'].upper()}")
        print("=" * 80)
        print()
        
        return result

def main():
    """Test the tool"""
    
    tool = RobloxApplyPatchTool()
    
    # Test cases
    test_inputs = [
        "5 level neon obby",
        "hard difficulty 10 platforms",
        "easy classic parkour",
    ]
    
    for test_input in test_inputs:
        try:
            result = tool.apply_patch(test_input)
        except Exception as e:
            print(f"Error: {str(e)}\n")

if __name__ == "__main__":
    main()
