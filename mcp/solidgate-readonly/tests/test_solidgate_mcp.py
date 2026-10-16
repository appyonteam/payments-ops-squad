"""Tests for the read-only Solidgate MCP. No network. Run: python3 -I -m unittest discover -s tests -t .

(-I does not put the cwd on sys.path; this file inserts the MCP root explicitly.)

Tests that compare the allowlist against the official OpenAPI need the documentation cache filled by
tools/sync_solidgate.py; they are skipped when the cache is absent.
"""

import base64
import hashlib
import hmac
import io
import json
import os
import re
import subprocess
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import sg_analysis  # noqa: E402
import sg_core  # noqa: E402
import server as srv  # noqa: E402

INDEX_PATH = ROOT.parent.parent / "knowledge" / "solidgate" / "indexes" / "openapi-operations.json"


def _cache_dir():
    """Same resolution order as tools/fetch_doc.py (without the script-install marker rule)."""
    env = os.environ.get("PAYMENTS_OPS_KNOWLEDGE")
    if env:
        return Path(env).expanduser()
    data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if data:
        return Path(data).expanduser() / "knowledge"
    return Path.home() / ".claude" / "payments-ops-squad" / "knowledge"


OPENAPI_DIR = _cache_dir() / "solidgate" / "openapi"
HAVE_OPENAPI = (OPENAPI_DIR / "v1.yaml").is_file() and (OPENAPI_DIR / "v2.yaml").is_file()

# Synthetic secrets assembled at runtime (this file does not contain the full literal).
FAKE_PK = "pk_FAKE_TEST_PUBLIC"
FAKE_SK = "sk_FAKE_TEST_SECRET"
FAKE_V2 = "as" + "ec_" + "FAKEFAKEFAKEFAKEFAKE0000"
FAKE_V1_SECRET_SHAPE = "api" + "_sk_" + "FAKEFAKEFAKEFAKE0000"
FAKE_WSEC = "ws" + "ec_" + "FAKEFAKEFAKE000"


class ExplodingClient:
    """Live client that fails the test if it is ever called."""
    def request(self, *a, **k):
        raise AssertionError("the live HTTP client must NOT have been called")


class RecordingClient:
    def __init__(self, status=200, payload=None):
        self.calls, self.status, self.payload = [], status, payload if payload is not None else {"ok": True}

    def request(self, method, url, headers, body, timeout):
        self.calls.append({"method": method, "url": url, "headers": headers, "body": body, "timeout": timeout})
        return self.status, {}, json.dumps(self.payload).encode()


def scan_openapi(path):
    """Indentation-based scanner (no PyYAML): {(method, path): operationId}."""
    out, in_paths, cur_path, cur_method = {}, False, None, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^paths:\s*$", line):
            in_paths = True
            continue
        if in_paths and re.match(r"^\S", line):
            break
        if not in_paths:
            continue
        m = re.match(r"^  (/\S*):\s*$", line)
        if m:
            cur_path, cur_method = m.group(1), None
            continue
        m = re.match(r"^    (get|post|put|patch|delete):\s*$", line)
        if m:
            cur_method = m.group(1).upper()
            continue
        m = re.match(r"^      operationId:\s*(\S+)\s*$", line)
        if m and cur_path and cur_method:
            out[(cur_method, cur_path)] = m.group(1)
    return out


