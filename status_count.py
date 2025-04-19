#!/usr/bin/env python3

import sqlite3
import os
from datetime import datetime, timedelta
import pandas as pd
import sys
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

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

def create_visualizations(status_data, time_data, output_dir, timestamp):
    """Create visualizations of the status code data."""
    # Set style
    plt.style.use('seaborn')
    
    # 1. Pie chart of status code distribution
    plt.figure(figsize=(12, 8))
    status_counts = status_data.set_index('status_code')['count']
    colors = plt.cm.Set3(np.linspace(0, 1, len(status_counts)))
    
    plt.pie(status_counts, labels=[f"{code}\n({get_status_description(code)})" for code in status_counts.index],
            autopct='%1.1f%%', colors=colors, startangle=90)
    plt.title('Distribution of HTTP Status Codes')
    plt.savefig(os.path.join(output_dir, f'status_distribution_{timestamp}.png'), bbox_inches='tight', dpi=300)
    plt.close()

    # 2. Time series of status codes
    plt.figure(figsize=(15, 8))
    
    # Convert timestamp to datetime
    time_data['timestamp'] = pd.to_datetime(time_data['timestamp'])
    
    # Group by hour and status_code
    hourly_data = time_data.groupby([pd.Grouper(key='timestamp', freq='H'), 'status_code']).size().unstack(fill_value=0)
    
    # Plot each status code
    for code in hourly_data.columns:
        label = f"{code} ({get_status_description(code)})"
        style = '-' if code == 200 else '--'
        plt.plot(hourly_data.index, hourly_data[code], label=label, linestyle=style)
    
    plt.title('Status Codes Over Time')
    plt.xlabel('Time')
    plt.ylabel('Number of Requests')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'status_timeline_{timestamp}.png'), bbox_inches='tight', dpi=300)
    plt.close()

    # 3. Heatmap of status codes by hour of day
    plt.figure(figsize=(15, 8))
    
    # Add hour of day
    time_data['hour'] = time_data['timestamp'].dt.hour
    hourly_heatmap = pd.crosstab(time_data['hour'], time_data['status_code'])
    
    # Create heatmap
    sns.heatmap(hourly_heatmap, cmap='YlOrRd', annot=True, fmt='d', cbar_kws={'label': 'Number of Requests'})
    plt.title('Status Codes by Hour of Day')
    plt.xlabel('Status Code')
    plt.ylabel('Hour of Day')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'status_heatmap_{timestamp}.png'), bbox_inches='tight', dpi=300)
    plt.close()

    # 4. Bar plot of unique hosts by status code
    plt.figure(figsize=(12, 6))
    
    plt.bar(range(len(status_data)), status_data['unique_hosts'], 
           tick_label=[f"{code}\n({get_status_description(code)})" for code in status_data['status_code']])
    plt.title('Unique Hosts by Status Code')
    plt.xlabel('Status Code')
    plt.ylabel('Number of Unique Hosts')
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'status_hosts_{timestamp}.png'), bbox_inches='tight', dpi=300)
    plt.close()

