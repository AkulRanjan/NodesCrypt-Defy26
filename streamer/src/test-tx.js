const { ethers } = require("ethers");

async function main() {
    const provider = new ethers.JsonRpcProvider("http://127.0.0.1:8545");
    const signer = await provider.getSigner(0);

    console.log("[TX Generator] Sending 5 test transactions...\n");

    for (let i = 0; i < 5; i++) {
        const tx = await signer.sendTransaction({
            to: "0x1000000000000000000000000000000000000001",
            value: 1000 + i
        });
        console.log(`[TX ${i + 1}] Hash: ${tx.hash}`);
    }

    console.log("\n[TX Generator] Done! Check streamer logs and database.");
}

main().catch(console.error);
