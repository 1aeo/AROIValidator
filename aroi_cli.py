#!/usr/bin/env python3
"""
AROI Validator CLI - Ultra-Simplified Dispatcher
"""
import sys
import subprocess
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="AROI Validator with Parallel Processing Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  interactive  Web UI with parallel validation controls (default)
  batch        Automated parallel batch processing
  viewer       View saved validation results

Environment Variables (for batch mode):
  BATCH_LIMIT   Max relays to validate (default: 100)
  PARALLEL      Use parallel processing (default: true)
  MAX_WORKERS   Number of worker threads (default: 10)

Examples:
  python aroi_cli.py                           # Interactive mode
  python aroi_cli.py batch                     # Batch with defaults
  BATCH_LIMIT=500 MAX_WORKERS=20 python aroi_cli.py batch
        """
    )
    
    parser.add_argument(
        'mode', 
        nargs='?', 
        default='interactive',
        choices=['interactive', 'batch', 'viewer'],
        help='Operational mode'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'batch':
        # Run batch mode directly
        subprocess.run([sys.executable, "app.py", "--mode", "batch"])
    else:
        # Run Streamlit for interactive/viewer modes
        print(f"Starting AROI Validator - {args.mode.capitalize()} Mode")
        print("=" * 50)
        print("Opening web interface on port 5000...")
        
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            "app.py", 
            "--server.port", "5000",
            "--server.address", "0.0.0.0", 
            "--server.headless", "true",
            "--", "--mode", args.mode
        ]
        
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            print("\nShutting down...")
            sys.exit(0)


if __name__ == "__main__":
    main()