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
    try:
        conn = sqlite3.connect('dns_results.db')
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Query for time series data
        time_query = """
        SELECT 
            strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
            ip_address,
            asn,
            COUNT(*) as count
        FROM dns_results
        WHERE timestamp > ?
        GROUP BY hour, ip_address, asn
        ORDER BY hour, count DESC
        """
        
        # Query for summary data
        summary_query = """
        SELECT 
            ip_address,
            asn,
            as_name,
            COUNT(*) as count,
            GROUP_CONCAT(DISTINCT hostname) as hostnames
        FROM dns_results
        WHERE timestamp > ?
        GROUP BY ip_address, asn, as_name
        ORDER BY count DESC
        LIMIT 20
        """
        
        df_time = pd.read_sql_query(time_query, conn, params=(cutoff_time.isoformat(),))
        df_summary = pd.read_sql_query(summary_query, conn, params=(cutoff_time.isoformat(),))
        
        conn.close()
        return df_time, df_summary
    except Exception as e:
        print(f"Error getting data: {e}")
        return pd.DataFrame(), pd.DataFrame()

def create_visualizations(df_time, df_summary, hours=24):
    if len(df_time) == 0 or len(df_summary) == 0:
        print("No data available for visualization")
        return
        
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    period = f"{hours}h"
    
    try:
        # 1. Time series plot
        plt.figure(figsize=(15, 8))
        
        # Convert hour to datetime
        df_time['hour'] = pd.to_datetime(df_time['hour'])
        
        # Plot each IP address as a line
        for ip in df_time['ip_address'].unique():
            ip_data = df_time[df_time['ip_address'] == ip]
            asn_value = ip_data['asn'].iloc[0]
            asn = asn_value.split()[0] if asn_value else 'Unknown'  # Handle None values
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
        plt.figure(figsize=(20, 10))
        
        # Create color map for ASNs, handling None values
        df_summary['asn'] = df_summary['asn'].fillna('Unknown ASN')
        unique_asns = df_summary['asn'].unique()
        colors = plt.cm.tab20(np.linspace(0, 1, len(unique_asns)))
        asn_color_map = dict(zip(unique_asns, colors))
        
        # Create bars with colors based on ASN
        bars = plt.bar(range(len(df_summary)), df_summary['count'],
                      color=[asn_color_map[asn] for asn in df_summary['asn']])
        plt.xticks(range(len(df_summary)), df_summary['ip_address'], rotation=45, ha='right')
        
        # Create legend entries for ASNs
        legend_elements = [plt.Rectangle((0,0),1,1, facecolor=color,
                          label=f"{asn.split()[0] if isinstance(asn, str) else 'Unknown'}: {' '.join(asn.split()[1:])[:40] if isinstance(asn, str) else 'Unknown ASN'}...")
                          for asn, color in asn_color_map.items()]
        plt.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.title(f'Top 20 IP Addresses (Past {hours} Hours)')
        plt.xlabel('IP Address')
        plt.ylabel('Number of DNS Resolutions')
        plt.tight_layout()
        plt.savefig(f'top_ips_{period}_{timestamp}.png', bbox_inches='tight')
        plt.close()
        
        # 3. Treemap of IPs grouped by ASN
        plt.figure(figsize=(20, 10))
        
        # Fill NA values in as_name
        df_summary['as_name'] = df_summary['as_name'].fillna('Unknown')
        asn_groups = df_summary.groupby(['asn', 'as_name'])['count'].sum().reset_index()
        
        # Create treemap data
        sizes = asn_groups['count']
        labels = [f'{asn.split()[0] if isinstance(asn, str) else "Unknown"}\n{name[:20]}...\n{count}' if len(str(name)) > 20 
                 else f'{asn.split()[0] if isinstance(asn, str) else "Unknown"}\n{name}\n{count}'
                 for asn, name, count in zip(asn_groups['asn'], asn_groups['as_name'], asn_groups['count'])]
        
        colors = plt.cm.viridis(np.linspace(0, 1, len(sizes)))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%')
        plt.title(f'Distribution of Top IPs by ASN (Past {hours} Hours)')
        plt.axis('equal')
        plt.savefig(f'top_ips_by_asn_{period}_{timestamp}.png', bbox_inches='tight')
        plt.close()
    except Exception as e:
        print(f"Error creating visualizations: {e}")

def main():
    try:
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
    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    main() 