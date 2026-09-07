#!/usr/bin/env python3
"""
CleanWeb Studio (x402 AI Agent Suite) - Autonomous Diagnostic Watchdog CLI.
Real-time deep self-audit runner across 5 mission-critical agent pipelines.
"""

import sys
import io
import time
import json
import argparse

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app.diagnostics import diagnostic_engine

# ANSI Color Codes
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_CYAN = "\033[96m"
COLOR_MAGENTA = "\033[95m"
COLOR_BOLD = "\033[1m"
COLOR_DIM = "\033[2m"
COLOR_RESET = "\033[0m"


def format_status(status_str: str) -> str:
    if status_str == "HEALTHY":
        return f"{COLOR_GREEN}{COLOR_BOLD}● HEALTHY{COLOR_RESET}"
    elif status_str == "DEGRADED":
        return f"{COLOR_YELLOW}{COLOR_BOLD}▲ DEGRADED{COLOR_RESET}"
    elif status_str == "CRITICAL":
        return f"{COLOR_RED}{COLOR_BOLD}✖ CRITICAL{COLOR_RESET}"
    return status_str


def print_watchdog_dashboard(audit: dict):
    overall = audit.get("system_health", "UNKNOWN")
    score = audit.get("overall_score", "")
    latency = audit.get("total_audit_latency_ms", 0.0)
    ts = audit.get("audit_timestamp_utc", "")

    if "ALL_SYSTEMS" in overall:
        banner_color = COLOR_GREEN
        banner_symbol = "✔ ALL SYSTEMS OPERATIONAL"
    elif "DEGRADED" in overall:
        banner_color = COLOR_YELLOW
        banner_symbol = "▲ DEGRADED PERFORMANCE DETECTED"
    else:
        banner_color = COLOR_RED
        banner_symbol = "✖ CRITICAL ATTENTION REQUIRED"

    print()
    print(f"{COLOR_CYAN}{COLOR_BOLD}╔══════════════════════════════════════════════════════════════════════════════╗{COLOR_RESET}")
    print(f"{COLOR_CYAN}{COLOR_BOLD}║      🏥 CleanWeb Studio x402 — Autonomous Self-Diagnostic Watchdog           ║{COLOR_RESET}")
    print(f"{COLOR_CYAN}{COLOR_BOLD}╚══════════════════════════════════════════════════════════════════════════════╝{COLOR_RESET}")
    print(f" {COLOR_DIM}Timestamp (UTC): {ts}  │  Total Scan Latency: {latency}ms{COLOR_RESET}")
    print()

    print(f" {COLOR_BOLD}SYSTEM VERDICT:{COLOR_RESET} {banner_color}{COLOR_BOLD}[ {banner_symbol} ]{COLOR_RESET}  {COLOR_CYAN}({score}){COLOR_RESET}")
    print(" ─" * 38)
    print()

    # Pipelines Table
    print(f" {COLOR_BOLD}{'PIPELINE SUBSYSTEM':<42} {'STATUS':<18} {'LATENCY':<10} {'DETAILS'}{COLOR_RESET}")
    print(" ─" * 38)

    for p in audit.get("pipelines", []):
        name = p.get("name", "Unknown")
        st = format_status(p.get("status", "UNKNOWN"))
        lat = f"{p.get('latency_ms', 0):.1f}ms"
        details = p.get("details", "")
        if len(details) > 42:
            details = details[:39] + "..."

        print(f"  {COLOR_BOLD}{name:<40}{COLOR_RESET} {st:<27} {COLOR_DIM}{lat:<10}{COLOR_RESET} {details}")

    print(" ─" * 38)
    print()

    # Anomaly Troubleshooting Hints if Degraded or Critical
    issues = [p for p in audit.get("pipelines", []) if p.get("status") in ("DEGRADED", "CRITICAL")]
    if issues:
        print(f" {COLOR_RED}{COLOR_BOLD}⚠️  Detected {len(issues)} Subsystem Anomalies:{COLOR_RESET}")
        for idx, item in enumerate(issues, 1):
            name = item.get("name")
            err = item.get("error", item.get("details"))
            print(f"   {idx}. {COLOR_BOLD}{name}{COLOR_RESET}: {err}")
        print()
    else:
        print(f" {COLOR_GREEN}✔ All 5 mission-critical agent pipelines verified with zero defects.{COLOR_RESET}")
        print()


def main():
    parser = argparse.ArgumentParser(description="CleanWeb x402 Diagnostic Watchdog CLI")
    parser.add_argument("--json", action="store_true", help="Output raw JSON format for CI/CD")
    parser.add_argument("--loop", action="store_true", help="Run continuously in watchdog polling loop")
    parser.add_argument("--interval", type=int, default=10, help="Polling interval in seconds (default: 10)")
    args = parser.parse_args()

    while True:
        audit = diagnostic_engine.run_full_diagnostic()

        if args.json:
            print(json.dumps(audit, indent=2))
        else:
            print_watchdog_dashboard(audit)

        is_critical = any(p.get("status") == "CRITICAL" for p in audit.get("pipelines", []))

        if not args.loop:
            sys.exit(1 if is_critical else 0)

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
