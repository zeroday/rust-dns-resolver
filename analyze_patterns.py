#!/usr/bin/env python3

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import re

def analyze_patterns():
    # Connect to the database
    conn = sqlite3.connect('dns_results.db')
    
    # Query to get base domains and their counts
    pattern_query = """
    SELECT 
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
    GROUP BY pattern
    ORDER BY count DESC
    """
    
    # Read data into pandas DataFrame
    df = pd.read_sql_query(pattern_query, conn)
    
    # Print basic statistics
    print("\n=== Top Hostname Patterns ===")
    print(f"Total unique patterns: {len(df)}")
    print(f"Total hostnames: {df['count'].sum()}")
    
    # Print top 10 patterns
    print("\nTop 10 Patterns:")
    for _, row in df.head(10).iterrows():
        percentage = (row['count'] / df['count'].sum()) * 100
        print(f"{row['pattern']}: {row['count']} ({percentage:.1f}%)")
    
    # Create visualization
    plt.figure(figsize=(12, 6))
    
    # Get top 15 patterns
    top_patterns = df.head(15)
    
    # Create bar chart
    bars = plt.bar(range(len(top_patterns)), 
                  top_patterns['count'],
                  color=plt.cm.tab20(range(len(top_patterns))))
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom')
    
    # Customize the plot
    plt.title('Top 15 Hostname Patterns')
    plt.xlabel('Pattern')
    plt.ylabel('Number of Hostnames')
    plt.xticks(range(len(top_patterns)), 
              [pattern[:20] + '...' if len(pattern) > 20 else pattern 
               for pattern in top_patterns['pattern']],
              rotation=45, ha='right')
    
    # Add percentage labels on the right side
    ax2 = plt.gca().twinx()
    ax2.set_ylim(plt.gca().get_ylim())
    ax2.set_yticklabels([f'{y/df["count"].sum()*100:.1f}%' 
                        for y in ax2.get_yticks()])
    ax2.set_ylabel('Percentage of Total')
    
    plt.tight_layout()
    plt.savefig('top_patterns.png', bbox_inches='tight')
    plt.close()
    print("\nPattern distribution plot saved as top_patterns.png")
    
    # Create pie chart for top 10 patterns
    plt.figure(figsize=(12, 8))
    
    # Get top 10 patterns and combine the rest into "Other"
    top_10 = df.head(10)
    other_count = df['count'].sum() - top_10['count'].sum()
    
    if other_count > 0:
        top_10 = pd.concat([top_10, 
                           pd.DataFrame({'pattern': ['Other'], 
                                       'count': [other_count]})])
    
    # Create pie chart
    plt.pie(top_10['count'], 
            labels=top_10['pattern'],
            autopct='%1.1f%%',
            startangle=90,
            pctdistance=0.85)
    
    plt.title('Distribution of Top 10 Hostname Patterns')
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig('pattern_pie.png', bbox_inches='tight')
    plt.close()
    print("\nPattern pie chart saved as pattern_pie.png")
    
    conn.close()

if __name__ == "__main__":
    analyze_patterns() 