#!/usr/bin/env python3

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from datetime import datetime, timedelta
import numpy as np
from collections import Counter

def create_ip_visualizations(df):
    """Create various visualizations of IP address relationships"""
    try:
        # 1. IP Address Distribution
        plt.figure(figsize=(12, 6))
        ip_counts = df['ip_address'].value_counts().head(10)
        plt.bar(range(len(ip_counts)), ip_counts.values)
        plt.xticks(range(len(ip_counts)), ip_counts.index, rotation=45)
        plt.title('Top 10 IP Addresses by Hostname Count')
        plt.xlabel('IP Address')
        plt.ylabel('Number of Hostnames')
        plt.tight_layout()
        plt.savefig('ip_distribution.png', bbox_inches='tight', dpi=100)
        plt.close()
        print("\nIP distribution plot saved as ip_distribution.png")

        # 2. IP to Hostname Network Graph
        plt.figure(figsize=(15, 10))
        G = nx.Graph()
        
        # Add nodes and edges
        for _, row in df.iterrows():
            G.add_node(row['ip_address'], node_type='ip')
            G.add_node(row['hostname'], node_type='hostname')
            G.add_edge(row['ip_address'], row['hostname'])
        
        # Get the largest connected component
        largest_cc = max(nx.connected_components(G), key=len)
        G = G.subgraph(largest_cc)
        
        # Position nodes using spring layout
        pos = nx.spring_layout(G, k=1, iterations=50)
        
        # Draw the graph
        nx.draw_networkx_nodes(G, pos, 
                             nodelist=[n for n in G.nodes() if G.nodes[n]['node_type'] == 'ip'],
                             node_color='lightblue',
                             node_size=500,
                             label='IP Addresses')
        nx.draw_networkx_nodes(G, pos, 
                             nodelist=[n for n in G.nodes() if G.nodes[n]['node_type'] == 'hostname'],
                             node_color='lightgreen',
                             node_size=300,
                             label='Hostnames')
        nx.draw_networkx_edges(G, pos, alpha=0.2)
        nx.draw_networkx_labels(G, pos, font_size=8)
        
        plt.title('IP Address to Hostname Relationships')
        plt.legend()
        plt.tight_layout()
        plt.savefig('ip_hostname_network.png', bbox_inches='tight', dpi=100)
        plt.close()
        print("IP-hostname network graph saved as ip_hostname_network.png")

        # 3. IP Address Heatmap by Hour
        plt.figure(figsize=(15, 8))
        df['hour'] = df['timestamp'].dt.floor('h')
        heatmap_data = df.pivot_table(
            index='hour',
            columns='ip_address',
            values='hostname',
            aggfunc='count',
            fill_value=0
        )
        
        # Get top 10 IPs by total count
        top_ips = df['ip_address'].value_counts().head(10).index
        heatmap_data = heatmap_data[top_ips]
        
        plt.imshow(heatmap_data.T, aspect='auto', cmap='YlOrRd', interpolation='nearest')
        plt.colorbar(label='Number of Hostnames')
        
        # Set labels
        hours = heatmap_data.index
        plt.yticks(range(len(top_ips)), top_ips)
        plt.xticks(range(0, len(hours), max(1, len(hours)//6)), 
                  [h.strftime('%H:%M') for h in hours[::max(1, len(hours)//6)]],
                  rotation=45)
        
        plt.title('IP Address Activity Heatmap (Hourly)')
        plt.xlabel('Time (Hour)')
        plt.ylabel('IP Address')
        plt.tight_layout()
        plt.savefig('ip_activity_heatmap.png', bbox_inches='tight', dpi=100)
        plt.close()
        print("IP activity heatmap saved as ip_activity_heatmap.png")

        return True
        
    except Exception as e:
        print(f"\nError creating visualizations: {str(e)}")
        plt.close('all')
        return False

def analyze_ips():
    conn = None
    try:
        # Connect to the database
        conn = sqlite3.connect('dns_results.db')
        
        # Get data from the last 12 hours
        last_12_hours = (datetime.now() - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Query to get IP address and hostname relationships
        query = """
        SELECT 
            datetime(timestamp) as timestamp,
            ip_address,
            hostname
        FROM dns_results
        WHERE datetime(timestamp) >= ?
        ORDER BY timestamp
        """
        
        # Read data into pandas DataFrame
        df = pd.read_sql_query(query, conn, params=[last_12_hours])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Print basic statistics
        print("\n=== IP Address Analysis (Last 12 Hours) ===")
        print(f"Time range: {df['timestamp'].min().strftime('%Y-%m-%d %H:%M')} to {df['timestamp'].max().strftime('%Y-%m-%d %H:%M')}")
        print(f"Total unique IP addresses: {df['ip_address'].nunique()}")
        print(f"Total unique hostnames: {df['hostname'].nunique()}")
        
        # Get top 5 IPs by hostname count
        top_ips = df['ip_address'].value_counts().head(5)
        print("\nTop 5 IP Addresses by Hostname Count:")
        for ip, count in top_ips.items():
            print(f"{ip}: {count} hostnames")
        
        # Create visualizations
        if not create_ip_visualizations(df):
            print("Warning: Some visualizations failed to create")
        
    except Exception as e:
        print(f"\nError during analysis: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()
    return True

if __name__ == "__main__":
    success = analyze_ips()
    sys.exit(0 if success else 1) 