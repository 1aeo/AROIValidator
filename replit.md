# AROI Validator Project Documentation

## Overview
A comprehensive Tor relay AROI (Autonomous Relay Operator Identity) validation system with three operational modes: interactive validation, automated batch processing, and results viewing. Built with Python and Streamlit for web interfaces.

## Project Architecture

### Core Components
- **aroi_cli.py** - Main CLI dispatcher supporting three operational modes
- **aroi_validator.py** - Core validation logic with DNS and URI checking capabilities
- **app_interactive.py** - Full-featured interactive Streamlit web interface
- **app_viewer.py** - Results viewer web interface for pre-computed data
- **batch_validator.py** - Automated batch processing suitable for cron jobs

### Operational Modes
1. **Interactive Mode** (default) - Complete web interface with real-time validation controls
2. **Batch Mode** - Automated validation with JSON output for monitoring systems
3. **Viewer Mode** - Web interface displaying validation results without validation controls

### Key Features
- DNS-RSA and URI-RSA proof validation with DNSSEC verification
- Real-time progress tracking with start/stop controls and partial result preservation
- Comprehensive error reporting with detailed validation step tracking
- Export capabilities and result filtering
- Automated batch processing suitable for cron job integration

## Recent Changes
- **2025-06-27**: Restructured application into modular architecture with three distinct operational modes
- **2025-06-27**: Implemented CLI dispatcher (aroi_cli.py) for mode selection via command line arguments
- **2025-06-27**: Created dedicated batch processing script for automated monitoring integration
- **2025-06-27**: Added results viewer interface for displaying pre-computed validation data
- **2025-06-27**: Separated interactive validation logic into app_interactive.py
- **2025-06-27**: Updated workflow configuration to use new CLI system
- **2025-06-27**: Created comprehensive README.md with usage examples and integration guides
- **2025-06-27**: Migration to Replit environment completed with automated setup script
- **2025-06-27**: Added setup.py for one-command environment configuration and dependency installation
- **2025-06-27**: Created Streamlit configuration for proper deployment on port 5000
- **2025-06-27**: Added run.sh helper script for quick application startup

## User Preferences
- Prefers command line flexibility for different operational scenarios
- Values automated processing capabilities for monitoring integration
- Wants separate viewing interface for stakeholders without validation access
- Appreciates comprehensive documentation and usage examples

## Technical Decisions
- **Modular Architecture**: Separated functionality into distinct modes for different use cases
- **CLI Interface**: Provides unified entry point with mode selection via command line arguments
- **File-based Results**: Batch mode saves timestamped JSON files for historical tracking
- **Session State Preservation**: Interactive mode maintains partial results during stop operations
- **Port Configuration**: All web interfaces use port 5000 for external accessibility

## Integration Examples
- Cron job automation for scheduled validation runs
- Monitoring system integration with JSON output parsing
- Dashboard integration using viewer mode for stakeholder access
- Historical trend analysis using timestamped batch results

## Future Considerations
- API endpoint implementation for programmatic access
- Database integration for result persistence and advanced analytics
- Microservices architecture for scalable deployment
- Container deployment options for production environments