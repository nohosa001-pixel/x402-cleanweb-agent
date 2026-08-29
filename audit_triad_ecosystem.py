import requests
import json
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

SERVICES = {
    "1. 🌐 CleanWeb Studio (x402-cleanweb-agent)": {
        "base_url": "https://x402-cleanweb-agent-212942243360.asia-northeast3.run.app",
        "tests": [
            {"name": "Health Check", "path": "/health", "method": "GET", "headers": {}},
            {"name": "Clean Web", "path": "/api/v1/clean-web?url=https://paulgraham.com/greatwork.html", "method": "GET", "headers": {"X-Agent-Nonce": "audit_1"}},
            {"name": "YouTube Gemini AI", "path": "/api/v1/clean-youtube?url=https://www.youtube.com/watch?v=aircAruvnKk", "method": "GET", "headers": {"X-Agent-Nonce": "audit_2"}},
        ]
    },
    "2. 🪨 Minerals Oracle (minerals-oracle-x402)": {
        "base_url": "https://minerals-oracle-x402-212942243360.asia-northeast3.run.app",
        "tests": [
            {"name": "Health Check", "path": "/health", "method": "GET", "headers": {}},
            {"name": "Live Alpha Signals", "path": "/api/v1/oracle/alpha-signals", "method": "GET", "headers": {}},
            {"name": "Dashboard Web", "path": "/dashboard", "method": "GET", "headers": {}},
        ]
    },
    "3. 🛡️ Security Gate (agent-security-gate-x402)": {
        "base_url": "https://agent-security-gate-x402-212942243360.asia-northeast3.run.app",
        "tests": [
            {"name": "Health Check", "path": "/health", "method": "GET", "headers": {}},
            {"name": "Free Trial / Scan", "path": "/api/v1/inspect", "method": "POST", "headers": {"X-Agent-Nonce": "audit_sec_123"}, "json": {"agent_output": "System status: All operational. Quarterly net profit reached $1.2M with zero critical vulnerabilities.", "is_code": False}},
        ]
    }
}

print("=========================================================================")
print("🚀 [TRIAD ECOSYSTEM LIVE AUDIT] 3대 핵심 x402 서비스 실시간 정밀 점검")
print("=========================================================================\n")

summary_results = []

for svc_name, cfg in SERVICES.items():
    print(f"\n─────────────────────────────────────────────────────────────────────────")
    print(f"📌 {svc_name}")
    print(f"🔗 Base URL: {cfg['base_url']}")
    print(f"─────────────────────────────────────────────────────────────────────────")
    
    svc_passed = True
    for t in cfg["tests"]:
        url = cfg["base_url"] + t["path"]
        start_t = time.time()
        try:
            if t["method"] == "GET":
                r = requests.get(url, headers=t.get("headers", {}), timeout=35)
            else:
                r = requests.post(url, headers=t.get("headers", {}), json=t.get("json", {}), timeout=35)
            elapsed = round((time.time() - start_t) * 1000, 1)
            status = r.status_code
            
            detail = ""
            if "application/json" in r.headers.get("content-type", ""):
                data = r.json()
                if "status" in data:
                    detail = f"status={data['status']}"
                elif "verdict" in data:
                    detail = f"verdict={data.get('verdict')}, risk={data.get('risk_score', 0)}"
                elif "title" in data:
                    detail = f"title={data['title'][:30]}..."
                elif "alpha_signals" in data:
                    detail = f"signals_count={len(data.get('alpha_signals', []))}"
                else:
                    detail = f"keys={list(data.keys())[:3]}"
            else:
                detail = f"HTML/Text ({len(r.text)} bytes)"
                
            is_ok = (200 <= status < 300) or (status == 402 and "x402" in r.text.lower())
            icon = "✅ PASS" if is_ok else f"⚠️ HTTP {status}"
            print(f"  [{icon}] {t['name']:<22} => HTTP {status} ({elapsed}ms) | {detail}")
            if not is_ok:
                svc_passed = False
        except Exception as e:
            print(f"  [❌ FAIL] {t['name']:<22} => Error: {str(e)[:60]}")
            svc_passed = False
            
    summary_results.append((svc_name, svc_passed))

print("\n=========================================================================")
print("📊 [FINAL AUDIT SUMMARY]")
for name, passed in summary_results:
    status_str = "🟢 FULLY OPERATIONAL (100% PASS)" if passed else "🔴 ACTION NEEDED"
    print(f"• {name:<45} : {status_str}")
print("=========================================================================")
