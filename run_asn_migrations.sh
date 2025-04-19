#!/bin/bash
cd /home/oliverday/rust-dns-resolver
python3 analyze_asn_migrations.py >> asn_migrations.log 2>&1 