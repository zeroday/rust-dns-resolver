#!/bin/bash

# Change to the script directory
cd /home/oliverday/rust-dns-resolver

# Run the analysis script and log any errors
python3 analyze_patterns.py --last12 >> /home/oliverday/rust-dns-resolver/analysis.log 2>&1
python3 analyze_top_ips.py
python3 analyze_top_ips.py --last12
python3 analyze_asn_migrations.py
python3 analyze_asn_migrations.py --last12 