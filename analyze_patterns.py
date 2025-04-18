#!/usr/bin/env python3

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def analyze_patterns():
    # Connect to the database
    conn = sqlite3.connect('dns_results.db')
    
    # Query to get pattern counts over time
    time_query = """
    SELECT 
        date(timestamp) as date,
        CASE 
            WHEN hostname LIKE 'sunpass.com%' THEN 'sunpass.com'
            WHEN hostname LIKE 'txtag.org%' THEN 'txtag.org'
            WHEN hostname LIKE 'thetollroads.com%' THEN 'thetollroads.com'
            WHEN hostname LIKE 'ezdrivema.com%' THEN 'ezdrivema.com'
            WHEN hostname LIKE 'paytoll%' THEN 'paytoll*.vip'
            ELSE substr(hostname, 1, instr(hostname, '.') + 3)
        END as pattern,
        COUNT(*) as count
    FROM dns_results
    GROUP BY date, pattern
    ORDER BY date, count DESC
    """
    
    # Read data into pandas DataFrame
    df = pd.read_sql_query(time_query, conn)
    df['date'] = pd.to_datetime(df['date'])
    
    # Print basic statistics
    print("\n=== Pattern Analysis Over Time ===")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Total unique patterns: {df['pattern'].nunique()}")
    
    # Get top 5 patterns overall
    top_patterns = df.groupby('pattern')['count'].sum().nlargest(5).index
    print("\nTop 5 Patterns Overall:")
    for pattern in top_patterns:
        total = df[df['pattern'] == pattern]['count'].sum()
        print(f"{pattern}: {total} hostnames")
    
    # Create time series visualization
    plt.figure(figsize=(15, 8))
    
    # Plot each top pattern's count over time
    for pattern in top_patterns:
        pattern_data = df[df['pattern'] == pattern]
        plt.plot(pattern_data['date'], pattern_data['count'], 
                label=pattern, marker='o', linewidth=2)
    
    plt.title('Top 5 Hostname Patterns Over Time')
    plt.xlabel('Date')
    plt.ylabel('Number of Hostnames')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True)
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('pattern_time_series.png', bbox_inches='tight')
    plt.close()
    print("\nTime series plot saved as pattern_time_series.png")
    
    # Create stacked area chart
    plt.figure(figsize=(15, 8))
    
    # Pivot the data for stacked area chart
    pivot_df = df.pivot(index='date', columns='pattern', values='count').fillna(0)
    
    # Get top 10 patterns by total count
    top_10_patterns = df.groupby('pattern')['count'].sum().nlargest(10).index
    pivot_df = pivot_df[top_10_patterns]
    
    # Calculate percentages
    pivot_df = pivot_df.div(pivot_df.sum(axis=1), axis=0) * 100
    
    # Create stacked area chart
    plt.stackplot(pivot_df.index, pivot_df.T, labels=pivot_df.columns)
    
    plt.title('Percentage Distribution of Top 10 Patterns Over Time')
    plt.xlabel('Date')
    plt.ylabel('Percentage of Total Hostnames')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('pattern_stacked_area.png', bbox_inches='tight')
    plt.close()
    print("\nStacked area chart saved as pattern_stacked_area.png")
    
    # Create heatmap of pattern activity
    plt.figure(figsize=(15, 8))
    
    # Create daily pattern matrix
    heatmap_data = df.pivot_table(
        index='date',
        columns='pattern',
        values='count',
        fill_value=0
    )
    
    # Get top 15 patterns
    top_15_patterns = df.groupby('pattern')['count'].sum().nlargest(15).index
    heatmap_data = heatmap_data[top_15_patterns]
    
    # Create heatmap
    plt.imshow(heatmap_data.T, aspect='auto', cmap='YlOrRd')
    plt.colorbar(label='Number of Hostnames')
    
    # Set labels
    plt.yticks(range(len(top_15_patterns)), top_15_patterns)
    plt.xticks(range(len(heatmap_data.index)), 
              [d.strftime('%Y-%m-%d') for d in heatmap_data.index],
              rotation=45)
    
    plt.title('Pattern Activity Heatmap')
    plt.xlabel('Date')
    plt.ylabel('Pattern')
    
    plt.tight_layout()
    plt.savefig('pattern_heatmap.png', bbox_inches='tight')
    plt.close()
    print("\nPattern activity heatmap saved as pattern_heatmap.png")
    
    conn.close()

if __name__ == "__main__":
    analyze_patterns() 