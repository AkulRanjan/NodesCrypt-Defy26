/**
 * Deploy SecurityAudit.sol to INCO Testnet
 * 
 * Usage:
 *   npx hardhat run scripts/deploy-inco.js --network inco
 * 
 * Prerequisites:
 *   1. Add PRIVATE_KEY to .env
 *   2. Get INCO tokens from https://faucet.inco.org
 */

const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
    console.log("=".repeat(60));
    console.log("[NODESCRYPT] Deploying to INCO Testnet");
    console.log("=".repeat(60));

    // Get deployer account
    const [deployer] = await hre.ethers.getSigners();
    console.log(`Deployer address: ${deployer.address}`);

    // Check balance
    const balance = await hre.ethers.provider.getBalance(deployer.address);
    console.log(`Balance: ${hre.ethers.formatEther(balance)} INCO`);

    if (balance === 0n) {
        console.error("\n❌ No INCO balance! Get tokens from faucet:");
        console.error("   Visit: https://faucet.inco.org");
        console.error("   Enter: " + deployer.address);
        process.exit(1);
    }

    // Deploy SecurityAudit
    console.log("\n[1/3] Compiling contracts...");
    const SecurityAudit = await hre.ethers.getContractFactory("SecurityAudit");

    console.log("[2/3] Deploying SecurityAudit...");
    const contract = await SecurityAudit.deploy();
    await contract.waitForDeployment();

    const contractAddress = await contract.getAddress();
    console.log(`\n✅ SecurityAudit deployed to: ${contractAddress}`);

    // Save deployment info
    console.log("\n[3/3] Saving deployment info...");
    const deploymentsPath = path.join(__dirname, "..", "deployments.json");

    let deployments = {};
    if (fs.existsSync(deploymentsPath)) {
        deployments = JSON.parse(fs.readFileSync(deploymentsPath, "utf8"));
    }

    deployments.inco = {
        network: "INCO Testnet (Gentry)",
        chainId: 9090,
        contract: "SecurityAudit",
        address: contractAddress,
        deployer: deployer.address,
        deployedAt: new Date().toISOString(),
        explorer: `https://explorer.inco.network/address/${contractAddress}`
    };

    fs.writeFileSync(deploymentsPath, JSON.stringify(deployments, null, 2));
    console.log("Saved to deployments.json");

    // Summary
    console.log("\n" + "=".repeat(60));
    console.log("🎉 INCO DEPLOYMENT COMPLETE!");
    console.log("=".repeat(60));
    console.log(`Contract:  SecurityAudit`);
    console.log(`Address:   ${contractAddress}`);
    console.log(`Network:   INCO Testnet (Chain ID: 9090)`);
    console.log(`Explorer:  https://explorer.inco.network/address/${contractAddress}`);
    console.log("=".repeat(60));
    console.log("\n📝 This contract stores confidential audit logs for NodesCrypt");
    console.log("   All security decisions are now logged on-chain!");

    return contractAddress;
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("Deployment failed:", error);
        process.exit(1);
    });
