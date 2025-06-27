#!/usr/bin/env python3
"""
AROI Batch Validator - Automated validation suitable for cron jobs

This script fetches all relay data from Onionoo API, validates AROI proofs,
and saves results to a timestamped JSON file.
"""

import json
import time
import sys
from datetime import datetime
from pathlib import Path
from aroi_validator import AROIValidator


def main():
    """Run batch validation and save results to JSON"""
    
    print(f"AROI Batch Validator - Started at {datetime.now().isoformat()}")
    
    try:
        # Initialize validator
        validator = AROIValidator()
        
        # Fetch relay data
        print("Fetching relay data from Onionoo API...")
        relays = validator.fetch_relay_data()
        
        if not relays:
            print("ERROR: No relay data available")
            sys.exit(1)
        
        print(f"Found {len(relays)} relays to validate")
        
        # Run validation
        print("Starting validation process...")
        results = []
        
        for i, relay in enumerate(relays):
            # Progress indicator every 50 relays
            if i % 50 == 0:
                print(f"Progress: {i}/{len(relays)} relays processed")
            
            result = validator.validate_relay(relay)
            results.append(result)
            
            # Small delay to avoid overwhelming APIs
            time.sleep(0.1)
        
        print(f"Validation complete: {len(results)} relays processed")
        
        # Calculate statistics
        valid_count = sum(1 for r in results if r['valid'])
        invalid_count = len(results) - valid_count
        
        dns_rsa_results = [r for r in results if r.get('proof_type') == 'dns-rsa']
        uri_rsa_results = [r for r in results if r.get('proof_type') == 'uri-rsa']
        no_proof_results = [r for r in results if not r.get('proof_type')]
        
        dns_rsa_valid = sum(1 for r in dns_rsa_results if r['valid'])
        uri_rsa_valid = sum(1 for r in uri_rsa_results if r['valid'])
        
        # Prepare output data
        timestamp = datetime.now().isoformat()
        output_data = {
            'metadata': {
                'timestamp': timestamp,
                'execution_time': time.time(),
                'total_relays': len(results),
                'valid_relays': valid_count,
                'invalid_relays': invalid_count,
                'success_rate': (valid_count / len(results)) * 100 if results else 0
            },
            'statistics': {
                'proof_types': {
                    'dns_rsa': {
                        'total': len(dns_rsa_results),
                        'valid': dns_rsa_valid,
                        'success_rate': (dns_rsa_valid / len(dns_rsa_results)) * 100 if dns_rsa_results else 0
                    },
                    'uri_rsa': {
                        'total': len(uri_rsa_results),
                        'valid': uri_rsa_valid,
                        'success_rate': (uri_rsa_valid / len(uri_rsa_results)) * 100 if uri_rsa_results else 0
                    },
                    'no_proof': {
                        'total': len(no_proof_results)
                    }
                }
            },
            'results': results
        }
        
        # Create output filename with timestamp
        output_dir = Path('validation_results')
        output_dir.mkdir(exist_ok=True)
        
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f'aroi_validation_{timestamp_str}.json'
        
        # Save results to JSON file
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        # Also save as latest.json for easy access
        latest_file = output_dir / 'latest.json'
        with open(latest_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        print(f"Timestamp: {timestamp}")
        print(f"Total relays: {len(results)}")
        print(f"Valid AROI: {valid_count} ({(valid_count/len(results)*100):.1f}%)")
        print(f"Invalid AROI: {invalid_count} ({(invalid_count/len(results)*100):.1f}%)")
        print()
        print("Proof Type Breakdown:")
        if dns_rsa_results:
            dns_rate = (dns_rsa_valid / len(dns_rsa_results)) * 100
            print(f"  DNS-RSA: {dns_rsa_valid}/{len(dns_rsa_results)} ({dns_rate:.1f}%)")
        if uri_rsa_results:
            uri_rate = (uri_rsa_valid / len(uri_rsa_results)) * 100
            print(f"  URI-RSA: {uri_rsa_valid}/{len(uri_rsa_results)} ({uri_rate:.1f}%)")
        if no_proof_results:
            print(f"  No Proof: {len(no_proof_results)}")
        print()
        print(f"Results saved to: {output_file}")
        print(f"Latest results: {latest_file}")
        print("="*60)
        
    except Exception as e:
        print(f"ERROR: Batch validation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()