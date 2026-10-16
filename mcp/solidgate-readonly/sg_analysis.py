"""LOCAL analyses over data that was already authorized (output of read tools, or fixtures).

They do not call any Solidgate endpoint: the API has no analysis operation.
Every output is flagged local_analysis=true. The status assumptions below are
HYPOTHESES to be validated against the order status documentation.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable

# Assumption (to validate): classification of card order statuses.
APPROVED = frozenset({"approved", "auth_ok", "settle_ok", "partial_settled", "refunded",
                      "partial_refunded", "void_ok", "chargebacked"})
DECLINED = frozenset({"declined", "auth_failed", "settle_failed", "failed", "rejected"})
PENDING = frozenset({"created", "processing", "3ds_verify", "auth_pending", "pending"})

ASSUMPTIONS = [
    "The status classification (approved/declined/pending) is an assumption to validate.",
    "Only the supplied data is analyzed; a small or truncated sample limits confidence.",
    "Correlation is not causation: hypotheses need validation with additional evidence.",
]


def _cls(status: Any) -> str:
    s = str(status or "").lower()
    if s in APPROVED:
        return "approved"
    if s in DECLINED:
        return "declined"
    if s in PENDING:
        return "pending"
    return "other"


def _first_card(o: dict[str, Any]) -> dict[str, Any]:
    tx = o.get("transactions") or []
    if tx and isinstance(tx[0], dict) and isinstance(tx[0].get("card"), dict):
        return tx[0]["card"]
    return {}


def _dim(o: dict[str, Any], dim: str) -> str:
    card = _first_card(o)
    if dim == "brand":
        return str(card.get("brand") or "unknown")
    if dim == "bin":
        return str(card.get("bin") or "unknown")
    if dim == "card_country":
        return str(card.get("country") or "unknown")
    if dim == "mid":
        steps = (o.get("routing") or {}).get("cascade_steps") or []
        if steps and isinstance(steps[-1], dict):
            return str(steps[-1].get("mid") or o.get("mid") or "unknown")
        return str(o.get("mid") or "unknown")
    return str(o.get(dim) or "unknown")


def _orders(orders: Any) -> list[dict[str, Any]]:
    if not isinstance(orders, list):
        raise ValueError("orders must be a list of objects (retrieve_card_orders format).")
    return [o for o in orders if isinstance(o, dict)]


def _envelope(kind: str, n: int, body: dict[str, Any]) -> dict[str, Any]:
    return {"local_analysis": True, "type": kind, "n_orders": n, "assumptions": ASSUMPTIONS,
            "warning": "Local analysis over supplied data; this is not a Solidgate API response.", **body}


def _rate(c: Counter[str]) -> dict[str, Any]:
    decided = c["approved"] + c["declined"]
    return {**{k: c[k] for k in ("approved", "declined", "pending", "other")},
            "approval_rate": round(c["approved"] / decided, 4) if decided else None,
            "decided": decided}


def analyze_approval_rate(orders: Any, group_by: str = "mid", min_n: int = 5) -> dict[str, Any]:
    data = _orders(orders)
    total: Counter[str] = Counter(_cls(o.get("status")) for o in data)
    groups: dict[str, Counter[str]] = defaultdict(Counter)
    for o in data:
        groups[_dim(o, group_by)][_cls(o.get("status"))] += 1
    rows = []
    for k, c in groups.items():
        r = _rate(c)
        r["group"] = k
        r["small_sample"] = r["decided"] < min_n
        rows.append(r)
    rows.sort(key=lambda r: (-(r["decided"]), r["group"]))
    return _envelope("approval_rate", len(data), {"grouped_by": group_by, "overall": _rate(total), "groups": rows})


def analyze_declines(orders: Any, group_by: str = "mid") -> dict[str, Any]:
    data = _orders(orders)
    declined = [o for o in data if _cls(o.get("status")) == "declined"]
    by_code = Counter(str(o.get("error_code") or "no_code") for o in declined)
    cross: dict[str, Counter[str]] = defaultdict(Counter)
    for o in declined:
        cross[_dim(o, group_by)][str(o.get("error_code") or "no_code")] += 1
    return _envelope("declines", len(data), {
        "declined": len(declined),
        "by_error_code": by_code.most_common(),
        "grouped_by": group_by,
        "codes_by_group": {g: c.most_common(5) for g, c in cross.items()},
        "note": "The meaning of each error code comes from the Solidgate documentation; it is not inferred here.",
    })


def analyze_routing(orders: Any) -> dict[str, Any]:
    data = _orders(orders)
    depth: Counter[int] = Counter()
    per_mid: dict[str, Counter[str]] = defaultdict(Counter)
    rescued = 0
    for o in data:
        steps = [s for s in ((o.get("routing") or {}).get("cascade_steps") or []) if isinstance(s, dict)]
        depth[len(steps)] += 1
        for i, s in enumerate(steps):
            per_mid[str(s.get("mid") or "unknown")]["attempts"] += 1
            if i == len(steps) - 1:
                per_mid[str(s.get("mid") or "unknown")][_cls(o.get("status"))] += 1
        if len(steps) > 1 and _cls(o.get("status")) == "approved":
            rescued += 1
    return _envelope("routing", len(data), {
        "cascade_step_distribution": sorted(depth.items()),
        "approved_after_cascade": rescued,
        "by_mid": {m: dict(c) for m, c in per_mid.items()},
        "note": "For the actual routing configuration use v2_get_routing_config / v2_get_routing_config_version.",
    })


def diagnose_incident(current: Any, baseline: Any, group_by: Iterable[str] = ("mid", "brand", "geo_country", "platform"),
                      min_n: int = 5) -> dict[str, Any]:
    cur, base = _orders(current), _orders(baseline)
    rc = _rate(Counter(_cls(o.get("status")) for o in cur))
    rb = _rate(Counter(_cls(o.get("status")) for o in base))
    suspects = []
    for dim in group_by:
        gc: dict[str, Counter[str]] = defaultdict(Counter)
        gb: dict[str, Counter[str]] = defaultdict(Counter)
        for o in cur:
            gc[_dim(o, dim)][_cls(o.get("status"))] += 1
        for o in base:
            gb[_dim(o, dim)][_cls(o.get("status"))] += 1
        for k, c in gc.items():
            a, b = _rate(c), _rate(gb.get(k, Counter()))
            if a["approval_rate"] is None or b["approval_rate"] is None:
                continue
            if a["decided"] < min_n or b["decided"] < min_n:
                continue
            suspects.append({"dimension": dim, "group": k, "current_rate": a["approval_rate"],
                             "baseline_rate": b["approval_rate"],
                             "delta": round(a["approval_rate"] - b["approval_rate"], 4),
                             "n_current": a["decided"], "n_baseline": b["decided"]})
    suspects.sort(key=lambda s: s["delta"])
    return _envelope("diagnose_incident", len(cur), {
        "overall_current": rc, "overall_baseline": rb,
        "overall_delta": (round(rc["approval_rate"] - rb["approval_rate"], 4)
                          if rc["approval_rate"] is not None and rb["approval_rate"] is not None else None),
        "hypotheses_ranked_by_drop": suspects[:10],
        "label": "HYPOTHESES (correlation). Validate with additional evidence before acting.",
    })
