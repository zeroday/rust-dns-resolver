#!/bin/bash

# Set up logging
exec 1> >(logger -s -t $(basename $0)) 2>&1

# Load environment variables
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export PYTHONPATH="/home/oliverday/.local/lib/python3.9/site-packages:$PYTHONPATH"

# Change to the script directory
cd /home/oliverday/rust-dns-resolver

# Log start of execution
echo "Starting analysis run at $(date)"

# Run the analysis scripts and log any errors
python3 analyze_patterns.py --last12 2>&1
python3 analyze_top_ips.py 2>&1
python3 analyze_top_ips.py --last12 2>&1
python3 analyze_asn_migrations.py 2>&1
python3 analyze_asn_migrations.py --last12 2>&1

# Log completion
echo "Analysis completed at $(date)" 