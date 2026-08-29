"""
Comprehensive x402 Micropayment Verification and Challenge Engine.
Supports Multi-Chain USDC (Polygon/Base/Arbitrum), Pre-funded Agent Vault, Lemon Squeezy Passes, and Instant Sandbox Free Trials.
"""

import os
import time
import secrets
from typing import Optional, Dict, Any, Tuple, List
from fastapi import Request
from fastapi.responses import JSONResponse
from web3 import Web3
from dotenv import load_dotenv

from app.schemas import PricingTier, PaymentMethod, PaymentChallenge, PaymentReceipt
from app.storage import storage_manager
from app.multi_chain import multi_chain_manager, SupportedChain, CHAIN_REGISTRY
from app.vault_manager import vault_manager

load_dotenv()

# Server Wallet Configuration
SERVER_WALLET_ADDRESS = Web3.to_checksum_address(
    os.getenv("SERVER_WALLET_ADDRESS", "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf")
)
ALLOW_DEV_BYPASS = os.getenv("ALLOW_DEV_BYPASS", "false").lower() in ("1", "true", "yes")

# Tiered Pricing Configuration (USDC)
TIER_PRICING: Dict[PricingTier, Dict[str, Any]] = {
    PricingTier.LIGHT: {
        "cost_usdc": 0.001,
        "units": "1000",
        "description": "Tier 1 (Light): Single web clean markdown extraction",
    },
    PricingTier.STANDARD: {
        "cost_usdc": 0.005,
        "units": "5000",
        "description": "Tier 2 (Standard): PDF paper parsing & concurrent batch scrape",
    },
    PricingTier.HEAVY: {
        "cost_usdc": 0.010,
        "units": "10000",
        "description": "Tier 3 (Heavy): Gemini AI YouTube full video analysis",
    },
    PricingTier.ONCHAIN: {
        "cost_usdc": 0.020,
        "units": "20000",
        "description": "Tier 4 (On-Chain): EIP-712 cryptographic attestation & ABI calldata",
    },
}

FREE_TRIAL_LIMIT = int(os.getenv("FREE_TRIAL_LIMIT", "2"))


