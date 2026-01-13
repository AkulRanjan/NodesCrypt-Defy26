"""
Real-Time Attack Data Sender
This script sends attack detection data from your model to the NodesCrypt website.

Usage:
1. Update SERVER_URL with your deployed server URL (or localhost for testing)
2. Run this script on the system where your model is running
3. Call send_attack_data() whenever your model detects an attack

Example:
    send_attack_data(
        attack_type="DDoS",
        severity="high",
        source_ip="192.168.1.100",
        target="node-5",
        status="blocked",
        details="Detected 10000 req/s from single source"
    )
"""

import requests
import json
from datetime import datetime
import time

# UPDATE THIS URL when you deploy your server to cloud
# For local testing: http://localhost:3001
# For cloud: https://your-server-url.com
SERVER_URL = "http://localhost:3001/api/attack-data"

def send_attack_data(attack_type, severity, source_ip, target, status, details):
    """
    Send attack data to the NodesCrypt website
    
    Args:
        attack_type (str): Type of attack (e.g., "DDoS", "Malware", "Intrusion")
        severity (str): Severity level ("low", "medium", "high", "critical")
        source_ip (str): Source IP address
        target (str): Target node/system
        status (str): Status ("detected", "blocked", "mitigated")
        details (str): Additional details about the attack
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    # Prepare data payload
    data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "attack_type": attack_type,
        "severity": severity,
        "source_ip": source_ip,
        "target": target,
        "status": status,
        "details": details
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
            print(f"✅ Attack data sent successfully: {attack_type} - {severity}")
            return True
        else:
            print(f"❌ Failed to send data. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending data: {e}")
        return False


def parse_and_send_from_output(output_line):
    """
    Parse your model's command prompt output and send to website
    
    Customize this function based on your model's output format
    
    Example output format:
    "ATTACK DETECTED | Type: DDoS | Severity: HIGH | Source: 192.168.1.100 | Target: node-5 | Status: BLOCKED"
    """
    
    # Example parsing logic - CUSTOMIZE THIS FOR YOUR MODEL'S OUTPUT
    try:
        if "ATTACK DETECTED" in output_line:
            parts = output_line.split("|")
            
            attack_type = parts[1].split(":")[1].strip() if len(parts) > 1 else "Unknown"
            severity = parts[2].split(":")[1].strip().lower() if len(parts) > 2 else "medium"
            source_ip = parts[3].split(":")[1].strip() if len(parts) > 3 else "Unknown"
            target = parts[4].split(":")[1].strip() if len(parts) > 4 else "Unknown"
            status = parts[5].split(":")[1].strip().lower() if len(parts) > 5 else "detected"
            
            send_attack_data(
                attack_type=attack_type,
                severity=severity,
                source_ip=source_ip,
                target=target,
                status=status,
                details=output_line
            )
    except Exception as e:
        print(f"Error parsing output: {e}")


# Example usage and testing
if __name__ == "__main__":
    print("🚀 NodesCrypt Attack Data Sender")
    print(f"📡 Server URL: {SERVER_URL}")
    print("-" * 50)
    
    # Test with sample data
    print("\n📊 Sending test attack data...")
    
    test_attacks = [
        {
            "attack_type": "DDoS",
            "severity": "high",
            "source_ip": "192.168.1.100",
            "target": "node-5",
            "status": "blocked",
            "details": "Detected 10000 req/s from single source"
        },
        {
            "attack_type": "Malware",
            "severity": "critical",
            "source_ip": "10.0.0.45",
            "target": "node-2",
            "status": "quarantined",
            "details": "Suspicious binary detected in transaction payload"
        },
        {
            "attack_type": "Intrusion",
            "severity": "medium",
            "source_ip": "172.16.0.88",
            "target": "node-7",
            "status": "monitoring",
            "details": "Unusual authentication pattern detected"
        }
    ]
    
    for attack in test_attacks:
        send_attack_data(**attack)
        time.sleep(2)  # Wait 2 seconds between sends
    
    print("\n✅ Test complete!")
    print("\n💡 To use with your model:")
    print("1. Import this module: from send_attack_data import send_attack_data")
    print("2. Call send_attack_data() when your model detects an attack")
    print("3. Or customize parse_and_send_from_output() to parse your model's output")
