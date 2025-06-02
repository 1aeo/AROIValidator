#!/usr/bin/env python3
"""
Simple script to run the copied AROI validator app
"""

import subprocess
import sys

if __name__ == "__main__":
    # Run the copied app on port 5000
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        "app_copy.py", 
        "--server.port", "5000",
        "--server.address", "0.0.0.0", 
        "--server.headless", "true"
    ]
    
    print("Starting AROI Validator Copy on port 5000...")
    subprocess.run(cmd)