class TestAllowlistAndRefusal(unittest.TestCase):
    def setUp(self):
        self.d = sg_core.Dispatcher(env={}, live_client=ExplodingClient())

    def test_write_operation_ids_refused_explicitly(self):
        for op in ["refund-card-order", "void-card-order", "settle-card-order", "make-card-charge",
                   "cancel-subscription", "create-product", "update-subscription", "delete-invoice",
                   "make-card-resign", "pay-invoice", "revoke-payment-instrument", "rotate-api-key",
                   "refund_card_order", "v2_cancel_subscription"]:
            with self.assertRaises(sg_core.WriteRefused, msg=op):
                self.d.call(op, {})

    def test_unknown_operation_refused(self):
        with self.assertRaises(sg_core.UnknownOperation):
            self.d.call("get-the-moon", {})
        with self.assertRaises(sg_core.UnknownOperation):
            self.d.allow.resolve("v1_nao_existe")

    def test_no_allowlisted_tool_has_write_semantics_in_index(self):
        idx = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        by = {(v, o["operationId"]): o for v, x in idx["versions"].items() for o in x["operations"]}
        reviewed_report_generators = {"prevention-alerts-by-date", "financial-entries-by-date", "routing-events-by-date"}
        for s in self.d.allow.by_tool.values():
            o = by[s.key]
            self.assertNotEqual(o["semantics"], "write", s["tool"])
            if o["semantics"] == "indeterminate":
                self.assertIn(s["operationId"], reviewed_report_generators)

    def test_ambiguous_operation_id_requires_version(self):
        # get-subscription exists only in v2 among the tools, but cancel-subscription exists in v1 and v2 (a write)
        with self.assertRaises(sg_core.WriteRefused):
            self.d.allow.resolve("cancel-subscription")

    def test_server_refuses_write_via_tools_call(self):
        s = srv.Server(self.d)
        with redirect_stderr(io.StringIO()):
            r = s.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                          "params": {"name": "refund-card-order", "arguments": {"order_id": "x"}}})
        self.assertTrue(r["result"]["isError"])
        self.assertIn("WriteRefused", r["result"]["content"][0]["text"])


@unittest.skipUnless(HAVE_OPENAPI, "OpenAPI cache missing: run tools/sync_solidgate.py first")
class TestMappingToOpenApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ops = {"v1": scan_openapi(OPENAPI_DIR / "v1.yaml"), "v2": scan_openapi(OPENAPI_DIR / "v2.yaml")}
        cls.specs = sg_core.load_specs()

    def test_scanner_sanity(self):
        self.assertGreaterEqual(len(self.ops["v1"]), 60)
        self.assertGreaterEqual(len(self.ops["v2"]), 50)

    def test_every_tool_maps_to_real_operation(self):
        self.assertGreater(len(self.specs), 0)
        for s in self.specs.values():
            got = self.ops[s["version"]].get((s["method"], s["path"]))
            self.assertEqual(got, s["operationId"], f"{s['tool']} does not map to the real operationId")

    def test_tool_names_encode_version_and_are_unique(self):
        names = list(self.specs)
        self.assertEqual(len(names), len(set(names)))
        for n, s in self.specs.items():
            self.assertTrue(n.startswith(s["version"] + "_"), n)

    def test_hosts_match_version(self):
        for s in self.specs.values():
            if s["version"] == "v2":
                self.assertEqual(s["host"], "https://api.solidgate.com/v2")
            else:
                self.assertTrue(s["host"].startswith("https://") and s["host"].split("/")[2] in sg_core.ALLOWED_HOSTS)


class TestRedaction(unittest.TestCase):
    def test_pan_luhn_redacted_non_luhn_kept(self):
        pan = "4" + "111" + "1111" + "1111" + "1111"
        self.assertNotIn(pan, sg_core.redact_text(f"card {pan} ok"))
        self.assertIn("[REDACTED_PAN]", sg_core.redact_text(f"card {' '.join([pan[i:i+4] for i in range(0,16,4)])}"))
        self.assertIn("1234567890123456", sg_core.redact_text("id 1234567890123456"))  # non-Luhn: preserved

    def test_email_and_secret_patterns(self):
        t = sg_core.redact_text(f"user@example.com {FAKE_V2} {FAKE_V1_SECRET_SHAPE} {FAKE_WSEC} Bearer abcdefgh12345678")
        for leaked in ("user@example.com", FAKE_V2, FAKE_V1_SECRET_SHAPE, FAKE_WSEC, "abcdefgh12345678"):
            self.assertNotIn(leaked, t)

    def test_sensitive_keys_and_nested(self):
        r = sg_core.redact({"signature": "x", "Authorization": "Bearer zzzzzzzzzz", "cvv": "123", "customer_email": "user@example.com",
                            "card_token": "t", "nested": [{"merchant": FAKE_PK, "bin": "444111", "status": "ok"}]})
        self.assertEqual(r["signature"], sg_core.REDACTED)
        self.assertEqual(r["Authorization"], sg_core.REDACTED)
        self.assertEqual(r["cvv"], sg_core.REDACTED)
        self.assertEqual(r["customer_email"], sg_core.REDACTED)
        self.assertEqual(r["card_token"], sg_core.REDACTED)
        self.assertEqual(r["nested"][0]["merchant"], sg_core.REDACTED)
        self.assertEqual(r["nested"][0]["bin"], "444111")  # useful data preserved

    def test_url_query_string_redacted(self):
        self.assertNotIn("SECRETSIG", sg_core.redact_text("https://x.solidgate.com/r.csv?X-Sig=SECRETSIG&a=1"))

    def test_log_goes_to_stderr_redacted(self):
        buf = io.StringIO()
        with redirect_stderr(buf):
            sg_core.log("t", secret_key=FAKE_SK, text=f"mail user@example.com {FAKE_V2}")
        out = buf.getvalue()
        self.assertNotIn(FAKE_SK, out)
        self.assertNotIn("user@example.com", out)
        self.assertNotIn(FAKE_V2, out)


