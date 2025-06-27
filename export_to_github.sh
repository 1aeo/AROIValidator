#!/bin/bash

# Export script for pushing AROI Validator to GitHub
# Repository: https://github.com/1aeo/AROIValidator

echo "AROI Validator - GitHub Export Script"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "aroi_cli.py" ]; then
    echo "Error: aroi_cli.py not found. Please run from project root."
    exit 1
fi

# Create export directory
mkdir -p aroi_export
cd aroi_export

# Copy core application files
echo "Copying core application files..."
cp ../aroi_cli.py .
cp ../aroi_validator.py .
cp ../app_interactive.py .
cp ../app_viewer.py .
cp ../batch_validator.py .

# Copy configuration files
echo "Copying configuration files..."
mkdir -p .streamlit
cp ../.streamlit/config.toml .streamlit/
cp ../.gitignore .
cp ../pyproject.toml .
cp ../uv.lock .

# Copy documentation
echo "Copying documentation..."
cp ../README.md .
cp ../replit.md .
cp ../GITHUB_PUSH_GUIDE.md .

# Initialize git repository
echo "Initializing git repository..."
git init

# Configure git (you may want to change these)
git config user.email "your-email@example.com"
git config user.name "Your Name"

# Add remote
echo "Adding GitHub remote..."
git remote add origin https://github.com/1aeo/AROIValidator.git

# Add all files
echo "Adding files to git..."
git add .

# Create commit
echo "Creating commit..."
git commit -m "Initial commit: AROI Validator with three operational modes

Features:
- Interactive mode with real-time validation controls and progress tracking
- Batch mode for automated processing suitable for cron jobs
- Viewer mode for results display without validation controls
- DNS-RSA and URI-RSA proof validation with DNSSEC verification
- Comprehensive error reporting and export capabilities
- Modular architecture supporting multiple operational scenarios

Core components:
- aroi_cli.py: Main CLI dispatcher for mode selection
- aroi_validator.py: Core validation logic with DNS and URI checking
- app_interactive.py: Full-featured interactive web interface
- app_viewer.py: Results viewer for pre-computed data
- batch_validator.py: Automated batch processing script"

# Instructions for push
echo ""
echo "Git repository prepared in ./aroi_export/"
echo ""
echo "To push to GitHub:"
echo "1. cd aroi_export"
echo "2. git config user.email \"your-email@example.com\""
echo "3. git config user.name \"Your Name\""
echo "4. git push -u origin main"
echo ""
echo "If authentication fails, use a Personal Access Token:"
echo "GitHub Settings > Developer settings > Personal access tokens"
echo ""
echo "Repository will be available at: https://github.com/1aeo/AROIValidator"