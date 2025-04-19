#!/bin/bash

# Change to the repository directory
cd /home/oliverday/rust-dns-resolver

# Log start time
echo "Starting auto-commit at $(date)" >> git_auto_commit.log

# Check for new PNG files in visualizations directory
if ls visualizations/*.png 1> /dev/null 2>&1; then
    # Add all new PNG files
    git add visualizations/*.png
    
    # Create commit with timestamp
    timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    git commit -m "Auto-commit: New visualizations at $timestamp" >> git_auto_commit.log 2>&1
    
    # Push to the status-check branch
    git push origin status-check >> git_auto_commit.log 2>&1
    
    echo "Completed auto-commit at $(date)" >> git_auto_commit.log
else
    echo "No new PNG files found at $(date)" >> git_auto_commit.log
fi 