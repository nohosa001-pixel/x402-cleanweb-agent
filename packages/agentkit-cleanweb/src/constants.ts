/**
 * Constants for agentkit-cleanweb
 */

export const VERSION = "1.0.0";

export const DEFAULT_GATEWAY_URL =
  "https://x402-cleanweb-agent-212942243360.asia-northeast3.run.app";

export const FALLBACK_GATEWAY_URL =
  "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app";

export const BASE_CHAIN_ID = 8453;
export const BASE_SEPOLIA_CHAIN_ID = 84532;

/**
 * Base Native USDC Token Contract Address (ERC-20)
 */
export const BASE_USDC_ADDRESS =
  "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913" as const;

/**
 * A.GRID Universal Modular Escrow Core Contract on Base Mainnet
 */
export const BASE_ESCROW_CORE =
  "0x99FEd65Cf2D5378182c3481B300124BB1a8Ad278" as const;

export const DEFAULT_TIMEOUT_MS = 15000;

export const ACTION_PRICING = {
  CLEAN_WEB: 0.001, // 0.001 USDC
  CLEAN_PDF: 0.005, // 0.005 USDC
  CLEAN_YOUTUBE: 0.005, // 0.005 USDC
  ORACLE_GROUNDING: 0.035, // 0.035 USDC (includes Gemini Flash + EIP-712 proof)
} as const;
