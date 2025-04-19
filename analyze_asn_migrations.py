#!/usr/bin/env python3

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import argparse
import os
import numpy as np
import matplotlib.dates as mdates

CLOUDFLARE_ASN = 'AS13335 Cloudflare, Inc.'
MAX_HOSTS = 50  # Maximum number of hosts to show in visualizations
VISUALIZATION_DIR = 'visualizations'  # Directory for saving visualizations

# Ensure visualization directory exists
os.makedirs(VISUALIZATION_DIR, exist_ok=True)

def create_ip_flow_diagram(df_migrations, df_cloudflare_stats, asn_names):
    """Create a flow diagram showing hostname migrations over time."""
    print("DEBUG: Starting hostname flow diagram creation")
    
    # Get unique hostnames and sort by most recent activity
    unique_hostnames = df_migrations['hostname'].unique()
    print(f"DEBUG: Found {len(df_migrations)} migrations among {len(unique_hostnames)} hostnames")
    
    # Split hostnames into chunks of 10
    chunk_size = 10
    hostname_chunks = [unique_hostnames[i:i + chunk_size] for i in range(0, len(unique_hostnames), chunk_size)]
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for chunk_idx, hostname_chunk in enumerate(hostname_chunks):
        # Filter migrations for current chunk
        chunk_migrations = df_migrations[df_migrations['hostname'].isin(hostname_chunk)]
        
        # Calculate time range
        min_time = pd.to_datetime(chunk_migrations['start_time'])
        max_time = pd.to_datetime(chunk_migrations['next_end_time'])
        time_range = (max_time.max() - min_time.min()).total_seconds() / 3600  # hours
        
        # Calculate figure dimensions - scale width based on time range
        width_per_hour = 100  # pixels per hour
        fig_width = max(1200, min(time_range * width_per_hour, 4000))  # cap between 1200 and 4000 pixels
        fig_height = 100 * len(hostname_chunk)  # 100 pixels per hostname
        
        plt.figure(figsize=(fig_width/100, fig_height/100))  # Convert pixels to inches (assuming 100 DPI)
        
        # Create color map for ASNs
        unique_asns = pd.concat([chunk_migrations['from_asn'], chunk_migrations['to_asn']]).unique()
        colors = plt.cm.tab20(np.linspace(0, 1, len(unique_asns)))
        asn_colors = dict(zip(unique_asns, colors))
        
        # Plot migrations for each hostname
        for i, hostname in enumerate(hostname_chunk):
            hostname_migrations = chunk_migrations[chunk_migrations['hostname'] == hostname]
            
            # Plot horizontal lines for each ASN period
            y_pos = i
            for _, migration in hostname_migrations.iterrows():
                from_asn = migration['from_asn']
                to_asn = migration['to_asn']
                start_time = pd.to_datetime(migration['start_time'])
                end_time = pd.to_datetime(migration['end_time'])
                next_start_time = pd.to_datetime(migration['next_start_time'])
                
                # Plot ASN transition arrow
                plt.arrow(mdates.date2num(end_time), y_pos, 
                         mdates.date2num(next_start_time) - mdates.date2num(end_time), 0,
                         head_width=0.2, head_length=0.1, fc=asn_colors[from_asn],
                         ec=asn_colors[to_asn], alpha=0.7)
                
                # Add ASN labels
                from_asn_number = from_asn.split()[0]
                to_asn_number = to_asn.split()[0]
                plt.text(mdates.date2num(end_time), y_pos + 0.2,
                        f"{from_asn_number} → {to_asn_number}", fontsize=8, rotation=45)
            
            # Add hostname label
            plt.text(mdates.date2num(min_time.min()) - 0.5, y_pos,
                    hostname, fontsize=8, ha='right')
        
        # Customize the plot
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.title(f'Hostname ASN Migrations (Part {chunk_idx + 1} of {len(hostname_chunks)})')
        plt.tight_layout()
        
        # Save the figure
        output_path = os.path.join(VISUALIZATION_DIR, f'hostname_migrations_{timestamp}_part{chunk_idx + 1}.png')
        plt.savefig(output_path, bbox_inches='tight', dpi=100)
        plt.close()
        
        print(f"DEBUG: Saved part {chunk_idx + 1} of {len(hostname_chunks)}")

