/**
 * Deploy All NodesCrypt Contracts
 * 
 * Usage:
 *   npx hardhat run scripts/deploy-all.js --network shardeum
 *   npx hardhat run scripts/deploy-all.js --network inco
 * 
 * Deploys in order:
 *   1. ContractRegistry (master index)
 *   2. SecurityAudit (incident logging)
 *   3. MerkleBatchAnchor (gas-optimized batching)
 *   4. PolicyRegistry (policy management)
 *   5. Governance (voting/approvals)
 *   6. AddressBook (watched addresses)
 */

const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
    const networkName = hre.network.name;
    console.log("=".repeat(70));
    console.log(`[NODESCRYPT] Deploying Full Contract Suite to ${networkName}`);
    console.log("=".repeat(70));

    // Get deployer
    const [deployer] = await hre.ethers.getSigners();
    console.log(`\nDeployer: ${deployer.address}`);

    // Check balance
    const balance = await hre.ethers.provider.getBalance(deployer.address);
    console.log(`Balance: ${hre.ethers.formatEther(balance)} tokens\n`);

    if (balance === 0n) {
        console.error("❌ No balance! Get testnet tokens first.");
        process.exit(1);
    }

    const deployedContracts = {};

    // ========================================
    // 1. Deploy ContractRegistry
    // ========================================
    console.log("[1/6] Deploying ContractRegistry...");
    const ContractRegistry = await hre.ethers.getContractFactory("ContractRegistry");
    const registry = await ContractRegistry.deploy(deployer.address);
    await registry.waitForDeployment();
    const registryAddress = await registry.getAddress();
    console.log(`      ✅ ContractRegistry: ${registryAddress}`);
    deployedContracts.ContractRegistry = registryAddress;

    // ========================================
    // 2. Deploy SecurityAudit
    // ========================================
    console.log("[2/6] Deploying SecurityAudit...");
    const SecurityAudit = await hre.ethers.getContractFactory("SecurityAudit");
    const securityAudit = await SecurityAudit.deploy(deployer.address);
    await securityAudit.waitForDeployment();
    const securityAuditAddress = await securityAudit.getAddress();
    console.log(`      ✅ SecurityAudit: ${securityAuditAddress}`);
    deployedContracts.SecurityAudit = securityAuditAddress;

    // ========================================
    // 3. Deploy MerkleBatchAnchor
    // ========================================
    console.log("[3/6] Deploying MerkleBatchAnchor...");
    const MerkleBatchAnchor = await hre.ethers.getContractFactory("MerkleBatchAnchor");
    const merkleBatch = await MerkleBatchAnchor.deploy(deployer.address);
    await merkleBatch.waitForDeployment();
    const merkleBatchAddress = await merkleBatch.getAddress();
    console.log(`      ✅ MerkleBatchAnchor: ${merkleBatchAddress}`);
    deployedContracts.MerkleBatchAnchor = merkleBatchAddress;

    // ========================================
    // 4. Deploy PolicyRegistry
    // ========================================
    console.log("[4/6] Deploying PolicyRegistry...");
    const PolicyRegistry = await hre.ethers.getContractFactory("PolicyRegistry");
    const policyRegistry = await PolicyRegistry.deploy(deployer.address);
    await policyRegistry.waitForDeployment();
    const policyRegistryAddress = await policyRegistry.getAddress();
    console.log(`      ✅ PolicyRegistry: ${policyRegistryAddress}`);
    deployedContracts.PolicyRegistry = policyRegistryAddress;

    // ========================================
    // 5. Deploy Governance
    // ========================================
    console.log("[5/6] Deploying Governance...");
    const Governance = await hre.ethers.getContractFactory("Governance");
    const governance = await Governance.deploy(
        deployer.address,
        2,        // requiredApprovals
        604800    // proposalDuration (7 days in seconds)
    );
    await governance.waitForDeployment();
    const governanceAddress = await governance.getAddress();
    console.log(`      ✅ Governance: ${governanceAddress}`);
    deployedContracts.Governance = governanceAddress;

    // ========================================
    // 6. Deploy AddressBook
    // ========================================
    console.log("[6/6] Deploying AddressBook...");
    const AddressBook = await hre.ethers.getContractFactory("AddressBook");
    const addressBook = await AddressBook.deploy(deployer.address);
    await addressBook.waitForDeployment();
    const addressBookAddress = await addressBook.getAddress();
    console.log(`      ✅ AddressBook: ${addressBookAddress}`);
    deployedContracts.AddressBook = addressBookAddress;

    // ========================================
    // Register all contracts in Registry
    // ========================================
    console.log("\n[REGISTRY] Registering contracts...");

    await registry.setContract("SecurityAudit", securityAuditAddress);
    await registry.setContract("MerkleBatchAnchor", merkleBatchAddress);
    await registry.setContract("PolicyRegistry", policyRegistryAddress);
    await registry.setContract("Governance", governanceAddress);
    await registry.setContract("AddressBook", addressBookAddress);

    console.log("      ✅ All contracts registered in ContractRegistry");

    // ========================================
    // Save deployment info
    // ========================================
    const deploymentsPath = path.join(__dirname, "..", "deployments", "ADDRESS_BOOK.json");
    const deploymentsDir = path.dirname(deploymentsPath);

    if (!fs.existsSync(deploymentsDir)) {
        fs.mkdirSync(deploymentsDir, { recursive: true });
    }

    let allDeployments = {};
    if (fs.existsSync(deploymentsPath)) {
        allDeployments = JSON.parse(fs.readFileSync(deploymentsPath, "utf8"));
    }

    allDeployments[networkName] = {
        ...deployedContracts,
        deployer: deployer.address,
        deployedAt: new Date().toISOString(),
        chainId: (await hre.ethers.provider.getNetwork()).chainId.toString()
    };

    fs.writeFileSync(deploymentsPath, JSON.stringify(allDeployments, null, 2));

    // ========================================
    // Summary
    // ========================================
    console.log("\n" + "=".repeat(70));
    console.log("🎉 DEPLOYMENT COMPLETE!");
    console.log("=".repeat(70));
    console.log(`Network: ${networkName}`);
    console.log(`Chain ID: ${(await hre.ethers.provider.getNetwork()).chainId}`);
    console.log("\nDeployed Contracts:");
    console.log("-".repeat(70));

    for (const [name, address] of Object.entries(deployedContracts)) {
        console.log(`  ${name.padEnd(20)} ${address}`);
    }

    console.log("-".repeat(70));
    console.log(`\nAddresses saved to: deployments/ADDRESS_BOOK.json`);
    console.log("=".repeat(70));

    return deployedContracts;
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("Deployment failed:", error);
        process.exit(1);
    });
