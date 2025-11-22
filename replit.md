# AROI Validator

## Overview

The AROI Validator is a validation tool for evaluating Tor relay operator proofs using the Accuracy, Relevance, Objectivity, and Informativeness (AROI) framework. The application validates relay operator contact information through DNS and URI-based RSA proofs, querying the Tor network's Onionoo API to fetch relay data and verify cryptographic proofs of ownership.

The system provides both a web-based interface (Streamlit) and command-line tools for batch processing Tor relay validations with parallel processing capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Structure

The application follows a modular Python architecture with three primary entry points:

1. **app.py** - Streamlit web application providing interactive UI for relay validation
2. **aroi_cli.py** - Command-line dispatcher supporting interactive, batch, and viewer modes
3. **aroi_validator.py** - Core validation engine with parallel processing support

**Rationale**: Separating concerns between UI (Streamlit), CLI orchestration, and validation logic allows for flexible usage patterns while maintaining a single source of truth for validation logic.

### Frontend Architecture

**Technology**: Streamlit web framework

**Design Decision**: Streamlit was chosen for rapid development of an interactive web interface without requiring separate frontend/backend implementation. It provides:
- Real-time validation feedback
- Session state management for tracking validation progress
- Built-in progress bars and status updates
- Data visualization with pandas integration

**Trade-offs**: 
- Pros: Fast development, Python-native, built-in UI components
- Cons: Limited customization compared to traditional web frameworks, primarily single-user focused

### Backend Architecture

**Core Component**: ParallelAROIValidator class in aroi_validator.py

**Key Features**:
1. Concurrent validation using ThreadPoolExecutor
2. Configurable worker pool (default: 10 workers)
3. Custom legacy TLS adapter for compatibility with older Tor relay servers
4. Session-based HTTP client with custom user agent

**Design Pattern**: The validator uses a class-based approach with parallel processing capabilities through Python's concurrent.futures module.

**Security Considerations**: 
- SSL verification is disabled for legacy Tor relays (TLSv1 support)
- Custom TLS adapter with reduced security level (SECLEVEL=1) to support older ciphers
- This is necessary for communicating with legacy Tor infrastructure but documented as a trade-off

### Validation Flow

1. Fetch relay data from Onionoo API
2. Extract AROI proof fields from relay contact information
3. Validate proofs via DNS TXT records or URI-based RSA verification
4. Support for both dns-rsa and uri-rsa proof types
5. Calculate success rates and categorize results by proof type

### Data Storage

**Format**: JSON files with timestamped filenames

**Location**: `validation_results/` directory

**Schema**:
```json
{
  "metadata": {
    "timestamp": "ISO timestamp",
    "total_relays": int,
    "valid_relays": int,
    "invalid_relays": int,
    "success_rate": float
  },
  "statistics": {
    "proof_types": {
      "dns_rsa": {...},
      "uri_rsa": {...},
      "no_proof": {...}
    }
  },
  "results": [...]
}
```

**Rationale**: JSON provides human-readable results that can be easily consumed by the viewer mode or external tools. Results are timestamped for historical tracking, with a `latest.json` symlink for quick access.

### Configuration Management

**Method**: Streamlit configuration via `.streamlit/config.toml`

**Setup Script**: setup.py handles dependency installation and configuration

**Dependencies**:
- streamlit - Web UI framework
- dnspython - DNS resolution and DNSSEC validation
- pandas - Data manipulation and display
- requests - HTTP client
- urllib3 - HTTP library with custom SSL handling

**Rationale**: Automated setup script simplifies deployment on new environments (particularly Replit), handling both uv (Replit's package manager) and pip as fallbacks.

## External Dependencies

### Third-Party APIs

**Onionoo API** (`https://onionoo.torproject.org/details`)
- Purpose: Tor network relay status and metadata
- Usage: Fetches relay details including contact information for validation
- No authentication required
- Rate limiting considerations apply

### Python Libraries

**Core Dependencies**:
- `streamlit` - Web application framework for interactive UI
- `dnspython` - DNS query and DNSSEC validation
- `pandas` - Data structures for relay statistics and result display
- `requests` - HTTP client with session management
- `urllib3` - Low-level HTTP handling with SSL customization

**Standard Library**:
- `concurrent.futures` - Parallel processing via ThreadPoolExecutor
- `ssl` - TLS/SSL context configuration
- `json` - Result serialization
- `base64` - Encoding for cryptographic operations
- `pathlib` - File system operations

### Network Services

**DNS Resolution**:
- Used for dns-rsa proof validation via TXT records
- DNSSEC validation support included in validation flow
- Relies on system DNS resolver configuration

**HTTP/HTTPS**:
- Legacy TLS support (TLSv1+) for older Tor relay servers
- Custom SSL context with reduced security requirements
- Session pooling for performance optimization

### Deployment Platform

**Replit-Specific**:
- Configuration assumes port 5000 for Streamlit server
- Setup script detects and prefers `uv` package manager
- Headless server mode enabled by default