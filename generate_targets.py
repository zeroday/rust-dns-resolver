#!/usr/bin/env python3
import sqlite3
from datetime import datetime, timedelta
import re
from collections import defaultdict
import ipaddress
import os

def extract_domain_pattern(hostnames):
    """Extract common patterns from hostnames."""
    patterns = defaultdict(int)
    
    for hostname in hostnames:
        # Find basic pattern structure
        parts = hostname.split('.')
        if len(parts) >= 2:
            tld = parts[-1]
            domain = parts[-2]
            prefix_pattern = '-'.join(parts[0].split('-')[:-1]) if '-' in parts[0] else parts[0]
            suffix_pattern = parts[0].split('-')[-1] if '-' in parts[0] else ''
            
            if suffix_pattern and len(suffix_pattern) == 4:  # If it matches the 4-char pattern
                pattern = f"{prefix_pattern}-XXXX.{domain}.{tld}"
                patterns[pattern] += 1
            else:
                patterns[hostname] += 1
    
    return patterns

def analyze_ip_ranges(ip_addresses):
    """Analyze IP addresses to find common ranges."""
    networks = defaultdict(int)
    
    for ip in ip_addresses:
        try:
            ip_obj = ipaddress.ip_address(ip)
            # Get /16 network
            network = str(ipaddress.ip_network(f"{ip_obj.exploded.rsplit('.', 2)[0]}.0.0/16", strict=False))
            networks[network] += 1
        except ValueError:
            continue
    
    return networks

def main():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, 'rust-dns-resolver', 'dns_results.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query recent results from both dns_results and scammer_hosts tables
    cursor.execute("""
        SELECT DISTINCT hostname, ip_address
        FROM (
            SELECT hostname, ip_address, timestamp
            FROM dns_results
            WHERE timestamp >= datetime('now', '-1 day')
            AND success = 1
            UNION ALL
            SELECT hostname, ip_address, timestamp
            FROM scammer_hosts
            WHERE timestamp >= datetime('now', '-1 day')
        )
        ORDER BY timestamp DESC
    """)
    
    results = cursor.fetchall()
    hostnames = [row[0] for row in results]
    ip_addresses = [row[1] for row in results if row[1]]
    
    # Analyze patterns
    domain_patterns = extract_domain_pattern(hostnames)
    ip_ranges = analyze_ip_ranges(ip_addresses)
    
    # Write results to targets.txt
    with open('targets.txt', 'w') as f:
        f.write("=== Domain Patterns ===\n")
        for pattern, count in sorted(domain_patterns.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{pattern} (matches: {count})\n")
        
        f.write("\n=== IP Ranges (/16) ===\n")
        for network, count in sorted(ip_ranges.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{network} (hosts: {count})\n")
        
        f.write("\n=== Individual Hosts ===\n")
        for hostname in sorted(set(hostnames)):
            f.write(f"{hostname}\n")

if __name__ == "__main__":
    main() 