#!/usr/bin/env python3
import subprocess
import os
import re
from typing import List, Set

def extract_base_patterns(targets_file: str) -> Set[str]:
    """Extract unique base patterns from targets.txt and convert them to regex patterns."""
    patterns = set()
    
    with open(targets_file, 'r') as f:
        lines = f.readlines()
    
    # Process each line
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and section headers
        if not line or line.startswith('==='):
            continue
            
        # Extract the domain pattern
        if 'sunpass.com-' in line:
            patterns.add('sunpass\.com-[a-z]{4}\.win')
        elif 'txtag.org-' in line:
            # Handle both 3 and 4 character patterns for txtag.org
            if re.search(r'txtag\.org-[a-z]{3}\.win', line):
                patterns.add('txtag\.org-[a-z]{3}\.win')
            elif re.search(r'txtag\.org-[a-z]{4}\.win', line):
                patterns.add('txtag\.org-[a-z]{4}\.win')
    
    return patterns

def generate_resolver_commands(patterns: Set[str]) -> List[str]:
    """Generate DNS resolver commands for each pattern."""
    commands = []
    resolver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                'rust-dns-resolver', 'target', 'release', 'rust-dns-resolver')
    
    for pattern in patterns:
        cmd = f"{resolver_path} --pattern '{pattern}'"
        commands.append(cmd)
    
    return commands

def main():
    # Extract patterns from targets.txt
    patterns = extract_base_patterns('targets.txt')
    
    # Generate commands
    commands = generate_resolver_commands(patterns)
    
    # Write commands to a shell script
    with open('run_resolvers.sh', 'w') as f:
        f.write('#!/bin/bash\n\n')
        f.write('# DNS resolver commands for detected patterns\n\n')
        
        for cmd in commands:
            # Add error handling and logging
            f.write(f'echo "Running: {cmd}"\n')
            f.write(f'{cmd} || echo "Failed: {cmd}"\n')
            f.write('echo "----------------------------------------"\n\n')
    
    # Make the shell script executable
    os.chmod('run_resolvers.sh', 0o755)
    
    print("Generated run_resolvers.sh with the following patterns:")
    for pattern in patterns:
        print(f"- {pattern}")
    print("\nYou can now run './run_resolvers.sh' to execute all resolver commands.")

if __name__ == "__main__":
    main() 