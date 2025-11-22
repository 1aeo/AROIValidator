#!/usr/bin/env python3
"""
AROI Validator CLI - Command line interface for different operational modes

Usage:
    python aroi_cli.py interactive    # Default: Full interactive Streamlit app
    python aroi_cli.py batch          # Batch mode: Validate and save to JSON
    python aroi_cli.py viewer         # Viewer mode: Web interface showing results only
"""

import argparse
import sys
import subprocess
from pathlib import Path


def run_interactive_mode():
    """Run the full interactive Streamlit application (default mode)"""
    print("Starting AROI Validator in interactive mode...")
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        "app.py", 
        "--server.port", "5000",
        "--server.address", "0.0.0.0", 
        "--server.headless", "true",
        "--", "--mode", "interactive"
    ]
    subprocess.run(cmd)


def run_batch_mode():
    """Run batch validation and save results to JSON"""
    print("Starting AROI Validator in batch mode...")
    subprocess.run([sys.executable, "app.py", "--mode", "batch"])


def run_viewer_mode():
    """Run results viewer web interface"""
    print("Starting AROI Validator in viewer mode...")
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        "app.py", 
        "--server.port", "5000",
        "--server.address", "0.0.0.0", 
        "--server.headless", "true",
        "--", "--mode", "viewer"
    ]
    subprocess.run(cmd)


def main():
    parser = argparse.ArgumentParser(
        description="AROI Validator - Multiple operational modes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Operational Modes:
  interactive  Full interactive validation with start/stop controls (default)
  batch        Automated validation with JSON output (suitable for cron)
  viewer       Web interface showing validation results only

Examples:
  python aroi_cli.py                    # Run interactive mode
  python aroi_cli.py interactive        # Run interactive mode explicitly
  python aroi_cli.py batch              # Run batch validation
  python aroi_cli.py viewer             # Run results viewer
        """
    )
    
    parser.add_argument(
        'mode', 
        nargs='?', 
        default='interactive',
        choices=['interactive', 'batch', 'viewer'],
        help='Operational mode (default: interactive)'
    )
    
    args = parser.parse_args()
    
    # Dispatch to appropriate mode
    if args.mode == 'interactive':
        run_interactive_mode()
    elif args.mode == 'batch':
        run_batch_mode()
    elif args.mode == 'viewer':
        run_viewer_mode()


if __name__ == "__main__":
    main()