def create_flow_diagram(df_migrations, df_cloudflare_stats, asn_names):
    """Create a flow diagram showing migrations to/from Cloudflare."""
    if len(df_migrations) == 0:
        return
        
    # Filter migrations to only include hostnames in df_cloudflare_stats
    recent_hostnames = set(df_cloudflare_stats['hostname'])
    df_migrations = df_migrations[df_migrations['hostname'].isin(recent_hostnames)]
    
    # Split migrations into to/from Cloudflare
    to_cloudflare = df_migrations[df_migrations['to_asn'] == CLOUDFLARE_ASN]
    from_cloudflare = df_migrations[df_migrations['from_asn'] == CLOUDFLARE_ASN]
    
    if len(to_cloudflare) == 0 and len(from_cloudflare) == 0:
        return
        
    plt.figure(figsize=(15, 10))
    
    # Create positions for ASNs
    all_asns = set(df_migrations['from_asn'].unique()) | set(df_migrations['to_asn'].unique())
    asn_positions = {}
    non_cloudflare_asns = sorted([asn for asn in all_asns if asn != CLOUDFLARE_ASN])
    
    # Position Cloudflare in the middle
    total_height = len(non_cloudflare_asns) + 1
    cloudflare_y = total_height / 2
    asn_positions[CLOUDFLARE_ASN] = cloudflare_y
    
    # Position other ASNs evenly
    other_positions = np.linspace(1, total_height, len(non_cloudflare_asns))
    for asn, pos in zip(non_cloudflare_asns, other_positions):
        asn_positions[asn] = pos
    
    # Plot migrations
    for _, row in df_migrations.iterrows():
        start_y = asn_positions[row['from_asn']]
        end_y = asn_positions[row['to_asn']]
        
        # Calculate control points for curved arrows
        mid_x = 0.5
        if row['to_asn'] == CLOUDFLARE_ASN:
            color = 'green'
            label = 'To Cloudflare'
        else:
            color = 'red'
            label = 'From Cloudflare'
            
        plt.annotate('',
                    xy=(1, end_y),
                    xytext=(0, start_y),
                    arrowprops=dict(arrowstyle='->',
                                  color=color,
                                  lw=2,
                                  connectionstyle='arc3,rad=.2'))
        
        # Add hostname labels
        plt.text(-0.1, start_y, row['hostname'],
                horizontalalignment='right',
                verticalalignment='center')
    
    # Add ASN labels
    for asn, pos in asn_positions.items():
        asn_label = asn.split()[0]  # Just show AS number
        plt.text(1.1, pos, asn_label,
                horizontalalignment='left',
                verticalalignment='center')
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], color='green', label='To Cloudflare', marker='>', linestyle='-'),
        plt.Line2D([0], [0], color='red', label='From Cloudflare', marker='>', linestyle='-')
    ]
    plt.legend(handles=legend_elements)
    
    plt.xlim(-0.2, 1.2)
    plt.ylim(0, total_height + 1)
    plt.title('Host Migrations To/From Cloudflare')
    plt.axis('off')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(VISUALIZATION_DIR, f'cloudflare_flow_{timestamp}.png')
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()