class TestSignatureV1(unittest.TestCase):
    # Vectors computed externally with `openssl dgst -sha512 -hmac` + base64 (independent of the code under test).
    BODY = '{"order_id":"FAKE-1"}'
    VEC_BODY = ("MjNjNWVjZTQ4Nzg5MTMzYmVkYzY2MWI3OGFkMDZiNjU0NmM0ZDA1YzFhMDgyZTc4OTI0MWUwODQ5ZmRiNDliZGU1MTUzMWE1OGI2YmE5ZjU1M2Zl"
                "ZWQ5MDkwM2RlNTMwZjVlMzg1MjlhMDk5NWQyMjU0NmM0MzlmZWI1MjQyZjY=")
    VEC_EMPTY = ("MjUyMTY5YmY1MGMwMTk2ZmJlMjQ5NjY0YjFmNWZkZjY5NzdhYmEzNDM4OGZkYzVmMmYxZjk3ZDU3NTNmNTU4NzA5ZTNjN2ZhMzA4MDg3YWViZDRl"
                 "NmE4NDVjN2ZkODYyNzk2NjQzNjI0MWI3Nzk3Yjc2ZDRlN2Q4NDU0NDMwZDM=")

    def test_vector_with_body(self):
        self.assertEqual(sg_core.sign_v1(FAKE_PK, FAKE_SK, self.BODY), self.VEC_BODY)

    def test_vector_empty_body_pk_plus_pk(self):
        self.assertEqual(sg_core.sign_v1(FAKE_PK, FAKE_SK, ""), self.VEC_EMPTY)

    def test_matches_independent_computation_in_test(self):
        for body in (self.BODY, "", '{"a": 1}'):
            hx = hmac.new(FAKE_SK.encode(), (FAKE_PK + body + FAKE_PK).encode(), hashlib.sha512).hexdigest()
            self.assertEqual(sg_core.sign_v1(FAKE_PK, FAKE_SK, body), base64.b64encode(hx.encode()).decode())

    def test_live_post_signs_exact_bytes_sent(self):
        rec = RecordingClient()
        d = sg_core.Dispatcher(env={sg_core.ENV_MODE: "live", sg_core.ENV_V1_PK: FAKE_PK, sg_core.ENV_V1_SK: FAKE_SK},
                               live_client=rec)
        with redirect_stderr(io.StringIO()):
            res = d.call("v1_get_status_card_order", {"order_id": "FAKE-1"})
        c = rec.calls[0]
        self.assertEqual(c["url"], "https://pay.solidgate.com/api/v1/status")
        self.assertEqual(c["headers"]["merchant"], FAKE_PK)
        self.assertEqual(c["headers"]["signature"], sg_core.sign_v1(FAKE_PK, FAKE_SK, c["body"].decode()))
        self.assertNotIn("Authorization", c["headers"])
        self.assertIs(res["verified_against_live_api"], False)

    def test_live_get_without_body_signs_pk_pk(self):
        rec = RecordingClient()
        d = sg_core.Dispatcher(env={sg_core.ENV_MODE: "live", sg_core.ENV_V1_PK: FAKE_PK, sg_core.ENV_V1_SK: FAKE_SK}, live_client=rec)
        with redirect_stderr(io.StringIO()):
            d.call("v1_get_product_by_id", {"product_id": "FAKE-P1"})
        c = rec.calls[0]
        self.assertEqual(c["method"], "GET")
        self.assertIsNone(c["body"])
        self.assertEqual(c["headers"]["signature"], self.VEC_EMPTY)
        self.assertTrue(c["url"].endswith("/products/FAKE-P1"))


