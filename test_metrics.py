"""
Quick script to test populating metrics for pie charts
Run this against the running metrics exporter
"""
import requests

# Since we can't directly modify the running exporter's metrics,
# we need to import and use the same prometheus_client registry
# This won't work across processes - the metrics are per-process

# Instead, we'll use the approach of making the flask app handle this
# by creating a quick Flask endpoint test

# For now, let's verify the metrics endpoint is working
response = requests.get("http://localhost:9100/metrics")
print("Metrics endpoint status:", response.status_code)

# Check for specific metrics
if "checkpoint_rl_decisions_total" in response.text:
    print("RL decisions metric found")
else:
    print("RL decisions metric NOT found")

if "checkpoint_threats_blocked_total" in response.text:
    print("Threats blocked metric found")
else:
    print("Threats blocked metric NOT found")

# Print relevant lines
for line in response.text.split('\n'):
    if 'rl_decisions' in line or 'threats_blocked' in line:
        print(line)
