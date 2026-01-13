require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

// Helper to get accounts - handles missing/invalid keys gracefully
function getAccounts() {
    const key = process.env.PRIVATE_KEY;
    if (!key || key === "your_private_key_here" || key.length < 64) {
        return [];  // Empty accounts = will fail on deploy but compile works
    }
    return [key.startsWith("0x") ? key : `0x${key}`];
}

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
    solidity: {
        version: "0.8.20",
        settings: {
            optimizer: {
                enabled: true,
                runs: 200
            }
        }
    },
    networks: {
        // Local development
        localhost: {
            url: "http://127.0.0.1:8545"
        },

        // Shardeum Sphinx Testnet (Validator)
        shardeum: {
            url: process.env.SHARDEUM_RPC || "https://sphinx.shardeum.org",
            chainId: 8082,
            accounts: getAccounts(),
            timeout: 60000
        },

        // Shardeum Dapp Testnet
        shardeumDapp: {
            url: "https://dapps.shardeum.org",
            chainId: 8081,
            accounts: getAccounts(),
            timeout: 60000
        },

        // INCO Testnet (Gentry)
        inco: {
            url: process.env.INCO_RPC || "https://testnet.inco.org",
            chainId: 9090,
            accounts: getAccounts(),
            timeout: 60000
        }
    },

    paths: {
        sources: "./contracts",
        tests: "./test",
        cache: "./cache",
        artifacts: "./artifacts"
    },

    etherscan: {
        apiKey: {
            shardeum: "no-api-key-needed",
            inco: "no-api-key-needed"
        },
        customChains: [
            {
                network: "shardeum",
                chainId: 8082,
                urls: {
                    apiURL: "https://explorer-sphinx.shardeum.org/api",
                    browserURL: "https://explorer-sphinx.shardeum.org"
                }
            },
            {
                network: "inco",
                chainId: 9090,
                urls: {
                    apiURL: "https://explorer.inco.network/api",
                    browserURL: "https://explorer.inco.network"
                }
            }
        ]
    }
};
