#!/usr/bin/env python3

import sqlite3
import os
from datetime import datetime, timedelta
import pandas as pd
import sys
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

def get_status_description(code):
    """Return a description for HTTP status codes."""
    descriptions = {
        0: "Connection Failed",
        200: "OK (Success)",
        301: "Moved Permanently",
        302: "Found (Temporary Redirect)",
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        451: "Unavailable For Legal Reasons",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        521: "Web Server Is Down",
        530: "Origin DNS Error"
    }
    return descriptions.get(code, "Unknown Status Code")

def create_visualizations(df, output_dir, timestamp):
    """Create and save visualizations of the status code data."""
    # Set the style
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # 1. Pie chart of status code distribution
    plt.figure(figsize=(10, 8))
    status_counts = df['status_code'].value_counts()
    plt.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%')
    plt.title('Distribution of HTTP Status Codes')
    plt.savefig(os.path.join(output_dir, f'status_distribution_pie_{timestamp}.png'))
    plt.close()

    # 2. Time series plot
    plt.figure(figsize=(15, 8))
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    status_over_time = df.groupby(['timestamp', 'status_code']).size().unstack(fill_value=0)
    status_over_time.plot(kind='line', marker='.')
    plt.title('Status Codes Over Time')
    plt.xlabel('Time')
    plt.ylabel('Count')
    plt.legend(title='Status Code', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'status_timeseries_{timestamp}.png'))
    plt.close()

    # 3. Heatmap of status codes by hour
    plt.figure(figsize=(12, 8))
    df['hour'] = df['timestamp'].dt.hour
    hourly_status = pd.crosstab(df['hour'], df['status_code'])
    sns.heatmap(hourly_status, cmap='YlOrRd', annot=True, fmt='d')
    plt.title('Status Codes by Hour of Day')
    plt.xlabel('Status Code')
    plt.ylabel('Hour of Day')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'status_heatmap_{timestamp}.png'))
    plt.close()

    # 4. Bar plot of unique hosts per status code
    plt.figure(figsize=(12, 6))
    hosts_per_status = df.groupby('status_code')['hostname'].nunique()
    hosts_per_status.plot(kind='bar')
    plt.title('Unique Hosts per Status Code')
    plt.xlabel('Status Code')
    plt.ylabel('Number of Unique Hosts')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'hosts_per_status_{timestamp}.png'))
    plt.close()

def count_status():
    """Count and analyze HTTP status codes from the database."""
    # Create output directory if it doesn't exist
    output_dir = Path('status_reports')
    output_dir.mkdir(exist_ok=True)
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'status_report_{timestamp}.txt'
    
    conn = sqlite3.connect('dns_results.db')
    
    # Get all status data
    query = """
    SELECT hostname, status_code, timestamp, response
    FROM status
    ORDER BY timestamp DESC
    """
    
    df = pd.read_sql_query(query, conn)
    
    # Prepare the report
    report = []
    report.append("=== Status Code Analysis ===")
    report.append(f"Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Total records
    total_records = len(df)
    report.append(f"Total records in status table: {total_records:,}\n")
    
    # Time range
    first_check = df['timestamp'].min()
    last_check = df['timestamp'].max()
    duration_hours = (pd.to_datetime(last_check) - pd.to_datetime(first_check)).total_seconds() / 3600
    
    report.append("Time Range:")
    report.append(f"First check: {first_check}")
    report.append(f"Last check:  {last_check}")
    report.append(f"Duration:    {duration_hours:.1f} hours\n")
    
    # Status code breakdown
    status_counts = df['status_code'].value_counts()
    report.append("Status Code Breakdown:")
    for status, count in status_counts.items():
        percentage = (count / total_records) * 100
        report.append(f"Status {status}: {count:,} ({percentage:.1f}%)")
    
    # Recent error responses
    error_responses = df[df['status_code'] >= 400].head(10)
    if not error_responses.empty:
        report.append("\nMost Recent Error Responses:")
        for _, row in error_responses.iterrows():
            report.append(f"Host: {row['hostname']}")
            report.append(f"Status: {row['status_code']}")
            report.append(f"Time: {row['timestamp']}")
            report.append(f"Response: {row['response']}")
            report.append("---")
    
    # Write report to file and print to console
    report_text = '\n'.join(report)
    with open(output_file, 'w') as f:
        f.write(report_text)
    
    print(report_text)
    
    # Create visualizations
    try:
        create_visualizations(df, output_dir, timestamp)
        print(f"\nVisualizations saved in {output_dir}/")
    except Exception as e:
        print(f"\nError while creating visualizations: {str(e)}")
    
    conn.close()

if __name__ == '__main__':
    count_status() 