import sqlite3
import shutil
import os

db_path = "data/x402_store.db"
bak_path = "data/x402_store.db.bak"

if os.path.exists(db_path):
    shutil.copyfile(db_path, bak_path)
    print(f"Backed up to {bak_path}")

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Remove test timestamps and fixture mock wallets
c.execute("DELETE FROM agent_vaults WHERE agent_address LIKE '0x1a0%' OR agent_address LIKE '0x9999%' OR agent_address = '0x1111111111111111111111111111111111111111'")
c.execute("DELETE FROM free_trials WHERE identifier LIKE '%test%' OR identifier LIKE '%audit%' OR identifier LIKE 'agent_nonce_%'")

conn.commit()

stats = c.execute("SELECT COUNT(*), COALESCE(SUM(balance_usdc), 0), COALESCE(SUM(total_consumed), 0) FROM agent_vaults").fetchone()
trials = c.execute("SELECT COUNT(*) FROM free_trials").fetchone()[0]
passes = c.execute("SELECT COUNT(*) FROM passes").fetchone()[0]

print(f"Cleaned Database Status:")
print(f"- Vault Accounts: {stats[0]}")
print(f"- Vault Balance: {stats[1]:.4f} USDC")
print(f"- Consumed: {stats[2]:.4f} USDC")
print(f"- Active Passes: {passes}")
print(f"- Real Free Trials: {trials}")

conn.close()
