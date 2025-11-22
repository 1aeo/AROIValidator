"""
AROI Validator with Parallel Processing Support
Simplified and optimized version with parallel validation capability
"""
import concurrent.futures
import time
import requests
import json
import base64
import re
import dns.resolver
import dns.dnssec
import dns.rdatatype
from typing import Dict, Any, List, Optional, Callable
from urllib.parse import urlparse, urljoin
from datetime import datetime
from pathlib import Path


class ParallelAROIValidator:
    """Simplified AROI validator with parallel processing support"""
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.onionoo_url = "https://onionoo.torproject.org/details"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AROIValidator/1.0'
        })
        
    def fetch_relay_data(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch relay data from Onionoo API"""
        try:
            response = self.session.get(
                self.onionoo_url,
                params={'type': 'relay', 'fields': 'nickname,fingerprint,contact'},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            relays = data.get('relays', [])
            return relays[:limit] if limit else relays
        except Exception as e:
            print(f"Error fetching relay data: {e}")
            return []
    
    def validate_relay(self, relay: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single relay's AROI proof"""
        result = {
            'nickname': relay.get('nickname', 'Unknown'),
            'fingerprint': relay.get('fingerprint', ''),
            'valid': False,
            'proof_type': None,
            'domain': None,
            'validation_steps': [],
            'error': None
        }
        
        contact = relay.get('contact', '')
        if not contact:
            result['error'] = "No contact information"
            return result
        
        # Parse AROI fields
        aroi_fields = self._parse_aroi_fields(contact)
        if not aroi_fields:
            result['error'] = "Missing AROI fields"
            return result
        
        # Check ciissversion
        if aroi_fields.get('ciissversion') != '2':
            result['error'] = f"Unsupported ciissversion: {aroi_fields.get('ciissversion')}"
            return result
        
        # Validate based on proof type
        proof_type = aroi_fields.get('proof')
        if proof_type == 'dns-rsa':
            result = self._validate_dns_rsa(relay, aroi_fields, result)
        elif proof_type == 'uri-rsa':
            result = self._validate_uri_rsa(relay, aroi_fields, result)
        else:
            result['error'] = f"Unsupported proof type: {proof_type}"
        
        return result
    
    def _parse_aroi_fields(self, contact: str) -> Optional[Dict[str, str]]:
        """Parse AROI fields from contact information"""
        fields = {}
        patterns = {
            'ciissversion': r'ciissversion:(\S+)',
            'proof': r'proof:(\S+)',
            'url': r'url:(\S+)',
            'email': r'email:(\S+)'
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, contact, re.IGNORECASE)
            if match:
                fields[field] = match.group(1)
        
        return fields if 'ciissversion' in fields and 'proof' in fields else None
    
    def _validate_dns_rsa(self, relay: Dict, aroi_fields: Dict, result: Dict) -> Dict:
        """Validate DNS-RSA proof"""
        url = aroi_fields.get('url')
        if not url:
            result['error'] = "Missing URL for dns-rsa proof"
            return result
        
        # Extract domain
        domain = self._extract_domain(url)
        if not domain:
            result['error'] = "Invalid URL for DNS lookup"
            return result
        
        result['proof_type'] = 'dns-rsa'
        result['domain'] = domain
        
        # Construct DNS query domain
        fingerprint = relay['fingerprint'].lower()
        query_domain = f"{fingerprint}.{domain}"
        
        # Query DNS TXT record
        try:
            answers = dns.resolver.resolve(query_domain, 'TXT')
            txt_records = [str(rdata).strip('"') for rdata in answers]
            
            # Validate proof
            if self._validate_proof_content(txt_records, relay['fingerprint']):
                result['valid'] = True
                result['validation_steps'].append({
                    'step': 'DNS TXT lookup',
                    'success': True,
                    'details': f"Found valid proof at {query_domain}"
                })
            else:
                result['error'] = "Invalid proof content in DNS TXT record"
        except Exception as e:
            result['error'] = f"DNS lookup failed: {str(e)}"
        
        return result
    
    def _validate_uri_rsa(self, relay: Dict, aroi_fields: Dict, result: Dict) -> Dict:
        """Validate URI-RSA proof"""
        url = aroi_fields.get('url')
        if not url:
            result['error'] = "Missing URL for uri-rsa proof"
            return result
        
        # Ensure URL has scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        result['proof_type'] = 'uri-rsa'
        result['domain'] = self._extract_domain(url)
        
        # Construct proof URL according to ContactInfo spec v2
        proof_url = urljoin(url.rstrip('/') + '/', f".well-known/tor-relay/{relay['fingerprint'].lower()}.txt")
        
        # Fetch proof
        try:
            response = self.session.get(proof_url, timeout=10)
            response.raise_for_status()
            
            # Validate proof content
            if self._validate_proof_content([response.text], relay['fingerprint']):
                result['valid'] = True
                result['validation_steps'].append({
                    'step': 'URI proof fetch',
                    'success': True,
                    'details': f"Found valid proof at {proof_url}"
                })
            else:
                result['error'] = "Invalid proof content at URI"
        except Exception as e:
            result['error'] = f"Failed to fetch URI proof: {str(e)}"
        
        return result
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        try:
            parsed = urlparse(url)
            return parsed.netloc or parsed.path.split('/')[0]
        except:
            return None
    
    def _validate_proof_content(self, content_list: List[str], fingerprint: str) -> bool:
        """Validate proof content according to ContactInfo spec v2"""
        # ContactInfo spec v2 requires "we-run-this-tor-relay" text
        expected_proof = "we-run-this-tor-relay"
        return any(expected_proof in content.lower() for content in content_list)
    
    def validate_parallel(
        self, 
        relays: Optional[List[Dict]] = None,
        limit: Optional[int] = None,
        progress_callback: Optional[Callable] = None,
        stop_check: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Validate relays in parallel using thread pool
        
        Args:
            relays: List of relays to validate (fetches if None)
            limit: Maximum number of relays to validate
            progress_callback: Function to call with (current, total, result)
            stop_check: Function that returns True if validation should stop
        
        Returns:
            List of validation results
        """
        # Fetch relays if not provided
        if relays is None:
            relays = self.fetch_relay_data(limit)
        elif limit:
            relays = relays[:limit]
        
        total_relays = len(relays)
        results = []
        completed = 0
        
        # Use ThreadPoolExecutor for parallel validation
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all validation tasks
            future_to_relay = {
                executor.submit(self.validate_relay, relay): relay 
                for relay in relays
            }
            
            # Process completed tasks as they finish
            for future in concurrent.futures.as_completed(future_to_relay):
                # Check if we should stop
                if stop_check and stop_check():
                    # Cancel remaining futures
                    for f in future_to_relay:
                        f.cancel()
                    break
                
                relay = future_to_relay[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    
                    # Report progress
                    if progress_callback:
                        progress_callback(completed, total_relays, result)
                        
                except Exception as e:
                    # Handle validation error
                    error_result = {
                        'nickname': relay.get('nickname', 'Unknown'),
                        'fingerprint': relay.get('fingerprint', ''),
                        'valid': False,
                        'error': f"Validation exception: {str(e)}"
                    }
                    results.append(error_result)
                    completed += 1
                    
                    if progress_callback:
                        progress_callback(completed, total_relays, error_result)
        
        return results


def run_validation(
    progress_callback: Optional[Callable] = None,
    stop_check: Optional[Callable] = None,
    limit: Optional[int] = None,
    parallel: bool = True,
    max_workers: int = 10
) -> List[Dict[str, Any]]:
    """
    Run AROI validation with optional parallel processing
    
    Args:
        progress_callback: Function to call with (current, total, result)
        stop_check: Function that returns True if validation should stop
        limit: Maximum number of relays to validate
        parallel: Whether to use parallel processing
        max_workers: Number of parallel workers (if parallel=True)
    
    Returns:
        List of validation results
    """
    validator = ParallelAROIValidator(max_workers=max_workers if parallel else 1)
    
    if parallel:
        print(f"Using parallel validation with {max_workers} workers")
        return validator.validate_parallel(
            limit=limit,
            progress_callback=progress_callback,
            stop_check=stop_check
        )
    else:
        print("Using sequential validation")
        # Sequential validation (backwards compatible)
        relays = validator.fetch_relay_data(limit)
        results = []
        
        for idx, relay in enumerate(relays):
            if stop_check and stop_check():
                break
            
            result = validator.validate_relay(relay)
            results.append(result)
            
            if progress_callback:
                progress_callback(idx + 1, len(relays), result)
        
        return results


def calculate_statistics(results: List[Dict]) -> Dict:
    """Calculate validation statistics"""
    total_relays = len(results)
    valid_relays = sum(1 for r in results if r['valid'])
    invalid_relays = total_relays - valid_relays
    success_rate = (valid_relays / total_relays * 100) if total_relays > 0 else 0
    
    # Proof type analysis
    dns_rsa_results = [r for r in results if r.get('proof_type') == 'dns-rsa']
    uri_rsa_results = [r for r in results if r.get('proof_type') == 'uri-rsa']
    no_proof_results = [r for r in results if not r.get('proof_type')]
    
    return {
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


def save_results(results: List[Dict], filename: Optional[str] = None) -> Path:
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


def load_results(filename: str = 'latest.json') -> Optional[Dict]:
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


def list_result_files() -> List[Path]:
    """List all available result files"""
    results_dir = Path('validation_results')
    
    if not results_dir.exists():
        return []
    
    json_files = list(results_dir.glob('aroi_validation_*.json'))
    json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    return json_files


if __name__ == "__main__":
    # Test parallel validation
    print("Testing Parallel AROI Validator")
    print("=" * 50)
    
    def progress_callback(current, total, result):
        status = "✓" if result['valid'] else "✗"
        print(f"[{current}/{total}] {status} {result.get('nickname', 'Unknown')}")
    
    # Test with 10 relays using parallel processing
    results = run_validation(
        progress_callback=progress_callback,
        limit=10,
        parallel=True,
        max_workers=5
    )
    
    stats = calculate_statistics(results)
    print("\n" + "=" * 50)
    print(f"Total: {stats['total_relays']}, Valid: {stats['valid_relays']} ({stats['success_rate']:.1f}%)")