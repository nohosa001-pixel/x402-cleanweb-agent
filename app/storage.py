"""
Persistent High-Performance SQLite Storage Layer for Passes, Replay Protection, Free Trials, and Pre-funded Vault Accounts.
Optimized with WAL (Write-Ahead Logging), multi-threading concurrency locks, and LRU Cache.
"""

import os
import sqlite3
import time
import threading
from typing import Optional, Dict, Any, Tuple, List


class StorageManager:
    """Thread-safe, WAL-enabled SQLite storage manager with memory caching."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            data_dir = os.getenv("DATA_DIR", "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "x402_store.db")
        self.db_path = db_path
        self._lock = threading.Lock()
        self._cache_used_txs: set = set()
        self._cache_active_passes: Dict[str, Dict[str, Any]] = {}
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=20)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for high concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.cursor()
                
                # 1. Passes (Lemon Squeezy or custom time passes)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS passes (
                    pass_token TEXT PRIMARY KEY,
                    buyer_email TEXT,
                    pass_type TEXT,
                    created_at INTEGER,
                    expires_at INTEGER,
                    is_active INTEGER DEFAULT 1,
                    order_id TEXT,
                    credits INTEGER DEFAULT 100
                )
                """)
                try:
                    cursor.execute("ALTER TABLE passes ADD COLUMN credits INTEGER DEFAULT 100")
                except Exception:
                    pass
                
                # Pre-seed default VIP Promos
                now_ts = int(time.time())
                exp_ts = now_ts + 31536000  # 1 year
                cursor.execute("""
                INSERT OR IGNORE INTO passes (pass_token, buyer_email, pass_type, created_at, expires_at, is_active, order_id, credits)
                VALUES ('WELCOME100', 'vip@cleanweb.ai', 'VIP_PROMO_100', ?, ?, 1, 'promo_welcome100', 100)
                """, (now_ts, exp_ts))
                cursor.execute("""
                INSERT OR IGNORE INTO passes (pass_token, buyer_email, pass_type, created_at, expires_at, is_active, order_id, credits)
                VALUES ('CLEANWEB100', 'vip@cleanweb.ai', 'VIP_PROMO_100', ?, ?, 1, 'promo_cleanweb100', 100)
                """, (now_ts, exp_ts))
                
                # 2. Used On-Chain TX Hashes (Anti-Replay)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS used_txs (
                    tx_hash TEXT PRIMARY KEY,
                    chain TEXT,
                    payer TEXT,
                    amount_usdc REAL,
                    used_at INTEGER
                )
                """)
                
                # 3. Free Trial Quota (by IP or nonce identifier)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS free_trials (
                    identifier TEXT PRIMARY KEY,
                    usage_count INTEGER DEFAULT 0,
                    last_used_at INTEGER
                )
                """)
                
                # 4. Agent Vault Ledger
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_vaults (
                    agent_address TEXT PRIMARY KEY,
                    balance_usdc REAL DEFAULT 0.0,
                    total_deposited REAL DEFAULT 0.0,
                    total_consumed REAL DEFAULT 0.0,
                    session_key TEXT UNIQUE,
                    created_at INTEGER,
                    last_active INTEGER,
                    query_count INTEGER DEFAULT 0
                )
                """)
                
                conn.commit()
            finally:
                conn.close()

    # --- Replay Protection with Memory Cache ---
    def is_tx_used(self, tx_hash: str) -> bool:
        tx_lower = tx_hash.lower()
        if tx_lower in self._cache_used_txs:
            return True

        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM used_txs WHERE tx_hash = ?", (tx_lower,))
                found = cur.fetchone() is not None
                if found:
                    self._cache_used_txs.add(tx_lower)
                return found
            finally:
                conn.close()

    def record_used_tx(self, tx_hash: str, chain: str, payer: str, amount_usdc: float):
        tx_lower = tx_hash.lower()
        self._cache_used_txs.add(tx_lower)
        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.cursor()
                cur.execute("""
                INSERT OR REPLACE INTO used_txs (tx_hash, chain, payer, amount_usdc, used_at)
                VALUES (?, ?, ?, ?, ?)
                """, (tx_lower, chain.lower(), payer.lower(), amount_usdc, int(time.time())))
                conn.commit()
            finally:
                conn.close()

    # --- Passes ---
    def get_pass(self, pass_token: str) -> Optional[Dict[str, Any]]:
        now = int(time.time())
        # Check Promo Code auto-seeding
        token_upper = pass_token.strip().upper()
        if token_upper in ("WELCOME100", "CLEANWEB100", "VIPAGENT"):
            pass_token = token_upper

        if pass_token in self._cache_active_passes:
            cached = self._cache_active_passes[pass_token]
            if cached.get("expires_at", 0) > now:
                return cached
            else:
                self._cache_active_passes.pop(pass_token, None)

        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.cursor()
                cur.execute("SELECT * FROM passes WHERE pass_token = ? AND is_active = 1", (pass_token,))
                row = cur.fetchone()
                if not row:
                    # If VIP code wasn't seeded yet, seed on demand
                    if pass_token in ("WELCOME100", "CLEANWEB100", "VIPAGENT"):
                        exp_ts = now + 31536000
                        cur.execute("""
                        INSERT OR REPLACE INTO passes (pass_token, buyer_email, pass_type, created_at, expires_at, is_active, order_id, credits)
                        VALUES (?, 'vip@cleanweb.ai', 'VIP_PROMO_100', ?, ?, 1, 'promo_instant', 100)
                        """, (pass_token, now, exp_ts))
                        conn.commit()
                        cur.execute("SELECT * FROM passes WHERE pass_token = ?", (pass_token,))
                        row = cur.fetchone()
                    else:
                        return None
                
                if row and row["expires_at"] > now:
                    res = dict(row)
                    self._cache_active_passes[pass_token] = res
                    return res
                return None
            finally:
                conn.close()

    def create_pass(self, pass_token: str, email: str, pass_type: str, duration_sec: int, order_id: str = "", credits: int = 100):
        now = int(time.time())
        expires = now + duration_sec
        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.cursor()
                cur.execute("""
                INSERT OR REPLACE INTO passes (pass_token, buyer_email, pass_type, created_at, expires_at, is_active, order_id, credits)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                """, (pass_token, email, pass_type, now, expires, order_id, credits))
                conn.commit()
                self._cache_active_passes[pass_token] = {
                    "pass_token": pass_token,
                    "buyer_email": email,
                    "pass_type": pass_type,
                    "created_at": now,
                    "expires_at": expires,
                    "is_active": 1,
                    "order_id": order_id,
                    "credits": credits
                }
            finally:
                conn.close()

    def use_pass(self, pass_token: str, deduct_credits: int = 1) -> Tuple[bool, int, Optional[Dict[str, Any]]]:
        """
        Deducts credits from a pass or verifies active duration.
        Returns (is_valid, remaining_credits, pass_dict).
        """
        pass_data = self.get_pass(pass_token)
        if not pass_data:
            return False, 0, None

        current_credits = pass_data.get("credits", 100)
        # If pass is unlimited time-based (e.g. credits == -1 or 'UNLIMITED' in pass_type)
        if current_credits == -1 or "UNLIMITED" in pass_data.get("pass_type", ""):
            return True, 999999, pass_data

        if current_credits < deduct_credits:
            return False, current_credits, pass_data

        new_credits = max(0, current_credits - deduct_credits)
        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.cursor()
                cur.execute("UPDATE passes SET credits = ? WHERE pass_token = ?", (new_credits, pass_data["pass_token"]))
                conn.commit()
                pass_data["credits"] = new_credits
                self._cache_active_passes[pass_data["pass_token"]] = pass_data
                return True, new_credits, pass_data
            finally:
                conn.close()

    # --- Free Trial ---
    def get_trial_usage(self, identifier: str) -> int:
        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.cursor()
                cur.execute("SELECT usage_count FROM free_trials WHERE identifier = ?", (identifier,))
                row = cur.fetchone()
                return row["usage_count"] if row else 0
            finally:
                conn.close()

    def increment_trial_usage(self, identifier: str) -> int:
        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.cursor()
                cur.execute("SELECT usage_count FROM free_trials WHERE identifier = ?", (identifier,))
                row = cur.fetchone()
                count = (row["usage_count"] + 1) if row else 1
                now = int(time.time())
                cur.execute("""
                INSERT OR REPLACE INTO free_trials (identifier, usage_count, last_used_at)
                VALUES (?, ?, ?)
                """, (identifier, count, now))
                conn.commit()
                return count
            finally:
                conn.close()

    # --- Agent Vault ---
    def get_vault(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Finds vault by agent_address or session_key."""
        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.cursor()
                cur.execute("""
                SELECT * FROM agent_vaults 
                WHERE LOWER(agent_address) = ? OR session_key = ?
                """, (identifier.lower(), identifier))
                row = cur.fetchone()
                return dict(row) if row else None
            finally:
                conn.close()

    def deposit_vault(self, agent_address: str, amount_usdc: float, session_key: str) -> Dict[str, Any]:
        now = int(time.time())
        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.cursor()
                cur.execute("SELECT * FROM agent_vaults WHERE LOWER(agent_address) = ?", (agent_address.lower(),))
                row = cur.fetchone()
                if row:
                    new_bal = round(row["balance_usdc"] + amount_usdc, 6)
                    total_dep = round(row["total_deposited"] + amount_usdc, 6)
                    s_key = row["session_key"] or session_key
                    cur.execute("""
                    UPDATE agent_vaults 
                    SET balance_usdc = ?, total_deposited = ?, last_active = ?, session_key = ?
                    WHERE LOWER(agent_address) = ?
                    """, (new_bal, total_dep, now, s_key, agent_address.lower()))
                else:
                    new_bal = amount_usdc
                    total_dep = amount_usdc
                    s_key = session_key
                    cur.execute("""
                    INSERT INTO agent_vaults (agent_address, balance_usdc, total_deposited, total_consumed, session_key, created_at, last_active, query_count)
                    VALUES (?, ?, ?, 0.0, ?, ?, ?, 0)
                    """, (agent_address.lower(), new_bal, total_dep, s_key, now, now))
                conn.commit()
                
                cur.execute("SELECT * FROM agent_vaults WHERE LOWER(agent_address) = ?", (agent_address.lower(),))
                return dict(cur.fetchone())
            finally:
                conn.close()

    def deduct_vault(self, agent_address: str, amount_usdc: float) -> Tuple[bool, float, Optional[Dict[str, Any]]]:
        now = int(time.time())
        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.cursor()
                cur.execute("SELECT * FROM agent_vaults WHERE LOWER(agent_address) = ?", (agent_address.lower(),))
                row = cur.fetchone()
                if not row:
                    return False, 0.0, None
                if row["balance_usdc"] < amount_usdc:
                    return False, row["balance_usdc"], dict(row)
                
                new_bal = round(row["balance_usdc"] - amount_usdc, 6)
                new_consumed = round(row["total_consumed"] + amount_usdc, 6)
                new_queries = row["query_count"] + 1
                cur.execute("""
                UPDATE agent_vaults 
                SET balance_usdc = ?, total_consumed = ?, last_active = ?, query_count = ?
                WHERE LOWER(agent_address) = ?
                """, (new_bal, new_consumed, now, new_queries, agent_address.lower()))
                conn.commit()
                
                cur.execute("SELECT * FROM agent_vaults WHERE LOWER(agent_address) = ?", (agent_address.lower(),))
                return True, new_bal, dict(cur.fetchone())
            finally:
                conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """Telemetry statistics for database health and volume."""
        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) as c FROM used_txs")
                tx_count = cur.fetchone()["c"]

                cur.execute("SELECT COUNT(*) as c, COALESCE(SUM(balance_usdc), 0.0) as total_bal, COALESCE(SUM(total_consumed), 0.0) as total_used FROM agent_vaults")
                v_row = cur.fetchone()
                vault_count = v_row["c"]
                total_vault_balance = round(v_row["total_bal"], 4)
                total_vault_consumed = round(v_row["total_used"], 4)

                cur.execute("SELECT COUNT(*) as c FROM passes WHERE is_active = 1")
                active_passes = cur.fetchone()["c"]

                return {
                    "used_transactions_count": tx_count,
                    "vault_accounts_count": vault_count,
                    "total_vault_balance_usdc": total_vault_balance,
                    "total_vault_consumed_usdc": total_vault_consumed,
                    "active_passes_count": active_passes,
                    "journal_mode": "WAL",
                    "cache_tx_size": len(self._cache_used_txs)
                }
            finally:
                conn.close()


storage_manager = StorageManager()

