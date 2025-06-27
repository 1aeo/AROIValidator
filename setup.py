#!/usr/bin/env python3
"""
AROI Validator Setup Script

This script automatically configures the AROI Validator project for Replit deployment.
It installs all required dependencies and creates the necessary configuration files.

Usage:
    python setup.py
"""

import os
import subprocess
import sys
from pathlib import Path

def create_streamlit_config():
    """Create the Streamlit configuration file for proper deployment"""
    config_dir = Path(".streamlit")
    config_dir.mkdir(exist_ok=True)
    
    config_content = """[server]
headless = true
address = "0.0.0.0"
port = 5000"""
    
    config_file = config_dir / "config.toml"
    with open(config_file, "w") as f:
        f.write(config_content)
    
    print("✓ Created Streamlit configuration")

def install_dependencies():
    """Install required Python packages"""
    dependencies = [
        "streamlit",
        "dnspython", 
        "pandas",
        "requests",
        "urllib3"
    ]
    
    print("Installing Python dependencies...")
    try:
        # Use uv (Replit's package manager)
        result = subprocess.run(["uv", "add"] + dependencies, check=True, capture_output=True, text=True)
        print("✓ Installed dependencies using uv")
        print(f"Output: {result.stdout}")
    except FileNotFoundError:
        print("❌ uv not found. Please install dependencies manually using:")
        print("   In Replit: Use the Package Manager in the sidebar")
        print("   Or run: uv add streamlit dnspython pandas requests urllib3")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies with uv: {e}")
        print("Error output:", e.stderr if hasattr(e, 'stderr') else '')
        print("\nPlease install dependencies manually using:")
        print("   In Replit: Use the Package Manager in the sidebar")
        print("   Or run: uv add streamlit dnspython pandas requests urllib3")
        return False
    
    return True

def create_run_script():
    """Create a simple run script for the application"""
    run_script = """#!/bin/bash
# Simple script to run the AROI Validator
python aroi_cli.py interactive
"""
    
    with open("run.sh", "w") as f:
        f.write(run_script)
    
    # Make it executable
    os.chmod("run.sh", 0o755)
    print("✓ Created run script")

def verify_project_structure():
    """Verify that all required project files exist"""
    required_files = [
        "aroi_cli.py",
        "aroi_validator.py", 
        "app_interactive.py",
        "app_viewer.py",
        "batch_validator.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"⚠️  Warning: Missing files: {', '.join(missing_files)}")
        return False
    
    print("✓ All project files present")
    return True

def main():
    """Main setup function"""
    print("AROI Validator Setup")
    print("===================")
    print()
    
    # Verify project structure
    if not verify_project_structure():
        print("❌ Project structure incomplete")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed")
        print("\nYou can still use the project if dependencies are already installed.")
        print("To check if dependencies are available, try running:")
        print("  python aroi_cli.py interactive")
        print()
        # Don't exit - let user proceed if deps are already there
    
    # Create configuration
    create_streamlit_config()
    
    # Create run script
    create_run_script()
    
    print()
    print("✅ Setup completed successfully!")
    print()
    print("To run the application:")
    print("  python aroi_cli.py interactive  # Interactive web interface")
    print("  python aroi_cli.py batch        # Batch validation")
    print("  python aroi_cli.py viewer       # Results viewer")
    print()
    print("Or use the run script:")
    print("  ./run.sh")

if __name__ == "__main__":
    main()