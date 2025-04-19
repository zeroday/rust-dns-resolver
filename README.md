# DNS Resolver and Analysis Tools

This repository contains tools for DNS resolution and analysis of potentially malicious domains, with a focus on toll-related phishing attempts.

## Analysis Scripts

### analyze_patterns.py

This script analyzes patterns in DNS hostnames from the `dns_results.db` database and creates visualizations to help identify trends and potential threats.

#### Features

- **Pattern Classification**: Groups hostnames into patterns based on known domains:
  - Known toll-related domains (sunpass.com, txtag.org, thetollroads.com, ezdrivema.com)
  - Paytoll-related domains
  - Generic pattern extraction for unknown domains

- **Time Filtering Options**:
  ```bash
  python3 analyze_patterns.py --today    # Show only today's data
  python3 analyze_patterns.py --last12   # Show data from last 12 hours
  python3 analyze_patterns.py            # Show all time data
  ```

#### Visualizations

1. **Time Series Plot**
   - Shows top 5 patterns over time
   - Tracks pattern frequency changes
   - Helps identify emerging threats

2. **Stacked Area Plot**
   - Displays relative distribution of top 10 patterns
   - Shows how pattern proportions change
   - Useful for identifying pattern shifts

3. **Heatmap**
   - Hourly activity visualization
   - Shows pattern intensity over time
   - Helps identify peak activity periods

#### Output
- PNG files with timestamps for each visualization
- Statistics including:
  - Total unique patterns
  - Date range analysis
  - Top 5 patterns with counts

### Automated Analysis

The repository includes `run_analysis.sh` which runs various analysis scripts every 30 minutes via cron:

```bash
*/30 * * * * /path/to/run_analysis.sh
```

This includes:
- Pattern analysis (last 12 hours)
- Top IP analysis (24 and 12 hours)
- ASN migration analysis (24 and 12 hours)

## Database Schema

The analysis uses `dns_results.db` (SQLite) with tables:
- `dns_results`: Stores DNS resolution results
- `status`: Tracks HTTP status checks

## Dependencies

Required Python packages:
- pandas
- matplotlib
- numpy
- seaborn

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip3 install pandas matplotlib numpy seaborn
   ```
3. Set up the cron job:
   ```bash
   crontab -e
   # Add: */30 * * * * /path/to/run_analysis.sh
   ```

## Monitoring

You can monitor the analysis:
- Check system logs: `sudo journalctl -u cron`
- View script output: `grep run_analysis.sh /var/log/syslog`
- Monitor visualization files in the repository directory

## Error Handling

The scripts include comprehensive error handling:
- Database connection management
- Memory cleanup after plotting
- Logging of errors and execution status
- Graceful handling of missing or invalid data 