class TestModesAndCredentials(unittest.TestCase):
    def test_default_mode_is_mock_and_no_network(self):
        d = sg_core.Dispatcher(env={}, live_client=ExplodingClient())
        self.assertEqual(d.mode, "mock")
        with redirect_stderr(io.StringIO()):
            r = d.call("v1_get_status_card_order", {"order_id": "x"})
        self.assertEqual(r["mode"], "mock")
        self.assertIs(r["verified_against_live_api"], False)

    def test_live_without_credential_fails_without_network(self):
        d = sg_core.Dispatcher(env={sg_core.ENV_MODE: "live"}, live_client=ExplodingClient())
        for tool, args in (("v1_get_status_card_order", {"order_id": "x"}), ("v2_get_settlement", {"id": "x"})):
            with self.assertRaises(sg_core.CredentialMissing), redirect_stderr(io.StringIO()):
                d.call(tool, args)

    def test_credential_without_live_flag_stays_mock(self):
        d = sg_core.Dispatcher(env={sg_core.ENV_V2_KEY: FAKE_V2}, live_client=ExplodingClient())
        self.assertEqual(d.mode, "mock")

    def test_v2_bearer_and_host_and_no_v1_headers(self):
        rec = RecordingClient()
        d = sg_core.Dispatcher(env={sg_core.ENV_MODE: "live", sg_core.ENV_V2_KEY: FAKE_V2,
                                    sg_core.ENV_V1_PK: FAKE_PK, sg_core.ENV_V1_SK: FAKE_SK}, live_client=rec)
        with redirect_stderr(io.StringIO()):
            r = d.call("v2_get_settlement", {"id": "FAKE-STL-1"})
        c = rec.calls[0]
        self.assertEqual(c["url"], "https://api.solidgate.com/v2/settlements/get")
        self.assertEqual(c["headers"]["Authorization"], "Bearer " + FAKE_V2)
        self.assertNotIn("signature", c["headers"])
        self.assertNotIn("merchant", c["headers"])
        self.assertNotIn(FAKE_V2, json.dumps(r))  # the key never comes back in the response

    def test_version_mixing_refused(self):
        rec = ExplodingClient()
        d = sg_core.Dispatcher(env={sg_core.ENV_MODE: "live", sg_core.ENV_V2_KEY: FAKE_V1_SECRET_SHAPE}, live_client=rec)
        with self.assertRaises(sg_core.CredentialMissing), redirect_stderr(io.StringIO()):
            d.call("v2_get_settlement", {"id": "x"})
        d = sg_core.Dispatcher(env={sg_core.ENV_MODE: "live", sg_core.ENV_V1_PK: FAKE_PK, sg_core.ENV_V1_SK: FAKE_V2}, live_client=rec)
        with self.assertRaises(sg_core.CredentialMissing), redirect_stderr(io.StringIO()):
            d.call("v1_get_status_card_order", {"order_id": "x"})

    def test_live_response_redacted(self):
        rec = RecordingClient(payload={"customer_email": "user@example.com", "note": "mail you@example.com " + FAKE_V2})
        d = sg_core.Dispatcher(env={sg_core.ENV_MODE: "live", sg_core.ENV_V2_KEY: FAKE_V2}, live_client=rec)
        with redirect_stderr(io.StringIO()):
            r = d.call("v2_get_settlement", {"id": "x"})
        txt = json.dumps(r)
        self.assertNotIn("you@example.com", txt)
        self.assertNotIn("user@example.com", txt)
        self.assertNotIn(FAKE_V2, txt)

    def test_transport_error_is_safe(self):
        class Boom:
            def request(self, *a, **k):
                raise TimeoutError("timed out with " + FAKE_V2)
        d = sg_core.Dispatcher(env={sg_core.ENV_MODE: "live", sg_core.ENV_V2_KEY: FAKE_V2}, live_client=Boom())
        with self.assertRaises(sg_core.SolidgateMcpError) as cm, redirect_stderr(io.StringIO()):
            d.call("v2_get_settlement", {"id": "x"})
        self.assertNotIn(FAKE_V2, str(cm.exception))


