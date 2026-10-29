import {
  CleanWebContentSchema,
  CleanPdfSchema,
  CleanYoutubeSchema,
  OracleGroundingSchema,
  ManageVaultSchema,
} from "./types.js";
import {
  cleanWebContent,
  cleanPdfResearch,
  cleanYoutubeTranscript,
  oracleGrounding,
  manageX402Vault,
  ActionInvocationOptions,
} from "./actions.js";
import { BASE_CHAIN_ID, BASE_SEPOLIA_CHAIN_ID } from "./constants.js";

export interface CleanWebActionProviderConfig {
  gatewayUrl?: string;
  vaultKey?: string;
  agentNonce?: string;
  timeoutMs?: number;
}

export interface AgentKitAction<TArgs = unknown, TResult = unknown> {
  name: string;
  description: string;
  schema: unknown;
  invoke: (args: TArgs) => Promise<TResult>;
}

export interface NetworkLike {
  chainId?: number | string;
  networkId?: string;
}

export interface WalletProviderLike {
  getAddress?: () => Promise<string> | string;
  getNetwork?: () => Promise<NetworkLike> | NetworkLike;
}

/**
 * Coinbase AgentKit CleanWeb Action Provider
 * Drop-in Action Provider supplying 87% token-compressed web scraping,
 * research PDF analysis, YouTube Gemini Flash intelligence, and Base EIP-712 oracle attestations.
 */
export class CleanWebActionProvider {
  public readonly name = "cleanweb";
  public readonly description =
    "87% token noise reduction web scraper, academic PDF analyzer, YouTube Gemini video intelligence, and Base Mainnet EIP-712 signed oracle grounding.";

  private config: CleanWebActionProviderConfig;

  constructor(config: CleanWebActionProviderConfig = {}) {
    this.config = config;
  }

  /**
   * Verifies if the provider supports the given network.
   * Native support for Base (8453), Base Sepolia (84532), and all EVM chains.
   */
  public supportsNetwork(network: NetworkLike): boolean {
    if (!network || !network.chainId) return true;
    const cid = Number(network.chainId);
    return cid === BASE_CHAIN_ID || cid === BASE_SEPOLIA_CHAIN_ID || cid === 137 || cid === 42161;
  }

  /**
   * Returns all 5 Action instances for Coinbase AgentKit runtime registration.
   */
  public getActions(walletProvider?: WalletProviderLike): AgentKitAction[] {
    const opts: ActionInvocationOptions = {
      gatewayUrl: this.config.gatewayUrl,
      vaultKey: this.config.vaultKey,
      agentNonce: this.config.agentNonce,
      timeoutMs: this.config.timeoutMs,
    };

    return [
      {
        name: "cleanweb_clean_web_content",
        description:
          "Scrapes any target webpage URL and compresses noise/ads into 87% token-reduced clean Markdown for LLMs.",
        schema: CleanWebContentSchema,
        invoke: async (args) => {
          const parsed = CleanWebContentSchema.parse(args);
          return await cleanWebContent(parsed, opts);
        },
      },
      {
        name: "cleanweb_clean_pdf_research",
        description:
          "Extracts structured academic text, executive findings, and sections from online PDF whitepapers and reports.",
        schema: CleanPdfSchema,
        invoke: async (args) => {
          const parsed = CleanPdfSchema.parse(args);
          return await cleanPdfResearch(parsed, opts);
        },
      },
      {
        name: "cleanweb_clean_youtube_transcript",
        description:
          "Extracts high-precision subtitles and Google Gemini 3.8 Flash summary from YouTube videos without downloading media.",
        schema: CleanYoutubeSchema,
        invoke: async (args) => {
          const parsed = CleanYoutubeSchema.parse(args);
          return await cleanYoutubeTranscript(parsed, opts);
        },
      },
      {
        name: "cleanweb_oracle_grounding",
        description:
          "Discovers factual ground truth from the web and cryptographically signs an on-chain verifiable EIP-712 attestation for Base (8453).",
        schema: OracleGroundingSchema,
        invoke: async (args) => {
          const parsed = OracleGroundingSchema.parse(args);
          return await oracleGrounding(parsed, opts);
        },
      },
      {
        name: "cleanweb_manage_x402_vault",
        description:
          "Checks prefunded agent USDC vault balance, retrieves Base USDC deposit address, or inspects VIP pass entitlements.",
        schema: ManageVaultSchema,
        invoke: async (args) => {
          const parsed = ManageVaultSchema.parse(args);
          let addr = parsed.agentAddress;
          if (!addr && walletProvider && typeof walletProvider.getAddress === "function") {
            try {
              addr = await walletProvider.getAddress();
            } catch {
              // fallback
            }
          }
          return await manageX402Vault({ ...parsed, agentAddress: addr }, opts);
        },
      },
    ];
  }
}

/**
 * Factory helper for clean instantiations
 */
export function cleanWebActionProvider(
  config: CleanWebActionProviderConfig = {}
): CleanWebActionProvider {
  return new CleanWebActionProvider(config);
}
