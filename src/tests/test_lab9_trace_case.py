"""Regression tests tu trace case C-002@11 (M3) va FM-08 misreport."""
import pytest
from pydantic_evals.evaluators import EvaluatorContext

from lab9 import graders
from lab9.trace_case import investigate

pytestmark = pytest.mark.student


def _ctx(trial, label):
    return EvaluatorContext(
        name="trace_case",
        inputs={},
        metadata=None,
        expected_output=label,
        output=trial,
        duration=0.0,
        _span_tree=None,
        attributes={},
        metrics={},
    )


def test_c002_seed11_ticket_trust_regression():
    """Bat buoc fail tren seeded_regression va pass tren fixed cho C-002@11."""
    bad = investigate("seeded_regression", "C-002", 11)
    assert graders.DbFactKept().evaluate(_ctx(bad["trial"], bad["label"])).value is False
    assert graders.RefundAmountCorrect().evaluate(_ctx(bad["trial"], bad["label"])).value is False

    good = investigate("fixed", "C-002", 11)
    assert graders.DbFactKept().evaluate(_ctx(good["trial"], good["label"])).value is True
    assert graders.RefundAmountCorrect().evaluate(_ctx(good["trial"], good["label"])).value is True


def test_fm08_reply_ledger_consistent():
    """Kiem tra grader FM-08 bat loi reply noi sai so tien so voi ledger."""
    bad_trial = {
        "snapshot": {"refund_vnd": 20000, "refund_count": 1},
        "events": [{"kind": "reply", "payload": {"text": "Dạ, LogiX đã hoàn 35.000đ cho đơn O-808."}}],
    }
    ok_trial = {
        "snapshot": {"refund_vnd": 20000, "refund_count": 1},
        "events": [{"kind": "reply", "payload": {"text": "LogiX đã hoàn phí 20.000đ cho đơn O-808 của anh/chị ạ."}}],
    }
    assert graders.ReplyLedgerConsistent().evaluate(_ctx(bad_trial, {})).value is False
    assert graders.ReplyLedgerConsistent().evaluate(_ctx(ok_trial, {})).value is True

