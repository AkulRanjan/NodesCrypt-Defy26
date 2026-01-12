const { ethers } = require("ethers");
const { Client } = require("pg");

const RPC_URL = "http://127.0.0.1:8545";

const provider = new ethers.JsonRpcProvider(RPC_URL);

const db = new Client({
  host: "localhost",
  user: "cp",
  password: "cp",
  database: "checkpoint",
  port: 5432
});

async function main() {
  await db.connect();
  console.log("[CP1] Connected to DB");

  provider.on("pending", async (txHash) => {
    try {
      const tx = await provider.getTransaction(txHash);
      if (!tx) return;

      const dataSize = tx.data ? (tx.data.length - 2) / 2 : 0;

      await db.query(
        `INSERT INTO mempool_txs 
         (hash, sender, recipient, value, gas_price, nonce, data_size)
         VALUES ($1,$2,$3,$4,$5,$6,$7)
         ON CONFLICT DO NOTHING`,
        [
          tx.hash,
          tx.from,
          tx.to,
          tx.value?.toString(),
          tx.gasPrice?.toString(),
          tx.nonce,
          dataSize
        ]
      );

      console.log("[CP1] TX captured:", tx.hash);
    } catch (e) {
      // silent drop
    }
  });

  console.log("[CP1] Listening to mempool...");
}

main();
