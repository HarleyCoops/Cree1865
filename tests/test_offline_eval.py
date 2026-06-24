from pathlib import Path

import pytest

if not Path("eval/score_extraction.py").exists():
    pytest.skip("offline eval package was not copied into Cree1865", allow_module_level=True)

from eval.score_extraction import load_pairs, score_pairs


def test_sample_fixtures_metrics():
    truth = load_pairs("eval/fixtures/sample_ground_truth.jsonl")
    pred = load_pairs("eval/fixtures/sample_predictions.jsonl")
    scores = score_pairs(pred, truth)
    assert scores.n == len(truth)
    assert 0 <= scores.token_acc <= 1
    assert 0 <= scores.diacritics <= 1
    assert scores.char_dist >= 0
