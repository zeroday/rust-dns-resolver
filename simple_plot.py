#!/usr/bin/env python3

import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import sys

def create_plot():
    try:
        # Connect to database
        conn = sqlite3.connect('dns_results.db')
        
        # Get data using pandas (handles datetime conversion automatically)
        query = """
            SELECT 
                datetime(timestamp) as time,
                status_code,
                COUNT(*) as count 
            FROM status 
            WHERE status_code IS NOT NULL
            GROUP BY datetime(timestamp), status_code 
            ORDER BY datetime(timestamp)
        """
        df = pd.read_sql_query(query, conn, parse_dates=['time'])
        
        if len(df) == 0:
            print("No data found in the status table")
            return False
            
        # Create plot
        plt.figure(figsize=(15, 8))
        
        # Plot each status code
        for code in sorted(df['status_code'].unique()):
            code_data = df[df['status_code'] == code]
            label = f'Status {code}'
            if code >= 200 and code < 300:
                label += ' (Success)'
            elif code >= 300 and code < 400:
                label += ' (Redirect)'
            elif code >= 400 and code < 500:
                label += ' (Client Error)'
            elif code >= 500:
                label += ' (Server Error)'
                
            plt.plot(code_data['time'], 
                    code_data['count'],
                    label=label,
                    marker='o' if len(code_data) < 50 else None,
                    linestyle='-' if code < 400 else '--')  # Dashed lines for error codes
        
        plt.title('HTTP Status Codes Over Time')
        plt.xlabel('Time')
        plt.ylabel('Number of Checks')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        
        # Rotate and align the tick labels so they look better
        plt.gcf().autofmt_xdate()
        
        # Use tight_layout with a larger right margin for the legend
        plt.tight_layout(rect=[0, 0, 0.85, 1])
        
        # Save plot
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'status_timeline_{timestamp}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Plot saved as {filename}")
        
        # Print summary statistics
        print("\nStatus Code Summary:")
        print("-" * 50)
        summary = df.groupby('status_code')['count'].agg(['count', 'sum', 'mean', 'max'])
        summary.columns = ['Number of Checks', 'Total Responses', 'Average per Time', 'Max at Once']
        print(summary)
        
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        plt.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = create_plot()
    sys.exit(0 if success else 1) 