def get_cloudflare_migrations():
    """Get data about hostnames that have moved to or from Cloudflare's ASN."""
    print("DEBUG: Starting get_cloudflare_migrations()")
    try:
        conn = sqlite3.connect('dns_results.db')
        print("DEBUG: Connected to database")
        
        # Query to get all hostname-ASN associations involving Cloudflare
        migration_query = """
        WITH hostname_asns AS (
            SELECT DISTINCT
                hostname,
                asn,
                MIN(timestamp) as first_seen,
                MAX(timestamp) as last_seen
            FROM dns_results
            WHERE 
                success = 1
                AND asn IS NOT NULL
            GROUP BY hostname, asn
            ORDER BY hostname, first_seen
        ),
        migrations AS (
            SELECT 
                h1.hostname,
                h1.asn as from_asn,
                h2.asn as to_asn,
                h1.first_seen as start_time,
                h1.last_seen as end_time,
                h2.first_seen as next_start_time,
                h2.last_seen as next_end_time
            FROM hostname_asns h1
            JOIN hostname_asns h2 ON h1.hostname = h2.hostname 
                AND h2.first_seen > h1.last_seen
            WHERE h1.asn != h2.asn
                AND (h1.asn = ? OR h2.asn = ?)
        )
        SELECT *
        FROM migrations
        ORDER BY start_time DESC
        """
        
        print(f"DEBUG: Executing migration query with Cloudflare ASN: {CLOUDFLARE_ASN}")
        df_migrations = pd.read_sql_query(migration_query, conn, params=(CLOUDFLARE_ASN, CLOUDFLARE_ASN))
        print(f"DEBUG: Found {len(df_migrations)} migrations")
        
        # Get additional Cloudflare-related statistics
        cloudflare_stats_query = """
        WITH cloudflare_hosts AS (
            SELECT DISTINCT
                hostname,
                asn,
                MIN(timestamp) as first_seen,
                MAX(timestamp) as last_seen,
                COUNT(*) as total_occurrences,
                GROUP_CONCAT(DISTINCT ip_address) as ip_addresses
            FROM dns_results
            WHERE asn = ?
            GROUP BY hostname, asn
        )
        SELECT *
        FROM cloudflare_hosts
        ORDER BY last_seen DESC
        """
        
        print("DEBUG: Executing Cloudflare stats query")
        df_cloudflare_stats = pd.read_sql_query(cloudflare_stats_query, conn, params=(CLOUDFLARE_ASN,))
        print(f"DEBUG: Found {len(df_cloudflare_stats)} Cloudflare entries")
        
        # Get ASN names for reference
        asn_query = """
        SELECT DISTINCT asn, as_name
        FROM dns_results
        WHERE asn IS NOT NULL
        """
        
        print("DEBUG: Getting ASN names")
        df_asns = pd.read_sql_query(asn_query, conn)
        asn_names = dict(zip(df_asns['asn'], df_asns['as_name']))
        print(f"DEBUG: Found {len(asn_names)} unique ASNs")
        
        conn.close()
        print("DEBUG: Database connection closed")
        return df_migrations, df_cloudflare_stats, asn_names
    except Exception as e:
        print(f"ERROR in get_cloudflare_migrations: {str(e)}")
        raise

def create_migration_timeline(df, output_file='asn_migration_timeline.png'):
    if df.empty:
        print("No migrations found in the specified time period.")
        return

    plt.figure(figsize=(15, 8))
    
    # Get unique ASNs and assign them y-positions
    all_asns = sorted(list(set(df['from_asn'].unique()) | set(df['to_asn'].unique())))
    asn_positions = {asn: i for i, asn in enumerate(all_asns)}
    
    # Plot horizontal lines for each ASN
    for asn in all_asns:
        plt.axhline(y=asn_positions[asn], color='gray', alpha=0.3, linestyle='--')
        plt.text(-0.1, asn_positions[asn], f'AS{asn}', 
                transform=plt.gca().get_yaxis_transform(), 
                ha='right', va='center')
    
    # Plot migrations
    colors = plt.cm.tab20(np.linspace(0, 1, len(df['hostname'].unique())))
    for i, (_, migration) in enumerate(df.iterrows()):
        color = colors[i % len(colors)]
        start_pos = asn_positions[migration['from_asn']]
        end_pos = asn_positions[migration['to_asn']]
        
        plt.plot([migration['start_time'], migration['end_time']], 
                [start_pos, end_pos],
                '-o', color=color, alpha=0.7, label=migration['hostname'])
    
    plt.ylabel('ASN')
    plt.title('ASN Migration Timeline (Last 24 Hours)')
    plt.xticks(rotation=45)
    
    # Adjust legend
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
    plt.tight_layout()
    
    # Save to visualization directory
    output_path = os.path.join(VISUALIZATION_DIR, output_file)
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()

