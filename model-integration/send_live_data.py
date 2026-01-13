"""
Universal Live Data Sender for NodesCrypt
Send ANY type of live data from your model to the website

Supported data types:
- attack: Security attacks and threats
- metric: System metrics (CPU, memory, network, etc.)
- log: General logs and events
- status: System status updates
- alert: Custom alerts

Usage:
    from send_live_data import send_live_data
    
    # Send an attack
    send_live_data(
        data_type="attack",
        attack_type="DDoS",
        severity="high",
        source_ip="192.168.1.100",
        target="node-5",
        status="blocked",
        details="Attack blocked successfully"
    )
    
    # Send a metric
    send_live_data(
        data_type="metric",
        metric_name="CPU Usage",
        value=85.5,
        unit="%",
        severity="high"
    )
    
    # Send a log
    send_live_data(
        data_type="log",
        message="Model training completed",
        accuracy=0.95,
        severity="info"
    )
"""

import requests
import json
from datetime import datetime
import time

# UPDATE THIS URL when you deploy your server to cloud
# For local testing: http://localhost:3001
# For cloud: https://your-server-url.com
SERVER_URL = "http://localhost:3001/api/live-data"

def send_live_data(data_type, severity="info", **kwargs):
    """
    Send any type of live data to the NodesCrypt website
    
    Args:
        data_type (str): Type of data ("attack", "metric", "log", "status", "alert")
        severity (str): Severity level ("low", "medium", "high", "critical", "info")
        **kwargs: Any additional data fields specific to your data type
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    # Prepare data payload
    data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "type": data_type,
        "severity": severity,
        **kwargs  # Include all additional fields
    }
    
    try:
        # Send HTTPS POST request
        response = requests.post(
            SERVER_URL,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"✅ {data_type} data sent successfully")
            return True
        else:
            print(f"❌ Failed to send data. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending data: {e}")
        return False


# Example usage and testing
if __name__ == "__main__":
    print("🚀 NodesCrypt Universal Live Data Sender")
    print(f"📡 Server URL: {SERVER_URL}")
    print("-" * 50)
    
    # Test with different types of data
    print("\n📊 Sending test data...")
    
    # 1. Attack data
    send_live_data(
        data_type="attack",
        attack_type="DDoS",
        severity="high",
        source_ip="192.168.1.100",
        target="node-5",
        status="blocked",
        details="Detected 10000 req/s from single source"
    )
    time.sleep(1)
    
    # 2. Metric data
    send_live_data(
        data_type="metric",
        metric_name="CPU Usage",
        value=85.5,
        unit="%",
        severity="high"
    )
    time.sleep(1)
    
    # 3. Another metric
    send_live_data(
        data_type="metric",
        metric_name="Network Throughput",
        value=1250,
        unit="Mbps",
        severity="info"
    )
    time.sleep(1)
    
    # 4. Log data
    send_live_data(
        data_type="log",
        message="Model training completed successfully",
        accuracy=0.95,
        epochs=100,
        severity="info"
    )
    time.sleep(1)
    
    # 5. Status update
    send_live_data(
        data_type="status",
        message="All nodes operational",
        active_nodes=12,
        total_nodes=12,
        severity="info"
    )
    time.sleep(1)
    
    # 6. Alert
    send_live_data(
        data_type="alert",
        message="High memory usage detected",
        memory_usage=92,
        threshold=90,
        severity="medium"
    )
    
    print("\n✅ Test complete!")
    print("\n💡 To use with your model:")
    print("1. Import: from send_live_data import send_live_data")
    print("2. Call send_live_data() with your data type and fields")
    print("3. All data will appear on the website in real-time!")
