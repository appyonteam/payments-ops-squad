import datetime as dt
import http.server
import io
import os
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import fetch_doc  # noqa: E402

PAGES = {
    "/robots.txt": "User-agent: *\nDisallow: /docs/private\n",
    "/docs/guide.md": "# Guide\nmarkdown body\n",
    "/docs/only-html": "<html>plain page</html>",
    "/docs/private.md": "# secret\n",
    "/docs/llms.txt": "# Index\n- [Guide](/docs/guide.md)\n",
}


class Handler(http.server.BaseHTTPRequestHandler):
    hits = []
    headers_seen = []
    redirects = {}

    def do_GET(self):
        Handler.hits.append(self.path)
        Handler.headers_seen.append(dict(self.headers))
        if self.path in Handler.redirects:
            self.send_response(302)
            self.send_header("Location", Handler.redirects[self.path])
            self.end_headers()
            return
        body = PAGES.get(self.path)
        if body is None:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        ctype = "text/markdown" if self.path.endswith(".md") else "text/plain"
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *args):
        pass


class OutsideHandler(http.server.BaseHTTPRequestHandler):
    """A host outside the allowlist; it must never be contacted."""
    hits = []

    def do_GET(self):
        OutsideHandler.hits.append(self.path)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"User-agent: *\nAllow: /\n")

    def log_message(self, *args):
        pass


class FetchDocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:%d" % cls.server.server_port
        cls.outside = http.server.HTTPServer(("127.0.0.1", 0), OutsideHandler)
        threading.Thread(target=cls.outside.serve_forever, daemon=True).start()
        cls.outside_base = "http://127.0.0.1:%d" % cls.outside.server_port

    @classmethod
    def tearDownClass(cls):
        for s in (cls.server, cls.outside):
            s.shutdown()
            s.server_close()

    def setUp(self):
        self.cache = tempfile.mkdtemp()
        self._saved = (fetch_doc.ALLOWED_PREFIXES, dict(fetch_doc.INDEXES), os.environ.get("PAYMENTS_OPS_KNOWLEDGE"))
        self._saved_scheme = fetch_doc.REQUIRED_SCHEME
        fetch_doc.REQUIRED_SCHEME = "http"
        fetch_doc.ALLOWED_PREFIXES = (self.base + "/docs/",)
        fetch_doc.INDEXES = {"test": self.base + "/docs/llms.txt"}
        fetch_doc._robots_cache.clear()
        os.environ["PAYMENTS_OPS_KNOWLEDGE"] = self.cache
        Handler.hits = []
        Handler.headers_seen = []
        Handler.redirects = {}
        OutsideHandler.hits = []

    def tearDown(self):
        fetch_doc.REQUIRED_SCHEME = self._saved_scheme
        fetch_doc.ALLOWED_PREFIXES, fetch_doc.INDEXES, env = self._saved
        if env is None:
            os.environ.pop("PAYMENTS_OPS_KNOWLEDGE", None)
        else:
            os.environ["PAYMENTS_OPS_KNOWLEDGE"] = env

    def run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = fetch_doc.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_fetches_markdown_variant_with_header(self):
        code, out, _ = self.run_main([self.base + "/docs/guide"])
        self.assertEqual(code, 0)
        self.assertIn("cache stored:", out)
        self.assertIn("source_url: %s/docs/guide.md" % self.base, out)
        self.assertRegex(out, r"fetched_at: \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ")
        self.assertIn("markdown body", out)
        path = out.splitlines()[0].split(": ", 1)[1]
        self.assertTrue(path.startswith(self.cache))

    def test_falls_back_to_plain_url(self):
        code, out, _ = self.run_main([self.base + "/docs/only-html"])
        self.assertEqual(code, 0)
        self.assertIn("source_url: %s/docs/only-html\n" % self.base, out)

    def test_cache_hit(self):
        self.run_main([self.base + "/docs/guide"])
        before = len([h for h in Handler.hits if h != "/robots.txt"])
        code, out, _ = self.run_main([self.base + "/docs/guide"])
        after = len([h for h in Handler.hits if h != "/robots.txt"])
        self.assertEqual(code, 0)
        self.assertIn("cache hit:", out)
        self.assertEqual(before, after)

    def test_ttl_expired_and_refresh(self):
        url = self.base + "/docs/guide"
        old = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=20)
        fetch_doc.fetch(url, now=old)
        path, _, hit = fetch_doc.fetch(url, max_age_days=14)
        self.assertFalse(hit)
        path, _, hit = fetch_doc.fetch(url, max_age_days=14)
        self.assertTrue(hit)
        code, out, _ = self.run_main([url, "--refresh"])
        self.assertIn("cache stored:", out)
        self.assertTrue(fetch_doc.fetch(url, max_age_days=30)[2])
        self.assertFalse(fetch_doc.fetch(url, max_age_days=0)[2])

    def test_refuses_other_domain(self):
        for url in ["https://example.com/docs/guide", "https://docs.stripe.com.evil.example/x",
                    self.base + "/other/page", self.base + "/docs/../robots.txt"]:
            code, _, err = self.run_main([url])
            self.assertEqual(code, 2, url)
            self.assertIn("refused", err)
        self.assertEqual(Handler.hits, [])

    def test_real_allowlist_is_official_docs_only(self):
        fetch_doc.ALLOWED_PREFIXES = self._saved[0]
        self.assertTrue(fetch_doc.is_allowed("https://docs.stripe.com/declines/codes"))
        self.assertTrue(fetch_doc.is_allowed("https://primer.io/docs/payments"))
        self.assertTrue(fetch_doc.is_allowed("https://funnelfox.com/docs/integrations/index.md"))
        self.assertFalse(fetch_doc.is_allowed("http://docs.stripe.com/declines"))
        self.assertFalse(fetch_doc.is_allowed("https://primer.io/blog/post"))
        self.assertFalse(fetch_doc.is_allowed("https://user:pw" + "@docs.stripe.com/x"))

    def test_redirect_outside_allowlist_refused_before_request(self):
        Handler.redirects = {"/docs/moved.md": self.outside_base + "/docs/moved.md"}
        code, _, err = self.run_main([self.base + "/docs/moved"])
        self.assertEqual(code, 2)
        self.assertIn("refused", err)
        self.assertIn("/docs/moved.md", Handler.hits)
        self.assertEqual(OutsideHandler.hits, [])

    def test_redirect_inside_allowlist_followed(self):
        Handler.redirects = {"/docs/old.md": "/docs/guide.md"}
        code, out, _ = self.run_main([self.base + "/docs/old"])
        self.assertEqual(code, 0)
        self.assertIn("source_url: %s/docs/guide.md" % self.base, out)

    def test_robots_redirect_outside_refused_before_request(self):
        Handler.redirects = {"/robots.txt": self.outside_base + "/robots.txt"}
        code, _, err = self.run_main([self.base + "/docs/guide"])
        self.assertEqual(code, 2)
        self.assertIn("refused", err)
        self.assertEqual(OutsideHandler.hits, [])
        self.assertNotIn("/docs/guide.md", Handler.hits)

    def test_redirect_requires_https_on_every_hop(self):
        fetch_doc.REQUIRED_SCHEME = "https"
        fetch_doc.ALLOWED_PREFIXES = self._saved[0]
        handler = fetch_doc._GuardedRedirect(fetch_doc.is_allowed)
        req = fetch_doc.urllib.request.Request("https://docs.stripe.com/a")
        with self.assertRaises(fetch_doc.Refused):
            handler.redirect_request(req, None, 302, "Found", {}, "http://docs.stripe.com/b")
        with self.assertRaises(fetch_doc.Refused):
            handler.redirect_request(req, None, 302, "Found", {}, "https://example.com/docs/b")
        robots = fetch_doc._GuardedRedirect(lambda u: fetch_doc._robots_target_ok(u, "docs.stripe.com"))
        with self.assertRaises(fetch_doc.Refused):
            robots.redirect_request(req, None, 302, "Found", {}, "http://docs.stripe.com/robots.txt")
        with self.assertRaises(fetch_doc.Refused):
            robots.redirect_request(req, None, 302, "Found", {}, "https://example.com/robots.txt")
        ok = robots.redirect_request(req, None, 302, "Found", {}, "https://docs.stripe.com/robots.txt")
        self.assertEqual(ok.full_url, "https://docs.stripe.com/robots.txt")

    def test_sends_accept_language_en(self):
        code, _, _ = self.run_main([self.base + "/docs/guide"])
        self.assertEqual(code, 0)
        self.assertTrue(Handler.headers_seen)
        for h in Handler.headers_seen:
            self.assertEqual(h.get("Accept-Language"), "en")

    def test_robots_disallow(self):
        code, _, err = self.run_main([self.base + "/docs/private"])
        self.assertEqual(code, 3)
        self.assertIn("robots.txt", err)
        self.assertNotIn("/docs/private.md", Handler.hits)

    def test_index(self):
        code, out, _ = self.run_main(["--index", "test"])
        self.assertEqual(code, 0)
        self.assertIn("source_url: %s/docs/llms.txt" % self.base, out)

    def test_missing_page_is_fetch_error(self):
        code, _, err = self.run_main([self.base + "/docs/nope"])
        self.assertEqual(code, 1)
        self.assertIn("HTTP 404", err)

    def test_script_install_sibling_cache(self):
        import importlib.util, shutil
        os.environ.pop("PAYMENTS_OPS_KNOWLEDGE", None)
        saved = os.environ.pop("CLAUDE_PLUGIN_DATA", None)
        try:
            home = tempfile.mkdtemp()
            tools = os.path.join(home, "payments-ops-squad", "tools")
            os.makedirs(tools)
            shutil.copy(fetch_doc.__file__, tools)
            spec = importlib.util.spec_from_file_location("fetch_doc_copy", os.path.join(tools, "fetch_doc.py"))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            knowledge = os.path.join(home, "payments-ops-squad", "knowledge")
            os.makedirs(knowledge)
            self.assertNotEqual(mod.cache_dir(), knowledge)  # no marker, no sibling cache
            open(os.path.join(knowledge, mod.CACHE_MARKER), "w").close()
            self.assertEqual(mod.cache_dir(), knowledge)
            # the repository checkout never caches into its own knowledge/ folder
            self.assertNotEqual(fetch_doc.cache_dir(), os.path.join(os.path.dirname(os.path.dirname(fetch_doc.__file__)), "knowledge"))
        finally:
            if saved is not None:
                os.environ["CLAUDE_PLUGIN_DATA"] = saved

    def test_cache_dir_precedence(self):
        os.environ.pop("PAYMENTS_OPS_KNOWLEDGE", None)
        saved = os.environ.get("CLAUDE_PLUGIN_DATA")
        try:
            os.environ["CLAUDE_PLUGIN_DATA"] = "/tmp/plugin-data"
            self.assertEqual(fetch_doc.cache_dir(), "/tmp/plugin-data/knowledge")
            os.environ.pop("CLAUDE_PLUGIN_DATA")
            self.assertTrue(fetch_doc.cache_dir().endswith(os.path.join(".claude", "payments-ops-squad", "knowledge")))
        finally:
            if saved is not None:
                os.environ["CLAUDE_PLUGIN_DATA"] = saved


if __name__ == "__main__":
    unittest.main()
