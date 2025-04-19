#!/bin/bash
cd /home/oliverday/rust-dns-resolver
python3 analyze_top_ips.py
python3 analyze_top_ips.py --last12 