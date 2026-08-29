"""
Interactive CLI Tester and Automated Diagnostic Suite for CleanWeb Studio (x402-cleanweb-agent).
"""

import sys
import os
import time
import json
from fastapi.testclient import TestClient

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

from app.main import app
from app.vault_manager import vault_manager
from app.onchain_signer import onchain_signer
from app.multi_chain import multi_chain_manager

client = TestClient(app)


def print_banner():
    print("=========================================================================")
    print("🚀 [CleanWeb Studio] x402 AI Agent Suite Interactive & Diagnostic Tester")
    print("=========================================================================")


def run_automated_suite():
    print("\n⚡ [RUNNING AUTOMATED DIAGNOSTIC SUITE] ...\n")
    passed = 0
    total = 0

    # Test 1: Health Check
    total += 1
    r = client.get("/health")
    if r.status_code == 200 and r.json().get("status") == "healthy":
        print("  [✅ PASS] Health Check Endpoint")
        passed += 1
    else:
        print(f"  [❌ FAIL] Health Check Endpoint: {r.status_code}")

    # Test 2: AP2 Protocol Manifest
    total += 1
    r = client.get("/.well-known/ap2")
    if r.status_code == 200 and "settlement" in r.text:
        print("  [✅ PASS] AP2 Protocol Manifest (/.well-known/ap2)")
        passed += 1
    else:
        print(f"  [❌ FAIL] AP2 Manifest: {r.status_code}")

    # Test 3: Clean Web (Free Sandbox Trial)
    total += 1
    r = client.get("/api/v1/clean-web?url=https://example.com", headers={"X-Agent-Nonce": f"test_nonce_{int(time.time())}"})
    if r.status_code == 200 and "Example Domain" in r.text:
        print("  [✅ PASS] Clean Web (Instant Sandbox Free Trial)")
        passed += 1
    else:
        print(f"  [❌ FAIL] Clean Web: {r.status_code} - {r.text[:100]}")

    # Test 4: Clean Web with EIP-712 Attestation
    total += 1
    r = client.get("/api/v1/clean-web?url=https://example.com&onchain_proof=true", headers={"Authorization": "Bearer dev-bypass"})
    if r.status_code == 200 and "onchain_proof" in r.json() and r.json()["onchain_proof"] is not None:
        print("  [✅ PASS] Clean Web EIP-712 Cryptographic Attestation & ABI Calldata")
        passed += 1
    else:
        print(f"  [❌ FAIL] EIP-712 Attestation: {r.status_code}")

    # Test 5: Vault Pre-funded Balance & Deduction
    total += 1
    demo_key = "vault_key_demo_agent_sandbox_2026"
    r = client.get("/api/v1/clean-web?url=https://example.com", headers={"X-Vault-Key": demo_key})
    if r.status_code == 200 and r.json().get("payment_receipt", {}).get("payment_method") == "VAULT_BALANCE":
        rem = r.json()["payment_receipt"].get("remaining_vault_balance")
        print(f"  [✅ PASS] Pre-funded Vault Automatic Deduction (Remaining: ${rem:.4f} USDC)")
        passed += 1
    else:
        print(f"  [❌ FAIL] Vault Deduction: {r.status_code}")

    # Test 6: Clean YouTube (oEmbed & AI Summary)
    total += 1
    r = client.get("/api/v1/clean-youtube?url=https://www.youtube.com/watch?v=aircAruvnKk", headers={"Authorization": "Bearer dev-bypass"})
    if r.status_code == 200 and r.json().get("video_id") == "aircAruvnKk":
        print(f"  [✅ PASS] Clean YouTube Video Intelligence (Method: {r.json().get('method_used')})")
        passed += 1
    else:
        print(f"  [❌ FAIL] Clean YouTube: {r.status_code}")

    # Test 7: Multi-Chain Config Verification
    total += 1
    poly = multi_chain_manager.get_chain_config("polygon")
    base = multi_chain_manager.get_chain_config("base")
    arb = multi_chain_manager.get_chain_config("arbitrum")
    if poly.chain_id == 137 and base.chain_id == 8453 and arb.chain_id == 42161:
        print("  [✅ PASS] Multi-Chain Registry (Polygon, Base, Arbitrum One)")
        passed += 1
    else:
        print("  [❌ FAIL] Multi-Chain Registry mismatch")

    print("\n" + "=" * 73)
    print(f"📊 [DIAGNOSTIC SUMMARY] {passed}/{total} Tests Passed (100% Success Rate)" if passed == total else f"⚠️ {passed}/{total} Passed")
    print("=" * 73 + "\n")


def interactive_menu():
    print_banner()
    while True:
        print("\n--- 🛠️ [CleanWeb Studio Tester Menu] ---")
        print("1. 🌐 Test Clean Web Content (Markdown Scraper)")
        print("2. 🎬 Test YouTube Video AI Intelligence")
        print("3. 📄 Test PDF Paper Parser")
        print("4. 💳 Test Vault Balance & Deposit")
        print("5. 🛡️ Test EIP-712 Cryptographic Signer & Calldata")
        print("6. ⚡ Run All Automated Diagnostic Tests")
        print("0. 🚪 Exit")
        
        choice = input("\nEnter choice [0-6]: ").strip()
        if choice == "0":
            print("Goodbye!")
            break
        elif choice == "1":
            target = input("Enter webpage URL (default: https://paulgraham.com/greatwork.html): ").strip() or "https://paulgraham.com/greatwork.html"
            r = client.get(f"/api/v1/clean-web?url={target}", headers={"Authorization": "Bearer dev-bypass"})
            print(f"\nResponse [HTTP {r.status_code}]:")
            data = r.json()
            print(f"Title: {data.get('title')}")
            print(f"Word Count: {data.get('word_count')}")
            print(f"Preview: {data.get('markdown_content', '')[:300]}...")
        elif choice == "2":
            target = input("Enter YouTube URL (default: https://www.youtube.com/watch?v=aircAruvnKk): ").strip() or "https://www.youtube.com/watch?v=aircAruvnKk"
            r = client.get(f"/api/v1/clean-youtube?url={target}", headers={"Authorization": "Bearer dev-bypass"})
            print(f"\nResponse [HTTP {r.status_code}]:")
            data = r.json()
            print(f"Title: {data.get('title')}")
            print(f"Method: {data.get('method_used')}")
            print(f"Summary: {data.get('ai_summary', '')[:300]}...")
        elif choice == "3":
            target = input("Enter PDF URL: ").strip() or "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
            r = client.get(f"/api/v1/clean-pdf?url={target}", headers={"Authorization": "Bearer dev-bypass"})
            print(f"\nResponse [HTTP {r.status_code}]:")
            print(r.json())
        elif choice == "4":
            acc = vault_manager.get_balance("vault_key_demo_agent_sandbox_2026")
            print(f"\nDemo Vault Balance: ${acc['balance_usdc']} USDC | Address: {acc['agent_address']}")
        elif choice == "5":
            proof = onchain_signer.sign_cleanweb_attestation("https://example.com", "Example Content for Attestation")
            print(f"\nOracle Signer: {proof.oracle_signer}")
            print(f"Content Hash: {proof.content_hash}")
            print(f"ABI Calldata: {proof.abi_calldata[:66]}...")
        elif choice == "6":
            run_automated_suite()
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--auto-test", "-a", "--test"):
        print_banner()
        run_automated_suite()
    else:
        interactive_menu()
