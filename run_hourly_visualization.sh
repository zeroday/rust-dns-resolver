#!/bin/bash

# Change to the script directory
cd /home/oliverday/rust-dns-resolver

# Run the visualization script
python3 visualize_last_hour.py >> /home/oliverday/rust-dns-resolver/visualization.log 2>&1 