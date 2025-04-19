#!/bin/bash

# Change to the repository directory
cd /home/oliverday/rust-dns-resolver

# Create logs directory if it doesn't exist
mkdir -p process_logs

# Generate timestamp
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOGFILE="process_logs/process_analysis_${TIMESTAMP}.txt"

# Write analysis to file
{
    echo "DNS Resolver Process Analysis"
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    echo "Timestamp (EST): $(TZ='America/New_York' date '+%Y-%m-%d %H:%M:%S %Z')"
    echo ""
    
    echo "=== Current Running Processes ==="
    ps aux | grep dns_resolver | grep -v grep
    echo ""
    
    echo "=== Process Resource Usage ==="
    top -b -n 1 | grep -i dns_resolver
    echo ""
    
    echo "=== Expected Patterns vs Running ==="
    echo "Expected patterns from go.sh:"
    echo "- sunpass.com-XXXX.win"
    echo "- txtag.org-XXX.win"
    echo "- txtag.org-XXXX.win"
    echo "- mass.gov-XXXX.win"
    echo "- michigan.gov-eXXXXX.win"
    echo "- ncquickpass.com-XXXX.win"
    echo "- ohioturnpike.org-XXXX.win"
    echo "- paturnpike.com-XXX.cc"
    echo ""
    
    echo "Currently running patterns:"
    ps aux | grep dns_resolver | grep -v grep | grep -o "\-\-pattern [^ ]*" || echo "No patterns currently running"
    echo ""
    
    echo "=== Memory Usage Per Process ==="
    ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%mem | grep dns_resolver | grep -v grep
    
} > "$LOGFILE"

# Add to git and commit
git add "$LOGFILE"
git commit -m "Process analysis report: ${TIMESTAMP}"
git push origin main >> auto_commit.log 2>&1 