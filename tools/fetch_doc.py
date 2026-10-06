#!/usr/bin/env python3
"""Fetch one official documentation page on demand and keep it in a local cache.

Only official Stripe, Primer and FunnelFox documentation is accepted. The page is fetched in its
Markdown form when the site offers one, robots.txt is respected, and the cached copy carries a YAML
header with the source URL and the UTC fetch time so that answers can cite both.

Usage:
    fetch_doc.py URL [--max-age-days N] [--refresh]
    fetch_doc.py --index stripe|primer|funnelfox [--max-age-days N] [--refresh]

Exit codes: 0 ok, 1 fetch error, 2 URL refused (not an allowed documentation prefix),
3 disallowed by robots.txt.

Every request, and every redirect hop (robots.txt included), must use https and stay inside the allowed
documentation prefixes (robots.txt may also stay on its own host); a hop that does not is refused before it is
requested. Requests send Accept-Language: en.

Python standard library only. Nothing is written outside the cache directory.
"""
import argparse
import datetime as _dt
import hashlib
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

USER_AGENT = "payments-ops-squad (+https://github.com/appyonteam/payments-ops-squad)"

ALLOWED_PREFIXES = (
    "https://docs.stripe.com/",
    "https://primer.io/docs/",
    "https://funnelfox.com/docs/",
)

INDEXES = {
    "stripe": "https://docs.stripe.com/llms.txt",
    "primer": "https://primer.io/docs/llms.txt",
    "funnelfox": "https://funnelfox.com/docs/llms.txt",
}

DEFAULT_MAX_AGE_DAYS = 14
CACHE_MARKER = ".payments-ops-cache"
MAX_BYTES = 5 * 1024 * 1024
TIMEOUT = 30

EXIT_OK, EXIT_FETCH, EXIT_REFUSED, EXIT_ROBOTS = 0, 1, 2, 3


class Refused(Exception):
    pass


class RobotsDisallowed(Exception):
    pass


def cache_dir():
    env = os.environ.get("PAYMENTS_OPS_KNOWLEDGE")
    if env:
        return os.path.abspath(os.path.expanduser(env))
    data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if data:
        return os.path.join(os.path.abspath(os.path.expanduser(data)), "knowledge")
    # Script install: <dest>/payments-ops-squad/tools/fetch_doc.py next to a knowledge/ folder that the
    # installer marked as a cache. The marker keeps a repository checkout from caching into its own tree.
    sibling = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge")
    if os.path.isfile(os.path.join(sibling, CACHE_MARKER)):
        return sibling
    return os.path.join(os.path.expanduser("~"), ".claude", "payments-ops-squad", "knowledge")


def is_allowed(url):
    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    if parts.username or parts.password or parts.fragment:
        return False
    if ".." in parts.path.split("/"):
        return False
    return any(url.startswith(p) for p in ALLOWED_PREFIXES)


def candidates(url):
    """Markdown variants first, then the URL itself."""
    path = urllib.parse.urlsplit(url).path
    if path.endswith((".md", ".txt")):
        return [url]
    base = url.split("?", 1)[0]
    if base.endswith("/"):
        return [base + "index.md", base.rstrip("/") + ".md", url]
    return [base + ".md", base + "/index.md", url]


def cache_path(url, root=None):
    parts = urllib.parse.urlsplit(url)
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", parts.path.strip("/")) or "index"
    slug = slug[:120]
    if slug.endswith(".md"):
        slug = slug[:-3]
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
    return os.path.join(root or cache_dir(), parts.hostname or "unknown", "%s-%s.md" % (slug, digest))


def read_header(path):
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None, None
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    header = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            header[k.strip()] = v.strip()
    return header, text


