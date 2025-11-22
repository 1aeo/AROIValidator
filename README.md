# AROI Validator

A validation tool for Tor relay operator proofs using the Accuracy, Relevance, Objectivity, and Informativeness (AROI) framework. Validates relay operator contact information through DNS and URI-based RSA proofs by querying the Tor network's Onionoo API.

## Quick Start

### Web Interface
```bash
# Install dependencies and configure
python setup.py

# Run the application
streamlit run app.py --server.port 5000
```

### Command Line
```bash
# Interactive mode (web UI)
python aroi_cli.py interactive

# Batch processing mode
python aroi_cli.py batch

# Results viewer mode
python aroi_cli.py viewer
```

## Script Parameters

### aroi_cli.py
The main command-line interface accepts a mode parameter:
- `interactive` - Launches the web UI for interactive validation
- `batch` - Runs automated validation with JSON output
- `viewer` - Opens the web-based results viewer

### app.py
Streamlit application with optional parameters:
- `--server.port` - Port number (default: 8501, use 5000 for Replit)
- `--mode` - Operation mode: interactive, batch, or viewer

### Batch Mode Environment Variables
Configure batch validation using environment variables:
- `BATCH_LIMIT` - Maximum number of relays to validate (default: 100, 0 = all)
- `PARALLEL` - Enable parallel processing: true/false (default: true)
- `MAX_WORKERS` - Number of worker threads (default: 10)

Example:
```bash
BATCH_LIMIT=500 MAX_WORKERS=20 python aroi_cli.py batch
```

## Features

- **Web Interface**: Streamlit application for interactive relay validation
- **Command Line Tool**: CLI interface for batch processing
- **Parallel Processing**: Concurrent validation with ThreadPoolExecutor
- **Proof Types**: Supports both dns-rsa and uri-rsa validation
- **Result Tracking**: JSON output with timestamps in `validation_results/`

## Architecture

### Core Components

- **app.py** - Streamlit web UI for interactive validation
- **aroi_cli.py** - Command-line dispatcher for batch operations
- **aroi_validator.py** - Core validation engine with parallel processing

### Validation Flow

1. Fetch relay data from Onionoo API
2. Extract AROI proof fields from relay contact info
3. Validate proofs via DNS TXT records or URI-based RSA
4. Calculate success rates by proof type
5. Save results as timestamped JSON

### Data Storage

Results saved to `validation_results/` as JSON:
```json
{
  "metadata": {
    "timestamp": "ISO timestamp",
    "total_relays": int,
    "valid_relays": int,
    "success_rate": float
  },
  "statistics": { ... },
  "results": [ ... ]
}
```

## Dependencies

- **streamlit** - Web UI framework
- **dnspython** - DNS/DNSSEC validation
- **pandas** - Data manipulation
- **requests** - HTTP client
- **urllib3** - SSL/TLS handling

## Security Notes

- Custom TLS adapter for legacy Tor relay compatibility (TLSv1+)
- Reduced security level (SECLEVEL=1) for older cipher support
- Required for communicating with legacy Tor infrastructure