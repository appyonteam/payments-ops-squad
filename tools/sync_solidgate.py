#!/usr/bin/env python3
"""Sync the official Solidgate documentation and OpenAPI specs into the local knowledge cache.

Nothing from the vendor is stored in the repository: pages and specs are downloaded on demand into
``<cache>/solidgate/`` (the same cache that ``tools/fetch_doc.py`` uses, resolved by its ``cache_dir()``)::

    <cache>/solidgate/docs/...             one Markdown file per page, with a YAML header (source_url, fetched_at)
    <cache>/solidgate/openapi/v1.yaml      official OpenAPI v1 and v2, byte for byte
    <cache>/solidgate/openapi/v2.yaml
    <cache>/solidgate/fetch-manifest.json  metadata only: url, file, title, sha256, bytes, status, fetched_at

Sources:
    * page index: https://docs.solidgate.com/sitemap.xml (docs.solidgate.com publishes no llms.txt);
    * https://docs.solidgate.com/changelog.md and the v1 and v2 "get started" pages on api-docs.solidgate.com;
    * OpenAPI: https://api-docs.solidgate.com/_bundle/api/@v1/index.yaml?download (and @v2).
    (The api-docs.solidgate.com/llms.txt index is available through ``fetch_doc.py --index solidgate``.)

Rules:
    * https only, and only docs.solidgate.com and api-docs.solidgate.com (every redirect hop is checked);
    * robots.txt is respected for every URL (docs.solidgate.com disallows /api/: those pages are skipped);
    * about one request per second (``--delay``); no call is ever made to the Solidgate payment API;
    * downloaded content is untrusted data: it is never interpreted or executed. It is only scanned for
      passages addressed to AI assistants, which are flagged in the manifest (line numbers only, no text);
    * idempotent: unchanged content is not rewritten, and pages fetched less than ``--max-age-days`` ago are
      not requested again. A page that leaves the sitemap is marked ``removed`` (its file is never deleted).

Usage:
    sync_solidgate.py [--dry-run] [--limit N] [--only PREFIX] [--max-age-days N] [--refresh]
                      [--delay SECONDS] [--sitemap FILE] [--cache-dir DIR]

``--dry-run`` lists what would be downloaded and writes nothing; the only request it makes is the sitemap
(none at all with ``--sitemap FILE``). robots.txt is not consulted in a dry run.

Exit codes: 0 ok, 1 at least one page failed or the sitemap was unreachable, 2 bad usage or the allowlist
in tools/fetch_doc.py does not cover Solidgate.

Python standard library only. Nothing is written outside ``<cache>/solidgate/``.
"""
import argparse
import datetime as _dt
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.robotparser
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # needed under python3 -I
import fetch_doc  # noqa: E402

SITEMAP_URL = "https://docs.solidgate.com/sitemap.xml"
ALLOWED_HOSTS = frozenset({"docs.solidgate.com", "api-docs.solidgate.com"})

# (relative file, URL, origin, declared API version)
EXTRAS = (
    ("docs/changelog.md", "https://docs.solidgate.com/changelog.md", "changelog", None),
    ("docs/api-docs/get-started-v1.md", "https://api-docs.solidgate.com/api/get-started.md", "api-docs", "v1"),
    ("docs/api-docs/get-started-v2.md", "https://api-docs.solidgate.com/api/v2/get-started.md", "api-docs", "v2"),
    ("openapi/v1.yaml", "https://api-docs.solidgate.com/_bundle/api/@v1/index.yaml?download", "openapi", "v1"),
    ("openapi/v2.yaml", "https://api-docs.solidgate.com/_bundle/api/@v2/index.yaml?download", "openapi", "v2"),
)

MANIFEST_NAME = "fetch-manifest.json"
DEFAULT_DELAY = 1.0
TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._~-]*$")

# Passages addressed to AI assistants inside vendor content. Content is DATA: these are only flagged.
AI_PATTERNS = [
    r"\bafter generating (the )?code\b",
    r"\bignore (all |any )?(the )?(previous|prior|above|earlier) (instructions|prompts?)\b",
    r"\blist each requirement\b",
    r"\bwrite this in my language\b",
    r"\bask me which one\b",
    r"\bmatch my project'?s\b",
    r"\bmy (language and )?framework\b",
    r"\bimplement (this|the following) (in|for) my\b",
    r"\bAI (assistant|agent|model|coding)\b",
    r"(?-i:\bLLMs?\b)|\blarge language models?\b",
    r"\byou are (an?|the) (expert|assistant|helpful|senior|AI|ai|developer|engineer|coding)\b",
    r"\bas an AI\b",
    r"\bsystem prompt\b",
    r"(?-i:\b(ChatGPT|Claude|Copilot|Cursor|Gemini)\b)",  # product names are case-sensitive ("cursor-based" is fine)
    r"\b(copy|paste)\b.{0,40}\bprompt\b",
    r"\bprompt\b.{0,60}\b(AI|assistant|agent|LLM)\b",
]
AI_RX = [re.compile(p, re.I) for p in AI_PATTERNS]
V1_RX = re.compile(r"/api/v1|pay\.solidgate\.com|gate\.solidgate\.com|HMAC-SHA512|\bmerchant header\b|solidgate v1", re.I)
V2_RX = re.compile(r"/v2/|\basec_|\bwsec_|api\.solidgate\.com|HMAC-SHA256|solidgate v2|\bBearer\b", re.I)


