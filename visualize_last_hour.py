#!/usr/bin/env python3

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import numpy as np

def get_data(db_path='dns_results.db'):
    conn = sqlite3.connect(db_path)
    
    # Get current time and time 1 hour ago
    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)
    
    # Query DNS results
    dns_query = """
    SELECT 
        hostname,
        ip_address,
        asn,
        as_name,
        timestamp,
        success
    FROM dns_results
    WHERE datetime(timestamp) > datetime(?)
    ORDER BY timestamp
    """
    
    # Query status results
    status_query = """
    SELECT 
        hostname,
        status_code,
        path,
        timestamp
    FROM status
    WHERE datetime(timestamp) > datetime(?)
    ORDER BY timestamp
    """
    
    # Load data into pandas
    dns_df = pd.read_sql_query(dns_query, conn, params=(hour_ago.isoformat(),))
    status_df = pd.read_sql_query(status_query, conn, params=(hour_ago.isoformat(),))
    
    # Convert timestamps
    dns_df['timestamp'] = pd.to_datetime(dns_df['timestamp'])
    status_df['timestamp'] = pd.to_datetime(status_df['timestamp'])
    
    # Convert success to float for proper aggregation
    dns_df['success'] = dns_df['success'].astype(float)
    
    conn.close()
    return dns_df, status_df

def create_visualizations(dns_df, status_df):
    # Create a figure with multiple subplots
    plt.style.use('default')
    fig = plt.figure(figsize=(15, 10))
    
    # 1. DNS Resolution Success Rate Over Time
    ax1 = plt.subplot(2, 2, 1)
    # Group by 5-minute intervals and calculate mean
    dns_df['minute_group'] = dns_df['timestamp'].dt.floor('5min')
    success_rate = dns_df.groupby('minute_group')['success'].mean()
    success_rate.plot(ax=ax1, marker='o', linestyle='-', color='blue')
    ax1.set_title('DNS Resolution Success Rate (5-minute intervals)')
    ax1.set_ylabel('Success Rate')
    ax1.grid(True)
    
    # 2. Status Code Distribution
    ax2 = plt.subplot(2, 2, 2)
    status_codes = status_df['status_code'].value_counts()
    status_codes.plot(kind='bar', ax=ax2, color='green')
    ax2.set_title('HTTP Status Code Distribution')
    ax2.set_xlabel('Status Code')
    ax2.set_ylabel('Count')
    
    # 3. ASN Distribution (Top 10)
    ax3 = plt.subplot(2, 2, 3)
    asn_counts = dns_df[dns_df['asn'].notna()]['asn'].value_counts().head(10)
    asn_counts.plot(kind='barh', ax=ax3, color='orange')
    ax3.set_title('Top 10 ASNs')
    ax3.set_xlabel('Count')
    
    # 4. Top 5 IP Addresses
    ax4 = plt.subplot(2, 2, 4)
    ip_counts = dns_df[dns_df['ip_address'].notna()]['ip_address'].value_counts().head(5)
    colors = plt.cm.Set3(np.linspace(0, 1, len(ip_counts)))
    
    bars = ip_counts.plot(kind='barh', ax=ax4, color=colors)
    ax4.set_title('Top 5 IP Addresses')
    ax4.set_xlabel('Count')
    
    # Add ASN information to the IP address labels
    labels = []
    for ip in ip_counts.index:
        ip_data = dns_df[dns_df['ip_address'] == ip].iloc[0]
        asn = ip_data['asn'] if pd.notna(ip_data['asn']) else 'Unknown ASN'
        as_name = ip_data['as_name'] if pd.notna(ip_data['as_name']) else 'Unknown Provider'
        labels.append(f"{ip}\n{asn}\n{as_name[:30]}")
    ax4.set_yticklabels(labels)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'last_hour_analysis_{timestamp}.png'
    
    plt.tight_layout()
    plt.savefig(filename, bbox_inches='tight', dpi=300)
    plt.close()
    return filename

def main():
    try:
        print("Fetching data from the last hour...")
        dns_df, status_df = get_data()
        
        print("\nDNS Resolution Statistics:")
        print(f"Total DNS queries: {len(dns_df)}")
        print(f"Successful resolutions: {int(dns_df['success'].sum())}")
        print(f"Unique ASNs found: {dns_df['asn'].nunique()}")
        
        if len(dns_df) > 0:
            print("\nTop ASNs:")
            top_asns = dns_df[dns_df['asn'].notna()].groupby('asn')['hostname'].count().sort_values(ascending=False).head(5)
            for asn, count in top_asns.items():
                as_name = dns_df[dns_df['asn'] == asn]['as_name'].iloc[0]
                print(f"- {asn} ({as_name}): {count} hostnames")
            
            print("\nTop 5 IP Addresses:")
            top_ips = dns_df[dns_df['ip_address'].notna()]['ip_address'].value_counts().head(5)
            for ip, count in top_ips.items():
                ip_data = dns_df[dns_df['ip_address'] == ip].iloc[0]
                asn = ip_data['asn'] if pd.notna(ip_data['asn']) else 'Unknown ASN'
                as_name = ip_data['as_name'] if pd.notna(ip_data['as_name']) else 'Unknown Provider'
                print(f"- {ip} ({asn} - {as_name}): {count} hostnames")
        
        print("\nHTTP Check Statistics:")
        print(f"Total HTTP checks: {len(status_df)}")
        print(f"Successful checks (200): {len(status_df[status_df['status_code'] == 200])}")
        print(f"Unique status codes: {status_df['status_code'].nunique()}")
        
        if len(status_df) > 0:
            print("\nStatus Code Distribution:")
            status_counts = status_df['status_code'].value_counts()
            for status_code, count in status_counts.items():
                print(f"- Status {status_code}: {count} responses")
        
        print("\nCreating visualizations...")
        filename = create_visualizations(dns_df, status_df)
        print(f"Visualizations saved as '{filename}'")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 