def create_visualizations(df_migrations, df_cloudflare_stats, asn_names):
    """Create visualizations focusing on Cloudflare migrations."""
    print("DEBUG: Starting create_visualizations()")
    try:
        if len(df_migrations) == 0 and len(df_cloudflare_stats) == 0:
            print("DEBUG: No Cloudflare-related migrations or activity found in the dataset")
            return
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        print(f"DEBUG: Using timestamp {timestamp}")
        
        # Create flow diagrams
        create_flow_diagram(df_migrations, df_cloudflare_stats, asn_names)
        create_ip_flow_diagram(df_migrations, df_cloudflare_stats, asn_names)
        
        # Create activity timeline
        if len(df_cloudflare_stats) > 0:
            print("DEBUG: Processing Cloudflare activity timeline")
            df_cloudflare_stats['first_seen'] = pd.to_datetime(df_cloudflare_stats['first_seen'])
            df_cloudflare_stats['last_seen'] = pd.to_datetime(df_cloudflare_stats['last_seen'])
            
            plt.figure(figsize=(15, 8))
            
            # Plot duration bars for each hostname
            for idx, row in df_cloudflare_stats.iterrows():
                plt.barh(y=idx, 
                        width=(row['last_seen'] - row['first_seen']).total_seconds() / 3600,
                        left=pd.Timestamp(row['first_seen']).timestamp() / 3600,
                        height=0.3,
                        label=row['hostname'])
            
            plt.yticks(range(len(df_cloudflare_stats)), df_cloudflare_stats['hostname'], fontsize=8)
            plt.xlabel('Time (hours)')
            plt.title(f'Duration of Cloudflare ASN Usage')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            output_path = os.path.join(VISUALIZATION_DIR, f'cloudflare_activity_{timestamp}.png')
            plt.savefig(output_path, bbox_inches='tight')
            plt.close()
            
            print(f"DEBUG: Saved activity timeline")
    except Exception as e:
        print(f"ERROR in create_visualizations: {str(e)}")
        raise

def print_cloudflare_summary(df_migrations, df_cloudflare_stats, asn_names):
    """Print a summary focusing on Cloudflare-related activities."""
    print("DEBUG: Starting print_cloudflare_summary()")
    try:
        print("\nCloudflare (AS13335) Migration Summary:")
        print("=" * 80)
        
        if len(df_migrations) > 0:
            # Filter migrations to only include hostnames in df_cloudflare_stats
            recent_hostnames = set(df_cloudflare_stats['hostname'])
            df_migrations = df_migrations[df_migrations['hostname'].isin(recent_hostnames)]
            
            # Analyze migrations to Cloudflare
            to_cloudflare = df_migrations[df_migrations['to_asn'] == CLOUDFLARE_ASN]
            from_cloudflare = df_migrations[df_migrations['from_asn'] == CLOUDFLARE_ASN]
            
            print(f"\nDEBUG: Found {len(to_cloudflare)} migrations TO Cloudflare")
            print("\nMigrations TO Cloudflare:")
            for _, row in to_cloudflare.iterrows():
                print(f"- {row['hostname']} from {row['from_asn'].split()[0]}")
                print(f"  Time: {row['next_start_time']}")
            
            print(f"\nDEBUG: Found {len(from_cloudflare)} migrations FROM Cloudflare")
            print("\nMigrations FROM Cloudflare:")
            for _, row in from_cloudflare.iterrows():
                print(f"- {row['hostname']} to {row['to_asn'].split()[0]}")
                print(f"  Time: {row['next_start_time']}")
        
        if len(df_cloudflare_stats) > 0:
            print("\nCloudflare Usage Statistics:")
            print(f"Total unique hostnames using Cloudflare: {len(df_cloudflare_stats)}")
            
            print("\nHostnames Using Cloudflare:")
            df_cloudflare_stats['duration'] = (pd.to_datetime(df_cloudflare_stats['last_seen']) - 
                                             pd.to_datetime(df_cloudflare_stats['first_seen']))
            
            for _, row in df_cloudflare_stats.sort_values('duration', ascending=False).iterrows():
                duration_hours = row['duration'].total_seconds() / 3600
                print(f"\n- {row['hostname']}")
                print(f"  Duration: {duration_hours:.2f} hours")
                print(f"  Total occurrences: {row['total_occurrences']}")
                print(f"  IP Addresses: {row['ip_addresses']}")
                print(f"  First seen: {row['first_seen']}")
                print(f"  Last seen: {row['last_seen']}")
        
        print("-" * 80)
    except Exception as e:
        print(f"ERROR in print_cloudflare_summary: {str(e)}")
        raise

