#!/usr/bin/env python3

import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime

# Connect to database
conn = sqlite3.connect('dns_results.db')
cursor = conn.cursor()

# Get data
cursor.execute("""
    SELECT datetime(timestamp) as time, status_code, COUNT(*) as count 
    FROM status 
    GROUP BY datetime(timestamp), status_code 
    ORDER BY datetime(timestamp)
""")
data = cursor.fetchall()

# Organize data by status code
status_codes = {}
for time, code, count in data:
    if code not in status_codes:
        status_codes[code] = {'times': [], 'counts': []}
    status_codes[code]['times'].append(datetime.strptime(time, '%Y-%m-%d %H:%M:%S'))
    status_codes[code]['counts'].append(count)

# Create plot
plt.figure(figsize=(15, 8))

# Plot each status code
for code in sorted(status_codes.keys()):
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

# Save plot
plt.savefig('status_timeline.png')
print("Plot saved as status_timeline.png")

# Close connection
conn.close() 