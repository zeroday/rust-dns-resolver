#!/usr/bin/env python3

import sqlite3
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
from datetime import datetime
import argparse

def analyze_hostnames(pattern):
    # Connect to the database
    conn = sqlite3.connect('dns_results.db')
    
    # Query to get ASN distribution over time
    time_query = """
    SELECT 
        asn,
        as_name,
        date(timestamp) as date,
        COUNT(*) as count
    FROM dns_results
    WHERE asn IS NOT NULL
    AND hostname LIKE ?
    GROUP BY asn, as_name, date
    ORDER BY date, count DESC
    """
    
    # Read data into pandas DataFrame
    time_df = pd.read_sql_query(time_query, conn, params=[f"{pattern}%"])
    time_df['date'] = pd.to_datetime(time_df['date'])
    
    # Print basic statistics
    print(f"\n=== ASN Distribution Over Time for '{pattern}%' ===")
    total_hostnames = time_df['count'].sum()
    print(f"Date range: {time_df['date'].min()} to {time_df['date'].max()}")
    print(f"Total unique ASNs: {time_df['asn'].nunique()}")
    print(f"Total hostnames: {total_hostnames}")
    
    # Print top 5 ASNs
    top_asns = time_df.groupby(['asn', 'as_name'])['count'].sum().nlargest(5)
    print("\nTop 5 ASNs:")
    for (asn, as_name), count in top_asns.items():
        percentage = (count / total_hostnames) * 100
        print(f"AS{asn} ({as_name}): {count} hostnames ({percentage:.1f}%)")
    
    # Create visualization
    plt.figure(figsize=(12, 6))
    
    # Get top 5 ASNs
    top_asns = time_df.groupby('asn')['count'].sum().nlargest(5).index
    
    # Plot each top ASN's count over time
    for asn in top_asns:
        asn_data = time_df[time_df['asn'] == asn]
        asn_name = asn_data['as_name'].iloc[0]
        plt.plot(asn_data['date'], asn_data['count'], 
                label=f"AS{asn}\n{asn_name[:20]}",
                marker='o')
    
    plt.title(f'Top 5 ASNs for {pattern}% over Time')
    plt.xlabel('Date')
    plt.ylabel('Number of Hostnames')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True)
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(f'asn_time_series_{pattern.replace(".", "_")}.png', bbox_inches='tight')
    plt.close()
    print(f"\nASN time series plot saved as asn_time_series_{pattern.replace('.', '_')}.png")
    
    # Create a heatmap of ASN activity
    plt.figure(figsize=(12, 6))
    
    # Pivot the data for heatmap
    heatmap_data = time_df.pivot_table(
        index='date',
        columns='asn',
        values='count',
        fill_value=0
    )
    
    # Get top 10 ASNs by total count
    top_asns = time_df.groupby('asn')['count'].sum().nlargest(10).index
    heatmap_data = heatmap_data[top_asns]
    
    plt.imshow(heatmap_data.T, aspect='auto', cmap='YlOrRd')
    plt.colorbar(label='Number of Hostnames')
    
    # Set labels
    plt.yticks(range(len(top_asns)), [f"AS{asn}" for asn in top_asns])
    plt.xticks(range(len(heatmap_data.index)), 
              [d.strftime('%Y-%m-%d') for d in heatmap_data.index],
              rotation=45)
    
    plt.title(f'ASN Activity Heatmap for {pattern}%')
    plt.xlabel('Date')
    plt.ylabel('ASN')
    
    plt.tight_layout()
    plt.savefig(f'asn_heatmap_{pattern.replace(".", "_")}.png', bbox_inches='tight')
    plt.close()
    print(f"\nASN activity heatmap saved as asn_heatmap_{pattern.replace('.', '_')}.png")
    
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze hostname patterns and their ASN distribution')
    parser.add_argument('pattern', help='Hostname pattern to analyze (e.g., sunpass.com)')
    args = parser.parse_args()
    
    analyze_hostnames(args.pattern) 