class X402Verifier:
    """Enterprise-grade, multi-strategy x402 payment verification engine."""

    def __init__(self):
        self.recipient_wallet = SERVER_WALLET_ADDRESS

    def get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "127.0.0.1"

    def build_402_challenge(self, tier: PricingTier = PricingTier.LIGHT, ip_or_nonce: str = "") -> PaymentChallenge:
        cfg = TIER_PRICING.get(tier, TIER_PRICING[PricingTier.LIGHT])
        cost = cfg["cost_usdc"]
        poly_cfg = multi_chain_manager.get_chain_config("polygon")
        
        usage = storage_manager.get_trial_usage(ip_or_nonce) if ip_or_nonce else 0
        remaining_trials = max(0, FREE_TRIAL_LIMIT - usage)

        return PaymentChallenge(
            chain="polygon",
            chain_id=137,
            recipient_wallet=self.recipient_wallet,
            amount_usdc=f"{cost:.4f}",
            token_address=poly_cfg.usdc_address,
            payment_methods_accepted=[
                "USDC_ONCHAIN_POLYGON",
                "USDC_ONCHAIN_BASE",
                "USDC_ONCHAIN_ARBITRUM",
                "VAULT_BALANCE",
                "LEMON_SQUEEZY_PASS",
                "SANDBOX_FREE_TRIAL"
            ],
            pass_options={
                "24_hour_pass": "https://cleanweb-agent.lemonsqueezy.com/buy/24h-pass",
                "7_day_unlimited": "https://cleanweb-agent.lemonsqueezy.com/buy/7d-unlimited"
            },
            vault_deposit_endpoint="/api/v1/vault/deposit",
            free_trial_remaining=remaining_trials,
            nonce=f"nonce_{secrets.token_hex(8)}",
            timestamp=int(time.time()),
        )

    def build_402_response(self, tier: PricingTier = PricingTier.LIGHT, request: Optional[Request] = None, custom_detail: Optional[str] = None) -> JSONResponse:
        ip_addr = self.get_client_ip(request) if request else "127.0.0.1"
        nonce_hdr = request.headers.get("x-agent-nonce", "") if request else ""
        identifier = nonce_hdr or ip_addr

        challenge = self.build_402_challenge(tier=tier, ip_or_nonce=identifier)
        cfg = TIER_PRICING.get(tier, TIER_PRICING[PricingTier.LIGHT])

        headers = {
            "WWW-Authenticate": f'x402 realm="CleanWeb Studio", amount="{cfg["cost_usdc"]:.4f}", token="USDC", address="{self.recipient_wallet}", chain="Polygon,Base,Arbitrum"',
            "X-Payment-Amount": f"{cfg['cost_usdc']:.4f}",
            "X-Payment-Recipient": self.recipient_wallet,
            "X-Payment-Token": "USDC",
            "X-Payment-Networks": "Polygon(137), Base(8453), Arbitrum(42161)",
            "X-Vault-Deposit-Endpoint": "/api/v1/vault/deposit",
        }

        body = {
            "error": "Payment Required",
            "status_code": 402,
            "tier_required": tier.value,
            "message": custom_detail or f"HTTP 402 Payment Required: {cfg['description']} ({cfg['cost_usdc']} USDC)",
            "challenge": challenge.model_dump(),
        }

        return JSONResponse(status_code=402, content=body, headers=headers)

    def verify_request(self, request: Request, tier: PricingTier = PricingTier.LIGHT) -> Tuple[bool, Optional[PaymentReceipt], Optional[JSONResponse]]:
        """
        Main multi-tiered payment verification pipeline.
        Returns (is_authorized, payment_receipt, error_402_response).
        """
        cost_usdc = TIER_PRICING.get(tier, TIER_PRICING[PricingTier.LIGHT])["cost_usdc"]
        auth_header = request.headers.get("authorization", "").strip()
        bearer_token = auth_header.replace("Bearer ", "").strip() if auth_header.startswith("Bearer ") else ""

        # --- Strategy 1: Dev Bypass ---
        if ALLOW_DEV_BYPASS or bearer_token == "dev-bypass":
            receipt = PaymentReceipt(
                receipt_id=f"rcpt_dev_{secrets.token_hex(6)}",
                tier=tier,
                payment_method=PaymentMethod.DEV_BYPASS,
                cost_usdc=0.0,
                settled_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
            return True, receipt, None

        # --- Strategy 2: Pre-funded Agent Vault ---
        vault_key = (
            request.headers.get("x-vault-key")
            or request.headers.get("x-session-key")
            or (bearer_token if bearer_token.startswith("vault_key_") else None)
            or request.headers.get("x-agent-wallet")
        )
        if vault_key:
            success, remaining_bal, acc = vault_manager.deduct(vault_key, cost_usdc)
            if success:
                receipt = PaymentReceipt(
                    receipt_id=f"rcpt_vault_{secrets.token_hex(6)}",
                    tier=tier,
                    payment_method=PaymentMethod.VAULT_BALANCE,
                    payer_address=acc.get("agent_address") if acc else None,
                    cost_usdc=cost_usdc,
                    remaining_vault_balance=remaining_bal,
                    settled_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                )
                return True, receipt, None
            elif acc is not None:
                # Vault exists but insufficient balance
                return False, None, self.build_402_response(
                    tier=tier,
                    request=request,
                    custom_detail=f"Insufficient Vault Balance. Current: {remaining_bal:.4f} USDC, Required: {cost_usdc:.4f} USDC. Please deposit via POST /api/v1/vault/deposit"
                )

        # --- Strategy 3: Lemon Squeezy Pass Token ---
        pass_token = (
            request.headers.get("x-pass-token")
            or (bearer_token if bearer_token.startswith("pass_") else None)
        )
        if pass_token:
            valid_pass = storage_manager.get_pass(pass_token)
            if valid_pass:
                receipt = PaymentReceipt(
                    receipt_id=f"rcpt_pass_{secrets.token_hex(6)}",
                    tier=tier,
                    payment_method=PaymentMethod.LEMON_SQUEEZY_PASS,
                    payer_address=valid_pass.get("buyer_email"),
                    cost_usdc=0.0,
                    settled_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                )
                return True, receipt, None

        # --- Strategy 4: Multi-Chain On-Chain TX Hash ---
        tx_hash = (
            request.headers.get("x-payment-tx")
            or request.headers.get("x-tx-hash")
            or (bearer_token if bearer_token.startswith("0x") and len(bearer_token) == 66 else None)
        )
        if tx_hash:
            chain_hdr = request.headers.get("x-chain", request.headers.get("x-chain-id", "polygon"))
            
            # Anti-Replay Check
            if storage_manager.is_tx_used(tx_hash):
                return False, None, self.build_402_response(
                    tier=tier,
                    request=request,
                    custom_detail="Transaction hash has already been redeemed. Please submit a fresh transaction."
                )

            is_valid, reason, details = multi_chain_manager.verify_usdc_transfer(
                tx_hash=tx_hash,
                chain_identifier=chain_hdr,
                expected_recipient=self.recipient_wallet,
                min_amount_usdc=cost_usdc
            )

            if is_valid and details:
                # Record to prevent replay
                storage_manager.record_used_tx(
                    tx_hash=tx_hash,
                    chain=details["chain"],
                    payer=details.get("payer", "0x"),
                    amount_usdc=details.get("amount_usdc", cost_usdc)
                )
                receipt = PaymentReceipt(
                    receipt_id=f"rcpt_tx_{secrets.token_hex(6)}",
                    tier=tier,
                    payment_method=PaymentMethod.USDC_ONCHAIN,
                    payer_address=details.get("payer"),
                    tx_hash=tx_hash,
                    cost_usdc=details.get("amount_usdc", cost_usdc),
                    settled_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                )
                return True, receipt, None
            else:
                return False, None, self.build_402_response(
                    tier=tier,
                    request=request,
                    custom_detail=f"On-chain verification failed: {reason}"
                )

        # --- Strategy 5: Instant Sandbox Free Trial ---
        nonce_hdr = request.headers.get("x-agent-nonce", "").strip()
        client_ip = self.get_client_ip(request)
        trial_id = nonce_hdr if nonce_hdr else f"ip_{client_ip}"

        current_usage = storage_manager.get_trial_usage(trial_id)
        if current_usage < FREE_TRIAL_LIMIT:
            storage_manager.increment_trial_usage(trial_id)
            rem = FREE_TRIAL_LIMIT - current_usage - 1
            receipt = PaymentReceipt(
                receipt_id=f"rcpt_trial_{secrets.token_hex(6)}",
                tier=tier,
                payment_method=PaymentMethod.SANDBOX_FREE_TRIAL,
                payer_address=f"sandbox_{trial_id[:16]}",
                cost_usdc=0.0,
                remaining_free_trials=rem,
                settled_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
            return True, receipt, None

        # --- Default: Return 402 Challenge ---
        return False, None, self.build_402_response(tier=tier, request=request)


x402_verifier = X402Verifier()