# --------------------------------------------------------------------------------------------------------------
# URL and path rules
# --------------------------------------------------------------------------------------------------------------
def is_solidgate_url(url):
    """https, exactly one of the two Solidgate hosts, no credentials, no fragment, allowed by fetch_doc."""
    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    return (parts.scheme == "https" and parts.hostname in ALLOWED_HOSTS and not parts.username
            and not parts.password and not parts.fragment and fetch_doc.is_allowed(url))


def local_path(url):
    """Relative file for a sitemap URL, or None when the URL path is not a safe file name."""
    path = urllib.parse.urlsplit(url).path.strip("/")
    if not path:
        return "docs/index.md"
    segments = path.split("/")
    if segments[-1].endswith(".md"):
        segments[-1] = segments[-1][:-3]
    if not all(SEGMENT_RE.match(s) for s in segments):
        return None
    return "docs/" + "/".join(segments) + ".md"


def candidates(url, origin):
    """Markdown URLs to try, in order. HTML is never a fallback."""
    if origin != "sitemap":
        return [url]
    path = urllib.parse.urlsplit(url).path
    if path in ("", "/"):
        return [url.rstrip("/") + "/index.md"]
    if path.endswith(".md"):
        return [url]
    return [url.rstrip("/") + ".md"] + ([url + "index.md"] if url.endswith("/") else [])


