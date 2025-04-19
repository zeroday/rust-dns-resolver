#!/bin/bash

# Change to the script directory
cd /home/oliverday/rust-dns-resolver

# Run the analysis script and log any errors
python3 analyze_patterns.py --last12 >> /home/oliverday/rust-dns-resolver/analysis.log 2>&1 