"""Sanitization gate for payments-ops-squad.

Scans file contents AND path names (files and directories) for:
  * terms from a private denylist kept outside the repository
    (one literal per line; a line starting with "re:" is a regular expression).
    Matching is case-insensitive by default, for literals and "re:" entries alike;
    pass --case-sensitive to match the denylist exactly as written;
  * syntactic patterns of sensitive data (Stripe IDs, secret keys, e-mails,
    URLs with credentials, IPv4 addresses, CPF, CNPJ, Brazilian phone numbers).

Output never contains the matched text: each finding is printed as
``path:line:rule`` (line 0 means the path name itself), denylist findings use
``denylist#<index>`` (1-based position among the denylist entries) and any
matched text inside a printed path is replaced by ``[REDACTED]``.

Not covered: the gate scans the working tree only. It does not scan git history
(commits, other branches, tags or stashes) and does not scan the content of binary
files (it only reports how many it skipped); check those separately before publishing.

Exit codes: 0 clean, 1 findings, 2 usage error.
"""
import argparse
import os
import re
import sys
import tempfile
import zipfile

STRIPE_PREFIXES = ("acct|pi|ch|cus|pm|prv|in|sub|txn|ca|re|dp|py|po|evt|seti|src|card|tok|issfr")

PATTERNS = [
    # Stripe object IDs: known prefix + body of 8+ chars containing at least one digit
    # (so in_progress, sub_total, ch_fallback or pi_XXXX placeholders do not match).
    ("stripe_id", re.compile(r"\b(?:" + STRIPE_PREFIXES + r")_(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{8,}\b")),
    ("secret_key", re.compile(r"\b(?:sk|rk)_(?:live|test)_|\bwhsec_")),
    ("userinfo_url", re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@")),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("ipv4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("cpf", re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")),
    ("cnpj", re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")),
    ("phone_br", re.compile(r"\+?55\s?\(?\d{2}\)?\s?9?\d{4}-?\d{4}")),
]

ALLOW = {
    "email": {"payments-ops-squad@users.noreply.github.com", "you@example.com", "user@example.com"},
    "ipv4": {"0.0.0.0", "127.0.0.1"},
}

# Relative directories never scanned: VCS metadata, a local vendor documentation folder
# (never versioned; fetched documentation lives in a cache outside the repository),
# build output (scanned through scan_zip_dir) and caches.
SKIP_DIRS = {".git", os.path.join("knowledge", "vendor"), "dist", "__pycache__"}

REDACTED = "[REDACTED]"


def load_denylist(path):
    """Read denylist entries. Comments (#) and blank lines are ignored; only the
    line break is stripped so entries may keep meaningful spaces."""
    terms = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\r\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            terms.append(line)
    return terms


def _compile_terms(terms, case_sensitive=False):
    flags = 0 if case_sensitive else re.IGNORECASE
    out = []
    for i, t in enumerate(terms, 1):
        if not t:
            continue
        if t.startswith("re:"):
            out.append(("denylist#%d" % i, re.compile(t[3:], flags)))
        else:
            out.append(("denylist#%d" % i, re.compile(re.escape(t), flags)))
    return out


def _matches(text, compiled_terms):
    """Yield (rule, span) for every finding in a piece of text."""
    for rule, rx in compiled_terms:
        for m in rx.finditer(text):
            yield rule, m.span()
    for rule, rx in PATTERNS:
        for m in rx.finditer(text):
            if m.group(0) in ALLOW.get(rule, ()):
                continue
            yield rule, m.span()


def _redact(name, compiled_terms):
    spans = sorted(span for _, span in _matches(name, compiled_terms))
    if not spans:
        return name
    out, pos = [], 0
    for start, end in spans:
        if end <= pos:
            continue
        out.append(name[pos:max(start, pos)])
        out.append(REDACTED)
        pos = end
    out.append(name[pos:])
    return "".join(out)


def _rules_in(text, compiled_terms):
    seen = []
    for rule, _ in _matches(text, compiled_terms):
        if rule not in seen:
            seen.append(rule)
    return seen


def _scan(root, compiled_terms, prefix=""):
    hits = []
    skipped_binary = 0
    for dp, dns, fns in os.walk(root):
        dns.sort()
        rel_dir = os.path.relpath(dp, root)
        rel_dir = "" if rel_dir == "." else rel_dir
        if rel_dir and any(rel_dir == s or rel_dir.startswith(s + os.sep) for s in SKIP_DIRS):
            dns[:] = []
            continue
        # Kept as a list of redacted components so that printed paths never leak.
        red_dir = os.sep.join(_redact(c, compiled_terms) for c in rel_dir.split(os.sep)) if rel_dir else ""
        if rel_dir:
            for rule in _rules_in(os.path.basename(rel_dir), compiled_terms):
                hits.append((prefix + red_dir, 0, rule))
        for fn in sorted(fns):
            p = os.path.join(dp, fn)
            shown = prefix + (os.path.join(red_dir, _redact(fn, compiled_terms)) if red_dir else _redact(fn, compiled_terms))
            for rule in _rules_in(fn, compiled_terms):
                hits.append((shown, 0, rule))
            try:
                with open(p, encoding="utf-8") as f:
                    lines = f.read().splitlines()
            except UnicodeDecodeError:
                skipped_binary += 1
                continue
            except OSError:
                continue
            for i, ln in enumerate(lines, 1):
                for rule in _rules_in(ln, compiled_terms):
                    hits.append((shown, i, rule))
    if skipped_binary:
        print("gate: %d binary file(s) not scanned for content" % skipped_binary, file=sys.stderr)
    return hits


def scan(root, terms, case_sensitive=False):
    """Scan a directory tree. Returns a list of (redacted_path, line, rule)."""
    return _scan(root, _compile_terms(terms, case_sensitive))


def scan_zip_dir(dist_dir, terms, case_sensitive=False):
    """Extract every .zip in dist_dir into a temporary directory and scan it.
    Paths are reported as ``<zip>!<entry>``."""
    compiled = _compile_terms(terms, case_sensitive)
    hits = []
    for name in sorted(os.listdir(dist_dir)):
        if not name.endswith(".zip"):
            continue
        shown_zip = _redact(name, compiled)
        for rule in _rules_in(name, compiled):
            hits.append((shown_zip, 0, rule))
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(os.path.join(dist_dir, name)) as z:
                z.extractall(tmp)  # extractall drops absolute paths and ".." components
            hits.extend(_scan(tmp, compiled, prefix=shown_zip + "!"))
    return hits


def report(hits):
    for f, i, r in hits:
        print("%s:%d:%s" % (f, i, r))
    return 1 if hits else 0


def main(argv=None):
    a = argparse.ArgumentParser(description="Sanitization gate (prints path:line:rule only).")
    a.add_argument("--denylist", required=True, help="private denylist file, kept outside the repository")
    a.add_argument("--root", default=".", help="directory tree to scan")
    a.add_argument("--dist", help="optional directory with .zip packages to scan")
    a.add_argument("--case-sensitive", action="store_true",
                   help="match denylist entries with exact case (default: case-insensitive)")
    o = a.parse_args(argv)
    if not os.path.isfile(o.denylist):
        print("gate: denylist not found", file=sys.stderr)
        return 2
    terms = load_denylist(o.denylist)
    hits = scan(o.root, terms, o.case_sensitive)
    if o.dist:
        hits += scan_zip_dir(o.dist, terms, o.case_sensitive)
    return report(hits)


if __name__ == "__main__":
    sys.exit(main())
