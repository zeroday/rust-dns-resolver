#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Read the CSV file
df = pd.read_csv('status_data.csv', names=['timestamp', 'status_code', 'count'], sep='|')
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Create the plot
plt.figure(figsize=(15, 8))

# Plot each status code as a separate line
for status in sorted(df['status_code'].unique()):
    status_data = df[df['status_code'] == status]
    plt.plot(status_data['timestamp'], status_data['count'], 
            label=f'Status {status}',
            marker='o' if len(status_data) < 50 else None,
            linewidth=2 if status == 200 else 1)

plt.title('HTTP Status Codes Over Time')
plt.xlabel('Time')
plt.ylabel('Number of Checks')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, alpha=0.3)

# Rotate x-axis labels for better readability
plt.xticks(rotation=45)

# Adjust layout to prevent label cutoff
plt.tight_layout()

# Save the plot
plt.savefig('status_timeline.png', bbox_inches='tight', dpi=300)
print("\nTimeline visualization saved as status_timeline.png")

# Print some statistics
print("\nTime range of data:")
print(f"Start: {df['timestamp'].min()}")
print(f"End: {df['timestamp'].max()}")
print(f"\nTotal unique timestamps: {df['timestamp'].nunique()}")
print(f"Total status codes tracked: {df['status_code'].nunique()}") 