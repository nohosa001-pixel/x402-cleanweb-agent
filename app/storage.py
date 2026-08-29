"""
Persistent SQLite Storage Layer for Passes, Replay Protection, Free Trials, and Pre-funded Vault Accounts.
"""

import os
import sqlite3
import time
import threading
from typing import Optional, Dict, Any, Tuple, List


class StorageManager:
    """Thread-safe SQLite storage manager."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            data_dir = os.getenv("DATA_DIR", "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "x402_store.db")
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=15)
        conn.row_factory = sqlite3.Row
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
                    order_id TEXT
                )
                """)
                
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

    # --- Replay Protection ---
    def is_tx_used(self, tx_hash: str) -> bool:
        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM used_txs WHERE tx_hash = ?", (tx_hash.lower(),))
                return cur.fetchone() is not None
            finally:
                conn.close()

    def record_used_tx(self, tx_hash: str, chain: str, payer: str, amount_usdc: float):
        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.cursor()
                cur.execute("""
                INSERT OR REPLACE INTO used_txs (tx_hash, chain, payer, amount_usdc, used_at)
                VALUES (?, ?, ?, ?, ?)
                """, (tx_hash.lower(), chain.lower(), payer.lower(), amount_usdc, int(time.time())))
                conn.commit()
            finally:
                conn.close()

    # --- Passes ---
    def get_pass(self, pass_token: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.cursor()
                cur.execute("SELECT * FROM passes WHERE pass_token = ? AND is_active = 1", (pass_token,))
                row = cur.fetchone()
                if not row:
                    return None
                now = int(time.time())
                if row["expires_at"] > now:
                    return dict(row)
                return None
            finally:
                conn.close()

    def create_pass(self, pass_token: str, email: str, pass_type: str, duration_sec: int, order_id: str = ""):
        now = int(time.time())
        expires = now + duration_sec
        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.cursor()
                cur.execute("""
                INSERT OR REPLACE INTO passes (pass_token, buyer_email, pass_type, created_at, expires_at, is_active, order_id)
                VALUES (?, ?, ?, ?, ?, 1, ?)
                """, (pass_token, email, pass_type, now, expires, order_id))
                conn.commit()
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
                    new_bal = row["balance_usdc"] + amount_usdc
                    total_dep = row["total_deposited"] + amount_usdc
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


storage_manager = StorageManager()
