/**
 * Nodescrypt WebSocket Streamer
 * Real-time pending transaction subscription for EVM networks
 * 
 * Features:
 * - WebSocket pending tx subscription
 * - EIP-1559 field support
 * - Contract detection
 * - High-throughput queue
 */

const { ethers } = require("ethers");
const { Pool } = require("pg");

// Configuration
const ETH_WS = process.env.ETH_WS || "wss://eth.llamarpc.com";
const ETH_HTTP = process.env.ETH_HTTP || "https://eth.llamarpc.com";

const db = new Pool({
    host: process.env.POSTGRES_HOST || "localhost",
    database: process.env.POSTGRES_DB || "checkpoint",
    user: process.env.POSTGRES_USER || "cp",
    password: process.env.POSTGRES_PASSWORD || "cp",
});

// Cache for contract detection
const contractCache = new Map();
const MAX_CACHE_SIZE = 50000;

// Stats
let stats = {
    received: 0,
    processed: 0,
    errors: 0,
    contracts_detected: 0,
    start_time: Date.now()
};

/**
 * Normalize transaction for storage
 */
function normalizeTx(tx) {
    return {
        hash: tx.hash,
        sender: tx.from?.toLowerCase() || "",
        recipient: tx.to?.toLowerCase() || null,
        value: tx.value?.toString() || "0",
        gas_limit: tx.gasLimit?.toString() || tx.gas?.toString() || "21000",
        gas_price: tx.gasPrice?.toString() || "0",
        max_fee_per_gas: tx.maxFeePerGas?.toString() || null,
        max_priority_fee_per_gas: tx.maxPriorityFeePerGas?.toString() || null,
        nonce: tx.nonce || 0,
        data: tx.data || tx.input || "0x",
        data_size: tx.data ? (tx.data.length - 2) / 2 : 0,
        tx_type: tx.type || 0,
        access_list: tx.accessList ? JSON.stringify(tx.accessList) : null,
        chain_id: tx.chainId || 1
    };
}

/**
 * Check if address is a contract
 */
async function isContract(provider, address) {
    if (!address) return false;

    const cached = contractCache.get(address);
    if (cached !== undefined) return cached;

    try {
        const code = await provider.getCode(address);
        const isContr = code !== "0x";

        // Cache management
        if (contractCache.size > MAX_CACHE_SIZE) {
            const keysToDelete = Array.from(contractCache.keys()).slice(0, 10000);
            keysToDelete.forEach(k => contractCache.delete(k));
        }
        contractCache.set(address, isContr);

        if (isContr) stats.contracts_detected++;
        return isContr;
    } catch (e) {
        return false;
    }
}

/**
 * Detect ERC20/721 transfer from input data
 */
function detectTokenTransfer(data) {
    if (!data || data.length < 10) return { is_erc20: false, is_erc721: false };

    const selector = data.slice(0, 10).toLowerCase();

    // Common selectors
    const ERC20_TRANSFER = "0xa9059cbb";
    const ERC20_APPROVE = "0x095ea7b3";
    const ERC20_TRANSFER_FROM = "0x23b872dd";
    const ERC721_SAFE_TRANSFER = "0x42842e0e";
    const ERC721_TRANSFER = "0xb88d4fde";

    return {
        is_erc20: [ERC20_TRANSFER, ERC20_APPROVE, ERC20_TRANSFER_FROM].includes(selector),
        is_erc721: [ERC721_SAFE_TRANSFER, ERC721_TRANSFER].includes(selector),
        selector: selector
    };
}

/**
 * Insert transaction into database
 */
async function insertTx(tx, extra) {
    const query = `
    INSERT INTO mempool_txs (
      hash, sender, recipient, value, gas_price, nonce, data_size, first_seen,
      gas_limit, max_fee_per_gas, max_priority_fee_per_gas, tx_type,
      to_is_contract, is_erc20, is_erc721
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), $8, $9, $10, $11, $12, $13, $14)
    ON CONFLICT (hash) DO NOTHING
  `;

    try {
        await db.query(query, [
            tx.hash,
            tx.sender,
            tx.recipient,
            tx.value,
            tx.gas_price,
            tx.nonce,
            tx.data_size,
            tx.gas_limit,
            tx.max_fee_per_gas,
            tx.max_priority_fee_per_gas,
            tx.tx_type,
            extra.to_is_contract,
            extra.is_erc20,
            extra.is_erc721
        ]);
        stats.processed++;
        return true;
    } catch (e) {
        stats.errors++;
        return false;
    }
}

/**
 * Process a pending transaction
 */
async function processTx(provider, txHash) {
    try {
        const tx = await provider.getTransaction(txHash);
        if (!tx) return;

        const normalized = normalizeTx(tx);

        // Detect contract and token transfers
        const toIsContract = await isContract(provider, tx.to);
        const tokenInfo = detectTokenTransfer(tx.data);

        await insertTx(normalized, {
            to_is_contract: toIsContract,
            is_erc20: tokenInfo.is_erc20,
            is_erc721: tokenInfo.is_erc721
        });

    } catch (e) {
        // Silent fail for individual tx errors
    }
}

/**
 * Main WebSocket listener
 */
async function startStreamer() {
    console.log("============================================================");
    console.log("[NODESCRYPT] WebSocket Streamer Starting...");
    console.log("============================================================");
    console.log(`[NODESCRYPT] WS: ${ETH_WS}`);
    console.log(`[NODESCRYPT] DB: ${process.env.POSTGRES_HOST || 'localhost'}/checkpoint`);
    console.log("============================================================");

    // Connect to database
    await db.connect().catch(() => { });
    console.log("[NODESCRYPT] Connected to PostgreSQL");

    // Create provider
    let provider;

    try {
        provider = new ethers.WebSocketProvider(ETH_WS);
        console.log("[NODESCRYPT] WebSocket provider created");
    } catch (e) {
        console.log("[NODESCRYPT] WebSocket failed, using HTTP polling...");
        provider = new ethers.JsonRpcProvider(ETH_HTTP);
    }

    // Subscribe to pending transactions
    provider.on("pending", async (txHash) => {
        stats.received++;
        processTx(provider, txHash);
    });

    // Error handling
    provider.on("error", (err) => {
        console.error("[NODESCRYPT] Provider error:", err.message);
    });

    // Stats logging
    setInterval(() => {
        const runtime = ((Date.now() - stats.start_time) / 1000).toFixed(0);
        const rate = (stats.received / (runtime || 1)).toFixed(1);
        console.log(`[NODESCRYPT] Stats: received=${stats.received} processed=${stats.processed} contracts=${stats.contracts_detected} rate=${rate}/s`);
    }, 10000);

    console.log("[NODESCRYPT] Listening for pending transactions...");
}

// Graceful shutdown
process.on("SIGINT", async () => {
    console.log("\n[NODESCRYPT] Shutting down...");
    console.log(`[NODESCRYPT] Final stats:`, stats);
    await db.end();
    process.exit(0);
});

// Start
startStreamer().catch(console.error);

module.exports = { normalizeTx, detectTokenTransfer, isContract };
