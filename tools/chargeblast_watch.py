#!/usr/bin/env python3
"""Read-only watcher for Chargeblast alerts that still need a response. Standard library only.

Lists Ethoca and CDRN alerts that are still unanswered (WIP) and how many hours are left before the
automatic decline. The 48 hours are counted from createdAt; the documentation does not state the clock start,
confirm in current docs. Alerts past 48 hours that are still WIP are listed too (observed in practice (2026-10),
confirm in current docs: they still accepted a response). matchScore is observed in practice (2026-10) and is not
in the published schema; confirm in current docs. It never answers an alert, never requests credit and
never refunds: every call is a GET. The output is a warning for a human to act on.

Usage:
    CHARGEBLAST_API_KEY=... python3 chargeblast_watch.py [--days 3] [--warn-hours 24] [--json]

The key is read from the environment variable named by --key-env (default CHARGEBLAST_API_KEY) and
is never printed. The API sits behind Cloudflare, so the request carries its own User-Agent.

Exit codes: 0 nothing close to expiry, 1 at least one alert expires within --warn-hours,
2 usage or configuration error, 3 API error.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = os.environ.get("CHARGEBLAST_API_BASE", "https://api.chargeblast.com")
USER_AGENT = "payments-ops-squad-chargeblast-watch (+https://github.com/appyonteam/payments-ops-squad)"
DEADLINE_HOURS = 48
UNANSWERED = ("WIP", "", "Unactioned")
PROGRAMS = ("Ethoca", "CDRN")


class ApiError(Exception):
    pass


def get_json(url, key):
    req = urllib.request.Request(url, method="GET", headers={"X-API-Key": key, "Accept": "application/json", "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise ApiError("HTTP %d" % e.code) from None
    except (urllib.error.URLError, ValueError) as e:
        raise ApiError(type(e).__name__) from None


def fetch_alerts(key, now, days):
    start = (now - timedelta(days=days)).strftime("%Y-%m-%d")
    end = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    alerts, page = [], 1
    while page <= 100:
        q = urllib.parse.urlencode({"filter[type]": ",".join(PROGRAMS), "filter[startDate]": start, "filter[endDate]": end, "page": page, "per": 100})
        batch = get_json("%s/api/v3/alerts?%s" % (API, q), key).get("alerts") or []
        alerts += [a for a in batch if isinstance(a, dict)]
        if len(batch) < 100:
            break
        page += 1
    else:
        print("chargeblast_watch: page limit reached, the list may be incomplete", file=sys.stderr)
    return alerts


def parse_time(value):
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00").replace("+0000", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def open_alerts(alerts, now):
    rows = []
    for a in alerts:
        if a.get("subprovider") not in PROGRAMS or str(a.get("reasonCode") or "") not in UNANSWERED or not a.get("createdAt"):
            continue
        left = DEADLINE_HOURS - (now - parse_time(a["createdAt"])).total_seconds() / 3600
        if left < -DEADLINE_HOURS:
            continue
        score = a.get("matchScore")  # returned by the API in practice, not in the published AlertV3 schema
        if left <= 0:
            hint = "past the 48 hour window but still WIP: check the state before assuming it was declined"
        elif not a.get("isMatched"):
            hint = "not matched: search the sale in every connected account before answering"
        elif score is None:
            hint = "matched (no match score returned): confirm the refund on the processor, then answer"
        elif score < 100:
            hint = "matched with a partial score: confirm the sale manually"
        else:
            hint = "matched: confirm the refund on the processor, then answer"
        rows.append({"id": a.get("id"), "program": a.get("subprovider"), "amount": a.get("amount"), "currency": a.get("currency"),
                     "hours_left": round(left, 1), "hint": hint})
    rows.sort(key=lambda r: r["hours_left"])
    return rows


def main(argv=None, now=None):
    ap = argparse.ArgumentParser(description="Read-only watcher for unanswered Chargeblast alerts.")
    ap.add_argument("--days", type=int, default=3, help="look-back window in days (default 3)")
    ap.add_argument("--warn-hours", type=float, default=24, help="warn when an alert expires within this many hours (default 24)")
    ap.add_argument("--key-env", default="CHARGEBLAST_API_KEY", help="environment variable that holds the API key")
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = ap.parse_args(argv)
    key = os.environ.get(args.key_env, "").strip()
    if not key:
        print("chargeblast_watch: set %s" % args.key_env, file=sys.stderr)
        return 2
    now = now or datetime.now(timezone.utc)
    try:
        rows = open_alerts(fetch_alerts(key, now, args.days), now)
    except ApiError as e:
        print("chargeblast_watch: API error (%s)" % e, file=sys.stderr)
        return 3
    urgent = [r for r in rows if r["hours_left"] <= args.warn_hours]
    if args.json:
        print(json.dumps({"open": rows, "urgent": len(urgent)}, indent=2))
    else:
        print("%d unanswered alert(s), %d expire within %g h (negative hours: past the window, still WIP)." % (len(rows), len(urgent), args.warn_hours))
        for r in rows:
            flag = "URGENT " if r in urgent else ""
            print("- %s%s %s %s %s, %.1f h left: %s" % (flag, r["id"], r["program"], r["amount"], r["currency"], r["hours_left"], r["hint"]))
    return 1 if urgent else 0


if __name__ == "__main__":
    sys.exit(main())
