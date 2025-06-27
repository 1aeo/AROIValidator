# GitHub Repository Setup Guide

Follow these steps to push the AROI Validator project to your GitHub account at github.com/1aeo

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `tor-aroi-validator`
3. Description: `Tor Relay AROI (Autonomous Relay Operator Identity) Validator with multiple operational modes`
4. Set to Public (recommended for open source)
5. Do NOT initialize with README, .gitignore, or license (we have these files)
6. Click "Create repository"

## Step 2: Download Project Files

Download all these files from your Replit project:

### Core Application Files
- `aroi_cli.py` - Main CLI dispatcher
- `aroi_validator.py` - Core validation logic
- `app_interactive.py` - Interactive web interface
- `app_viewer.py` - Results viewer interface
- `batch_validator.py` - Batch processing script

### Configuration Files
- `.streamlit/config.toml` - Streamlit configuration
- `.gitignore` - Git ignore rules
- `pyproject.toml` - Python dependencies
- `uv.lock` - Dependency lock file

### Documentation
- `README.md` - Comprehensive project documentation
- `SETUP_GITHUB.md` - This setup guide
- `replit.md` - Project documentation and preferences

### Legacy Files (Optional)
- `app.py` - Original application (can be excluded)
- `app_copy.py` - Copy of original app (can be excluded)
- `aroi_validator_copy.py` - Copy of validator (can be excluded)
- `run_copy.py` - Copy runner script (can be excluded)

## Step 3: Local Git Setup

Open terminal in your project directory and run:

```bash
# Initialize git repository
git init

# Add remote origin (replace with your actual repository URL)
git remote add origin https://github.com/1aeo/tor-aroi-validator.git

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: AROI Validator with three operational modes

- Interactive mode: Full web interface with validation controls
- Batch mode: Automated validation suitable for cron jobs  
- Viewer mode: Results display interface
- Comprehensive validation logic for DNS-RSA and URI-RSA proofs
- Real-time progress tracking and detailed error reporting"

# Push to GitHub
git push -u origin main
```

## Step 4: Verify Repository

1. Go to https://github.com/1aeo/tor-aroi-validator
2. Verify all files are present
3. Check that README.md displays properly
4. Test clone functionality: `git clone https://github.com/1aeo/tor-aroi-validator.git`

## Step 5: Repository Settings (Optional)

### Topics
Add these topics to help with discoverability:
- `tor`
- `aroi`
- `validation`
- `cryptography`
- `dns`
- `streamlit`
- `python`

### About Section
- Description: "Tor Relay AROI Validator with interactive, batch, and viewer modes"
- Website: Link to your deployment if available
- Topics: Add the topics listed above

### Branch Protection (Recommended)
- Go to Settings > Branches
- Add rule for `main` branch
- Require pull request reviews before merging
- Require status checks to pass

## Alternative: Quick Setup Script

Save this as `setup_git.sh` and run it:

```bash
#!/bin/bash
git init
git remote add origin https://github.com/1aeo/tor-aroi-validator.git
git add .
git commit -m "Initial commit: AROI Validator with three operational modes"
git push -u origin main
echo "Repository setup complete!"
```

## Troubleshooting

### Authentication Issues
If you get authentication errors:

1. **Personal Access Token** (Recommended):
   - Go to GitHub Settings > Developer settings > Personal access tokens
   - Generate new token with `repo` scope
   - Use token as password when prompted

2. **SSH Keys**:
   - Generate SSH key: `ssh-keygen -t ed25519 -C "your_email@example.com"`
   - Add to GitHub: Settings > SSH and GPG keys
   - Use SSH URL: `git@github.com:1aeo/tor-aroi-validator.git`

### Repository Already Exists
If repository exists:
```bash
git remote set-url origin https://github.com/1aeo/tor-aroi-validator.git
git push -u origin main
```

## Next Steps

After successful setup:

1. **Add repository description and topics**
2. **Create releases** for stable versions
3. **Set up GitHub Actions** for automated testing (optional)
4. **Add contributors** if working with a team
5. **Star your own repository** to bookmark it

## File Structure Summary

```
tor-aroi-validator/
├── aroi_cli.py              # Main CLI entry point
├── aroi_validator.py        # Core validation logic
├── app_interactive.py       # Interactive web interface
├── app_viewer.py           # Results viewer interface
├── batch_validator.py      # Batch processing script
├── .streamlit/
│   └── config.toml         # Streamlit configuration
├── .gitignore              # Git ignore rules
├── pyproject.toml          # Python dependencies
├── README.md               # Project documentation
└── replit.md              # Development documentation
```

Your repository will be accessible at: https://github.com/1aeo/tor-aroi-validator