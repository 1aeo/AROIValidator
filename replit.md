# AROI Validator

## Overview

AROI Validator is a web-based and CLI tool for validating Tor relay operators' contact information using the AROI (Accuracy, Relevance, Objectivity, and Informativeness) framework. The application validates Tor relay metadata by checking DNS records and URI-based proofs to verify relay operator authenticity. It supports both interactive web-based validation through Streamlit and automated batch processing with parallel execution capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Structure

The application uses a modular architecture with three primary interfaces:

1. **Web Interface (app.py)**: Streamlit-based interactive UI for real-time validation with visual feedback and progress tracking
2. **CLI Interface (aroi_cli.py)**: Command-line dispatcher that routes between interactive, batch, and viewer modes
3. **Core Validator (aroi_validator.py)**: Contains the validation logic with parallel processing support using Python's concurrent.futures

**Rationale**: Separation of interfaces from core logic allows the same validation engine to be used across different interaction modes while maintaining code reusability.

### Parallel Processing Architecture

The validator implements a thread-pool based parallel processing system through the `ParallelAROIValidator` class:

- Uses `concurrent.futures.ThreadPoolExecutor` for concurrent relay validation
- Configurable worker thread count (default: 10)
- Progress tracking with callback mechanisms for UI updates

**Rationale**: Validating Tor relays involves network I/O (DNS queries, HTTP requests), making it ideal for parallel processing. Thread-based concurrency is chosen over async/await because the underlying libraries (requests, dnspython) are synchronous.

**Trade-offs**: Thread pools have GIL limitations for CPU-bound tasks, but this application is I/O-bound, making threads appropriate. The alternative would be multiprocessing, which has higher overhead for this use case.

### Validation Logic

The core validation process checks two proof types:

1. **DNS RSA Proofs**: Validates cryptographic signatures in DNS TXT records
2. **URI RSA Proofs**: Validates signatures served via HTTP/HTTPS endpoints

**Architectural Decision**: The validator uses a custom `LegacyTLSAdapter` that relaxes TLS requirements to support older Tor relay servers:
- Sets minimum TLS version to TLSv1
- Disables certificate verification for legacy compatibility
- Uses reduced security level ciphers

**Rationale**: Tor relay operators may run older server configurations, and strict TLS validation would cause false negatives. Security is acceptable here because the cryptographic validation happens at the application layer through RSA signature verification.

### State Management

The Streamlit application uses session state for tracking:
- Validation progress and results
- Stop/start controls for batch operations
- Configuration settings (parallel mode, worker count, batch limits)

**Rationale**: Streamlit's session state provides a simple way to maintain state across reruns without external storage, suitable for a single-user validation tool.

### Data Persistence

Validation results are stored as JSON files in the `validation_results/` directory:
- Timestamped files for historical tracking
- A `latest.json` symlink for quick access
- Structured format with metadata, statistics, and individual relay results

**Rationale**: JSON provides human-readable storage without database overhead, appropriate for the validation use case where results are primarily for analysis rather than querying.

## External Dependencies

### Core Libraries

1. **Streamlit**: Web UI framework for the interactive interface
   - Provides real-time UI updates and progress tracking
   - Handles user input and result visualization

2. **dnspython**: DNS query and DNSSEC validation library
   - Used for querying TXT records containing proof data
   - Performs DNSSEC validation when available

3. **requests + urllib3**: HTTP client libraries
   - Fetches URI-based proofs from relay operator websites
   - Custom adapter for legacy TLS support

4. **pandas**: Data manipulation and display
   - Formats validation results for tabular display in Streamlit UI

### External Services

1. **Onionoo API** (https://onionoo.torproject.org/details)
   - Official Tor Project service providing relay metadata
   - Source of relay information including fingerprints, nicknames, and contact details
   - No authentication required; public read-only API

**Rationale**: Onionoo is the authoritative source for Tor relay data, making it the natural choice for relay discovery and metadata retrieval.

### Python Standard Library Dependencies

- `concurrent.futures`: Parallel processing implementation
- `ssl`: TLS configuration for legacy server support
- `json`, `pathlib`, `datetime`: Data handling and file operations
- `argparse`, `subprocess`: CLI interface implementation

### Development and Deployment

The project includes a `setup.py` script that:
- Creates Streamlit configuration for Replit deployment
- Installs dependencies via `uv` (Replit's package manager) with pip fallback
- Configures the server to run on port 5000 with headless mode

**Rationale**: Automated setup reduces deployment friction on Replit and ensures consistent configuration across instances.