def count_status():
    """Analyze HTTP status codes in the database."""
    # Create output directory if it doesn't exist
    output_dir = "status_reports"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create timestamped filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'status_report_{timestamp}.txt')
    
    # Function to write to both file and console
    def write_output(text, file):
        print(text)
        print(text, file=file)
    
    # Check if database exists
    if not os.path.exists('dns_results.db'):
        print("\nError: dns_results.db not found!")
        print("Please run the DNS resolver first to collect data.")
        return False
        
    try:
        # Connect to the database
        conn = sqlite3.connect('dns_results.db')
        
        with open(output_file, 'w') as f:
            # Get overall statistics
            write_output("\n=== Status Code Analysis ===", f)
            write_output(f"Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", f)
            
            # Get total count
            total_count = pd.read_sql_query("SELECT COUNT(*) as count FROM status", conn).iloc[0]['count']
            write_output(f"\nTotal records in status table: {total_count:,}", f)
            
            # Get time range
            time_range = pd.read_sql_query("""
                SELECT 
                    MIN(timestamp) as earliest,
                    MAX(timestamp) as latest
                FROM status
                WHERE timestamp IS NOT NULL
            """, conn)
            
            if not time_range.empty and not time_range['earliest'].isnull().iloc[0]:
                earliest = pd.to_datetime(time_range['earliest'].iloc[0])
                latest = pd.to_datetime(time_range['latest'].iloc[0])
                duration = latest - earliest
                hours = duration.total_seconds() / 3600
                
                write_output(f"\nTime Range:", f)
                write_output(f"First check: {earliest.strftime('%Y-%m-%d %H:%M:%S')}", f)
                write_output(f"Last check:  {latest.strftime('%Y-%m-%d %H:%M:%S')}", f)
                write_output(f"Duration:    {hours:.1f} hours", f)
            else:
                write_output("\nNo valid timestamp data found", f)
            
            # Get status code breakdown
            status_data = pd.read_sql_query("""
                SELECT 
                    status_code,
                    COUNT(*) as count,
                    COUNT(DISTINCT hostname) as unique_hosts,
                    MIN(timestamp) as first_seen,
                    MAX(timestamp) as last_seen
                FROM status 
                WHERE status_code IS NOT NULL
                GROUP BY status_code 
                ORDER BY count DESC
            """, conn)
            
            # Get time series data for visualizations
            time_data = pd.read_sql_query("""
                SELECT timestamp, status_code
                FROM status
                WHERE status_code IS NOT NULL
                ORDER BY timestamp
            """, conn)
            
            # Create visualizations
            create_visualizations(status_data, time_data, output_dir, timestamp)
            
            write_output("\nBreakdown by status code:", f)
            write_output("-" * 100, f)
            header = f"{'Code':<6} {'Description':<30} {'Count':>8} {'%':>7} {'Unique Hosts':>12} {'First Seen':>20} {'Last Seen':>20}"
            write_output(header, f)
            write_output("-" * 100, f)
            
            for _, row in status_data.iterrows():
                code = row['status_code']
                count = row['count']
                percentage = (count / total_count) * 100
                description = get_status_description(code)
                first_seen = pd.to_datetime(row['first_seen']).strftime('%Y-%m-%d %H:%M:%S')
                last_seen = pd.to_datetime(row['last_seen']).strftime('%Y-%m-%d %H:%M:%S')
                
                line = f"{code:<6} {description[:30]:<30} {count:>8,} {percentage:>6.1f}% {row['unique_hosts']:>12,} {first_seen:>20} {last_seen:>20}"
                write_output(line, f)
            
            # Get recent errors
            write_output("\nMost Recent Error Responses (Last Hour):", f)
            write_output("-" * 100, f)
            recent_errors = pd.read_sql_query("""
                SELECT 
                    timestamp as time,
                    hostname,
                    status_code,
                    response
                FROM status 
                WHERE 
                    status_code NOT IN (200, 302)
                    AND status_code IS NOT NULL
                    AND timestamp > datetime('now', '-1 hour')
                ORDER BY timestamp DESC
                LIMIT 5
            """, conn)
            
            if len(recent_errors) > 0:
                for _, row in recent_errors.iterrows():
                    write_output(f"Time: {pd.to_datetime(row['time']).strftime('%Y-%m-%d %H:%M:%S')}", f)
                    write_output(f"Host: {row['hostname']}", f)
                    write_output(f"Code: {row['status_code']} ({get_status_description(row['status_code'])})", f)
                    write_output(f"Response: {str(row['response'])[:100]}...", f)
                    write_output("-" * 50, f)
            else:
                write_output("No errors in the last hour", f)
            
            write_output(f"\nReport saved to: {output_file}", f)
            write_output("\nVisualizations saved:", f)
            write_output(f"1. Distribution: status_distribution_{timestamp}.png", f)
            write_output(f"2. Timeline: status_timeline_{timestamp}.png", f)
            write_output(f"3. Heatmap: status_heatmap_{timestamp}.png", f)
            write_output(f"4. Unique Hosts: status_hosts_{timestamp}.png", f)
            
        return True
            
    except sqlite3.Error as e:
        print(f"\nDatabase error: {str(e)}")
        return False
    except Exception as e:
        print(f"\nError while processing data: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = count_status()
    exit(0 if success else 1) 