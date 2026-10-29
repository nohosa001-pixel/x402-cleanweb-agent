import { z } from "zod";

/**
 * 1. Clean Web Content Schema
 */
export const CleanWebContentSchema = z
  .object({
    url: z.string().url().describe("The HTTP/HTTPS webpage URL to scrape and compress into clean Markdown"),
    maxLength: z
      .number()
      .int()
      .positive()
      .optional()
      .default(50000)
      .describe("Maximum character length for the returned markdown body (default 50,000)"),
    includeLinks: z
      .boolean()
      .optional()
      .default(true)
      .describe("Whether to preserve relevant markdown links in the cleaned text"),
  })
  .strip()
  .describe("Parameters for scraping and reducing webpage token noise by 87%");

export type CleanWebContentParams = z.infer<typeof CleanWebContentSchema>;

/**
 * 2. Clean Research PDF Schema
 */
export const CleanPdfSchema = z
  .object({
    pdfUrl: z.string().url().describe("The direct URL of the PDF whitepaper, financial filing, or arXiv research report"),
    maxPages: z
      .number()
      .int()
      .min(1)
      .max(100)
      .optional()
      .default(50)
      .describe("Maximum number of pages to parse (1-100, default 50)"),
  })
  .strip()
  .describe("Parameters for extracting clean academic and financial text from online PDF whitepapers");

export type CleanPdfParams = z.infer<typeof CleanPdfSchema>;

/**
 * 3. Clean YouTube Transcript Schema
 */
export const CleanYoutubeSchema = z
  .object({
    videoUrl: z.string().describe("YouTube video URL or 11-character video ID"),
    includeSummary: z
      .boolean()
      .optional()
      .default(true)
      .describe("Whether to generate Gemini 3.8 Flash bullet-point executive summary"),
  })
  .strip()
  .describe("Parameters for extracting timestamped subtitles and AI summaries from YouTube videos");

export type CleanYoutubeParams = z.infer<typeof CleanYoutubeSchema>;

/**
 * 4. Oracle Grounding & EIP-712 Attestation Schema
 */
export const OracleGroundingSchema = z
  .object({
    query: z.string().min(3).describe("The factual proposition or topic to verify (e.g. 'Base TVL surpasses 4B' or 'CRMA compliance')"),
    targetUrl: z
      .string()
      .url()
      .optional()
      .describe("Optional target webpage URL to ground the facts against"),
    chainId: z
      .number()
      .int()
      .optional()
      .default(8453)
      .describe("Target blockchain network ID for EIP-712 signature (Base Mainnet: 8453, Base Sepolia: 84532)"),
  })
  .strip()
  .describe("Parameters for web ground-truth discovery with on-chain verifiable EIP-712 cryptographic attestation");

export type OracleGroundingParams = z.infer<typeof OracleGroundingSchema>;

/**
 * 5. Manage x402 Agent Vault Schema
 */
export const ManageVaultSchema = z
  .object({
    action: z
      .enum(["balance", "deposit_info", "pass_status"])
      .describe("Action to perform: 'balance' (check prefunded USDC balance), 'deposit_info' (get deposit address & chain parameters), or 'pass_status' (check agent VIP pass)"),
    agentAddress: z
      .string()
      .regex(/^0x[a-fA-F0-9]{40}$/, "Must be a valid EVM address (0x...)")
      .optional()
      .describe("The agent's EVM wallet address on Base Mainnet"),
  })
  .strip()
  .describe("Parameters for managing gasless sub-millisecond x402 USDC micropayment session vaults");

export type ManageVaultParams = z.infer<typeof ManageVaultSchema>;

/**
 * CleanWeb Universal Action Result Interfaces
 */
export interface CleanWebContentResult {
  success: boolean;
  url: string;
  title: string;
  cleanMarkdown: string;
  tokenReductionRate: string;
  sourceTokensEstimate: number;
  compressedTokensEstimate: number;
  latencyMs: number;
}

export interface CleanPdfResult {
  success: boolean;
  pdfUrl: string;
  title: string;
  pageCount: number;
  wordCount: number;
  text: string;
  latencyMs: number;
}

export interface CleanYoutubeResult {
  success: boolean;
  videoId: string;
  title: string;
  channel: string;
  summary?: string;
  transcriptSample: string;
  fullTranscriptLength: number;
  latencyMs: number;
}

export interface OracleGroundingResult {
  success: boolean;
  query: string;
  groundedFacts: string[];
  summary: string;
  verdict: "VERIFIED" | "CONTRADICTED" | "UNVERIFIED";
  confidence: number;
  attestation?: {
    chainId: number;
    signerAddress: string;
    merkleRoot: string;
    signature: string;
    eip712Domain: Record<string, unknown>;
  };
  latencyMs: number;
}

export interface ManageVaultResult {
  success: boolean;
  action: string;
  agentAddress?: string;
  balanceUsdc?: number;
  totalConsumedUsdc?: number;
  depositAddress?: string;
  supportedChains?: string[];
  passTier?: string;
  passActive?: boolean;
}
