import os
from unittest.mock import patch, MagicMock
from fastapi import Request
from app.schemas import PricingTier
from app.x402_verifier import X402Verifier, FREE_TRIAL_ELIGIBLE_TIERS


def _make_mock_request(ip: str = "203.0.113.55", nonce: str = "nonce_1") -> Request:
    req = MagicMock(spec=Request)
    req.headers = {"x-agent-nonce": nonce, "x-forwarded-for": ip}
    req.client = MagicMock()
    req.client.host = ip
    req.url = MagicMock()
    req.url.path = "/api/v1/clean-web"
    return req


def test_expensive_tiers_blocked_from_free_trial_in_production():
    verifier = X402Verifier()
    req = _make_mock_request(ip="198.51.100.10", nonce="fresh_nonce")

    with patch.dict(os.environ, {"ENVIRONMENT": "production"}), patch("app.x402_verifier.sys") as mock_sys:
        mock_sys.modules = {}  # Simulate non-pytest production runtime
        for tier in [PricingTier.DEEP_RESEARCH, PricingTier.ORACLE_GROUNDING, PricingTier.HEAVY, PricingTier.EXTRACT_JSON]:
            assert tier not in FREE_TRIAL_ELIGIBLE_TIERS
            is_auth, receipt, err_resp = verifier.verify_request(req, tier=tier)
            assert is_auth is False
            assert receipt is None
            assert err_resp is not None
            assert err_resp.status_code == 402


def test_light_tier_ip_enforced_prevents_nonce_rotation_bypass():
    verifier = X402Verifier()
    usage_store = {}

    def mock_get(key):
        return usage_store.get(key, 0)

    def mock_inc(key):
        usage_store[key] = usage_store.get(key, 0) + 1

    with patch.dict(os.environ, {"ENVIRONMENT": "production"}), \
         patch("app.x402_verifier.sys") as mock_sys, \
         patch("app.x402_verifier.FREE_TRIAL_LIMIT", 3), \
         patch("app.x402_verifier.storage_manager.get_trial_usage", side_effect=mock_get), \
         patch("app.x402_verifier.storage_manager.increment_trial_usage", side_effect=mock_inc):
        mock_sys.modules = {}

        # Calls 1, 2, 3 with DIFFERENT nonces from same IP should succeed (3 total)
        for i in range(1, 4):
            req = _make_mock_request(ip="198.51.100.22", nonce=f"rotating_nonce_{i}")
            is_auth, receipt, err_resp = verifier.verify_request(req, tier=PricingTier.LIGHT)
            assert is_auth is True
            assert receipt is not None

        # Call 4 with yet another rotating nonce from same IP MUST fail with 402
        req4 = _make_mock_request(ip="198.51.100.22", nonce="rotating_nonce_4")
        is_auth, receipt, err_resp = verifier.verify_request(req4, tier=PricingTier.LIGHT)
        assert is_auth is False
        assert err_resp is not None
        assert err_resp.status_code == 402