class TestValidation(unittest.TestCase):
    def setUp(self):
        self.d = sg_core.Dispatcher(env={}, live_client=ExplodingClient())

    def call(self, *a):
        with redirect_stderr(io.StringIO()):
            return self.d.call(*a)

    def test_missing_required(self):
        with self.assertRaises(sg_core.ValidationFailed):
            self.call("v1_get_status_card_order", {})
        with self.assertRaises(sg_core.ValidationFailed):
            self.call("v1_retrieve_card_orders", {"date_from": "2000-01-01 00:00:00"})

    def test_wrong_type_and_unknown_param(self):
        with self.assertRaises(sg_core.ValidationFailed):
            self.call("v1_get_status_card_order", {"order_id": 123})
        with self.assertRaises(sg_core.ValidationFailed):
            self.call("v1_get_status_card_order", {"order_id": "x", "amount": 1})

    def test_path_param_traversal_refused(self):
        with self.assertRaises(sg_core.ValidationFailed):
            self.call("v1_get_product_by_id", {"product_id": "../../refund"})

    def test_rate_limit(self):
        t = [0.0]
        d = sg_core.Dispatcher(env={}, limiter=sg_core.RateLimiter(per_minute=2, clock=lambda: t[0]))
        with redirect_stderr(io.StringIO()):
            d.call("v1_get_status_card_order", {"order_id": "a"})
            d.call("v1_get_status_card_order", {"order_id": "a"})
            with self.assertRaises(sg_core.RateLimited):
                d.call("v1_get_status_card_order", {"order_id": "a"})
            t[0] = 61.0
            d.call("v1_get_status_card_order", {"order_id": "a"})


class TestAnalysis(unittest.TestCase):
    def test_local_analyses_on_fixture(self):
        d = sg_core.Dispatcher(env={})
        s = srv.Server(d)
        with redirect_stderr(io.StringIO()):
            res = s.call_tool("analyze_approval_rate", {"date_from": "2000-01-01 00:00:00", "date_to": "2000-01-02 00:00:00"})
            dec = s.call_tool("analyze_declines", {"date_from": "2000-01-01 00:00:00", "date_to": "2000-01-02 00:00:00"})
            rt = s.call_tool("analyze_routing", {"date_from": "2000-01-01 00:00:00", "date_to": "2000-01-02 00:00:00"})
        a = json.loads(res["content"][0]["text"])
        self.assertTrue(a["local_analysis"])
        self.assertIs(a["verified_against_live_api"], False)
        self.assertEqual(a["overall"]["declined"], 9)
        self.assertEqual(json.loads(dec["content"][0]["text"])["declined"], 9)
        self.assertEqual(json.loads(rt["content"][0]["text"])["approved_after_cascade"], 2)

    def test_diagnose_flags_drop(self):
        mk = lambda st, mid, n: [{"status": st, "mid": mid} for _ in range(n)]
        base = mk("settle_ok", "M1", 20) + mk("settle_ok", "M2", 20)
        cur = mk("settle_ok", "M1", 20) + mk("auth_failed", "M2", 15) + mk("settle_ok", "M2", 5)
        out = sg_analysis.diagnose_incident(cur, base, group_by=("mid",))
        top = out["hypotheses_ranked_by_drop"][0]
        self.assertEqual((top["group"], top["delta"]), ("M2", -0.75))
        self.assertIn("HYPOTHESES", out["label"])

    def test_bad_input_rejected(self):
        with self.assertRaises(ValueError):
            sg_analysis.analyze_declines("not-a-list")


