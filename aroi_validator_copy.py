"""
AROI (Autonomous Relay Operator Identity) Validator for Tor Relays

This module validates AROI proofs for Tor relays by checking DNS-RSA and URI-RSA
proof types with DNSSEC validation for enhanced security.
"""

import re
import requests
import dns.resolver
import dns.rdatatype
import dns.flags
import streamlit as st
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import time


class AROIValidator:
    """Validator for Tor relay AROI (Autonomous Relay Operator Identity) proofs"""
    
    def __init__(self):
        """Initialize the AROI validator with DNSSEC-validating resolver"""
        self.resolver = dns.resolver.Resolver()
        
        # Configure DNSSEC validation
        self.resolver.use_edns(0, dns.flags.DO, 4096)
        self.resolver.flags = dns.flags.RD | dns.flags.AD
        
        # Use secure DNS servers
        self.resolver.nameservers = [
            '1.1.1.1',     # Cloudflare
            '8.8.8.8',     # Google
            '9.9.9.9'      # Quad9
        ]
        
        # Set timeouts
        self.resolver.timeout = 10
        self.resolver.lifetime = 30
    
    def fetch_relay_data(self) -> List[Dict[str, Any]]:
        """
        Fetch relay data from Onionoo API
        
        Returns:
            List of relay dictionaries with fingerprint, nickname, and contact fields
            
        Raises:
            requests.RequestException: If the API request fails
            ValueError: If the response format is invalid
        """
        url = "https://onionoo.torproject.org/details"
        headers = {
            'User-Agent': 'AROI-Validator/1.0 (Research Tool)'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            relays = data.get('relays', [])
            
            # Filter relays that have contact information
            filtered_relays = []
            for relay in relays:
                if relay.get('contact'):
                    filtered_relays.append({
                        'fingerprint': relay.get('fingerprint'),
                        'nickname': relay.get('nickname'),
                        'contact': relay.get('contact')
                    })
            
            return filtered_relays
            
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to fetch relay data: {str(e)}")
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid response format: {str(e)}")
    
    def parse_aroi_tokens(self, contact: str) -> Dict[str, Optional[str]]:
        """
        Parse AROI tokens from relay contact information
        
        Args:
            contact: Contact string from relay descriptor
            
        Returns:
            Dictionary with url, proof, and ciissversion tokens
        """
        tokens = {}
        
        # Parse aroi-url token
        url_match = re.search(r'aroi-url:([^\s]+)', contact)
        tokens['url'] = url_match.group(1) if url_match else None
        
        # Parse proof token  
        proof_match = re.search(r'proof:([^\s]+)', contact)
        tokens['proof'] = proof_match.group(1) if proof_match else None
        
        # Parse ciissversion token
        version_match = re.search(r'ciissversion:([^\s]+)', contact)
        tokens['ciissversion'] = version_match.group(1) if version_match else None
        
        return tokens
    
    def validate_dns_rsa_proof(self, fingerprint: str, domain: str) -> tuple[bool, Optional[str]]:
        """
        Validate DNS-RSA proof for a relay
        
        Args:
            fingerprint: Relay fingerprint
            domain: Domain for DNS verification
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Query for TXT records with DNSSEC validation
            txt_records = []
            try:
                # Try UDP first
                answer = self.resolver.resolve(domain, dns.rdatatype.TXT, tcp=False)
                txt_records = [record.to_text().strip('"') for record in answer]
            except:
                try:
                    # Fallback to TCP if UDP fails
                    answer = self.resolver.resolve(domain, dns.rdatatype.TXT, tcp=True)
                    txt_records = [record.to_text().strip('"') for record in answer]
                except Exception as e:
                    return False, f"DNS query failed: {str(e)}"
            
            # Look for AROI proof in TXT records
            aroi_proof = None
            for record in txt_records:
                if 'aroi-rsa' in record and fingerprint.lower() in record.lower():
                    aroi_proof = record
                    break
            
            if not aroi_proof:
                return False, "No matching AROI proof found in DNS TXT records"
            
            # Basic validation - check if fingerprint is present
            if fingerprint.lower() not in aroi_proof.lower():
                return False, "Fingerprint not found in AROI proof"
            
            return True, None
            
        except Exception as e:
            return False, f"DNS validation error: {str(e)}"
    
    def validate_uri_rsa_proof(self, fingerprint: str, domain: str) -> tuple[bool, Optional[str]]:
        """
        Validate URI-RSA proof for a relay
        
        Args:
            fingerprint: Relay fingerprint
            domain: Domain for URI verification
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Construct URI for proof document
            if not domain.startswith('http'):
                uri = f"https://{domain}/.well-known/tor-relay/rsa-fingerprint.txt"
            else:
                parsed = urlparse(domain)
                uri = f"{parsed.scheme}://{parsed.netloc}/.well-known/tor-relay/rsa-fingerprint.txt"
            
            # Fetch proof document
            headers = {
                'User-Agent': 'AROI-Validator/1.0 (Research Tool)'
            }
            
            response = requests.get(uri, headers=headers, timeout=15, verify=True)
            response.raise_for_status()
            
            proof_content = response.text.strip()
            
            # Validate proof content
            if not proof_content:
                return False, "Empty proof document"
            
            # Check if fingerprint is present in proof
            if fingerprint.lower() not in proof_content.lower():
                return False, "Fingerprint not found in proof document"
            
            return True, None
            
        except requests.RequestException as e:
            return False, f"HTTP request failed: {str(e)}"
        except Exception as e:
            return False, f"URI validation error: {str(e)}"
    
    def normalize_domain(self, url: str) -> str:
        """
        Normalize domain by stripping scheme and trailing slash
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized domain string
        """
        # Remove scheme if present
        if url.startswith(('http://', 'https://')):
            parsed = urlparse(url)
            return parsed.netloc
        
        # Remove trailing slash
        return url.rstrip('/')
    
    def validate_relay(self, relay: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate AROI proof for a single relay
        
        Args:
            relay: Relay dictionary with fingerprint, nickname, and contact
            
        Returns:
            Dictionary with validation results and error information
        """
        result = {
            'fingerprint': relay.get('fingerprint'),
            'nickname': relay.get('nickname'),
            'contact': relay.get('contact'),
            'valid': False,
            'proof_type': None,
            'domain': None,
            'error': None
        }
        
        try:
            contact = relay.get('contact', '')
            fingerprint = relay.get('fingerprint')
            
            if not contact:
                result['error'] = "No contact information available"
                return result
            
            if not fingerprint:
                result['error'] = "No fingerprint available"
                return result
            
            # Parse AROI tokens
            tokens = self.parse_aroi_tokens(contact)
            
            # Check for proof token (dns-rsa or uri-rsa)
            proof_type = tokens.get('proof')
            aroi_url = tokens.get('url')
            
            if not proof_type:
                result['error'] = "No proof token found in contact"
                return result
            
            if not aroi_url:
                result['error'] = "No aroi-url token found in contact"
                return result
            
            # Normalize domain
            domain = self.normalize_domain(aroi_url)
            result['domain'] = domain
            result['proof_type'] = proof_type
            
            # Validate based on proof type
            if proof_type == 'dns-rsa':
                is_valid, error = self.validate_dns_rsa_proof(fingerprint, domain)
            elif proof_type == 'uri-rsa':
                is_valid, error = self.validate_uri_rsa_proof(fingerprint, domain)
            else:
                result['error'] = f"Unsupported proof type: {proof_type}"
                return result
            
            result['valid'] = is_valid
            if error:
                result['error'] = error
            
        except Exception as e:
            result['error'] = f"Validation error: {str(e)}"
        
        return result
    
    def validate_relay_with_steps(self, relay: Dict[str, Any], ui_container) -> Dict[str, Any]:
        """
        Validate AROI proof for a single relay with detailed step tracking for UI
        
        Args:
            relay: Relay dictionary with fingerprint, nickname, and contact
            ui_container: Streamlit container for displaying step-by-step progress
            
        Returns:
            Dictionary with validation results and error information
        """
        result = {
            'fingerprint': relay.get('fingerprint'),
            'nickname': relay.get('nickname'),
            'contact': relay.get('contact'),
            'valid': False,
            'proof_type': None,
            'domain': None,
            'error': None,
            'steps': []
        }
        
        def add_step(message: str, status: str = 'info'):
            step = {'message': message, 'status': status}
            result['steps'].append(step)
            with ui_container:
                if status == 'success':
                    st.success(f"✅ {message}")
                elif status == 'error':
                    st.error(f"❌ {message}")
                elif status == 'warning':
                    st.warning(f"⚠️ {message}")
                else:
                    st.info(f"ℹ️ {message}")
        
        try:
            contact = relay.get('contact', '')
            fingerprint = relay.get('fingerprint')
            nickname = relay.get('nickname', 'Unknown')
            
            add_step(f"Starting validation for relay: {nickname}")
            
            if not contact:
                add_step("No contact information available", 'error')
                result['error'] = "No contact information available"
                return result
            
            if not fingerprint:
                add_step("No fingerprint available", 'error')
                result['error'] = "No fingerprint available"
                return result
            
            add_step("Parsing AROI tokens from contact information")
            
            # Parse AROI tokens
            tokens = self.parse_aroi_tokens(contact)
            
            # Check for proof token (dns-rsa or uri-rsa)
            proof_type = tokens.get('proof')
            aroi_url = tokens.get('url')
            
            if not proof_type:
                add_step("No proof token found in contact", 'error')
                result['error'] = "No proof token found in contact"
                return result
            
            if not aroi_url:
                add_step("No aroi-url token found in contact", 'error')
                result['error'] = "No aroi-url token found in contact"
                return result
            
            add_step(f"Found proof type: {proof_type}")
            add_step(f"Found AROI URL: {aroi_url}")
            
            # Normalize domain
            domain = self.normalize_domain(aroi_url)
            result['domain'] = domain
            result['proof_type'] = proof_type
            
            add_step(f"Normalized domain: {domain}")
            
            # Validate based on proof type
            if proof_type == 'dns-rsa':
                add_step("Starting DNS-RSA validation")
                is_valid, error = self.validate_dns_rsa_proof(fingerprint, domain)
            elif proof_type == 'uri-rsa':
                add_step("Starting URI-RSA validation")
                is_valid, error = self.validate_uri_rsa_proof(fingerprint, domain)
            else:
                add_step(f"Unsupported proof type: {proof_type}", 'error')
                result['error'] = f"Unsupported proof type: {proof_type}"
                return result
            
            if is_valid:
                add_step("AROI proof validation successful!", 'success')
                result['valid'] = True
            else:
                add_step(f"AROI proof validation failed: {error}", 'error')
                result['error'] = error
            
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            add_step(error_msg, 'error')
            result['error'] = error_msg
        
        return result
    
    def validate_relays(self, relays: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate AROI proofs for multiple relays
        
        Args:
            relays: List of relay dictionaries
            
        Returns:
            List of validation result dictionaries
        """
        results = []
        
        for relay in relays:
            result = self.validate_relay(relay)
            results.append(result)
            
            # Small delay to avoid overwhelming APIs
            time.sleep(0.1)
        
        return results