def parse_sitemap(raw):
    """Extract <loc> URLs with a regex: no XML parser, so no entity expansion on untrusted input."""
    if raw[:2] == b"\x1f\x8b":
        raw = _gunzip(raw)
    text = raw.decode("utf-8", "replace")
    urls = [html.unescape(u) for u in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", text)]
    return list(dict.fromkeys(urls))


def _gunzip(raw):
    d = zlib.decompressobj(16 + zlib.MAX_WBITS)
    out = d.decompress(raw, fetch_doc.MAX_BYTES + 1)
    if len(out) > fetch_doc.MAX_BYTES:
        raise OSError("decompressed body larger than %d bytes" % fetch_doc.MAX_BYTES)
    return out


# --------------------------------------------------------------------------------------------------------------
# HTTP client: throttled, allowlisted, robots-aware
# --------------------------------------------------------------------------------------------------------------
class Client:
    """Every request goes through fetch_doc._open: https only, allowlisted URL, guarded redirects."""

    def __init__(self, delay=DEFAULT_DELAY, opener=None, sleep=time.sleep, clock=time.monotonic):
        self.delay = max(delay, 0.0)
        self.opener = opener or fetch_doc._open
        self.sleep, self.clock = sleep, clock
        self._last = None
        self._robots = {}

    def _throttle(self):
        if self._last is not None:
            wait = self.delay - (self.clock() - self._last)
            if wait > 0:
                self.sleep(wait)
        self._last = self.clock()

    def get(self, url, attempts=2):
        """Return (status, body or None, error or None). Never raises for network problems."""
        error = None
        for i in range(attempts):
            self._throttle()
            try:
                with self.opener(url) as r:
                    if not fetch_doc.is_allowed(r.geturl()):
                        raise fetch_doc.Refused(r.geturl())
                    body = r.read(fetch_doc.MAX_BYTES + 1)
                    if len(body) > fetch_doc.MAX_BYTES:
                        return 200, None, "larger than %d bytes" % fetch_doc.MAX_BYTES
                    if body[:2] == b"\x1f\x8b":
                        body = _gunzip(body)
                    return getattr(r, "status", 200), body, None
            except fetch_doc.Refused as e:
                return 0, None, "refused (not an allowed Solidgate URL): %s" % e
            except urllib.error.HTTPError as e:
                e.close()
                if e.code in (404, 410):
                    return e.code, None, "HTTP %d" % e.code
                if e.code in (401, 403):
                    return e.code, None, "HTTP %d" % e.code
                error = "HTTP %d" % e.code
            except urllib.error.URLError as e:
                error = "%s" % (e.reason,)
            except (OSError, ValueError) as e:
                error = "%s" % type(e).__name__
            if i + 1 < attempts:
                self.sleep(min(3.0, self.delay * 3 + 1.0))
        return 0, None, error

    def robots_ok(self, url):
        parts = urllib.parse.urlsplit(url)
        origin = "%s://%s" % (parts.scheme, parts.netloc)
        rp = self._robots.get(origin)
        if rp is None:
            rp = urllib.robotparser.RobotFileParser()
            status, body, err = self.get(origin + "/robots.txt")
            if body is not None:
                rp.parse(body.decode("utf-8", "replace").splitlines())
            elif status in (404, 410):
                rp.allow_all = True
            else:  # 401/403, refused or unreachable: fail closed for this run
                rp.disallow_all = True
            self._robots[origin] = rp
        return rp.can_fetch(fetch_doc.USER_AGENT, url)


# --------------------------------------------------------------------------------------------------------------
# Content helpers
# --------------------------------------------------------------------------------------------------------------
def looks_like_html(body):
    head = body[:300].lstrip().lower()
    return head.startswith((b"<!doctype", b"<html", b"<?xml")) or b"<html" in head


def looks_like_openapi(body):
    return re.search(rb"^\s*[\"']?openapi[\"']?\s*:", body[:1000], re.M) is not None


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def title_of(text):
    t = text.lstrip("\ufeff")
    m = re.match(r"---\n.*?\n---\n", t, re.S)
    if t.startswith("---") and m:
        t = t[m.end():]
    for line in t.splitlines():
        m = re.match(r"#{1,6}\s+(.+?)\s*#*\s*$", line)
        if m:
            return m.group(1).strip()
    for line in t.splitlines():  # OpenAPI: info.title
        m = re.match(r"\s+title:\s*(.+)$", line)
        if m:
            return m.group(1).strip().strip("'\"")
    return None


def category_of(rel, origin):
    if origin == "openapi":
        return "openapi/" + os.path.splitext(os.path.basename(rel))[0]
    if origin == "api-docs":
        return "api-docs"
    segments = rel[len("docs/"):-len(".md")].split("/")
    return "/".join(segments[:2]) if len(segments) > 1 else segments[0]


def api_version_of(text, declared):
    if declared:
        return declared, "declared (origin of the file)"
    a, b = bool(V1_RX.search(text)), bool(V2_RX.search(text))
    version = "v1+v2" if a and b else "v1" if a else "v2" if b else "n.a."
    return version, "inferred (content markers; confirm on the page)"


def scan_ai_instructions(text):
    """Line numbers of passages addressed to AI assistants. The text itself is never kept."""
    return [n for n, line in enumerate(text.splitlines(), 1) if any(rx.search(line) for rx in AI_RX)]


def metadata_of(body, rel, origin, declared):
    text = body.decode("utf-8", "replace")
    version, version_origin = api_version_of(text, declared)
    hits = scan_ai_instructions(text)
    return {
        "title": title_of(text),
        "category": category_of(rel, origin),
        "api_version": version,
        "api_version_origin": version_origin,
        "contains_ai_instructions": bool(hits),
        "ai_instruction_total_lines": len(hits),
        "ai_instruction_lines": hits[:4],
    }


def with_header(body, final_url, requested_url, stamp):
    head = "---\nsource_url: %s\nrequested_url: %s\nfetched_at: %s\n---\n" % (final_url, requested_url, stamp)
    return head.encode("utf-8") + body


def strip_header(data):
    m = re.match(rb"---\n(?:.*?)\n---\n", data, re.S)
    return data[m.end():] if data.startswith(b"---\n") and m else data


def write_atomic(path, data, root):
    real_root = os.path.realpath(root)
    real_dest = os.path.realpath(path)
    if os.path.commonpath([real_root, real_dest]) != real_root:
        raise OSError("refusing to write outside the cache: %s" % path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


# --------------------------------------------------------------------------------------------------------------
# Download of one target
# --------------------------------------------------------------------------------------------------------------
def download(client, url, origin):
    """Return (status, body, source_md_url, error). status: ok | failed | no_markdown | skipped_robots."""
    last = ("no_markdown", None, url, "no candidate URL")
    for cand in candidates(url, origin):
        if not is_solidgate_url(cand):
            return "failed", None, cand, "refused (not an allowed Solidgate URL)"
        if not client.robots_ok(cand):
            return "skipped_robots", None, cand, "disallowed by robots.txt"
        status, body, err = client.get(cand)
        if body is None:
            if status in (404, 410):
                last = ("no_markdown", None, cand, err)
                continue
            return "failed", None, cand, err
        if origin == "openapi":
            if looks_like_openapi(body):
                return "ok", body, cand, None
            return "no_markdown", None, cand, "response does not look like OpenAPI"
        if looks_like_html(body):
            last = ("no_markdown", None, cand, "HTML response")
            continue
        return "ok", body, cand, None
    return last


# --------------------------------------------------------------------------------------------------------------
# Main flow
# --------------------------------------------------------------------------------------------------------------
def build_targets(sitemap_urls, log):
    """[(url, relative file, origin, declared version)], extras first, then the sitemap pages sorted by file."""
    targets, seen = [], set()
    for rel, url, origin, version in EXTRAS:
        targets.append((url, rel, origin, version))
        seen.add(rel)
    pages = []
    for url in sitemap_urls:
        parts = urllib.parse.urlsplit(url)
        if not is_solidgate_url(url) or parts.query:
            log("  skip (not an allowed page URL): %s" % url)
            continue
        rel = local_path(url)
        if rel is None:
            log("  skip (unsafe file name): %s" % url)
            continue
        if rel in seen:
            continue
        seen.add(rel)
        pages.append((url, rel, "sitemap", None))
    return targets + sorted(pages, key=lambda t: t[1])


def load_manifest(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def run(opts, client=None, now=None, out=print):
    """Run one sync. Returns (exit code, counters)."""
    now = now or _dt.datetime.now(_dt.timezone.utc)
    stamp = now.strftime(TS_FORMAT)
    base = os.path.abspath(os.path.expanduser(opts.cache_dir)) if opts.cache_dir else fetch_doc.cache_dir()
    root = os.path.join(base, "solidgate")
    manifest_path = os.path.join(root, MANIFEST_NAME)
    client = client or Client(delay=opts.delay)

    if not (is_solidgate_url(SITEMAP_URL) and all(is_solidgate_url(e[1]) for e in EXTRAS)):
        out("sync_solidgate: tools/fetch_doc.py does not allow the Solidgate hosts; apply fetch_doc.patch first")
        return 2, {}

    if opts.sitemap:
        with open(opts.sitemap, "rb") as f:
            raw = f.read(fetch_doc.MAX_BYTES + 1)
    else:
        if not opts.dry_run and not client.robots_ok(SITEMAP_URL):
            out("sync_solidgate: robots.txt disallows the sitemap")
            return 1, {}
        status, raw, err = client.get(SITEMAP_URL)
        if raw is None:
            out("sync_solidgate: sitemap unreachable (%s)" % err)
            return 1, {}
    sitemap_urls = parse_sitemap(raw)

    manifest = load_manifest(manifest_path)
    prev = {d["url"]: d for d in manifest.get("docs", []) if isinstance(d, dict) and "url" in d}
    targets = build_targets(sitemap_urls, out)
    in_scope = (lambda rel: rel.startswith(opts.only) or rel[len("docs/"):].startswith(opts.only)) if opts.only else (lambda rel: True)
    selected = [t for t in targets if in_scope(t[1])]
    if opts.limit is not None:
        selected = selected[:max(opts.limit, 0)]
    partial = bool(opts.only) or opts.limit is not None

    out("[sync] %s | cache %s | sitemap %d URLs | targets %d | dry_run=%s" % (
        stamp, root, len(sitemap_urls), len(selected), opts.dry_run))
    c = dict.fromkeys(("new", "changed", "unchanged", "fresh", "failed", "no_markdown", "skipped_robots", "removed"), 0)
    entries = dict(prev)

    for i, (url, rel, origin, declared) in enumerate(selected, 1):
        dest = os.path.join(root, rel)
        old = prev.get(url)
        on_disk = None
        if os.path.isfile(dest):
            with open(dest, "rb") as f:
                on_disk = sha256(strip_header(f.read()) if origin != "openapi" else f.read())
        is_fresh = (old and old.get("status") == "ok" and old.get("sha256") == on_disk and not opts.refresh
                    and fetch_doc.is_fresh({"fetched_at": old.get("fetched_at", "")}, opts.max_age_days, now))
        if is_fresh:
            c["fresh"] += 1
            continue
        if opts.dry_run:
            label = "NEW" if on_disk is None else "RECHECK"
            c["new" if on_disk is None else "changed"] += 1
            out("  [%d/%d] would download (%s): %s" % (i, len(selected), label, rel))
            continue

        status, body, source_md, err = download(client, url, origin)
        if status != "ok":
            key = status if status in c else "failed"
            c[key] += 1
            entry = dict(old) if old else {"url": url, "file": rel, "origin": origin, "bytes": None, "sha256": None}
            if old and old.get("status") == "ok":
                entry["last_error"] = err  # keep the good copy's metadata, record the problem
            else:
                entry.update({"status": status, "error": err, "source_md": source_md})
            entries[url] = entry
            out("  [%d/%d] %-14s %s (%s)" % (i, len(selected), status.upper(), rel, err))
            continue

        digest = sha256(body)
        if old and old.get("status") == "ok" and old.get("sha256") == digest and on_disk == digest:
            c["unchanged"] += 1
            kept = dict(old)
            kept.pop("last_error", None)
            entries[url] = kept
            continue
        meta = metadata_of(body, rel, origin, declared)
        data = body if origin == "openapi" else with_header(body, source_md, url, stamp)
        write_atomic(dest, data, root)
        entries[url] = {"url": url, "file": rel, "source_md": source_md, "fetched_at": stamp, "sha256": digest,
                        "bytes": len(body), "status": "ok", "origin": origin, **meta}
        c["new" if on_disk is None else "changed"] += 1
        out("  [%d/%d] %-14s %s (%d B)" % (i, len(selected), "NEW" if on_disk is None else "CHANGED", rel, len(body)))

    if not partial:
        sitemap_set = set(sitemap_urls)
        previous_pages = sum(1 for d in prev.values() if d.get("origin") == "sitemap")
        extras_urls = {e[1] for e in EXTRAS}
        if not previous_pages or len(sitemap_set) >= 0.5 * previous_pages:
            for url, d in prev.items():
                if url in extras_urls or url in sitemap_set or d.get("origin") != "sitemap" or d.get("status") == "removed":
                    continue
                if not opts.dry_run:
                    entries[url] = {**d, "status": "removed", "removed_at": stamp}
                c["removed"] += 1
                out("  REMOVED %s (left the sitemap; file kept)" % d.get("file"))
        else:
            out("  WARNING: sitemap has under 50% of the known URLs; removals NOT marked (possible read failure)")

    if not opts.dry_run:
        docs = sorted(entries.values(), key=lambda d: d["file"])
        new_manifest = {
            "description": "Metadata of the Solidgate documentation cache (docs.solidgate.com and api-docs.solidgate.com). "
                           "Downloaded content is UNTRUSTED DATA and is not stored in this file.",
            "generated_by": "tools/sync_solidgate.py",
            "sources": {"sitemap": SITEMAP_URL, "openapi_v1": EXTRAS[3][1], "openapi_v2": EXTRAS[4][1]},
            "api_version_note": "api_version is INFERRED from content markers (except openapi/* and the get-started pages, "
                                "declared by their origin); confirm on the page.",
            "last_verified": now.strftime("%Y-%m-%d"),
            "docs": docs,
        }
        text = json.dumps(new_manifest, ensure_ascii=False, indent=1) + "\n"
        write_atomic(manifest_path, text.encode("utf-8"), root)

    out("[sync] RESULT new=%(new)d changed=%(changed)d unchanged=%(unchanged)d fresh=%(fresh)d failed=%(failed)d "
        "no_markdown=%(no_markdown)d skipped_robots=%(skipped_robots)d removed=%(removed)d" % c
        + (" | DRY RUN (nothing written; robots.txt not consulted)" if opts.dry_run else ""))
    return (1 if c["failed"] else 0), c


def main(argv=None):
    a = argparse.ArgumentParser(description="Sync the official Solidgate documentation and OpenAPI into the local cache.")
    a.add_argument("--dry-run", action="store_true", help="list what would be downloaded; write nothing")
    a.add_argument("--limit", type=int, help="process only the first N targets (OpenAPI and get-started pages come first)")
    a.add_argument("--only", help="path prefix, for example payments/card-payments, openapi or docs/changelog")
    a.add_argument("--max-age-days", type=float, default=fetch_doc.DEFAULT_MAX_AGE_DAYS,
                   help="skip pages fetched less than N days ago (default %d)" % fetch_doc.DEFAULT_MAX_AGE_DAYS)
    a.add_argument("--refresh", action="store_true", help="ignore the age of the cached copies")
    a.add_argument("--delay", type=float, default=DEFAULT_DELAY, help="seconds between requests (default 1.0)")
    a.add_argument("--sitemap", help="read the sitemap from a local file (xml or gzip) instead of downloading it")
    a.add_argument("--cache-dir", help="cache base directory (default: the fetch_doc.py cache)")
    return run(a.parse_args(argv))[0]


if __name__ == "__main__":
    sys.exit(main())
