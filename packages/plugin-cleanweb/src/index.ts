import { scrapeWebAction } from "./actions/scrape.js";
import { cleanWebIntelligenceProvider } from "./providers/intelligence.js";
import { groundTruthSignalEvaluator } from "./evaluators/signal.js";

export const cleanWebPlugin = {
  name: "cleanweb",
  description: "CleanWeb Studio 87% Token Reduction, Fresh Ground Truth Discovery, and Solana x402 Autonomous Micropayment Rail for ElizaOS",
  actions: [scrapeWebAction],
  providers: [cleanWebIntelligenceProvider],
  evaluators: [groundTruthSignalEvaluator],
  services: []
};

export default cleanWebPlugin;
export * from "./actions/scrape.js";
export * from "./providers/intelligence.js";
export * from "./evaluators/signal.js";
