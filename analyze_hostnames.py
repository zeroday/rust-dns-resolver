#!/usr/bin/env python3

import sqlite3
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
from datetime import datetime

def analyze_hostnames():
    # Connect to the database
    conn = sqlite3.connect('dns_results.db')
    
    # Query to get ASN distribution over time
    time_query = """
    SELECT 
        CASE 
            WHEN hostname LIKE 'mass.gov.com%' THEN 'mass.gov.com'
            WHEN hostname LIKE 'sunpass.com%' THEN 'sunpass.com'
            ELSE 'other'
        END as pattern,
        asn,
        as_name,
        date(timestamp) as date,
        COUNT(*) as count
    FROM dns_results
    WHERE asn IS NOT NULL
    GROUP BY pattern, asn, as_name, date
    ORDER BY date, count DESC
    """
    
    # Read data into pandas DataFrame
    time_df = pd.read_sql_query(time_query, conn)
    time_df['date'] = pd.to_datetime(time_df['date'])
    
    # Print basic statistics
    print("\n=== ASN Distribution Over Time ===")
    for pattern in time_df['pattern'].unique():
        pattern_data = time_df[time_df['pattern'] == pattern]
        print(f"\n{pattern} domains:")
        print(f"Date range: {pattern_data['date'].min()} to {pattern_data['date'].max()}")
        print(f"Total unique ASNs: {pattern_data['asn'].nunique()}")
    
    # Create visualization
    plt.figure(figsize=(15, 8))
    
    # Get top 5 ASNs for each pattern
    patterns = time_df['pattern'].unique()
    for i, pattern in enumerate(patterns):
        pattern_data = time_df[time_df['pattern'] == pattern]
        top_asns = pattern_data.groupby('asn')['count'].sum().nlargest(5).index
        
        plt.subplot(1, len(patterns), i+1)
        
        # Plot each top ASN's count over time
        for asn in top_asns:
            asn_data = pattern_data[pattern_data['asn'] == asn]
            asn_name = asn_data['as_name'].iloc[0]
            plt.plot(asn_data['date'], asn_data['count'], 
                    label=f"AS{asn}\n{asn_name[:20]}",
                    marker='o')
        
        plt.title(f'Top 5 ASNs for {pattern} over Time')
        plt.xlabel('Date')
        plt.ylabel('Number of Domains')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True)
        plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('asn_time_series.png', bbox_inches='tight')
    plt.close()
    print("\nASN time series plot saved as asn_time_series.png")
    
    # Create a heatmap of ASN activity
    plt.figure(figsize=(15, 8))
    
    for i, pattern in enumerate(patterns):
        pattern_data = time_df[time_df['pattern'] == pattern]
        # Pivot the data for heatmap
        heatmap_data = pattern_data.pivot_table(
            index='date',
            columns='asn',
            values='count',
            fill_value=0
        )
        
        # Get top 10 ASNs by total count
        top_asns = pattern_data.groupby('asn')['count'].sum().nlargest(10).index
        heatmap_data = heatmap_data[top_asns]
        
        plt.subplot(1, len(patterns), i+1)
        plt.imshow(heatmap_data.T, aspect='auto', cmap='YlOrRd')
        plt.colorbar(label='Number of Domains')
        
        # Set labels
        plt.yticks(range(len(top_asns)), [f"AS{asn}" for asn in top_asns])
        plt.xticks(range(len(heatmap_data.index)), 
                  [d.strftime('%Y-%m-%d') for d in heatmap_data.index],
                  rotation=45)
        
        plt.title(f'ASN Activity Heatmap for {pattern}')
        plt.xlabel('Date')
        plt.ylabel('ASN')
    
    plt.tight_layout()
    plt.savefig('asn_heatmap.png', bbox_inches='tight')
    plt.close()
    print("\nASN activity heatmap saved as asn_heatmap.png")
    
    conn.close()

if __name__ == "__main__":
    analyze_hostnames() 