"""
Shared validation orchestration for AROI Validator
"""
import json
import time
from datetime import datetime
from pathlib import Path
from aroi_validator import AROIValidator


def run_validation(progress_callback=None, stop_check=None):
    """
    Run validation with optional progress callback and stop check
    
    Args:
        progress_callback: Function to call with (current, total, result) for progress updates
        stop_check: Function that returns True if validation should stop
        
    Returns:
        List of validation results
    """
    validator = AROIValidator()
    results = []
    
    relays = validator.fetch_relay_data()
    total_relays = len(relays)
    
    for idx, relay in enumerate(relays):
        # Check if we should stop
        if stop_check and stop_check():
            break
            
        result = validator.validate_relay(relay)
        results.append(result)
        
        # Report progress
        if progress_callback:
            progress_callback(idx + 1, total_relays, result)
    
    return results


def calculate_statistics(results):
    """Calculate comprehensive statistics from validation results"""
    total_relays = len(results)
    valid_relays = sum(1 for r in results if r['valid'])
    invalid_relays = total_relays - valid_relays
    success_rate = (valid_relays / total_relays * 100) if total_relays > 0 else 0
    
    # Proof type analysis
    dns_rsa_results = [r for r in results if r.get('proof_type') == 'dns-rsa']
    uri_rsa_results = [r for r in results if r.get('proof_type') == 'uri-rsa']
    no_proof_results = [r for r in results if not r.get('proof_type')]
    
    statistics = {
        'total_relays': total_relays,
        'valid_relays': valid_relays,
        'invalid_relays': invalid_relays,
        'success_rate': success_rate,
        'proof_types': {
            'dns_rsa': {
                'total': len(dns_rsa_results),
                'valid': sum(1 for r in dns_rsa_results if r['valid']),
                'success_rate': (sum(1 for r in dns_rsa_results if r['valid']) / len(dns_rsa_results) * 100) if dns_rsa_results else 0
            },
            'uri_rsa': {
                'total': len(uri_rsa_results),
                'valid': sum(1 for r in uri_rsa_results if r['valid']),
                'success_rate': (sum(1 for r in uri_rsa_results if r['valid']) / len(uri_rsa_results) * 100) if uri_rsa_results else 0
            },
            'no_proof': {
                'total': len(no_proof_results)
            }
        }
    }
    
    return statistics


def save_results(results, filename=None):
    """Save validation results to JSON file"""
    results_dir = Path('validation_results')
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if filename is None:
        filename = f'aroi_validation_{timestamp}.json'
    
    statistics = calculate_statistics(results)
    
    output_data = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'total_relays': statistics['total_relays'],
            'valid_relays': statistics['valid_relays'],
            'invalid_relays': statistics['invalid_relays'],
            'success_rate': statistics['success_rate']
        },
        'statistics': statistics,
        'results': results
    }
    
    # Save with timestamp
    file_path = results_dir / filename
    with open(file_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    # Also save as latest
    latest_path = results_dir / 'latest.json'
    with open(latest_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    return file_path


def load_results(filename='latest.json'):
    """Load validation results from JSON file"""
    results_dir = Path('validation_results')
    file_path = results_dir / filename
    
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def list_result_files():
    """List all available result files"""
    results_dir = Path('validation_results')
    
    if not results_dir.exists():
        return []
    
    json_files = list(results_dir.glob('aroi_validation_*.json'))
    json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    return json_files