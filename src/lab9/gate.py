"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item
from lab9.graders import GRADERS


def _ratchet_problems(spec: dict, base_spec: dict) -> list[str]:
    """Kiem tra quy tac ratchet: cung eval_set_version chi duoc siet chat nguong."""
    if spec.get("eval_set_version") != base_spec.get("eval_set_version"):
        return []
    problems: list[str] = []
    cur_m = {m["id"]: m for m in spec.get("metrics") or []}
    for bm in base_spec.get("metrics") or []:
        mid = bm["id"]
        cm = cur_m.get(mid)
        if cm is None:
            problems.append(f"ratchet_missing_metric:{mid}")
            continue
        if bm.get("blocking") and not cm.get("blocking"):
            problems.append(f"ratchet_unblocked:{mid}")
        bth, cth = bm.get("threshold") or {}, cm.get("threshold") or {}
        if "max" in bth and ("max" not in cth or cth["max"] > bth["max"]):
            problems.append(f"ratchet_max_raised:{mid}")
        if "max_increase" in bth and ("max_increase" not in cth or cth["max_increase"] > bth["max_increase"]):
            problems.append(f"ratchet_max_increase_raised:{mid}")
        if "min" in bth and ("min" not in cth or cth["min"] < bth["min"]):
            problems.append(f"ratchet_min_lowered:{mid}")
        if bth.get("no_significant_drop") and not cth.get("no_significant_drop"):
            problems.append(f"ratchet_dropped_ci:{mid}")

    cur_s = {(s["name"], s["metric"]): s for s in spec.get("slices") or []}
    for bs in base_spec.get("slices") or []:
        key = (bs["name"], bs["metric"])
        cs = cur_s.get(key)
        if cs is None:
            problems.append(f"ratchet_missing_slice:{key[0]}/{key[1]}")
            continue
        if bs.get("blocking") and not cs.get("blocking"):
            problems.append(f"ratchet_unblocked_slice:{key[0]}/{key[1]}")
        if "min" in bs and ("min" not in cs or cs["min"] < bs["min"]):
            problems.append(f"ratchet_slice_min_lowered:{key[0]}/{key[1]}")
        if bs.get("no_significant_drop") and not cs.get("no_significant_drop"):
            problems.append(f"ratchet_slice_dropped_ci:{key[0]}/{key[1]}")
    return problems


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """Kiem tra tinh toan ven report va spec de chan gian lan eval (M7)."""
    problems: list[str] = []
    for k, v in (pr.get("metrics") or {}).items():
        if isinstance(v, (int, float)) and not math.isfinite(v):
            problems.append(f"non_finite_metric:{k}")
    if pr.get("evaluator_failures"):
        problems.append(f"evaluator_failures:{len(pr['evaluator_failures'])}")

    rows = pr.get("rows") or []
    base_rows = base.get("rows") or []
    manifest = pr.get("manifest") or {}
    expected_n = int(manifest.get("items", 0)) * len(manifest.get("seeds") or [])
    if len(rows) != expected_n:
        problems.append(f"row_count:{len(rows)}!=expected:{expected_n}")

    pr_keys = [(r.get("item_id"), r.get("seed")) for r in rows]
    if len(set(pr_keys)) != len(pr_keys):
        problems.append("duplicate_item_seed_rows")
    base_keys = {(r.get("item_id"), r.get("seed")) for r in base_rows}
    if set(pr_keys) != base_keys:
        problems.append("item_seed_set_mismatch")

    row_metrics = sorted({
        m["id"]
        for m in spec.get("metrics") or []
        if m["id"] in GRADERS or any(m["id"] in r for r in base_rows) or any(m["id"] in r for r in rows)
    })
    for mid in row_metrics:
        if any(r.get(mid) is None or (isinstance(r.get(mid), float) and not math.isfinite(r.get(mid))) for r in rows):
            problems.append(f"missing_row_metric:{mid}")
        elif rows and mid in (pr.get("metrics") or {}) and isinstance(pr["metrics"][mid], (int, float)) and math.isfinite(pr["metrics"][mid]):
            exp = sum(bool(r[mid]) for r in rows) if mid in ("secret_leak", "approval_bypass") else sum(float(r[mid]) for r in rows) / len(rows)
            if abs(float(pr["metrics"][mid]) - exp) > 1e-3:
                problems.append(f"metric_row_mismatch:{mid}")

    base_slices = {r.get("item_id"): sorted(set(r.get("slices") or [])) for r in base_rows}
    bad_slice_items = sorted({
        str(r.get("item_id"))
        for r in rows
        if sorted(set(r.get("slices") or [])) != base_slices.get(r.get("item_id"), [])
    })
    for iid in bad_slice_items:
        problems.append(f"slice_tags_changed:{iid}")

    if base_spec is not None:
        problems.extend(_ratchet_problems(spec, base_spec))
    return problems


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """Kiem tra tung slice trong spec["slices"] de chan hoi quy cuc bo (M5)."""
    blocked: list[str] = []
    lines: list[str] = []
    bs = spec.get("bootstrap", {})
    for s in spec.get("slices") or []:
        name, metric = s["name"], s["metric"]
        a = per_item(pr, metric, slice_name=name)
        val = (sum(a.values()) / len(a)) if a else None
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "min" in s and val < s["min"]:
            verdict = "fail"
        if s.get("no_significant_drop") and val is not None:
            b = per_item(base, metric, slice_name=name)
            keys = sorted(set(a) & set(b))
            if keys:
                d, lo, hi = stats.paired_bootstrap(
                    [a[k] for k in keys],
                    [b[k] for k in keys],
                    n_resamples=bs.get("n_resamples", 1000),
                    rng=bs.get("rng", 2027),
                )
                note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                if hi < 0:
                    verdict = "fail"
        sid = f"slice:{name}/{metric}"
        if verdict != "ok" and s.get("blocking"):
            blocked.append(sid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if s.get("blocking") else "warn")
        val_str = f"{val:.4f}" if val is not None else "None"
        lines.append(f"  {sid:<30} {val_str:<8} min={s.get('min', '-'):<6} {note:<28} {label}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
