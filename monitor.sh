#!/bin/bash

echo "Starting monitor for mass.gov.com hostnames..."
echo "Press Ctrl+C to stop monitoring"

while true; do
    echo -e "\n$(date '+%Y-%m-%d %H:%M:%S') - Checking database..."
    
    # Query for mass.gov.com hostnames with IP addresses
    echo -e "\nDNS Results:"
    sqlite3 dns_results.db <<EOF
.headers on
.mode column
SELECT 
    hostname, 
    ip_address, 
    asn, 
    as_name, 
    timestamp 
FROM dns_results 
WHERE hostname LIKE 'mass.gov.com%' 
    AND ip_address IS NOT NULL 
ORDER BY timestamp DESC;
EOF
    
    # Query for HTTP status results
    echo -e "\nHTTP Status Results:"
    sqlite3 dns_results.db <<EOF
.headers on
.mode column
SELECT 
    hostname,
    path,
    status_code,
    response,
    timestamp
FROM http_results
WHERE hostname LIKE 'mass.gov.com%'
ORDER BY timestamp DESC;
EOF
    
    # Show count of all mass.gov.com hostnames processed
    echo -e "\nTotal mass.gov.com hostnames processed:"
    sqlite3 dns_results.db "SELECT COUNT(*) FROM dns_results WHERE hostname LIKE 'mass.gov.com%';"
    
    # Show count of HTTP checks performed
    echo -e "\nTotal HTTP checks performed:"
    sqlite3 dns_results.db "SELECT COUNT(*) FROM http_results WHERE hostname LIKE 'mass.gov.com%';"
    
    # Wait 5 minutes before next check
    echo -e "\nNext check in 5 minutes..."
    sleep 300
done 