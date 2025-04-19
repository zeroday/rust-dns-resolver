#!/bin/bash

# Log the current time and environment
echo "=== Cron Test Run at $(date) ===" >> cron_test.log
echo "Current directory: $(pwd)" >> cron_test.log
echo "Python version: $(python3 --version)" >> cron_test.log
echo "Environment variables:" >> cron_test.log
env >> cron_test.log
echo "----------------------------------------" >> cron_test.log 