import requests
import dns.resolver
import dns.query
import dns.message
import dns.flags
import dns.rdatatype
import json
import urllib3
from typing import List, Dict, Any, Optional

# Disable SSL warnings for domains with certificate issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AROIValidator:
    """Validator for Tor relay AROI (Autonomous Relay Operator Identity) proofs"""
    
    def __init__(self):
        """Initialize the AROI validator with DNSSEC-validating resolver"""
        # Set up a DNSSEC-validating resolver (Cloudflare 1.1.1.1)
        self.dns_resolver = dns.resolver.Resolver()
        self.dns_resolver.nameservers = ["1.1.1.1"]
        
        # Onionoo API endpoint
        self.onionoo_url = "https://onionoo.torproject.org/details?type=relay&fields=fingerprint,nickname,contact"
    
    def fetch_relay_data(self) -> List[Dict[str, Any]]:
        """
        Fetch relay data from Onionoo API
        
        Returns:
            List of relay dictionaries with fingerprint, nickname, and contact fields
            
        Raises:
            requests.RequestException: If the API request fails
            ValueError: If the response format is invalid
        """
        try:
            response = requests.get(self.onionoo_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to fetch data from Onionoo: {e}")
        
        try:
            data = response.json()
            relays = data.get("relays", [])
        except (json.JSONDecodeError, AttributeError) as e:
            raise ValueError(f"Invalid JSON response from Onionoo: {e}")
        
        if not isinstance(relays, list):
            raise ValueError("Expected 'relays' to be a list in Onionoo response")
            
        return relays
    
    def parse_aroi_tokens(self, contact: str) -> Dict[str, Optional[str]]:
        """
        Parse AROI tokens from relay contact information
        
        Args:
            contact: Contact string from relay descriptor
            
        Returns:
            Dictionary with url, proof, and ciissversion tokens
        """
        aroi_info = {}
        
        # Extract AROI tokens (url:, proof:, ciissversion:)
        for token in contact.split():
            if token.startswith("url:"):
                aroi_info["url"] = token[len("url:"):]
            elif token.startswith("proof:"):
                aroi_info["proof"] = token[len("proof:"):]
            elif token.startswith("ciissversion:"):
                aroi_info["ciissversion"] = token[len("ciissversion:"):]
        
        return aroi_info
    
    def validate_dns_rsa_proof(self, fingerprint: str, domain: str) -> tuple[bool, Optional[str]]:
        """
        Validate DNS-RSA proof for a relay
        
        Args:
            fingerprint: Relay fingerprint
            domain: Domain for DNS verification
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        record_name = f"{fingerprint.lower()}.{domain}"
        
        try:
            # Build DNS query with DNSSEC (DO flag) and request AD bit
            query = dns.message.make_query(record_name, dns.rdatatype.TXT, want_dnssec=True)
            query.flags |= dns.flags.AD
            
            # First try UDP
            response = dns.query.udp(query, self.dns_resolver.nameservers[0], timeout=5)
            if response.flags & dns.flags.TC:
                # If truncated, retry over TCP
                response = dns.query.tcp(query, self.dns_resolver.nameservers[0], timeout=5)
                
        except Exception as e:
            return False, f"DNS query exception: {e}"
        
        # Collect all TXT strings in the response
        txt_values = []
        for answer in response.answer:
            if answer.rdtype == dns.rdatatype.TXT:
                for txt_data in answer:
                    txt_val = b"".join(txt_data.strings).decode("utf-8", errors="ignore")
                    txt_values.append(txt_val)
        
        expected_value = "we-run-this-tor-relay"
        
        if not txt_values:
            return False, f"No TXT records found at {record_name}; expected '{expected_value}'."
        
        if expected_value not in txt_values:
            found_vals = ", ".join(f"'{v}'" for v in txt_values)
            return False, (
                f"TXT record mismatch at {record_name}: found {found_vals}; "
                f"expected '{expected_value}'."
            )
        
        # Check DNSSEC validation
        dnssec_valid = bool(response.flags & dns.flags.AD)
        if not dnssec_valid:
            return False, "DNSSEC validation failed (AD flag not set)."
        
        return True, None
    
    def validate_uri_rsa_proof(self, fingerprint: str, domain: str) -> tuple[bool, Optional[str]]:
        """
        Validate URI-RSA proof for a relay
        
        Args:
            fingerprint: Relay fingerprint
            domain: Domain for URI verification
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        proof_url = f"https://{domain}/.well-known/tor-relay/rsa-fingerprint.txt"
        
        # Try with SSL verification first
        try:
            resp = requests.get(proof_url, timeout=10, allow_redirects=False, verify=True)
            
            # If redirect, ensure it stays on the same domain
            if 300 <= resp.status_code < 400:
                redirect_loc = resp.headers.get("Location", "")
                if not redirect_loc or domain not in redirect_loc:
                    return False, f"Redirect to disallowed domain: '{redirect_loc}'."
                
                resp = requests.get(redirect_loc, timeout=10, allow_redirects=False, verify=True)
            
            resp.raise_for_status()
            
        except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as ssl_error:
            # If SSL verification fails, try without verification but note it in error
            try:
                # Use a more permissive session for problematic SSL configurations
                session = requests.Session()
                session.verify = False
                
                # Set user agent and headers to improve compatibility
                headers = {
                    'User-Agent': 'Mozilla/5.0 (compatible; AROI-Validator/1.0)',
                    'Accept': 'text/plain, */*'
                }
                
                resp = session.get(proof_url, timeout=10, allow_redirects=False, headers=headers)
                
                # If redirect, ensure it stays on the same domain
                if 300 <= resp.status_code < 400:
                    redirect_loc = resp.headers.get("Location", "")
                    if not redirect_loc or domain not in redirect_loc:
                        return False, f"Redirect to disallowed domain: '{redirect_loc}'."
                    
                    resp = session.get(redirect_loc, timeout=10, allow_redirects=False, headers=headers)
                
                resp.raise_for_status()
                
                # Note SSL issue but continue validation
                ssl_warning = f" (SSL/TLS issue bypassed: {str(ssl_error)})"
                
            except requests.RequestException as e:
                return False, f"Connection failed even without SSL verification: {str(e)[:100]}..."
                
        except requests.RequestException as e:
            return False, f"HTTP exception: {e}"
        
        if resp.status_code != 200:
            return False, f"HTTP returned status {resp.status_code} from '{proof_url}'."
        
        # Check that fingerprint appears in the file (case-insensitive)
        content = resp.text
        relay_fp = fingerprint.upper()
        found = any(line.strip().upper() == relay_fp for line in content.splitlines())
        
        if not found:
            return False, f"Fingerprint '{relay_fp}' not found in .well-known file at '{proof_url}'."
        
        # Return success, with SSL warning if applicable
        ssl_warning = locals().get('ssl_warning', '')
        if ssl_warning:
            return True, f"Valid (with SSL warning){ssl_warning}"
        
        return True, None
    
    def normalize_domain(self, url: str) -> str:
        """
        Normalize domain by stripping scheme and trailing slash
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized domain string
        """
        domain = url
        if domain.startswith("http://") or domain.startswith("https://"):
            domain = domain.split("://", 1)[1]
        domain = domain.rstrip("/")
        return domain
    
    def validate_relay(self, relay: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate AROI proof for a single relay
        
        Args:
            relay: Relay dictionary with fingerprint, nickname, and contact
            
        Returns:
            Dictionary with validation results and error information
        """
        fingerprint = relay.get("fingerprint")
        contact = relay.get("contact", "")
        nickname = relay.get("nickname", "")
        
        # Parse AROI tokens from contact information
        aroi_info = self.parse_aroi_tokens(contact)
        
        # Check for missing fields
        missing_fields = [field for field in ("url", "proof", "ciissversion") if field not in aroi_info]
        if missing_fields:
            return {
                "fingerprint": fingerprint,
                "nickname": nickname,
                "domain": aroi_info.get("url", None),
                "proof_type": aroi_info.get("proof", None),
                "ciissversion": aroi_info.get("ciissversion", None),
                "valid": False,
                "error": f"Missing AROI fields: {', '.join(missing_fields)}."
            }
        
        # Check version support
        version = aroi_info["ciissversion"]
        if version != "2":
            return {
                "fingerprint": fingerprint,
                "nickname": nickname,
                "domain": aroi_info["url"],
                "proof_type": aroi_info["proof"],
                "ciissversion": version,
                "valid": False,
                "error": f"Unsupported ciissversion: {version}"
            }
        
        # Normalize domain
        domain = self.normalize_domain(aroi_info["url"])
        proof_type = aroi_info["proof"]
        
        # Validate based on proof type
        if proof_type == "dns-rsa":
            valid, error_msg = self.validate_dns_rsa_proof(fingerprint, domain)
        elif proof_type == "uri-rsa":
            valid, error_msg = self.validate_uri_rsa_proof(fingerprint, domain)
        else:
            valid = False
            error_msg = f"Unsupported proof type: '{proof_type}'."
        
        return {
            "fingerprint": fingerprint,
            "nickname": nickname,
            "domain": domain,
            "proof_type": proof_type,
            "ciissversion": version,
            "valid": valid,
            "error": error_msg
        }
    
    def validate_relay_with_steps(self, relay: Dict[str, Any], ui_container) -> Dict[str, Any]:
        """
        Validate AROI proof for a single relay with detailed step tracking for UI
        
        Args:
            relay: Relay dictionary with fingerprint, nickname, and contact
            ui_container: Streamlit container for displaying step-by-step progress
            
        Returns:
            Dictionary with validation results and error information
        """
        fingerprint = relay.get("fingerprint", "")
        contact = relay.get("contact", "")
        nickname = relay.get("nickname", "")
        
        # Step 1: Parse contact information
        with ui_container:
            ui_container.write("**Step 1:** Parsing contact information")
            aroi_info = self.parse_aroi_tokens(contact)
            
            if contact:
                ui_container.write(f"Contact length: {len(contact)} characters")
                # Display full contact info in a code block with horizontal scrolling
                ui_container.code(contact)
            else:
                ui_container.write("❌ No contact information found")
            
            # Show parsed tokens
            if aroi_info:
                parsed_display = []
                for key, value in aroi_info.items():
                    parsed_display.append(f"{key}: {value}")
                ui_container.write(f"✅ Parsed tokens: {', '.join(parsed_display)}")
            else:
                ui_container.write("❌ No AROI tokens found")
        
        # Step 2: Check required fields
        with ui_container:
            ui_container.write("**Step 2:** Checking required AROI fields")
            missing_fields = [field for field in ("url", "proof", "ciissversion") if field not in aroi_info]
            
            for field in ("url", "proof", "ciissversion"):
                if field in aroi_info:
                    ui_container.write(f"✅ {field}: {aroi_info[field]}")
                else:
                    ui_container.write(f"❌ {field}: Missing")
            
            if missing_fields:
                error_msg = f"Missing AROI fields: {', '.join(missing_fields)}."
                ui_container.write(f"❌ Validation failed: {error_msg}")
                return {
                    "fingerprint": fingerprint,
                    "nickname": nickname,
                    "domain": aroi_info.get("url", None),
                    "proof_type": aroi_info.get("proof", None),
                    "ciissversion": aroi_info.get("ciissversion", None),
                    "valid": False,
                    "error": error_msg
                }
        
        # Step 3: Check version support
        with ui_container:
            ui_container.write("**Step 3:** Checking version support")
            version = aroi_info["ciissversion"]
            
            if version == "2":
                ui_container.write(f"✅ Supported version: {version}")
            else:
                error_msg = f"Unsupported ciissversion: {version}"
                ui_container.write(f"❌ {error_msg}")
                return {
                    "fingerprint": fingerprint,
                    "nickname": nickname,
                    "domain": aroi_info["url"],
                    "proof_type": aroi_info["proof"],
                    "ciissversion": version,
                    "valid": False,
                    "error": error_msg
                }
        
        # Step 4: Normalize domain
        with ui_container:
            ui_container.write("**Step 4:** Normalizing domain")
            original_url = aroi_info["url"]
            domain = self.normalize_domain(original_url)
            ui_container.write(f"Original URL: {original_url}")
            ui_container.write(f"✅ Normalized domain: {domain}")
        
        proof_type = aroi_info["proof"]
        
        # Step 5: Validate proof
        with ui_container:
            ui_container.write(f"**Step 5:** Validating {proof_type} proof")
            
            if proof_type == "dns-rsa":
                record_name = f"{fingerprint.lower()}.{domain}"
                ui_container.write(f"Looking up TXT record: {record_name}")
                ui_container.write(f"Expected value: 'we-run-this-tor-relay'")
                
                valid, error_msg = self.validate_dns_rsa_proof(fingerprint, domain)
                
                if valid:
                    ui_container.write("✅ DNS-RSA proof validation successful")
                    ui_container.write("✅ DNSSEC validation passed")
                else:
                    ui_container.write(f"❌ DNS-RSA proof validation failed: {error_msg}")
                    
            elif proof_type == "uri-rsa":
                proof_url = f"https://{domain}/.well-known/tor-relay/rsa-fingerprint.txt"
                ui_container.write(f"Checking URL: {proof_url}")
                ui_container.write(f"Looking for fingerprint: {fingerprint.upper()}")
                
                valid, error_msg = self.validate_uri_rsa_proof(fingerprint, domain)
                
                if valid:
                    if error_msg and "SSL" in error_msg:
                        ui_container.write("✅ URI-RSA proof validation successful")
                        ui_container.write(f"⚠️ SSL Warning: {error_msg}")
                    else:
                        ui_container.write("✅ URI-RSA proof validation successful")
                else:
                    ui_container.write(f"❌ URI-RSA proof validation failed: {error_msg}")
                    
            else:
                valid = False
                error_msg = f"Unsupported proof type: '{proof_type}'."
                ui_container.write(f"❌ {error_msg}")
        
        return {
            "fingerprint": fingerprint,
            "nickname": nickname,
            "domain": domain,
            "proof_type": proof_type,
            "ciissversion": version,
            "valid": valid,
            "error": error_msg
        }
    
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
        return results
