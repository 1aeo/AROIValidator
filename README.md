# AROI Validator - Replit Setup Guide

A comprehensive Tor relay AROI (Autonomous Relay Operator Identity) validation system with three operational modes: interactive validation, automated batch processing, and results viewing.

## Quick Setup

### Automatic Setup (Recommended)
Run the setup script to automatically configure everything:

```bash
python setup.py
```

This will:
- Install all required dependencies (streamlit, dnspython, pandas, requests, urllib3)
- Create Streamlit configuration for proper deployment
- Verify project structure
- Create helper scripts

### Manual Setup
If you prefer manual setup:

1. **Install Dependencies**
   ```bash
   # Using Replit's package manager (recommended)
   uv add streamlit dnspython pandas requests urllib3
   
   # Or using pip
   pip install streamlit dnspython pandas requests urllib3
   ```

2. **Create Streamlit Configuration**
   Create `.streamlit/config.toml`:
   ```toml
   [server]
   headless = true
   address = "0.0.0.0"
   port = 5000
   ```

## Running the Application

### Three Operational Modes

1. **Interactive Mode** (Default)
   ```bash
   python aroi_cli.py interactive
   ```
   Full web interface with real-time validation controls

2. **Batch Mode**
   ```bash
   python aroi_cli.py batch
   ```
   Automated validation with JSON output for monitoring systems

3. **Viewer Mode**
   ```bash
   python aroi_cli.py viewer
   ```
   Web interface displaying validation results without validation controls

### Quick Start Script
```bash
./run.sh
```
Runs the interactive mode directly.

## Project Structure

```
aroi-validator/
├── aroi_cli.py           # Main CLI dispatcher
├── aroi_validator.py     # Core validation logic
├── app_interactive.py    # Interactive Streamlit interface
├── app_viewer.py         # Results viewer interface
├── batch_validator.py    # Batch processing script
├── setup.py             # Automated setup script
├── run.sh               # Quick run script
├── .streamlit/
│   └── config.toml      # Streamlit configuration
└── README.md            # This file
```

## Features

- **DNS-RSA and URI-RSA** proof validation with DNSSEC verification
- **Real-time progress tracking** with start/stop controls
- **Comprehensive error reporting** with detailed validation steps
- **Export capabilities** and result filtering
- **Automated batch processing** suitable for cron job integration

## Integration Examples

### Cron Job Automation
```bash
# Add to crontab for daily validation
0 2 * * * cd /path/to/aroi-validator && python aroi_cli.py batch
```

### Monitoring System Integration
```bash
# Run batch validation and parse JSON output
python aroi_cli.py batch
cat validation_results_*.json | jq '.summary.total_validated'
```

### Dashboard Integration
```bash
# Run viewer mode for stakeholder access
python aroi_cli.py viewer
```

## Troubleshooting

### Common Issues

1. **Module not found errors**
   ```bash
   python setup.py  # Run setup script
   ```

2. **Port conflicts**
   The application uses port 5000. Ensure it's available.

3. **DNS resolution issues**
   Check network connectivity and DNS settings.

### Logs and Debugging
- Interactive mode: Check browser console and Streamlit logs
- Batch mode: Results saved to timestamped JSON files
- All modes: Detailed error messages in terminal output

## Security Considerations

- Uses DNSSEC validation for enhanced security
- Separates client/server concerns properly
- No sensitive data stored in configuration files
- Follows secure coding practices for network requests

## Development

### Adding New Features
1. Core validation logic: `aroi_validator.py`
2. Interactive UI: `app_interactive.py`
3. Batch processing: `batch_validator.py`
4. CLI interface: `aroi_cli.py`

### Testing
Run the setup script to verify environment:
```bash
python setup.py
```

## Support

For issues with:
- **Replit deployment**: Check `.streamlit/config.toml` configuration
- **DNS validation**: Verify network connectivity
- **Performance**: Consider batch mode for large datasets