class TestRepoHygiene(unittest.TestCase):
    def test_no_credentials_in_folder(self):
        pats = [re.compile(p) for p in (r"\basec_[A-Za-z0-9]{12,}", r"\bapi_sk_[A-Za-z0-9]{12,}", r"\bwsec_[A-Za-z0-9]{12,}",
                                        r"(?i)bearer\s+[A-Za-z0-9._\-]{20,}", r"sk_(live|test)_[A-Za-z0-9]{10,}")]
        hits = []
        for p in ROOT.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix in {".py", ".json", ".md", ".rb", ".txt", ""}:
                txt = p.read_text(encoding="utf-8", errors="ignore")
                for pat in pats:
                    if pat.search(txt):
                        hits.append((str(p.relative_to(ROOT)), pat.pattern))
        self.assertEqual(hits, [])

    def test_fixtures_are_synthetic(self):
        files = list((ROOT / "fixtures").rglob("*.json"))
        self.assertGreater(len(files), 5)
        for f in files:
            d = json.loads(f.read_text(encoding="utf-8"))
            self.assertTrue(d.get("_not_evidence"), f.name)
            self.assertNotRegex(f.read_text(encoding="utf-8"), r"@(?!example\.(?:invalid|com)\b)[A-Za-z0-9.-]+\.[a-z]{2,}")

    def test_env_vars_only_names_no_values_in_code(self):
        src = (ROOT / "sg_core.py").read_text(encoding="utf-8")
        self.assertIn("SOLIDGATE_V1_PUBLIC_KEY", src)
        self.assertNotRegex(src, r"os\.environ\[.*\]\s*=")


class TestStdioServer(unittest.TestCase):
    def run_server(self, lines, extra_env=None):
        env = {k: v for k, v in os.environ.items() if not k.startswith("SOLIDGATE_")}
        env.update(extra_env or {})
        p = subprocess.run([sys.executable, "-I", str(ROOT / "server.py")], input="\n".join(lines) + "\n",
                           capture_output=True, text=True, timeout=30, env=env)
        return [json.loads(x) for x in p.stdout.splitlines() if x.strip()], p.stderr

    def test_initialize_list_call_via_stdio_mock(self):
        out, err = self.run_server([
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}}),
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
            json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                        "params": {"name": "v2_get_settlement", "arguments": {"id": "FAKE-STL-0001"}}}),
            json.dumps({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                        "params": {"name": "make-card-charge", "arguments": {}}}),
            json.dumps({"jsonrpc": "2.0", "id": 5, "method": "nope"}),
        ])
        by = {m["id"]: m for m in out}
        self.assertEqual(len(out), 5)  # a notification gets no response
        self.assertEqual(by[1]["result"]["serverInfo"]["name"], "solidgate-readonly")
        tools = by[2]["result"]["tools"]
        self.assertGreaterEqual(len(tools), 40)
        self.assertTrue(all(t["annotations"]["readOnlyHint"] for t in tools))
        self.assertTrue(all(t["inputSchema"]["type"] == "object" for t in tools))
        names = {t["name"] for t in tools}
        self.assertTrue({"analyze_declines", "diagnose_incident", "v1_get_status_card_order", "v2_get_settlement"} <= names)
        body = json.loads(by[3]["result"]["content"][0]["text"])
        self.assertEqual((body["mode"], body["verified_against_live_api"]), ("mock", False))
        self.assertTrue(by[4]["result"]["isError"])
        self.assertEqual(by[5]["error"]["code"], -32601)
        self.assertIn("mode", err)  # log goes to stderr
        self.assertNotIn("jsonrpc", err)

    def test_stdio_does_not_leak_secret_in_stderr_or_stdout(self):
        out, err = self.run_server([
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                        "params": {"name": "v2_get_settlement", "arguments": {"id": "x"}}})],
            extra_env={sg_core.ENV_V2_KEY: FAKE_V2})  # without the live flag it stays in mock
        self.assertNotIn(FAKE_V2, err)
        self.assertNotIn(FAKE_V2, json.dumps(out))
        self.assertEqual(json.loads(out[0]["result"]["content"][0]["text"])["mode"], "mock")


if __name__ == "__main__":
    unittest.main()
