"""
Prometheus Metrics Exporter
Exports real-time metrics from all Checkpoint components for Grafana visualization.

This is the SOURCE OF TRUTH for all metrics.
"""
from prometheus_client import Counter, Gauge, Histogram, start_http_server, generate_latest, CONTENT_TYPE_LATEST
from flask import Flask, Response
import psycopg2
import threading
import time
import sys
import os

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)

# ============================================
# PROMETHEUS METRICS DEFINITIONS
# ============================================

# CP1 - Ingestion Metrics
TRANSACTIONS_RECEIVED = Counter(
    'checkpoint_transactions_received_total',
    'Total transactions received from mempool'
)

TRANSACTIONS_IN_MEMPOOL = Gauge(
    'checkpoint_mempool_size',
    'Current number of transactions in mempool'
)

# CP2 - Feature Metrics
FEATURES_EXTRACTED = Counter(
    'checkpoint_features_extracted_total',
    'Total transaction features extracted'
)

AVG_FEE_RATE = Gauge(
    'checkpoint_avg_fee_rate',
    'Average fee rate in mempool'
)

CONGESTION_SCORE = Gauge(
    'checkpoint_congestion_score',
    'Current mempool congestion score'
)

# CP3 - ML Metrics
SPAM_DETECTIONS = Counter(
    'checkpoint_spam_detected_total',
    'Total spam transactions detected by ML'
)

AVG_SPAM_SCORE = Gauge(
    'checkpoint_avg_spam_score',
    'Average spam score across transactions'
)

ML_INFERENCE_TIME = Histogram(
    'checkpoint_ml_inference_seconds',
    'ML inference time in seconds',
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5]
)

# CP4 - RL Metrics
RL_DECISIONS = Counter(
    'checkpoint_rl_decisions_total',
    'Total RL decisions made',
    ['action']
)

RL_REWARD = Gauge(
    'checkpoint_rl_reward_avg',
    'Average RL reward'
)

# CP5 - Mitigation Metrics
THREATS_BLOCKED = Counter(
    'checkpoint_threats_blocked_total',
    'Total threats blocked by mitigation',
    ['threat_type']
)

MITIGATION_MODE = Gauge(
    'checkpoint_mitigation_mode',
    'Current mitigation mode (0=NORMAL, 1=FEE_FILTER, 2=SPAM, 3=DEFENSIVE)'
)

MIN_FEE_THRESHOLD = Gauge(
    'checkpoint_min_fee_threshold',
    'Current minimum fee threshold in gwei'
)

# CP6 - Audit Metrics
INCIDENTS_LOGGED = Counter(
    'checkpoint_incidents_logged_total',
    'Total incidents logged to INCO'
)

# CP7 - Monitoring Metrics
DRIFT_ALERTS = Counter(
    'checkpoint_drift_alerts_total',
    'Total drift alerts triggered',
    ['alert_type']
)

HEALING_ACTIONS = Counter(
    'checkpoint_healing_actions_total',
    'Total healing actions taken',
    ['action_type']
)

# System Health
SERVICE_UP = Gauge(
    'checkpoint_service_up',
    'Service health (1=up, 0=down)',
    ['service']
)

# ============================================
# DATABASE CONNECTION
# ============================================

def get_db_connection():
    try:
        return psycopg2.connect(
            host="localhost",
            database="checkpoint",
            user="cp",
            password="cp"
        )
    except Exception as e:
        print(f"[METRICS] DB connection failed: {e}")
        return None

# ============================================
# METRICS COLLECTION
# ============================================

