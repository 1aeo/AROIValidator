# Tor Relay AROI Validator

A comprehensive validation system for Tor relay AROI (Autonomous Relay Operator Identity) proofs with multiple operational modes.

## Features

- **DNS-RSA and URI-RSA validation** with DNSSEC verification
- **Three operational modes** for different use cases
- **Real-time validation tracking** with start/stop controls
- **Batch processing** suitable for automated monitoring
- **Results viewing** with filtering and export capabilities
- **Comprehensive error reporting** and detailed validation steps

## Quick Start

```bash
# Interactive mode (default) - Full web interface with validation controls
python aroi_cli.py

# Batch mode - Automated validation with JSON output (suitable for cron)
python aroi_cli.py batch

# Viewer mode - Web interface showing results only
python aroi_cli.py viewer
```

## Operational Modes

### 1. Interactive Mode (Default)
Full-featured web interface with real-time validation controls.

```bash
python aroi_cli.py interactive
```

**Features:**
- Start/stop validation with preserved partial results
- Real-time progress tracking and live result updates
- Detailed step-by-step validation display
- Interactive result filtering and analysis
- Export capabilities for validation results

**Use Cases:**
- Manual AROI auditing and troubleshooting
- Research analysis and educational purposes
- Interactive exploration of relay configurations

### 2. Batch Mode
Automated validation suitable for scheduled monitoring.

```bash
python aroi_cli.py batch
```

**Features:**
- Fetches all relay data from Onionoo API
- Validates all relays automatically
- Saves timestamped results to JSON files
- Provides comprehensive statistics and summaries
- Suitable for cron job automation

**Output Files:**
- `validation_results/aroi_validation_YYYYMMDD_HHMMSS.json` - Timestamped results
- `validation_results/latest.json` - Always contains most recent results

**Use Cases:**
- Scheduled network monitoring (cron jobs)
- Historical tracking of AROI adoption
- Automated compliance reporting
- Integration with monitoring systems

**Example Cron Job:**
```bash
# Run validation every 6 hours
0 */6 * * * /path/to/python /path/to/aroi_cli.py batch
```

### 3. Viewer Mode
Web interface for viewing pre-computed validation results.

```bash
python aroi_cli.py viewer
```

**Features:**
- Display results from batch validation runs
- Filter results by status, proof type, and domain
- Historical data analysis with multiple result files
- Export filtered results
- Auto-refresh for latest results

**Use Cases:**
- Dashboard for displaying validation status
- Analysis of historical validation trends
- Sharing results without validation capabilities
- Read-only access for stakeholders

## Installation

### Prerequisites
- Python 3.8+
- Required packages (install via pip):

```bash
pip install streamlit pandas requests dnspython
```

### Setup
1. Clone or download the project files
2. Install dependencies
3. Run the desired mode

## API Validation Details

### Supported Proof Types

**DNS-RSA Proofs:**
- Validates TXT records in DNS containing cryptographic proofs
- Uses DNSSEC validation for enhanced security
- Checks for relay fingerprint presence in proof data

**URI-RSA Proofs:**
- Fetches proof documents from `/.well-known/tor-relay/rsa-fingerprint.txt`
- Validates HTTPS certificates and document content
- Verifies relay fingerprint in proof document

### AROI Token Parsing

The validator parses these tokens from relay contact information:
- `aroi-url:` - Domain or URL for proof verification
- `proof:` - Proof type (dns-rsa or uri-rsa)
- `ciissversion:` - CIISS version (informational)

## Output Format

### Batch Mode JSON Structure
```json
{
  "metadata": {
    "timestamp": "2025-06-27T04:21:30",
    "total_relays": 1500,
    "valid_relays": 45,
    "invalid_relays": 1455,
    "success_rate": 3.0
  },
  "statistics": {
    "proof_types": {
      "dns_rsa": {
        "total": 30,
        "valid": 25,
        "success_rate": 83.3
      },
      "uri_rsa": {
        "total": 20,
        "valid": 20,
        "success_rate": 100.0
      }
    }
  },
  "results": [...]
}
```

## Architecture

### Core Components
- `aroi_cli.py` - Command line interface and mode dispatcher
- `aroi_validator.py` - Core validation logic with DNS and URI checking
- `app_interactive.py` - Interactive Streamlit web interface
- `app_viewer.py` - Results viewer web interface
- `batch_validator.py` - Automated batch processing

### File Structure
```
├── aroi_cli.py              # Main CLI entry point
├── aroi_validator.py        # Core validation logic
├── app_interactive.py       # Interactive web interface
├── app_viewer.py           # Results viewer interface
├── batch_validator.py      # Batch processing script
├── validation_results/     # Output directory for batch results
├── .streamlit/             # Streamlit configuration
└── README.md              # This file
```

## Integration Examples

### Monitoring System Integration
```bash
#!/bin/bash
# monitoring_script.sh

# Run validation
python aroi_cli.py batch

# Parse results for alerts
if [ -f "validation_results/latest.json" ]; then
    SUCCESS_RATE=$(jq '.metadata.success_rate' validation_results/latest.json)
    if (( $(echo "$SUCCESS_RATE < 80" | bc -l) )); then
        echo "ALERT: AROI validation success rate below 80%: $SUCCESS_RATE%"
    fi
fi
```

### Data Pipeline Integration
```python
import json
from pathlib import Path

# Load latest results
with open('validation_results/latest.json', 'r') as f:
    data = json.load(f)

# Extract metrics for dashboard
metrics = {
    'timestamp': data['metadata']['timestamp'],
    'total_relays': data['metadata']['total_relays'],
    'success_rate': data['metadata']['success_rate'],
    'dns_rsa_rate': data['statistics']['proof_types']['dns_rsa']['success_rate'],
    'uri_rsa_rate': data['statistics']['proof_types']['uri_rsa']['success_rate']
}

# Send to monitoring system
send_to_dashboard(metrics)
```

## Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Check what's using port 5000
lsof -i :5000

# Use different port for testing
streamlit run app_interactive.py --server.port 8501
```

**DNS Resolution Failures:**
- Ensure DNS servers are accessible
- Check DNSSEC validation settings
- Verify network connectivity

**API Rate Limiting:**
- Batch mode includes delays between requests
- Monitor Onionoo API usage guidelines
- Consider running validation less frequently

### Debug Mode
Add debug output to any mode:
```bash
# Enable verbose logging
export STREAMLIT_LOGGER_LEVEL=debug
python aroi_cli.py batch
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with appropriate tests
4. Submit a pull request

## License

This project is open source. Please respect the Tor Project's guidelines when using relay data.