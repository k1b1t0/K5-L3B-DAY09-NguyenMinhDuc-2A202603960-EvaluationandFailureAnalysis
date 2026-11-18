"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """Ma tran nham lan tp/fp/fn/tn voi lop duong tinh la FAIL."""
    if len(human) != len(judge):
        raise ValueError("human and judge must have the same length")
    tp = fp = fn = tn = 0
    for h, j in zip(human, judge):
        hp, jp = h.strip().upper() == POS, j.strip().upper() == POS
        if hp and jp:
            tp += 1
        elif not hp and jp:
            fp += 1
        elif hp and not jp:
            fn += 1
        else:
            tn += 1
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    """Tinh precision va recall cho lop FAIL; tra 0.0 neu mau so bang 0."""
    cm = confusion(human, judge)
    p = cm["tp"] / (cm["tp"] + cm["fp"]) if cm["tp"] + cm["fp"] else 0.0
    r = cm["tp"] / (cm["tp"] + cm["fn"]) if cm["tp"] + cm["fn"] else 0.0
    return p, r


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """Tinh Cohen's kappa; nem ValueError neu khong xac dinh (p_e == 1)."""
    n = len(human)
    if n == 0:
        raise ValueError("empty labels")
    cm = confusion(human, judge)
    p_o = (cm["tp"] + cm["tn"]) / n
    p_e = (
        ((cm["tp"] + cm["fn"]) / n) * ((cm["tp"] + cm["fp"]) / n)
        + ((cm["fp"] + cm["tn"]) / n) * ((cm["fn"] + cm["tn"]) / n)
    )
    if abs(1.0 - p_e) <= 1e-12:
        raise ValueError("kappa undefined when p_e == 1")
    return (p_o - p_e) / (1.0 - p_e)


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Hieu chinh ty le loi quan sat theo Rogan-Gladen va cat trong [0, 1]."""
    denom = sensitivity + specificity - 1.0
    if abs(denom) <= 1e-12:
        return max(0.0, min(1.0, float(observed_rate)))
    est = (observed_rate + specificity - 1.0) / denom
    return max(0.0, min(1.0, est))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    # TODO M4
    raise NotImplementedError


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    # TODO M6
    raise NotImplementedError


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    # TODO M6
    raise NotImplementedError
