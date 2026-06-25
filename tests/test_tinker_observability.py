from __future__ import annotations

import math

from dakota_rl_training.tinker_integration.observability import (
    add_reward_distribution_metrics,
    augment_dashboard_metrics,
    install_tinker_metric_augmentation,
)


def test_augment_dashboard_metrics_adds_loss_gradient_and_perplexity_aliases():
    metrics = {
        "loss": 1.25,
        "policy_loss": 0.75,
        "kl_penalty": 0.125,
        "cross_entropy": 2.0,
        "global_grad_norm": 4.5,
        "grad_norm_clipped": 1.0,
        "param_norm": 42.0,
        "clip_frac": 0.25,
    }

    augment_dashboard_metrics(metrics)

    assert metrics["train/loss"] == 1.25
    assert metrics["loss/total"] == 1.25
    assert metrics["loss/policy"] == 0.75
    assert metrics["loss/kl_penalty"] == 0.125
    assert metrics["loss/cross_entropy"] == 2.0
    assert metrics["train/perplexity"] == math.exp(2.0)
    assert metrics["optim/grad_norm"] == 4.5
    assert metrics["optim/grad_norm_clipped"] == 1.0
    assert metrics["optim/param_norm"] == 42.0
    assert metrics["optim/clip_frac"] == 0.25


def test_augment_dashboard_metrics_adds_reward_eval_and_perf_aliases():
    metrics = {
        "env/all/reward/total": 0.2,
        "env/all/reward/std": 0.05,
        "env/all/total_ac_tokens": 10,
        "env/all/total_ob_tokens": 90,
        "env/all/total_episodes": 4,
        "time/total": 5.0,
        "test/env/all/reward/mean": 0.3,
        "test/env/all/reward/std": 0.04,
        "test/env/all/ledger/exact_match_norm": 0.2,
        "test/env/all/ledger/char_overlap_norm": 0.6,
        "test/env/all/ledger/parse_success": 1.0,
    }

    augment_dashboard_metrics(metrics)

    assert metrics["reward/mean"] == 0.2
    assert metrics["reward/std"] == 0.05
    assert metrics["perf/step_time"] == 5.0
    assert metrics["perf/tokens_per_sec"] == 20.0
    assert metrics["perf/samples_per_sec"] == 0.8
    assert metrics["eval/reward/mean"] == 0.3
    assert metrics["eval/reward/std"] == 0.04
    assert metrics["eval/exact_match"] == 0.2
    assert metrics["eval/char_overlap"] == 0.6
    assert metrics["eval/parse_success"] == 1.0


def test_augment_dashboard_metrics_adds_cree_direction_and_target_aliases():
    metrics = {
        "env/target/cree/reward/mean": 0.18,
        "env/target/english/reward/mean": 0.31,
        "env/target/cree/ledger/orthography_raw": 0.44,
        "env/target/cree/ledger/char_f1_raw": 0.52,
        "env/direction/english_to_cree/reward/mean": 0.18,
        "env/direction/cree_to_english/reward/mean": 0.31,
        "test/env/target/cree/reward/mean": 0.21,
        "test/env/target/english/reward/mean": 0.35,
        "test/env/target/cree/ledger/exact_raw": 0.09,
        "test/env/target/cree/ledger/target_containment_raw": 0.16,
        "test/env/direction/english_to_cree/ledger/char_f1_raw": 0.49,
    }

    augment_dashboard_metrics(metrics)

    assert metrics["slice/target_cree/reward_mean"] == 0.18
    assert metrics["slice/target_english/reward_mean"] == 0.31
    assert math.isclose(metrics["slice/target_cree_gap"], 0.13)
    assert metrics["slice/target_cree/orthography"] == 0.44
    assert metrics["slice/target_cree/char_f1"] == 0.52
    assert metrics["slice/english_to_cree/reward_mean"] == 0.18
    assert metrics["slice/cree_to_english/reward_mean"] == 0.31
    assert math.isclose(metrics["slice/direction_gap"], 0.13)
    assert metrics["eval/slice/target_cree/reward_mean"] == 0.21
    assert metrics["eval/slice/target_english/reward_mean"] == 0.35
    assert math.isclose(metrics["eval/slice/target_cree_gap"], 0.14)
    assert metrics["eval/slice/target_cree/exact"] == 0.09
    assert metrics["eval/slice/target_cree/target_containment"] == 0.16
    assert metrics["eval/slice/english_to_cree/char_f1"] == 0.49


class _TrajectoryGroup:
    def __init__(self, rewards):
        self._rewards = rewards

    def get_total_rewards(self):
        return self._rewards


def test_add_reward_distribution_metrics_records_mean_std_min_and_max():
    metrics = {}

    add_reward_distribution_metrics(
        metrics,
        [_TrajectoryGroup([0.1, 0.3]), _TrajectoryGroup([0.2, 0.4])],
    )

    assert metrics["env/all/reward/mean"] == 0.25
    assert metrics["env/all/reward/std"] == math.sqrt(0.0125)
    assert metrics["env/all/reward/min"] == 0.1
    assert metrics["env/all/reward/max"] == 0.4


def test_install_tinker_metric_augmentation_patches_cookbook_entry_points():
    from tinker_cookbook.rl import metric_util, train
    from tinker_cookbook.utils import ml_log

    install_tinker_metric_augmentation()

    assert getattr(train.train_step, "_dakota_metric_augmented", False)
    assert getattr(train.compute_trajectory_metrics, "_dakota_metric_augmented", False)
    assert getattr(metric_util.compute_trajectory_metrics, "_dakota_metric_augmented", False)
    assert getattr(ml_log.MultiplexLogger.log_metrics, "_dakota_metric_augmented", False)
