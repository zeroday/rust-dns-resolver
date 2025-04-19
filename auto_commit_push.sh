#!/bin/bash

# Change to the repository directory
cd /home/oliverday/rust-dns-resolver

# Get current timestamp for the commit message
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Add any new or modified files
git add .

# Check if there are any changes to commit
if git diff --staged --quiet; then
    echo "[${TIMESTAMP}] No changes to commit." >> auto_commit.log
    exit 0
fi

# Commit changes with timestamp
git commit -m "Auto-commit: Updates from ${TIMESTAMP}"

# Push changes to GitHub
git push origin main >> auto_commit.log 2>&1

# Log the result
if [ $? -eq 0 ]; then
    echo "[${TIMESTAMP}] Successfully pushed changes to GitHub." >> auto_commit.log
else
    echo "[${TIMESTAMP}] Failed to push changes to GitHub." >> auto_commit.log
fi 