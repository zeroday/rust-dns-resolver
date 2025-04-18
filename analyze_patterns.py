#!/usr/bin/env python3

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import argparse
import sys
import numpy as np

def create_visualization(df, visualization_type, time_filter=None):
    """Helper function to create and save a visualization"""
    try:
        if visualization_type == 'time_series':
            plt.figure(figsize=(15, 8))
            top_patterns = df.groupby('pattern')['count'].sum().nlargest(5).index
            for pattern in top_patterns:
                pattern_data = df[df['pattern'] == pattern]
                plt.plot(pattern_data['date'], pattern_data['count'], 
                        label=pattern, marker='o', linewidth=2)
            
            # Create title based on time range
            start_time = df['date'].min().strftime('%Y-%m-%d %H:%M')
            end_time = df['date'].max().strftime('%Y-%m-%d %H:%M')
            if time_filter == 'today':
                title = f'Top 5 Hostname Patterns for {start_time}'
            elif time_filter == 'last12':
                title = f'Top 5 Hostname Patterns (Last 12 Hours: {start_time} to {end_time})'
            else:
                title = f'Top 5 Hostname Patterns (All Time: {start_time} to {end_time})'
            
            plt.title(title)
            plt.xlabel('Date')
            plt.ylabel('Number of Hostnames')
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.grid(True)
            plt.xticks(rotation=45)
            
        elif visualization_type == 'stacked_area':
            plt.figure(figsize=(15, 8))
            pivot_df = df.pivot(index='date', columns='pattern', values='count').fillna(0)
            top_10_patterns = df.groupby('pattern')['count'].sum().nlargest(10).index
            pivot_df = pivot_df[top_10_patterns]
            pivot_df = pivot_df.div(pivot_df.sum(axis=1), axis=0) * 100
            plt.stackplot(pivot_df.index, pivot_df.T, labels=pivot_df.columns)
            plt.title('Percentage Distribution of Top 10 Patterns Over Time')
            plt.xlabel('Date')
            plt.ylabel('Percentage of Total Hostnames')
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            
        elif visualization_type == 'heatmap':
            # Create a smaller figure for the heatmap
            plt.figure(figsize=(12, 6))
            
            # Aggregate data by hour to reduce the number of time points
            df['hour'] = df['date'].dt.floor('H')
            heatmap_data = df.groupby(['hour', 'pattern'])['count'].sum().unstack(fill_value=0)
            
            # Get top 10 patterns instead of 15 to reduce complexity
            top_patterns = df.groupby('pattern')['count'].sum().nlargest(10).index
            heatmap_data = heatmap_data[top_patterns]
            
            # Create the heatmap with a more efficient colormap
            plt.imshow(heatmap_data.T, aspect='auto', cmap='YlOrRd', interpolation='nearest')
            plt.colorbar(label='Number of Hostnames')
            
            # Set labels with reduced frequency
            hours = heatmap_data.index
            plt.yticks(range(len(top_patterns)), top_patterns)
            plt.xticks(range(0, len(hours), max(1, len(hours)//6)), 
                      [h.strftime('%H:%M') for h in hours[::max(1, len(hours)//6)]],
                      rotation=45)
            
            plt.title('Pattern Activity Heatmap (Hourly Aggregation)')
            plt.xlabel('Time (Hour)')
            plt.ylabel('Pattern')
        
        plt.tight_layout()
        time_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        if time_filter:
            filename = f'pattern_{visualization_type}_{time_filter}_{time_str}.png'
        else:
            filename = f'pattern_{visualization_type}.png'
        
        # Save with lower DPI to reduce memory usage
        plt.savefig(filename, bbox_inches='tight', dpi=100)
        plt.close()
        print(f"\n{visualization_type.replace('_', ' ').title()} plot saved as {filename}")
        return True
        
    except Exception as e:
        print(f"\nError creating {visualization_type} visualization: {str(e)}")
        plt.close('all')
        return False

def analyze_patterns(today_only=False, last12=False):
    conn = None
    try:
        # Connect to the database
        conn = sqlite3.connect('dns_results.db')
        
        # Base query
        base_query = """
        SELECT 
            datetime(timestamp) as date,
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
        """
        
        # Add date filter if today_only or last12 is True
        if today_only:
            today = datetime.now().strftime('%Y-%m-%d')
            base_query += f" WHERE date(timestamp) = '{today}'"
        elif last12:
            last_12_hours = (datetime.now() - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')
            base_query += f" WHERE datetime(timestamp) >= '{last_12_hours}'"
        
        # Complete the query
        base_query += " GROUP BY datetime(timestamp), pattern ORDER BY datetime(timestamp), count DESC"
        
        # Read data into pandas DataFrame
        df = pd.read_sql_query(base_query, conn)
        df['date'] = pd.to_datetime(df['date'])
        
        # Print basic statistics
        print("\n=== Pattern Analysis Over Time ===")
        if today_only:
            print(f"Showing data for: {df['date'].min().strftime('%Y-%m-%d')}")
        elif last12:
            print(f"Showing data for last 12 hours: {df['date'].min().strftime('%Y-%m-%d %H:%M')} to {df['date'].max().strftime('%Y-%m-%d %H:%M')}")
        else:
            print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"Total unique patterns: {df['pattern'].nunique()}")
        
        # Get top 5 patterns overall
        top_patterns = df.groupby('pattern')['count'].sum().nlargest(5).index
        print("\nTop 5 Patterns Overall:")
        for pattern in top_patterns:
            total = df[df['pattern'] == pattern]['count'].sum()
            print(f"{pattern}: {total} hostnames")
        
        # Create visualizations
        time_filter = 'today' if today_only else 'last12' if last12 else None
        
        # Create visualizations one at a time with proper cleanup
        if not create_visualization(df, 'time_series', time_filter):
            print("Warning: Failed to create time series plot")
        if not create_visualization(df, 'stacked_area', time_filter):
            print("Warning: Failed to create stacked area plot")
        if not create_visualization(df, 'heatmap', time_filter):
            print("Warning: Failed to create heatmap")
        
    except Exception as e:
        print(f"\nError during analysis: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze DNS hostname patterns')
    parser.add_argument('--today', action='store_true', help='Show only today\'s data')
    parser.add_argument('--last12', action='store_true', help='Show data from the last 12 hours')
    args = parser.parse_args()
    
    if args.today and args.last12:
        print("Error: Cannot use both --today and --last12 options together")
        sys.exit(1)
    
    success = analyze_patterns(args.today, args.last12)
    sys.exit(0 if success else 1) 