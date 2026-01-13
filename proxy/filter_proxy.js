/**
 * Nodescrypt Filter Proxy
 * HTTP/WebSocket proxy for transaction filtering and mitigation
 * 
 * Actions:
 * - PASS: Forward immediately
 * - DELAY: Add delay before forwarding
 * - DROP: Reject transaction
 * - ESCALATE: Flag for manual review
 */

const express = require("express");
const cors = require("cors");
const axios = require("axios");
const { ethers } = require("ethers");

const app = express();
app.use(cors());
app.use(express.json());

// Configuration
const PORT = process.env.PROXY_PORT || 8545;
const UPSTREAM_RPC = process.env.UPSTREAM_RPC || "https://eth.llamarpc.com";
const ML_SERVICE = process.env.ML_SERVICE || "http://127.0.0.1:8002";
const ENABLE_FILTERING = process.env.ENABLE_FILTERING === "true";

// Stats
const stats = {
    requests: 0,
    passed: 0,
    delayed: 0,
    dropped: 0,
    escalated: 0,
    errors: 0,
    start_time: Date.now()
};

// Action constants
const ACTIONS = {
    PASS: 0,
    DELAY: 1,
    DROP: 2,
    ESCALATE: 3
};

/**
 * Analyze transaction for risk
 */
async function analyzeTransaction(tx) {
    try {
        // Extract basic features
        const features = {
            value: parseFloat(tx.value || "0"),
            gas_price: parseFloat(tx.gasPrice || tx.maxFeePerGas || "0"),
            data_size: tx.data ? (tx.data.length - 2) / 2 : 0,
            to: tx.to?.toLowerCase() || null
        };

        // Call ML service if available
        try {
            const response = await axios.post(`${ML_SERVICE}/predict/spam`, {
                features: [
                    features.gas_price / 1e9,
                    features.value / 1e18,
                    features.data_size,
                    0, // nonce_gap
                    1, // sender_tx_count
                    features.gas_price / 1e9, // avg_fee
                ]
            }, { timeout: 100 });

            return {
                spam_score: response.data.prediction || 0,
                mev_risk: 0,
                risk_level: response.data.prediction > 0.7 ? "HIGH" : "LOW"
            };
        } catch (e) {
            // ML service unavailable, use heuristics
            return {
                spam_score: features.gas_price < 1e9 ? 0.7 : 0.1,
                mev_risk: 0,
                risk_level: "UNKNOWN"
            };
        }
    } catch (e) {
        return { spam_score: 0, mev_risk: 0, risk_level: "ERROR" };
    }
}

/**
 * Decide action based on analysis
 */
function decideAction(analysis) {
    if (!ENABLE_FILTERING) {
        return ACTIONS.PASS;
    }

    if (analysis.spam_score > 0.9) {
        return ACTIONS.DROP;
    }

    if (analysis.spam_score > 0.7) {
        return ACTIONS.DELAY;
    }

    if (analysis.mev_risk > 0.8) {
        return ACTIONS.ESCALATE;
    }

    return ACTIONS.PASS;
}

/**
 * Forward request to upstream RPC
 */
async function forwardRequest(body) {
    const response = await axios.post(UPSTREAM_RPC, body, {
        headers: { "Content-Type": "application/json" },
        timeout: 30000
    });
    return response.data;
}

/**
 * Sleep utility
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Handle JSON-RPC request
 */
async function handleRequest(req, res) {
    stats.requests++;

    const { method, params, id, jsonrpc } = req.body;

    // Non-transaction methods: forward directly
    if (method !== "eth_sendRawTransaction" && method !== "eth_sendTransaction") {
        try {
            const result = await forwardRequest(req.body);
            return res.json(result);
        } catch (e) {
            stats.errors++;
            return res.json({ jsonrpc: "2.0", id, error: { code: -32000, message: e.message } });
        }
    }

    // Transaction methods: analyze and filter
    try {
        const rawTx = params[0];

        // Decode transaction
        let tx;
        try {
            tx = ethers.Transaction.from(rawTx);
        } catch (e) {
            // Can't decode, forward anyway
            const result = await forwardRequest(req.body);
            stats.passed++;
            return res.json(result);
        }

        // Analyze
        const analysis = await analyzeTransaction(tx);
        const action = decideAction(analysis);

        // Execute action
        switch (action) {
            case ACTIONS.DROP:
                stats.dropped++;
                console.log(`[PROXY] DROPPED tx from ${tx.from?.slice(0, 10)}... spam=${analysis.spam_score.toFixed(2)}`);
                return res.status(403).json({
                    jsonrpc: "2.0",
                    id,
                    error: {
                        code: -32003,
                        message: "Transaction rejected by Nodescrypt filter"
                    }
                });

            case ACTIONS.DELAY:
                stats.delayed++;
                console.log(`[PROXY] DELAYED tx from ${tx.from?.slice(0, 10)}... (500ms)`);
                await sleep(500);
                break;

            case ACTIONS.ESCALATE:
                stats.escalated++;
                console.log(`[PROXY] ESCALATED tx from ${tx.from?.slice(0, 10)}... (high MEV risk)`);
                // In production: notify operators, but still forward
                break;

            default:
                stats.passed++;
        }

        // Forward to upstream
        const result = await forwardRequest(req.body);
        return res.json(result);

    } catch (e) {
        stats.errors++;
        console.error("[PROXY] Error:", e.message);
        return res.json({ jsonrpc: "2.0", id, error: { code: -32000, message: e.message } });
    }
}

// RPC endpoint
app.post("/", handleRequest);
app.post("/rpc", handleRequest);

// Health check
app.get("/health", (req, res) => {
    res.json({
        status: "healthy",
        filtering: ENABLE_FILTERING,
        stats: stats,
        uptime: (Date.now() - stats.start_time) / 1000
    });
});

// Stats endpoint
app.get("/stats", (req, res) => {
    const uptime = (Date.now() - stats.start_time) / 1000;
    res.json({
        ...stats,
        uptime,
        requests_per_second: stats.requests / uptime,
        drop_rate: stats.requests > 0 ? stats.dropped / stats.requests : 0
    });
});

// Toggle filtering
app.post("/admin/toggle-filter", (req, res) => {
    const { enabled } = req.body;
    if (typeof enabled === "boolean") {
        process.env.ENABLE_FILTERING = enabled ? "true" : "false";
        res.json({ filtering: enabled });
    } else {
        res.status(400).json({ error: "enabled must be boolean" });
    }
});

// Start server
app.listen(PORT, () => {
    console.log("============================================================");
    console.log("[NODESCRYPT] Filter Proxy Starting...");
    console.log("============================================================");
    console.log(`[NODESCRYPT] Listen: http://0.0.0.0:${PORT}`);
    console.log(`[NODESCRYPT] Upstream: ${UPSTREAM_RPC}`);
    console.log(`[NODESCRYPT] ML Service: ${ML_SERVICE}`);
    console.log(`[NODESCRYPT] Filtering: ${ENABLE_FILTERING ? "ENABLED" : "DISABLED (monitor-only)"}`);
    console.log("============================================================");

    // Stats logging
    setInterval(() => {
        console.log(`[NODESCRYPT] Stats: reqs=${stats.requests} passed=${stats.passed} dropped=${stats.dropped} delayed=${stats.delayed}`);
    }, 30000);
});

module.exports = app;
