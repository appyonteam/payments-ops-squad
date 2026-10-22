import ast
import io
import json
import os
import sys
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools")
sys.path.insert(0, TOOLS)
import chargeblast_watch  # noqa: E402

NOW = datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc)
KEY = "test-key-not-real-123"
ALERTS = [
    {"id": "alert-a", "subprovider": "Ethoca", "reasonCode": "WIP", "createdAt": "2026-01-09T00:00:00.000+0000", "isMatched": True, "matchScore": 100, "amount": 19, "currency": "USD"},
    {"id": "alert-b", "subprovider": "CDRN", "reasonCode": "WIP", "createdAt": "2026-01-10T10:00:00.000+0000", "isMatched": False, "amount": 29.9, "currency": "USD"},
    {"id": "alert-c", "subprovider": "Ethoca", "reasonCode": "Resolved", "createdAt": "2026-01-10T10:00:00.000+0000", "isMatched": True, "amount": 9.9, "currency": "USD"},
    {"id": "alert-d", "subprovider": "RDR", "reasonCode": "WIP", "createdAt": "2026-01-10T10:00:00.000+0000", "amount": 9.9, "currency": "USD"},
    {"id": "alert-e", "subprovider": "Ethoca", "reasonCode": "WIP", "createdAt": "2026-01-07T00:00:00.000+0000", "isMatched": True, "amount": 9.9, "currency": "USD"},
]


class Handler(BaseHTTPRequestHandler):
    seen = []

    def log_message(self, *a):
        pass

    def do_GET(self):
        Handler.seen.append(("GET", self.path, self.headers.get("X-API-Key"), self.headers.get("User-Agent")))
        body = json.dumps({"alerts": ALERTS}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def _deny(self):
        Handler.seen.append((self.command, self.path, None, None))
        self.send_response(405)
        self.end_headers()

    do_POST = do_PUT = do_PATCH = do_DELETE = _deny


class WatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls._api = chargeblast_watch.API
        chargeblast_watch.API = "http://127.0.0.1:%d" % cls.srv.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        chargeblast_watch.API = cls._api

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        os.environ["CHARGEBLAST_API_KEY"] = KEY
        with redirect_stdout(out), redirect_stderr(err):
            code = chargeblast_watch.main(list(args), now=NOW)
        return code, out.getvalue(), err.getvalue()

    def test_lists_only_unanswered_ethoca_cdrn_within_window(self):
        Handler.seen.clear()
        code, out, _ = self.run_main("--json")
        rows = json.loads(out)["open"]
        self.assertEqual([r["id"] for r in rows], ["alert-e", "alert-a", "alert-b"])
        self.assertLess(rows[0]["hours_left"], 0)  # past the window, still WIP, listed for a human check
        self.assertIn("past the 48 hour window", rows[0]["hint"])
        self.assertIn("matched:", rows[1]["hint"])
        self.assertIn("not matched", rows[2]["hint"])
        self.assertEqual(code, 1)  # alert-a expires in 12 h
        self.assertTrue(all(m == "GET" for m, *_ in Handler.seen))
        self.assertTrue(all(ua and ua.startswith("payments-ops-squad") for *_, ua in Handler.seen))

    def test_key_is_never_printed(self):
        code, out, err = self.run_main()
        self.assertNotIn(KEY, out + err)
        self.assertIn("URGENT alert-a", out)

    def test_naive_timestamp_and_missing_score(self):
        rows = chargeblast_watch.open_alerts([{"id": "x", "subprovider": "Ethoca", "reasonCode": "WIP", "createdAt": "2026-01-10T00:00:00",
                                               "isMatched": True}], NOW)
        self.assertEqual(rows[0]["hours_left"], 36.0)
        self.assertIn("no match score", rows[0]["hint"])

    def test_missing_key(self):
        os.environ.pop("CHARGEBLAST_API_KEY", None)
        err = io.StringIO()
        with redirect_stderr(err), redirect_stdout(io.StringIO()):
            self.assertEqual(chargeblast_watch.main(["--key-env", "CB_KEY_ABSENT"], now=NOW), 2)

    def test_source_uses_only_get(self):
        with open(os.path.join(TOOLS, "chargeblast_watch.py"), encoding="utf-8") as fh:
            src = fh.read()
        for verb in ("POST", "PUT", "PATCH", "DELETE"):
            self.assertNotIn('"%s"' % verb, src)
            self.assertNotIn("'%s'" % verb, src)
        calls = [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.keyword) and n.arg == "method"]
        self.assertTrue(calls and all(isinstance(k.value, ast.Constant) and k.value.value == "GET" for k in calls))
        self.assertNotIn("data=", src)


if __name__ == "__main__":
    unittest.main()
