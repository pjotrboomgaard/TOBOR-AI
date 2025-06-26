#!/bin/bash

echo "Starting Git repository cleanup..."

# Remove the problematic .git directory
rm -rf .git

# Initialize new Git repository
git init

# Add remote
git remote add origin https://github.com/pjotrboomgaard/TOBOR-AI.git

# Add all files (gitignore will protect sensitive files)
git add .

# Commit
git commit -m "Initial commit: TOBOR-AI with enhanced multi-character system"

# Push to GitHub
git push --force-with-lease origin main

echo "Git repository cleanup complete!" 