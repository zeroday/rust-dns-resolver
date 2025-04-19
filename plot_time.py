#!/usr/bin/env python3

import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime
import os

def plot_time_series():
    # Connect to database
    conn = sqlite3.connect('dns_results.db')
    cursor = conn.cursor()

    try:
        # Get data
        cursor.execute("""
            SELECT datetime(timestamp) as time, status_code, COUNT(*) as count 
            FROM status 
            WHERE timestamp IS NOT NULL
            GROUP BY datetime(timestamp), status_code 
            ORDER BY datetime(timestamp)
        """)
        data = cursor.fetchall()

        if not data:
            print("No data found in the status table")
            return

        # Organize data by status code
        status_codes = {}
        for time_str, code, count in data:
            if time_str and code is not None:  # Skip NULL values
                if code not in status_codes:
                    status_codes[code] = {'times': [], 'counts': []}
                try:
                    time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                    status_codes[code]['times'].append(time)
                    status_codes[code]['counts'].append(count)
                except ValueError:
                    print(f"Warning: Could not parse timestamp: {time_str}")

        if not status_codes:
            print("No valid data found after filtering")
            return

        # Create plot
        plt.figure(figsize=(15, 8))

        # Plot each status code
        for code in sorted(status_codes.keys()):
            if status_codes[code]['times']:  # Only plot if we have data
                plt.plot(status_codes[code]['times'], 
                        status_codes[code]['counts'],
                        label=f'Status {code}',
                        marker='o' if len(status_codes[code]['times']) < 50 else None)

        plt.title('HTTP Status Codes Over Time')
        plt.xlabel('Time')
        plt.ylabel('Number of Checks')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Create visualizations directory if it doesn't exist
        if not os.path.exists('visualizations'):
            os.makedirs('visualizations')

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'visualizations/status_timeline_{timestamp}.png'

        # Save plot
        plt.savefig(filename)
        print(f"\nPlot saved as {filename}")

        # Print statistics
        print("\nStatus code statistics:")
        for code in sorted(status_codes.keys()):
            total = sum(status_codes[code]['counts'])
            print(f"Status {code}: {total} checks")

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    plot_time_series() 