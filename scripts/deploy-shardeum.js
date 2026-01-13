/**
 * Deploy NodescryptAudit.sol to Shardeum Sphinx Testnet
 * 
 * Usage:
 *   npx hardhat run scripts/deploy-shardeum.js --network shardeum
 * 
 * Prerequisites:
 *   1. Add PRIVATE_KEY to .env
 *   2. Get SHM tokens from Discord faucet: /faucet YOUR_ADDRESS
 */

const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
    console.log("=".repeat(60));
    console.log("[NODESCRYPT] Deploying to Shardeum Sphinx Testnet");
    console.log("=".repeat(60));

    // Get deployer account
    const [deployer] = await hre.ethers.getSigners();
    console.log(`Deployer address: ${deployer.address}`);

    // Check balance
    const balance = await hre.ethers.provider.getBalance(deployer.address);
    console.log(`Balance: ${hre.ethers.formatEther(balance)} SHM`);

    if (balance === 0n) {
        console.error("\n❌ No SHM balance! Get tokens from Discord faucet:");
        console.error("   Join: https://discord.gg/shardeum");
        console.error("   Command: /faucet " + deployer.address);
        process.exit(1);
    }

    // Deploy NodescryptAudit
    console.log("\n[1/3] Compiling contracts...");
    const NodescryptAudit = await hre.ethers.getContractFactory("NodescryptAudit");

    console.log("[2/3] Deploying NodescryptAudit...");
    const contract = await NodescryptAudit.deploy();
    await contract.waitForDeployment();

    const contractAddress = await contract.getAddress();
    console.log(`\n✅ NodescryptAudit deployed to: ${contractAddress}`);

    // Save deployment info
    console.log("\n[3/3] Saving deployment info...");
    const deploymentsPath = path.join(__dirname, "..", "deployments.json");

    let deployments = {};
    if (fs.existsSync(deploymentsPath)) {
        deployments = JSON.parse(fs.readFileSync(deploymentsPath, "utf8"));
    }

    deployments.shardeum = {
        network: "Shardeum Sphinx Testnet",
        chainId: 8082,
        contract: "NodescryptAudit",
        address: contractAddress,
        deployer: deployer.address,
        deployedAt: new Date().toISOString(),
        explorer: `https://explorer-sphinx.shardeum.org/address/${contractAddress}`
    };

    fs.writeFileSync(deploymentsPath, JSON.stringify(deployments, null, 2));
    console.log("Saved to deployments.json");

    // Summary
    console.log("\n" + "=".repeat(60));
    console.log("🎉 SHARDEUM DEPLOYMENT COMPLETE!");
    console.log("=".repeat(60));
    console.log(`Contract:  NodescryptAudit`);
    console.log(`Address:   ${contractAddress}`);
    console.log(`Network:   Shardeum Sphinx (Chain ID: 8082)`);
    console.log(`Explorer:  https://explorer-sphinx.shardeum.org/address/${contractAddress}`);
    console.log("=".repeat(60));

    // Verify contract exists
    const code = await hre.ethers.provider.getCode(contractAddress);
    if (code !== "0x") {
        console.log("\n✅ Contract verified on-chain!");
    }

    return contractAddress;
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("Deployment failed:", error);
        process.exit(1);
    });
