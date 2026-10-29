import { test, describe } from "node:test";
import assert from "node:assert/strict";

import {
  CleanWebActionProvider,
  cleanWebActionProvider,
  CleanWebContentSchema,
  CleanPdfSchema,
  CleanYoutubeSchema,
  OracleGroundingSchema,
  ManageVaultSchema,
  BASE_CHAIN_ID,
  BASE_USDC_ADDRESS,
  BASE_ESCROW_CORE,
  manageX402Vault,
} from "../dist/index.js";

describe("Coinbase AgentKit CleanWeb Action Provider Suite", () => {
  test("1. CleanWebActionProvider metadata and network support", () => {
    const provider = cleanWebActionProvider();
    assert.equal(provider.name, "cleanweb");
    assert.ok(provider.description.includes("87% token noise reduction"));

    // Network support verification
    assert.equal(provider.supportsNetwork({ chainId: 8453 }), true, "Supports Base Mainnet");
    assert.equal(provider.supportsNetwork({ chainId: 84532 }), true, "Supports Base Sepolia");
    assert.equal(provider.supportsNetwork({ chainId: 137 }), true, "Supports Polygon");
    assert.equal(provider.supportsNetwork({ chainId: 42161 }), true, "Supports Arbitrum");
  });

  test("2. getActions() registers exactly 5 actions with valid schemas", () => {
    const mockWallet = {
      getAddress: async () => "0x1234567890123456789012345678901234567890",
      getNetwork: () => ({ chainId: 8453 }),
    };

    const provider = new CleanWebActionProvider();
    const actions = provider.getActions(mockWallet);

    assert.equal(actions.length, 5);

    const actionNames = actions.map((a) => a.name);
    assert.ok(actionNames.includes("cleanweb_clean_web_content"));
    assert.ok(actionNames.includes("cleanweb_clean_pdf_research"));
    assert.ok(actionNames.includes("cleanweb_clean_youtube_transcript"));
    assert.ok(actionNames.includes("cleanweb_oracle_grounding"));
    assert.ok(actionNames.includes("cleanweb_manage_x402_vault"));

    // Verify schemas and invoke functions exist
    for (const action of actions) {
      assert.ok(action.schema, `${action.name} must have a schema`);
      assert.equal(typeof action.invoke, "function", `${action.name} invoke must be a function`);
    }
  });

  test("3. Zod schema validation checks", () => {
    // CleanWebContentSchema
    const validWeb = CleanWebContentSchema.parse({ url: "https://ethereum.org" });
    assert.equal(validWeb.url, "https://ethereum.org");
    assert.equal(validWeb.maxLength, 50000);
    assert.throws(() => CleanWebContentSchema.parse({ url: "not-a-url" }));

    // CleanPdfSchema
    const validPdf = CleanPdfSchema.parse({ pdfUrl: "https://arxiv.org/pdf/1706.03762.pdf" });
    assert.equal(validPdf.maxPages, 50);
    assert.throws(() => CleanPdfSchema.parse({ pdfUrl: "invalid" }));

    // CleanYoutubeSchema
    const validYt = CleanYoutubeSchema.parse({ videoUrl: "https://youtube.com/watch?v=dQw4w9WgXcQ" });
    assert.equal(validYt.includeSummary, true);

    // OracleGroundingSchema
    const validOracle = OracleGroundingSchema.parse({ query: "Base network TVL" });
    assert.equal(validOracle.chainId, 8453);

    // ManageVaultSchema
    const validVault = ManageVaultSchema.parse({
      action: "deposit_info",
      agentAddress: "0x1234567890123456789012345678901234567890",
    });
    assert.equal(validVault.action, "deposit_info");
  });

  test("4. Constants and contract addresses", () => {
    assert.equal(BASE_CHAIN_ID, 8453);
    assert.equal(BASE_USDC_ADDRESS, "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913");
    assert.equal(BASE_ESCROW_CORE, "0x99FEd65Cf2D5378182c3481B300124BB1a8Ad278");
  });

  test("5. manageX402Vault deposit_info action invocation", async () => {
    const res = await manageX402Vault({
      action: "deposit_info",
    });

    assert.equal(res.success, true);
    assert.equal(res.action, "deposit_info");
    assert.equal(res.depositAddress, BASE_ESCROW_CORE);
    assert.ok(res.supportedChains?.includes("Base (8453)"));
  });
});
