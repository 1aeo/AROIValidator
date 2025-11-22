# AROI Validator

## Overview

AROI Validator is a specialized tool for validating Tor relay operator proofs using the Accuracy, Relevance, Objectivity, and Informativeness (AROI) framework. The application validates relay operator contact information through DNS TXT records and URI-based RSA cryptographic proofs. It features both an interactive web interface built with Streamlit and a command-line interface for batch processing operations.

The validator fetches relay data from the Tor Project's Onionoo API, extracts AROI proof fields from relay contact information, validates these proofs against DNS records or URIs, and generates comprehensive validation reports with success rate analytics.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Structure

The application follows a modular, three-tier architecture:

1. **Presentation Layer** (`app.py`) - Streamlit-based web interface providing interactive validation controls, real-time progress tracking, and result visualization with pandas DataFrames
2. **CLI Dispatcher** (`aroi_cli.py`) - Command-line entry point supporting three operational modes: interactive (web UI), batch (automated processing), and viewer (results browser)
3. **Core Validation Engine** (`aroi_validator.py`) - The ParallelAROIValidator class handles all validation logic with concurrent processing capabilities

### Parallel Processing Design

**Problem**: Validating large numbers of Tor relays sequentially is time-consuming, with each validation requiring network I/O for DNS lookups and HTTP requests.

**Solution**: Concurrent validation using Python's ThreadPoolExecutor with configurable worker pools (default: 10 workers).

**Rationale**: Network I/O-bound operations benefit from thread-based parallelism. ThreadPoolExecutor provides a simple, managed approach to concurrent processing without the complexity of multiprocessing. The 10-worker default balances throughput with resource consumption.

**Tradeoffs**: Thread-based parallelism in Python is limited by the GIL for CPU-bound operations, but since validation is primarily I/O-bound (DNS queries, HTTP requests), this is not a constraint. Worker count can be tuned via environment variables or UI controls.

### Validation Flow Architecture

**Multi-stage validation pipeline**:
1. Fetch relay metadata from Onionoo API (https://onionoo.torproject.org/details)
2. Parse contact information to extract AROI-specific fields (url, proof, ciissversion)
3. Determine proof type (dns-rsa or uri-rsa) based on contact format
4. Execute proof-specific validation (DNS TXT record lookup or URI-based RSA verification)
5. Aggregate results and calculate statistics by proof type
6. Persist results as timestamped JSON files

**Design Decision**: The validation pipeline is designed to be fault-tolerant, with each relay validation independent of others. Failed validations are captured with error details rather than halting the entire process.

### Legacy TLS Support

**Problem**: Some relay operators host proof URIs on servers with outdated TLS configurations that modern Python SSL contexts reject.

**Solution**: Custom LegacyTLSAdapter extending requests.adapters.HTTPAdapter with relaxed SSL settings (TLSv1 minimum, SECLEVEL=1, disabled hostname verification).

**Rationale**: Ensuring maximum compatibility with diverse relay operator infrastructure. Since proof validation doesn't involve sensitive data transmission, relaxed TLS verification is acceptable.

**Security Note**: SSL warnings are suppressed via urllib3.disable_warnings(). This is appropriate for the validation use case but should be reconsidered if the application handles sensitive data.

### State Management

**Web Interface State**: Streamlit session_state manages validation lifecycle (validation_results, validation_in_progress, validation_stopped flags) to provide responsive UI updates during long-running parallel operations.

**Results Persistence**: JSON-based storage in `validation_results/` directory with ISO timestamp filenames plus a `latest.json` symlink/copy for quick access to most recent results.

### DNS Resolution

Uses dnspython library for DNS operations, supporting both standard DNS queries and DNSSEC validation capabilities (dns.resolver, dns.dnssec modules imported).

### Session Management

A persistent requests.Session object with custom User-Agent ('AROIValidator/1.0') is maintained for efficient HTTP connection pooling across multiple relay validations.

## External Dependencies

### Required Python Packages

- **streamlit** - Web UI framework for interactive validation interface
- **dnspython** - DNS resolution and DNSSEC validation for dns-rsa proof type
- **pandas** - Data manipulation and result visualization in Streamlit UI
- **requests** - HTTP client for Onionoo API access and uri-rsa proof validation
- **urllib3** - Low-level HTTP utilities, used for SSL warning suppression

### External APIs

- **Onionoo API** (https://onionoo.torproject.org/details) - Tor Project's relay metadata service, provides JSON-formatted relay details including contact information, fingerprints, and nicknames

### Development Tools

- **uv** - Replit's preferred package manager (with pip fallback in setup.py)
- Package installation handled by `setup.py` with automatic Streamlit configuration generation

### File System Dependencies

- **Validation Results Directory** (`validation_results/`) - Persistent storage for validation run outputs, storing JSON files with metadata, statistics, and per-relay validation details
- **Streamlit Configuration** (`.streamlit/config.toml`) - Auto-generated server configuration for headless operation on port 5000

### Environment Variables (Batch Mode)

- `BATCH_LIMIT` - Maximum number of relays to validate (default: 100)
- `PARALLEL` - Enable/disable parallel processing (default: true)
- `MAX_WORKERS` - Thread pool size for concurrent validation (default: 10)