#!/bin/bash
# Git setup and commit script for AROI Validator migration

echo "AROI Validator - Git Setup Script"
echo "================================="
echo

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "Error: Not in a git repository"
    exit 1
fi

echo "Setting up git configuration..."
git config user.name "1aeo"
git config user.email "github@1aeo.com"

echo "Git configuration set:"
echo "  Name: $(git config user.name)"
echo "  Email: $(git config user.email)"
echo

echo "Current git status:"
git status
echo

echo "Adding files to staging..."
git add setup.py run.sh README.md replit.md .streamlit/config.toml
echo

echo "Files staged:"
git status --cached
echo

echo "Committing changes..."
git commit -m "Migrate AROI Validator to Replit environment

- Add automated setup script (setup.py) for dependency installation
- Create Streamlit configuration for proper deployment
- Add comprehensive README with setup and usage instructions
- Create run.sh helper script for quick startup
- Update project documentation in replit.md
- Ensure security best practices and client/server separation"

echo
echo "Checking commit status..."
git log --oneline -1
echo

echo "Pushing to origin..."
git push origin main

echo
echo "✅ Git setup and push completed!"
echo "Repository updated with migration changes."