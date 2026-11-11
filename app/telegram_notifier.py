import os
import json
import logging
import urllib.request
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("telegram_notifier")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_NOTIFICATIONS_ENABLED = os.getenv("TELEGRAM_NOTIFICATIONS_ENABLED", "true").lower() in ("true", "1", "yes")

def send_telegram_alert(message: str, parse_mode: str = "Markdown") -> bool:
    """Non-blocking Telegram alert dispatcher for A-GRID payment and security events."""
    if not TELEGRAM_NOTIFICATIONS_ENABLED:
        return False
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
        
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": parse_mode
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return resp.status == 200
    except Exception as e:
        logger.debug(f"[Telegram Alert Error] {e}")
        return False

def notify_payment_received(chain: str, amount_usdc: float, payer: str, tx_hash: str = ""):
    """Sends notification when an autonomous agent settles an x402 payment."""
    tx_short = f"`{tx_hash[:10]}...{tx_hash[-6:]}`" if tx_hash and len(tx_hash) > 16 else f"`{tx_hash}`"
    msg = (
        f"💰 *[CleanWeb Agent] 온체인 결제 정산 완료!*\n\n"
        f"• **체인**: `{chain.upper()}`\n"
        f"• **정산 금액**: `+{amount_usdc:.4f} USDC`\n"
        f"• **결제 에이전트**: `{payer[:8]}...{payer[-6:]}`\n"
        f"• **수취 금고**: D'CENT 지문인증 지갑\n"
        f"• **트랜잭션**: {tx_short}\n"
    )
    return send_telegram_alert(msg)

