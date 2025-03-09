#!/usr/bin/env python3
"""
Environment Variable Usage Validator
-----------------------------------
This script validates that all necessary environment variables are set in .env
and no hardcoded values exist in the main Python files.
"""

import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

# Files to check
FILES_TO_CHECK = [
    "agent.py",
    "webhook_server.py",
    "app.py",
    "core/agent.py",
    "core/config.py",
    "start_services.sh",
    "stop_services.sh"
]

# Load environment variables
load_dotenv()

def check_env_var_usage():
    """Check if all .env variables are used and no hardcoded values exist."""
    
    # Get all environment variables from .env
    env_vars = {}
    with open(".env", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key] = value
    
    print(f"Found {len(env_vars)} environment variables in .env")
    
    # Check files for environment variable usage
    for file_path in FILES_TO_CHECK:
        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} does not exist. Skipping.")
            continue
        
        print(f"\nChecking {file_path}...")
        
        # Read file content
        with open(file_path, "r") as f:
            content = f.read()
        
        # Check for environment variable usage
        for var_name in env_vars:
            # Different patterns for Python and Shell scripts
            if file_path.endswith(".py"):
                patterns = [
                    f'os.getenv\\("{var_name}"',
                    f'os.environ\\["{var_name}"\\]',
                    f'os.environ.get\\("{var_name}"'
                ]
            else:  # Shell scripts
                patterns = [
                    f'\\${var_name}',
                    f'\\${{var_name}}'
                ]
            
            found = False
            for pattern in patterns:
                if re.search(pattern, content):
                    found = True
                    break
            
            if found:
                print(f"  ✅ Variable {var_name} is used")
            else:
                # Only report if the variable is likely relevant to this file
                # (simple heuristic based on key words)
                relevant_keywords = {
                    "agent.py": ["SOCKET", "MOCK", "CLIENT", "API"],
                    "webhook_server.py": ["WEBHOOK", "FLASK", "API", "HOOKDECK"],
                    "app.py": ["FLASK", "APP", "PORT", "API"],
                    "core/agent.py": ["API", "CLIENT", "SOCKET", "BLUEFIN", "CLAUDE", "PERPLEXITY"],
                    "core/config.py": ["ALL"],  # All variables relevant
                    "start_services.sh": ["PORT", "HOST", "PATH"],
                    "stop_services.sh": ["PORT", "PID"]
                }
                
                keywords = relevant_keywords.get(file_path, ["ALL"])
                is_relevant = keywords == ["ALL"] or any(keyword in var_name for keyword in keywords)
                
                if is_relevant and not var_name.startswith("PERPLEXITY_MODEL_"):
                    print(f"  ❌ Variable {var_name} is NOT used but may be relevant")
        
        # Check for hardcoded values that should be environment variables
        hardcoded_patterns = {
            "port": r'port\s*=\s*([0-9]+)',
            "host": r'host\s*=\s*"([^"]+)"',
            "localhost url": r'http://localhost:([0-9]+)',
            "api key": r'api_key\s*=\s*"([^"]+)"',
            "webhook url": r'webhook_url\s*=\s*"([^"]+)"'
        }
        
        for pattern_name, pattern in hardcoded_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                print(f"  ⚠️  Found potentially hardcoded {pattern_name}: {matches}")

if __name__ == "__main__":
    print("Environment Variable Usage Validator")
    print("-----------------------------------")
    check_env_var_usage() 