def get_asn_migrations(conn, hours_ago=24):
    # First, get the cutoff time
    cutoff_query = "SELECT datetime('now', ?);"
    cutoff_time = pd.read_sql_query(cutoff_query, conn, params=[f'-{hours_ago} hours']).iloc[0, 0]
    print(f"Looking for migrations after: {cutoff_time}")
    
    # Debug query to show data range
    debug_query = """
    SELECT 
        MIN(timestamp) as earliest,
        MAX(timestamp) as latest,
        COUNT(DISTINCT hostname) as unique_hosts,
        COUNT(DISTINCT asn) as unique_asns,
        COUNT(*) as total_records
    FROM dns_results
    WHERE timestamp > ?;
    """
    debug_df = pd.read_sql_query(debug_query, conn, params=[cutoff_time])
    print("\nData available in time period:")
    print(debug_df)
    
    query = """
    WITH changes AS (
        SELECT 
            hostname,
            asn as from_asn,
            timestamp as start_time,
            LEAD(asn) OVER (PARTITION BY hostname ORDER BY timestamp) as to_asn,
            LEAD(timestamp) OVER (PARTITION BY hostname ORDER BY timestamp) as end_time
        FROM dns_results
        WHERE timestamp > ?
            AND asn IS NOT NULL
        ORDER BY timestamp DESC
    )
    SELECT *,
        julianday(end_time) - julianday(start_time) as duration_days
    FROM changes
    WHERE to_asn IS NOT NULL 
        AND from_asn != to_asn
    ORDER BY start_time DESC
    LIMIT 50;
    """
    
    df = pd.read_sql_query(query, conn, params=[cutoff_time])
    print(f"\nFound {len(df)} migrations in the specified time period")
    if not df.empty:
        print("\nSample of migrations found:")
        print(df[['hostname', 'from_asn', 'to_asn', 'start_time', 'end_time']].head())
    return df

def analyze_migrations(df):
    if df.empty:
        print("No migrations found in the specified time period.")
        return

    print("ASN Migration Analysis")
    print("-" * 80)
    
    # Most common migration paths
    migration_paths = df.groupby(['from_asn', 'to_asn']).size().reset_index(name='count')
    migration_paths = migration_paths.sort_values('count', ascending=False)
    
    print("\nMost Common Migration Paths:")
    for _, path in migration_paths.iterrows():
        print(f"AS{path['from_asn']} → AS{path['to_asn']}: {path['count']} migrations")
    
    # Migration timing statistics
    df['duration_hours'] = df['duration_days'] * 24
    print("\nMigration Timing Statistics:")
    print(f"Average time between migrations: {df['duration_hours'].mean():.2f} hours")
    print(f"Median time between migrations: {df['duration_hours'].median():.2f} hours")
    print(f"Minimum time between migrations: {df['duration_hours'].min():.2f} hours")
    print(f"Maximum time between migrations: {df['duration_hours'].max():.2f} hours")
    
    # Most active hostnames
    hostname_counts = df.groupby('hostname').size().sort_values(ascending=False)
    print("\nMost Active Hostnames (by number of migrations):")
    for hostname, count in hostname_counts.items():
        print(f"{hostname}: {count} migrations")
    
    # ASN Statistics
    print("\nASN Statistics:")
    source_asns = df['from_asn'].value_counts()
    dest_asns = df['to_asn'].value_counts()
    all_asns = pd.concat([source_asns, dest_asns]).index.unique()
    
    for asn in all_asns:
        sources = len(df[df['from_asn'] == asn])
        destinations = len(df[df['to_asn'] == asn])
        print(f"AS{asn}:")
        print(f"  Migrations from: {sources}")
        print(f"  Migrations to: {destinations}")
        print(f"  Net change: {destinations - sources}")

def main():
    print("\nDEBUG: Starting script execution")
    try:
        conn = sqlite3.connect('dns_results.db')
        
        # Check different time windows
        for hours in [48, 72]:
            print(f"\nAnalyzing migrations for the last {hours} hours:")
            print("=" * 50)
            
            # Get migrations for the specified time window
            migrations_df = get_asn_migrations(conn, hours)
            
            if not migrations_df.empty:
                # Create visualization
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f'asn_migration_timeline_{hours}h_{timestamp}.png'
                create_migration_timeline(migrations_df, output_file)
                
                # Analyze migrations
                analyze_migrations(migrations_df)
            else:
                print(f"No migrations found in the last {hours} hours.")
        
        conn.close()
        
        print("\nDEBUG: Script completed successfully")
    except Exception as e:
        print(f"ERROR in main: {str(e)}")
        raise

if __name__ == "__main__":
    main() 