#!/usr/bin/env python3

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import argparse
import os
import numpy as np

def get_data(hours=24):
    """Get IP address data from the database for the specified time period."""
    conn = sqlite3.connect('dns_results.db')
    
    # Calculate the timestamp for hours ago
    time_ago = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
    
    # First query to get top 20 IPs overallC
    top_ips_query = """
    SELECT ip_address, COUNT(*) as count
    FROM dns_results 
    WHERE 
        datetime(timestamp) >= datetime(?)
        AND ip_address IS NOT NULL
        AND success = 1
    GROUP BY ip_address
    ORDER BY count DESC
    LIMIT 20
    """
    
    top_ips = pd.read_sql_query(top_ips_query, conn, params=(time_ago,))['ip_address'].tolist()
    
    # Second query to get time series data for these IPs
    time_series_query = """
    SELECT 
        ip_address,
        asn,
        as_name,
        strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
        COUNT(*) as count
    FROM dns_results 
    WHERE 
        datetime(timestamp) >= datetime(?)
        AND ip_address IN ({})
        AND success = 1
    GROUP BY ip_address, asn, as_name, hour
    ORDER BY hour, count DESC
    """.format(','.join(['?'] * len(top_ips)))
    
    # Parameters for the query (time_ago and all top IPs)
    params = [time_ago] + top_ips
    
    df_time = pd.read_sql_query(time_series_query, conn, params=params)
    
    # Get summary data for these IPs
    summary_query = """
    SELECT 
        ip_address,
        asn,
        as_name,
        COUNT(*) as count,
        GROUP_CONCAT(DISTINCT hostname) as hostnames
    FROM dns_results 
    WHERE 
        datetime(timestamp) >= datetime(?)
        AND ip_address IN ({})
        AND success = 1
    GROUP BY ip_address, asn, as_name
    ORDER BY count DESC
    """.format(','.join(['?'] * len(top_ips)))
    
    df_summary = pd.read_sql_query(summary_query, conn, params=[time_ago] + top_ips)
    
    conn.close()
    return df_time, df_summary

def create_visualizations(df_time, df_summary, hours=24):
    """Create various visualizations for top IP addresses."""
    # Set the style
    sns.set_style("whitegrid")
    
    # Create timestamp for file names
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    period = "last12" if hours == 12 else "last24"
    
    # 1. Time series plot
    plt.figure(figsize=(20, 10))  # Increased figure size for more IPs
    
    # Convert hour to datetime
    df_time['hour'] = pd.to_datetime(df_time['hour'])
    
    # Plot each IP address as a line
    for ip in df_time['ip_address'].unique():
        ip_data = df_time[df_time['ip_address'] == ip]
        asn = ip_data['asn'].iloc[0].split()[0]  # Get just the AS number
        label = f"{ip}\n({asn})"
        plt.plot(ip_data['hour'], ip_data['count'], marker='o', label=label, linewidth=2)
    
    plt.title(f'IP Address Activity Over Time (Past {hours} Hours)')
    plt.xlabel('Time')
    plt.ylabel('Number of DNS Resolutions per Hour')
    plt.xticks(rotation=45)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(f'top_ips_time_series_{period}_{timestamp}.png', bbox_inches='tight')
    plt.close()
    
    # 2. Bar plot of top IPs by count
    plt.figure(figsize=(20, 10))  # Increased figure size for more IPs
    
    # Create color map for ASNs
    unique_asns = df_summary['asn'].unique()
    colors = plt.cm.tab20(np.linspace(0, 1, len(unique_asns)))
    asn_color_map = dict(zip(unique_asns, colors))
    
    # Create bars with colors based on ASN
    bars = plt.bar(range(len(df_summary)), df_summary['count'], 
                  color=[asn_color_map[asn] for asn in df_summary['asn']])
    plt.xticks(range(len(df_summary)), df_summary['ip_address'], rotation=45, ha='right')
    
    # Create legend entries for ASNs
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=color, 
                      label=f"{asn.split()[0] if asn else 'Unknown'}: {' '.join(asn.split()[1:])[:40] if asn else 'Unknown ASN'}...")
                      for asn, color in asn_color_map.items()]
    plt.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.title(f'Top 20 IP Addresses (Past {hours} Hours)')
    plt.xlabel('IP Address')
    plt.ylabel('Number of DNS Resolutions')
    plt.tight_layout()
    plt.savefig(f'top_ips_{period}_{timestamp}.png', bbox_inches='tight')
    plt.close()
    
    # 3. Treemap of IPs grouped by ASN
    plt.figure(figsize=(20, 10))  # Increased figure size for more IPs
    asn_groups = df_summary.groupby(['asn', 'as_name'])['count'].sum().reset_index()
    
    # Create treemap data
    sizes = asn_groups['count']
    labels = [f'{asn}\n{name[:20]}...\n{count}' if len(name) > 20 
             else f'{asn}\n{name}\n{count}'
             for asn, name, count in zip(asn_groups['asn'], asn_groups['as_name'], asn_groups['count'])]
    
    colors = plt.cm.viridis(np.linspace(0, 1, len(sizes)))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%')
    plt.title(f'Distribution of Top IPs by ASN (Past {hours} Hours)')
    plt.axis('equal')
    plt.savefig(f'top_ips_by_asn_{period}_{timestamp}.png', bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Analyze top IP addresses from DNS results')
    parser.add_argument('--last12', action='store_true', help='Show data from last 12 hours instead of 24')
    args = parser.parse_args()
    
    hours = 12 if args.last12 else 24
    df_time, df_summary = get_data(hours)
    
    if len(df_summary) == 0:
        print(f"No data found for the past {hours} hours")
        return
    
    create_visualizations(df_time, df_summary, hours)
    
    # Print summary to console
    print(f"\nTop IP Addresses (Past {hours} Hours):")
    print("=" * 80)
    for _, row in df_summary.iterrows():
        print(f"IP: {row['ip_address']}")
        print(f"ASN: {row['asn']} ({row['as_name']})")
        print(f"Count: {row['count']}")
        print(f"Hostnames: {row['hostnames']}")
        print("-" * 80)

if __name__ == "__main__":
    main() 