#!/usr/bin/env python3

import sqlite3
import pandas as pd
from datetime import datetime
import os

def generate_cloudflare_csv():
    # Check if database exists
    if not os.path.exists('dns_results.db'):
        print("Error: Database file dns_results.db not found")
        return

    try:
        # Connect to the database
        conn = sqlite3.connect('dns_results.db')
        
        # Query to get Cloudflare-related DNS results
        query = """
        SELECT hostname, ip_address, asn, as_name, timestamp
        FROM dns_results
        WHERE as_name LIKE '%Cloudflare%'
        ORDER BY timestamp DESC
        """
        
        # Read data into pandas DataFrame
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("No Cloudflare DNS results found in the database")
            return
            
        # Generate filename with current date
        current_date = datetime.now().strftime('%Y%m%d')
        filename = f'cloudflare-{current_date}.csv'
        
        # Save to CSV
        df.to_csv(filename, index=False)
        print(f"Successfully generated {filename} with {len(df)} records")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    generate_cloudflare_csv() 