def collect_database_metrics():
    """Collect metrics from database."""
    conn = get_db_connection()
    if not conn:
        SERVICE_UP.labels(service='postgres').set(0)
        return
    
    SERVICE_UP.labels(service='postgres').set(1)
    
    try:
        cur = conn.cursor()
        
        # Mempool size
        cur.execute("SELECT COUNT(*) FROM mempool_txs")
        count = cur.fetchone()[0]
        TRANSACTIONS_IN_MEMPOOL.set(count)
        
        # Feature count
        cur.execute("SELECT COUNT(*) FROM tx_features")
        feature_count = cur.fetchone()[0]
        FEATURES_EXTRACTED._value._value = feature_count
        
        # Get min fee, avg fee, and avg spam score from tx_features
        cur.execute("""
            SELECT 
                MIN(fee_rate) as min_fee,
                AVG(fee_rate) as avg_fee,
                AVG(spam_score) as avg_spam,
                AVG(mev_risk_score) as avg_mev,
                COUNT(CASE WHEN spam_score > 0.5 THEN 1 END) as spam_count
            FROM tx_features
            WHERE first_seen > NOW() - INTERVAL '1 hour'
        """)
        row = cur.fetchone()
        if row:
            min_fee = float(row[0]) if row[0] else 0
            avg_fee = float(row[1]) if row[1] else 0
            avg_spam = float(row[2]) if row[2] else 0
            avg_mev = float(row[3]) if row[3] else 0
            spam_count = int(row[4]) if row[4] else 0
            
            # Set the min fee threshold (actual minimum in recent txs)
            MIN_FEE_THRESHOLD.set(min_fee)
            AVG_FEE_RATE.set(avg_fee)
            AVG_SPAM_SCORE.set(avg_spam)
            
            # Update spam detections counter based on DB count
            if spam_count > 0:
                SPAM_DETECTIONS._value._value = spam_count
        
        # Congestion from mempool_features if available
        cur.execute("""
            SELECT tx_count, avg_fee_rate, congestion_score
            FROM mempool_features
            ORDER BY snapshot_time DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        if row:
            if row[2]:
                CONGESTION_SCORE.set(float(row[2]))
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"[METRICS] Collection error: {e}")

def collect_service_health():
    """Check health of all services."""
    import requests
    
    # ML Service
    try:
        resp = requests.get("http://127.0.0.1:8002/health", timeout=5)
        SERVICE_UP.labels(service='ml_service').set(1 if resp.status_code == 200 else 0)
    except:
        SERVICE_UP.labels(service='ml_service').set(0)

def metrics_collector_loop():
    """Background loop to collect metrics."""
    while True:
        try:
            collect_database_metrics()
            collect_service_health()
        except Exception as e:
            print(f"[METRICS] Loop error: {e}")
        time.sleep(5)

# ============================================
# METRICS ENDPOINT
# ============================================

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/health')
def health():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.route('/simulate')
def simulate():
    """Generate sample data for testing pie charts."""
    # Record some RL decisions for pie chart
    RL_DECISIONS.labels(action='DO_NOTHING').inc(10)
    RL_DECISIONS.labels(action='RAISE_FEE').inc(3)
    RL_DECISIONS.labels(action='DEPRIORITIZE').inc(2)
    RL_DECISIONS.labels(action='DEFENSIVE').inc(1)
    
    # Record some threat types for pie chart
    THREATS_BLOCKED.labels(threat_type='spam').inc(5)
    THREATS_BLOCKED.labels(threat_type='mev').inc(3)
    THREATS_BLOCKED.labels(threat_type='nonce_attack').inc(1)
    THREATS_BLOCKED.labels(threat_type='dust').inc(1)
    
    return {"status": "simulated", "message": "Sample data added to RL decisions and threats"}

# ============================================
# HELPER FUNCTIONS FOR OTHER MODULES
# ============================================

def record_transaction_received():
    """Record a new transaction received."""
    TRANSACTIONS_RECEIVED.inc()

def record_spam_detected(spam_score: float):
    """Record spam detection."""
    if spam_score > 0.5:
        SPAM_DETECTIONS.inc()
    AVG_SPAM_SCORE.set(spam_score)

def record_rl_decision(action: int):
    """Record RL decision."""
    action_names = ['DO_NOTHING', 'RAISE_FEE', 'DEPRIORITIZE', 'DEFENSIVE']
    RL_DECISIONS.labels(action=action_names[action]).inc()

def record_threat_blocked(threat_type: str):
    """Record a blocked threat."""
    THREATS_BLOCKED.labels(threat_type=threat_type).inc()

def record_mitigation_mode(mode: str, min_fee: int):
    """Record current mitigation state."""
    mode_values = {'NORMAL': 0, 'FEE_FILTER': 1, 'SPAM_DEPRIORITIZATION': 2, 'DEFENSIVE': 3}
    MITIGATION_MODE.set(mode_values.get(mode, 0))
    MIN_FEE_THRESHOLD.set(min_fee)

def record_incident_logged():
    """Record INCO incident logging."""
    INCIDENTS_LOGGED.inc()

def record_drift_alert(alert_type: str):
    """Record drift alert."""
    DRIFT_ALERTS.labels(alert_type=alert_type).inc()

def record_healing_action(action_type: str):
    """Record healing action."""
    HEALING_ACTIONS.labels(action_type=action_type).inc()

# ============================================
# MAIN
# ============================================

def initialize_labeled_metrics():
    """Initialize labeled metrics so Grafana pie charts have data to display."""
    # Initialize RL action labels with 0 values
    for action in ['DO_NOTHING', 'RAISE_FEE', 'DEPRIORITIZE', 'DEFENSIVE']:
        RL_DECISIONS.labels(action=action)
    
    # Initialize threat type labels with 0 values
    for threat_type in ['spam', 'mev', 'nonce_attack', 'dust']:
        THREATS_BLOCKED.labels(threat_type=threat_type)
    
    # Initialize drift alert types
    for alert_type in ['model_drift', 'congestion', 'latency']:
        DRIFT_ALERTS.labels(alert_type=alert_type)
    
    # Initialize healing action types
    for action_type in ['retrain', 'scale', 'fallback']:
        HEALING_ACTIONS.labels(action_type=action_type)
    
    print("[METRICS] Initialized labeled metrics for Grafana")

if __name__ == '__main__':
    print("=" * 60)
    print("[METRICS] Prometheus Exporter Starting...")
    print("=" * 60)
    print("[METRICS] Endpoints:")
    print("  - http://localhost:9100/metrics (Prometheus)")
    print("  - http://localhost:9100/health")
    print("=" * 60)
    
    # Initialize labeled metrics for pie charts
    initialize_labeled_metrics()
    
    # Start background collector
    collector_thread = threading.Thread(target=metrics_collector_loop, daemon=True)
    collector_thread.start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=9100)