def is_fresh(header, max_age_days, now=None):
    if not header or "fetched_at" not in header:
        return False
    try:
        fetched = _dt.datetime.strptime(header["fetched_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dt.timezone.utc)
    except ValueError:
        return False
    now = now or _dt.datetime.now(_dt.timezone.utc)
    return now - fetched < _dt.timedelta(days=max_age_days)


# Every hop, redirects included, must use this scheme. Tests override it to reach a local HTTP server.
REQUIRED_SCHEME = "https"

REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/markdown, text/plain;q=0.9, */*;q=0.5",
    "Accept-Language": "en",
}


def _scheme_ok(url):
    return urllib.parse.urlsplit(url).scheme == REQUIRED_SCHEME


def _robots_target_ok(url, origin_netloc):
    """robots.txt may only move to robots.txt on the same host, or to an allowed documentation URL."""
    parts = urllib.parse.urlsplit(url)
    if parts.username or parts.password:
        return False
    return (parts.netloc == origin_netloc and parts.path == "/robots.txt") or is_allowed(url)


class _GuardedRedirect(urllib.request.HTTPRedirectHandler):
    """Checks every redirect hop before it is requested; a refused hop raises Refused."""

    def __init__(self, allow):
        self.allow = allow

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        newurl = urllib.parse.urljoin(req.full_url, newurl)
        if not (_scheme_ok(newurl) and self.allow(newurl)):
            raise Refused(newurl)
        return urllib.request.HTTPRedirectHandler.redirect_request(self, req, fp, code, msg, headers, newurl)


def _open(url, allow=None):
    allow = allow or is_allowed
    if not (_scheme_ok(url) and allow(url)):
        raise Refused(url)
    req = urllib.request.Request(url, headers=dict(REQUEST_HEADERS))
    return urllib.request.build_opener(_GuardedRedirect(allow)).open(req, timeout=TIMEOUT)


_robots_cache = {}


def robots_allows(url):
    parts = urllib.parse.urlsplit(url)
    origin = "%s://%s" % (parts.scheme, parts.netloc)
    rp = _robots_cache.get(origin)
    if rp is None:
        rp = urllib.robotparser.RobotFileParser()
        try:
            with _open(origin + "/robots.txt", lambda u: _robots_target_ok(u, parts.netloc)) as r:
                rp.parse(r.read(MAX_BYTES).decode("utf-8", "replace").splitlines())
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                rp.disallow_all = True
            else:
                rp.allow_all = True
        _robots_cache[origin] = rp
    return rp.can_fetch(USER_AGENT, url)


def _download(url):
    """Return (final_url, text) for the first candidate that answers 200 with text content."""
    last_error = None
    for cand in candidates(url):
        if not robots_allows(cand):
            raise RobotsDisallowed(cand)
        try:
            with _open(cand) as r:
                final = r.geturl()
                if not is_allowed(final):
                    raise Refused(final)
                ctype = r.headers.get("Content-Type", "")
                if ctype and not (ctype.startswith("text/") or "markdown" in ctype or "json" in ctype):
                    last_error = "unsupported content type %s at %s" % (ctype, cand)
                    continue
                body = r.read(MAX_BYTES + 1)
                if len(body) > MAX_BYTES:
                    last_error = "page larger than %d bytes at %s" % (MAX_BYTES, cand)
                    continue
                return final, body.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            last_error = "HTTP %d at %s" % (e.code, cand)
        except urllib.error.URLError as e:
            last_error = "%s at %s" % (e.reason, cand)
    raise OSError(last_error or "no candidate URL")


def fetch(url, max_age_days=DEFAULT_MAX_AGE_DAYS, refresh=False, root=None, now=None):
    """Return (path, text, from_cache). Raises Refused, RobotsDisallowed or OSError."""
    if not is_allowed(url):
        raise Refused(url)
    path = cache_path(url, root)
    if not refresh:
        header, text = read_header(path)
        if is_fresh(header, max_age_days, now):
            return path, text, True
    final, body = _download(url)
    now = now or _dt.datetime.now(_dt.timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    text = "---\nsource_url: %s\nrequested_url: %s\nfetched_at: %s\n---\n%s" % (final, url, stamp, body)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)
    return path, text, False


def main(argv=None):
    a = argparse.ArgumentParser(description="Fetch official Stripe, Primer or FunnelFox documentation into a local cache.")
    a.add_argument("url", nargs="?", help="documentation page URL")
    a.add_argument("--index", choices=sorted(INDEXES), help="fetch only the vendor llms.txt index")
    a.add_argument("--max-age-days", type=float, default=DEFAULT_MAX_AGE_DAYS, help="cache TTL in days (default 14)")
    a.add_argument("--refresh", action="store_true", help="ignore the cached copy")
    o = a.parse_args(argv)
    if bool(o.url) == bool(o.index):
        a.print_usage(sys.stderr)
        print("fetch_doc: give exactly one of URL or --index", file=sys.stderr)
        return EXIT_REFUSED
    url = INDEXES[o.index] if o.index else o.url
    try:
        path, text, hit = fetch(url, o.max_age_days, o.refresh)
    except Refused as e:
        print("fetch_doc: refused, not an allowed documentation URL: %s" % e, file=sys.stderr)
        print("fetch_doc: allowed prefixes: %s" % ", ".join(ALLOWED_PREFIXES), file=sys.stderr)
        return EXIT_REFUSED
    except RobotsDisallowed as e:
        print("fetch_doc: robots.txt disallows %s" % e, file=sys.stderr)
        return EXIT_ROBOTS
    except OSError as e:
        print("fetch_doc: fetch failed: %s" % e, file=sys.stderr)
        return EXIT_FETCH
    print("cache %s: %s" % ("hit" if hit else "stored", path))
    sys.stdout.write(text if text.endswith("\n") else text + "\n")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
