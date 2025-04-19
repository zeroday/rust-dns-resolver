#!/usr/bin/env python3

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

def analyze_cloudflare_usage():
    # Connect to the database
    conn = sqlite3.connect('dns_results.db')
    
    # Query to get all records with Cloudflare ASN (AS13335)
    query = """
    SELECT 
        date(timestamp) as date,
        hostname,
        ip_address,
        asn,
        as_name,
        COUNT(*) as count
    FROM dns_results
    WHERE asn = '13335'  -- Cloudflare ASN
    GROUP BY date, hostname, ip_address, asn, as_name
    ORDER BY date, count DESC
    """
    
    # Read data into pandas DataFrame
    df = pd.read_sql_query(query, conn)
    
    if df.empty:
        print("No Cloudflare IP addresses found in the database.")
        conn.close()
        return
        
    df['date'] = pd.to_datetime(df['date'])
    
    # Basic statistics
    print("\n=== Cloudflare Usage Analysis ===")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    total_records = df['count'].sum()
    unique_ips = df['ip_address'].nunique()
    unique_hosts = df['hostname'].nunique()
    print(f"Total DNS records using Cloudflare: {total_records}")
    print(f"Unique IP addresses: {unique_ips}")
    print(f"Unique hostnames: {unique_hosts}")
    
    # Get top hostnames using Cloudflare
    top_hosts = df.groupby('hostname')['count'].sum().sort_values(ascending=False).head(10)
    print("\nTop 10 Hostnames using Cloudflare:")
    for host, count in top_hosts.items():
        percentage = (count / total_records) * 100
        print(f"{host}: {count} records ({percentage:.1f}%)")
    
    # Create time series plot
    plt.figure(figsize=(12, 6))
    daily_counts = df.groupby('date')['count'].sum()
    plt.plot(daily_counts.index, daily_counts.values, marker='o')
    plt.title('Cloudflare IP Usage Over Time')
    plt.xlabel('Date')
    plt.ylabel('Number of DNS Records')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    plt.savefig(f'cloudflare_usage_{timestamp}.png')
    plt.close()
    print(f"\nTime series plot saved as cloudflare_usage_{timestamp}.png")
    
    # Create hostname distribution heatmap
    plt.figure(figsize=(15, 8))
    pivot_data = df.pivot_table(
        index='hostname',
        columns='date',
        values='count',
        fill_value=0
    )
    
    # Get top 15 hostnames by total count
    top_15_hosts = df.groupby('hostname')['count'].sum().nlargest(15).index
    pivot_data = pivot_data.loc[top_15_hosts]
    
    sns.heatmap(pivot_data, cmap='YlOrRd', cbar_kws={'label': 'Number of Records'})
    plt.title('Cloudflare Usage Heatmap by Hostname')
    plt.xlabel('Date')
    plt.ylabel('Hostname')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'cloudflare_heatmap_{timestamp}.png')
    plt.close()
    print(f"Hostname heatmap saved as cloudflare_heatmap_{timestamp}.png")
    
    # Get IP address distribution
    print("\nIP Address Distribution:")
    ip_distribution = df.groupby('ip_address')['count'].sum().sort_values(ascending=False).head(10)
    for ip, count in ip_distribution.items():
        percentage = (count / total_records) * 100
        print(f"{ip}: {count} records ({percentage:.1f}%)")
    
    # Calculate percentage of total DNS records using Cloudflare
    total_query = "SELECT COUNT(*) as total FROM dns_results"
    total_df = pd.read_sql_query(total_query, conn)
    total_dns_records = total_df['total'].iloc[0]
    cloudflare_percentage = (total_records / total_dns_records) * 100
    print(f"\nPercentage of all DNS records using Cloudflare: {cloudflare_percentage:.1f}%")
    
    conn.close()

if __name__ == "__main__":
    analyze_cloudflare_usage() 