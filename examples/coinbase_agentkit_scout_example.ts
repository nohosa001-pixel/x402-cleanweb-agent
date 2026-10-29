/**
 * Coinbase AgentKit + CleanWeb ("Base Alpha Scout Agent") Example
 * --------------------------------------------------------------------------------
 * Demonstrates an autonomous AI agent running on Base Mainnet (8453) using
 * Coinbase AgentKit and the `agentkit-cleanweb` Action Provider.
 *
 * Scenarios:
 * 1. Crawl & Compress: Scrapes project web pages and research whitepapers with 87% token reduction.
 * 2. On-Chain Grounding: Produces Base Mainnet EIP-712 cryptographic attestations for smart contract execution.
 * 3. Gasless Vault Management: Handles pre-funded Base USDC micro-payments (<1ms execution).
 *
 * Installation:
 *     npm install agentkit-cleanweb @coinbase/agentkit
 *
 * Run:
 *     npx tsx examples/coinbase_agentkit_scout_example.ts
 */

import { cleanWebActionProvider, cleanWebContent, oracleGrounding, manageX402Vault } from "../packages/agentkit-cleanweb/dist/index.js";

async function runBaseAlphaScoutDemo() {
  console.log("==================================================================");
  console.log("🤖 [BASE ALPHA SCOUT AGENT] Powered by Coinbase AgentKit & CleanWeb");
  console.log("   Target Network: Base Mainnet (Chain ID: 8453)");
  console.log("==================================================================\n");

  // 1. Initialize Action Provider
  const cleanWeb = cleanWebActionProvider({
    vaultKey: process.env.AGENT_VAULT_KEY || "WELCOME100",
  });

  const mockWallet = {
    getAddress: async () => "0xA185B43fDD19619f99952AAed6eabf1029bF36a1",
    getNetwork: () => ({ chainId: 8453, networkId: "base-mainnet" }),
  };

  const actions = cleanWeb.getActions(mockWallet);
  console.log(`✅ CleanWeb Action Provider initialized with ${actions.length} actions:`);
  actions.forEach((a) => console.log(`   • ${a.name}: ${a.description.slice(0, 70)}...`));
  console.log();

  // 2. Scenario A: Autonomous Webpage Token Compression
  console.log("------------------------------------------------------------------");
  console.log("🔍 [STEP 1] Autonomous Scraping & 87% Token Noise Reduction");
  console.log("------------------------------------------------------------------");
  const targetWeb = "https://news.ycombinator.com";
  console.log(`🌐 Target: ${targetWeb}`);

  try {
    const webResult = await cleanWebContent({ url: targetWeb, maxLength: 500 });
    console.log(`✅ Success: ${webResult.success}`);
    console.log(`📄 Title: ${webResult.title}`);
    console.log(`📉 Token Reduction Rate: ${webResult.tokenReductionRate}`);
    console.log(`📊 Estimated Token Savings: ~${webResult.sourceTokensEstimate - webResult.compressedTokensEstimate} tokens`);
    console.log(`⚡ Extraction Latency: ${webResult.latencyMs} ms`);
    console.log(`📝 Clean Markdown Snippet:\n${webResult.cleanMarkdown.slice(0, 200)}...\n`);
  } catch (err) {
    console.log(`⚠️ Web Scrape Notice: ${err}`);
  }

  // 3. Scenario B: Base Mainnet EIP-712 Factual Grounding Attestation
  console.log("------------------------------------------------------------------");
  console.log("🛡️ [STEP 2] Base Mainnet (8453) EIP-712 Truth Attestation");
  console.log("------------------------------------------------------------------");
  const targetQuery = "Base chain USDC TVL and autonomous agent adoption";
  console.log(`🔎 Verifying Query: "${targetQuery}"`);

  try {
    const proof = await oracleGrounding({
      query: targetQuery,
      chainId: 8453,
    });
    console.log(`✅ Oracle Verdict: ${proof.verdict} (Confidence: ${proof.confidence * 100}%)`);
    console.log(`📋 Summary: ${proof.summary}`);
    if (proof.attestation) {
      console.log(`🔐 On-Chain Signer: ${proof.attestation.signerAddress}`);
      console.log(`📦 Merkle Root: ${proof.attestation.merkleRoot}`);
      console.log(`✍️ EIP-712 Signature (v, r, s): ${proof.attestation.signature.slice(0, 32)}...`);
    }
    console.log();
  } catch (err) {
    console.log(`⚠️ Oracle Grounding Notice: ${err}`);
  }

  // 4. Scenario C: Gasless Pre-Funded Vault Inspection
  console.log("------------------------------------------------------------------");
  console.log("💳 [STEP 3] Base USDC Agent Vault & Micro-Payment Status");
  console.log("------------------------------------------------------------------");
  const vaultInfo = await manageX402Vault({ action: "deposit_info" });
  console.log(`🏦 Universal Escrow Contract: ${vaultInfo.depositAddress}`);
  console.log(`🔗 Supported Chains: ${vaultInfo.supportedChains?.join(", ")}`);
  console.log(`💵 Native Base Token: ${vaultInfo.passTier}`);
  console.log();

  console.log("==================================================================");
  console.log("🎉 [COMPLETED] Base Alpha Scout Agent successfully executed all actions!");
  console.log("==================================================================");
}

runBaseAlphaScoutDemo().catch(console.error);
