import React, { useEffect, useState, useRef } from 'react';
import './RealTimeMonitor.css';

const API_URL = 'https://mara-monogrammatic-shiftily.ngrok-free.dev/api/dashboard';
const HISTORY_LENGTH = 60; // Keep last 60 data points for graphs

const METRICS_CONFIG = {
    mempoolSize: {
        key: 'mempoolSize',
        label: 'Mempool Size',
        icon: '📊',
        color: '#3673f5',
        colorClass: 'primary'
    },
    threatsBlocked: {
        key: 'threatsBlocked',
        label: 'Threats Blocked',
        icon: '🛡️',
        color: '#10b981',
        colorClass: 'success'
    },
    totalThreats: {
        key: 'totalThreats',
        label: 'Total Threats',
        icon: '⚠️',
        color: '#f59e0b',
        colorClass: 'warning'
    },
    rlDecisions: {
        key: 'rlDecisions',
        label: 'RL Decisions',
        icon: '🤖',
        color: '#8b5cf6',
        colorClass: 'purple'
    }
};

const RealTimeMonitor = () => {
    const [metrics, setMetrics] = useState({
        status: 'connecting',
        mempoolSize: 0,
        threatsBlocked: 0,
        systemMode: 'INITIALIZING',
        rlDecisions: 0,
        totalThreats: 0,
        spamScore: 0,
        timestamp: null
    });
    const [history, setHistory] = useState({
        mempoolSize: [],
        threatsBlocked: [],
        totalThreats: [],
        rlDecisions: []
    });
    const [selectedMetric, setSelectedMetric] = useState('mempoolSize');
    const [isConnected, setIsConnected] = useState(false);
    const [error, setError] = useState(null);
    const intervalRef = useRef(null);

    const fetchMetrics = async () => {
        try {
            const response = await fetch(API_URL, {
                headers: {
                    'ngrok-skip-browser-warning': 'true'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            const newMetrics = {
                status: data.status || 'unknown',
                mempoolSize: data.mempool_size || 0,
                threatsBlocked: data.threats_blocked || 0,
                systemMode: data.system_mode || 'UNKNOWN',
                rlDecisions: data.rl_decisions || 0,
                totalThreats: data.total_threats || 0,
                spamScore: data.ml_scores?.spam_score || 0,
                timestamp: data.timestamp || new Date().toISOString()
            };

            setMetrics(newMetrics);

            // Update history for graphs
            setHistory(prev => ({
                mempoolSize: [...prev.mempoolSize, newMetrics.mempoolSize].slice(-HISTORY_LENGTH),
                threatsBlocked: [...prev.threatsBlocked, newMetrics.threatsBlocked].slice(-HISTORY_LENGTH),
                totalThreats: [...prev.totalThreats, newMetrics.totalThreats].slice(-HISTORY_LENGTH),
                rlDecisions: [...prev.rlDecisions, newMetrics.rlDecisions].slice(-HISTORY_LENGTH)
            }));

            setIsConnected(true);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch metrics:', err);
            setIsConnected(false);
            setError(err.message);
        }
    };

    useEffect(() => {
        // Initial fetch
        fetchMetrics();

        // Set up polling every 1 second
        intervalRef.current = setInterval(fetchMetrics, 1000);

        // Cleanup on unmount
        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, []);

    const formatNumber = (num) => {
        return num.toLocaleString();
    };

    const formatTime = (timestamp) => {
        if (!timestamp) return '--:--:--';
        const date = new Date(timestamp);
        // Add 5 hours 30 minutes for IST
        date.setTime(date.getTime() + (5 * 60 + 30) * 60 * 1000);
        return date.toLocaleTimeString('en-IN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });
    };

    // Generate SVG path for sparkline (relative to 0)
    const generateSparklinePath = (data, width, height, useZeroBase = false) => {
        if (data.length < 2) return '';

        const min = useZeroBase ? 0 : Math.min(...data);
        const max = Math.max(...data);
        const range = max - min || 1;

        const points = data.map((value, index) => {
            const x = (index / (data.length - 1)) * width;
            const y = height - ((value - min) / range) * height * 0.9 - height * 0.05;
            return `${x},${y}`;
        });

        return `M ${points.join(' L ')}`;
    };

    // Generate area fill path
    const generateAreaPath = (data, width, height, useZeroBase = false) => {
        if (data.length < 2) return '';

        const linePath = generateSparklinePath(data, width, height, useZeroBase);
        if (!linePath) return '';

        return `${linePath} L ${width},${height} L 0,${height} Z`;
    };

    const LargeGraph = ({ data, color, label }) => {
        const width = 800;
        const height = 200;

        // Dynamic min/max based on actual data for better visualization
        const dataMin = data.length > 0 ? Math.min(...data) : 0;
        const dataMax = data.length > 0 ? Math.max(...data) : 0;
        // Add 5% padding to the range for better visualization
        const range = dataMax - dataMin || 1;
        const min = Math.max(0, dataMin - range * 0.05);
        const max = dataMax + range * 0.05;
        const current = data.length > 0 ? data[data.length - 1] : 0;

        // Generate path with dynamic range
        const generateDynamicPath = (data) => {
            if (data.length < 2) return '';
            const effectiveRange = max - min || 1;
            const points = data.map((value, index) => {
                const x = (index / (data.length - 1)) * width;
                const y = height - ((value - min) / effectiveRange) * height * 0.9 - height * 0.05;
                return `${x},${y}`;
            });
            return `M ${points.join(' L ')}`;
        };

        const generateDynamicAreaPath = (data) => {
            const linePath = generateDynamicPath(data);
            if (!linePath) return '';
            return `${linePath} L ${width},${height} L 0,${height} Z`;
        };

        return (
            <div className="large-graph-container">
                <div className="graph-labels">
                    <span className="graph-max">{formatNumber(Math.round(max))}</span>
                    <span className="graph-mid">{formatNumber(Math.round((max + min) / 2))}</span>
                    <span className="graph-min">{formatNumber(Math.round(min))}</span>
                </div>
                <svg className="large-graph" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
                    <defs>
                        <linearGradient id="largeGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stopColor={color} stopOpacity="0.4" />
                            <stop offset="100%" stopColor={color} stopOpacity="0.05" />
                        </linearGradient>
                    </defs>
                    {/* Grid lines */}
                    {[0, 1, 2, 3, 4].map(i => (
                        <line
                            key={i}
                            x1="0"
                            y1={height * i / 4}
                            x2={width}
                            y2={height * i / 4}
                            stroke="rgba(255,255,255,0.05)"
                            strokeWidth="1"
                        />
                    ))}
                    {/* Area fill */}
                    <path
                        d={generateDynamicAreaPath(data)}
                        fill="url(#largeGradient)"
                    />
                    {/* Line */}
                    <path
                        d={generateDynamicPath(data)}
                        fill="none"
                        stroke={color}
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />
                    {/* Current value dot */}
                    {data.length > 0 && (
                        <circle
                            cx={width}
                            cy={height - ((current - min) / (max - min || 1)) * height * 0.9 - height * 0.05}
                            r="6"
                            fill={color}
                        />
                    )}
                </svg>
            </div>
        );
    };

    const selectedConfig = METRICS_CONFIG[selectedMetric];

    return (
        <section className="realtime-monitor section-padding">
            <div className="container">
                <div className="section-header">
                    <span className="section-tag">LIVE MONITORING</span>
                    <h2>
                        Real-Time <span className="gradient-text">Blockchain Metrics</span>
                    </h2>
                    <p className="section-subtitle">
                        Live data stream from our AI-powered defense system
                    </p>
                </div>

                {/* Connection Status */}
                <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
                    <div className="status-indicator"></div>
                    <span>{isConnected ? 'Connected to Live Feed' : 'Connecting...'}</span>
                    {error && <span className="error-msg">({error})</span>}
                </div>

                {/* 4 Small Metric Cards */}
                <div className="metrics-row">
                    {Object.values(METRICS_CONFIG).map((config) => (
                        <div
                            key={config.key}
                            className={`metric-card-small ${config.colorClass} ${selectedMetric === config.key ? 'selected' : ''}`}
                            onClick={() => setSelectedMetric(config.key)}
                        >
                            <div className="card-header">
                                <span className="card-icon">{config.icon}</span>
                            </div>
                            <div className="card-value">{formatNumber(metrics[config.key])}</div>
                            <div className="card-label">{config.label}</div>
                        </div>
                    ))}
                </div>

                {/* Large Graph Card */}
                <div className={`graph-card ${selectedConfig.colorClass}`}>
                    <div className="graph-card-header">
                        <span className="graph-icon">{selectedConfig.icon}</span>
                        <h3>{selectedConfig.label}</h3>
                        <span className="graph-value">{formatNumber(metrics[selectedMetric])}</span>
                    </div>
                    <LargeGraph
                        data={history[selectedMetric]}
                        color={selectedConfig.color}
                        label={selectedConfig.label}
                    />
                </div>

                {/* Footer: Status, System Mode, Last Updated */}
                <div className="last-updated">
                    <span className="update-label">Status:</span>
                    <span className={`status-badge status-${metrics.status}`}>
                        {metrics.status.toUpperCase()}
                    </span>
                    <span className="update-label">System Mode:</span>
                    <span className={`system-mode mode-${metrics.systemMode.toLowerCase()}`}>
                        {metrics.systemMode}
                    </span>
                    <span className="update-label">Last Updated:</span>
                    <span className="update-time">{formatTime(metrics.timestamp)}</span>
                </div>
            </div>
        </section>
    );
};

export default RealTimeMonitor;
