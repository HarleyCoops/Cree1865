from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Sequence


TOTAL_LOSS_KEYS = (
    "train/loss",
    "loss/total",
    "total_loss",
    "mean_loss",
    "loss",
    "optim/loss",
    "objective/loss",
    "forward_backward/loss",
    "fwdbwd/loss",
)
POLICY_LOSS_KEYS = (
    "loss/policy",
    "policy_loss",
    "pg_loss",
    "actor_loss",
    "loss/actor",
    "clipped_policy_loss",
)
KL_PENALTY_LOSS_KEYS = (
    "loss/kl_penalty",
    "kl_penalty_loss",
    "kl_loss",
    "kl_penalty",
    "loss/kl",
)
VALUE_LOSS_KEYS = ("loss/value", "value_loss", "critic_loss", "loss/critic")
REWARD_LOSS_KEYS = ("loss/reward", "reward_loss")
CROSS_ENTROPY_KEYS = (
    "loss/cross_entropy",
    "cross_entropy",
    "cross_entropy_loss",
    "ce_loss",
)
NLL_KEYS = ("loss/nll", "nll", "nll_loss", "negative_log_likelihood")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _first_number(metrics: Mapping[str, Any], keys: Iterable[str]) -> float | None:
    for key in keys:
        value = metrics.get(key)
        if _is_number(value):
            return float(value)
    return None


def _set_if_number(
    metrics: MutableMapping[str, Any],
    target: str,
    keys: Iterable[str],
    *,
    overwrite: bool = False,
) -> float | None:
    if not overwrite and _is_number(metrics.get(target)):
        return float(metrics[target])
    value = _first_number(metrics, keys)
    if value is not None:
        metrics[target] = value
    return value


def _safe_perplexity(loss: float) -> float | None:
    if not math.isfinite(loss) or loss > 709.0:
        return None
    return math.exp(loss)


def augment_dashboard_metrics(metrics: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Add canonical dashboard names for Tinker/GRPO metrics in-place.

    The Tinker backend can emit metric keys that vary by loss function and
    version. This normalizes known raw keys into stable W&B dashboard names
    without fabricating unavailable values.
    """

    total_loss = _set_if_number(metrics, "train/loss", TOTAL_LOSS_KEYS)
    if total_loss is not None:
        metrics.setdefault("loss/total", total_loss)
    else:
        total_loss = _set_if_number(metrics, "loss/total", TOTAL_LOSS_KEYS)
        if total_loss is not None:
            metrics.setdefault("train/loss", total_loss)

    _set_if_number(metrics, "loss/policy", POLICY_LOSS_KEYS)
    _set_if_number(metrics, "loss/kl_penalty", KL_PENALTY_LOSS_KEYS)
    _set_if_number(metrics, "loss/value", VALUE_LOSS_KEYS)
    _set_if_number(metrics, "loss/reward", REWARD_LOSS_KEYS)

    ce_loss = _set_if_number(metrics, "loss/cross_entropy", CROSS_ENTROPY_KEYS)
    nll_loss = _set_if_number(metrics, "loss/nll", NLL_KEYS)
    perplexity_source = ce_loss if ce_loss is not None else nll_loss
    if perplexity_source is not None and not _is_number(metrics.get("train/perplexity")):
        perplexity = _safe_perplexity(perplexity_source)
        if perplexity is not None:
            metrics["train/perplexity"] = perplexity

    _set_if_number(
        metrics,
        "optim/grad_norm",
        ("optim/grad_norm", "grad_norm", "global_grad_norm", "optim/global_grad_norm"),
    )
    _set_if_number(
        metrics,
        "optim/grad_norm_clipped",
        ("optim/grad_norm_clipped", "grad_norm_clipped", "clipped_grad_norm"),
    )
    _set_if_number(metrics, "optim/param_norm", ("optim/param_norm", "param_norm", "weight_norm"))
    _set_if_number(metrics, "optim/clip_frac", ("optim/clip_frac", "clip_frac", "clipped_fraction"))

    _set_if_number(
        metrics,
        "reward/mean",
        ("reward/mean", "env/all/reward/mean", "env/all/reward/total", "env/all/reward/scalar"),
    )
    _set_if_number(metrics, "reward/std", ("reward/std", "env/all/reward/std"))
    _set_if_number(metrics, "reward/min", ("reward/min", "env/all/reward/min"))
    _set_if_number(metrics, "reward/max", ("reward/max", "env/all/reward/max"))
    _set_if_number(metrics, "reward/kl_coef", ("reward/kl_coef", "kl_penalty_coef"))

    _set_if_number(
        metrics,
        "eval/loss",
        ("eval/loss", "test/loss", "test/train/loss", "test/loss/total"),
    )
    eval_ce = _set_if_number(
        metrics,
        "eval/cross_entropy",
        ("eval/cross_entropy", "test/cross_entropy", "test/loss/cross_entropy"),
    )
    eval_nll = _set_if_number(metrics, "eval/nll", ("eval/nll", "test/nll", "test/loss/nll"))
    eval_perplexity_source = eval_ce if eval_ce is not None else eval_nll
    if eval_perplexity_source is not None and not _is_number(metrics.get("eval/perplexity")):
        perplexity = _safe_perplexity(eval_perplexity_source)
        if perplexity is not None:
            metrics["eval/perplexity"] = perplexity

    _set_if_number(
        metrics,
        "eval/reward/mean",
        (
            "eval/reward/mean",
            "test/env/all/reward/mean",
            "test/env/all/reward/total",
            "test/env/all/reward/scalar",
        ),
    )
    _set_if_number(metrics, "eval/reward/std", ("eval/reward/std", "test/env/all/reward/std"))
    _set_if_number(
        metrics,
        "eval/exact_match",
        (
            "eval/exact_match",
            "test/env/all/ledger/exact_match_norm",
            "test/env/all/ledger/exact_match_raw",
        ),
    )
    _set_if_number(
        metrics,
        "eval/char_overlap",
        (
            "eval/char_overlap",
            "test/env/all/ledger/char_overlap_norm",
            "test/env/all/ledger/char_overlap_raw",
        ),
    )
    _set_if_number(
        metrics,
        "eval/parse_success",
        ("eval/parse_success", "test/env/all/ledger/parse_success"),
    )

    step_time = _set_if_number(metrics, "perf/step_time", ("perf/step_time", "time/total"))
    if step_time and step_time > 0:
        total_tokens = _first_number(metrics, ("env/all/total_tokens",))
        if total_tokens is None:
            ac_tokens = _first_number(metrics, ("env/all/total_ac_tokens",)) or 0.0
            ob_tokens = _first_number(metrics, ("env/all/total_ob_tokens",)) or 0.0
            total_tokens = ac_tokens + ob_tokens
        if total_tokens and not _is_number(metrics.get("perf/tokens_per_sec")):
            metrics["perf/tokens_per_sec"] = total_tokens / step_time

        total_samples = _first_number(metrics, ("env/all/total_episodes", "env/all/total_turns"))
        if total_samples and not _is_number(metrics.get("perf/samples_per_sec")):
            metrics["perf/samples_per_sec"] = total_samples / step_time

    return metrics


def _mean_std(values: Sequence[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return mean, math.sqrt(variance)


def _trajectory_rewards(trajectory_groups: Iterable[Any]) -> list[float]:
    rewards: list[float] = []
    for trajectory_group in trajectory_groups:
        get_total_rewards = getattr(trajectory_group, "get_total_rewards", None)
        if callable(get_total_rewards):
            rewards.extend(float(value) for value in get_total_rewards())
    return rewards


def add_reward_distribution_metrics(
    metrics: MutableMapping[str, Any],
    trajectory_groups: Iterable[Any],
    *,
    prefix: str = "env/all",
) -> MutableMapping[str, Any]:
    rewards = _trajectory_rewards(trajectory_groups)
    if not rewards:
        return metrics
    mean, std = _mean_std(rewards)
    metrics.setdefault(f"{prefix}/reward/mean", mean)
    metrics.setdefault(f"{prefix}/reward/std", std)
    metrics.setdefault(f"{prefix}/reward/min", min(rewards))
    metrics.setdefault(f"{prefix}/reward/max", max(rewards))
    return metrics


def _mean_metric_dicts(items: Iterable[Mapping[str, Any]]) -> dict[str, float]:
    values_by_key: dict[str, list[float]] = defaultdict(list)
    for item in items:
        for key, value in item.items():
            if _is_number(value):
                values_by_key[key].append(float(value))
    return {key: sum(values) / len(values) for key, values in values_by_key.items() if values}


def _merge_forward_backward_metrics(
    metrics: MutableMapping[str, Any] | None,
    raw_metrics: Iterable[Mapping[str, Any]],
) -> None:
    if metrics is None:
        return
    merged = _mean_metric_dicts(raw_metrics)
    for key, value in merged.items():
        metrics.setdefault(key, value)
        metrics.setdefault(f"train/fwdbwd/{key}", value)
    augment_dashboard_metrics(metrics)


def _make_augmented_train_step(train_module: Any) -> Callable[..., Any]:
    async def train_step(
        data_D: list[Any],
        training_client: Any,
        learning_rate: float,
        num_substeps: int,
        loss_fn: Any,
        loss_fn_config: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> list[Any]:
        batches = train_module.split_list(data_D, min(num_substeps, len(data_D)))
        if not batches:
            return []

        import tinker

        adam_params = tinker.AdamParams(
            learning_rate=learning_rate,
            beta1=0.9,
            beta2=0.95,
            eps=1e-8,
        )
        training_logprobs_D: list[Any] = []
        optim_result: Any | None = None
        fwd_bwd_metric_records: list[Mapping[str, Any]] = []

        fwd_bwd_future = await training_client.forward_backward_async(
            [train_module._remove_mask(d) for d in batches[0]],
            loss_fn=loss_fn,
            loss_fn_config=loss_fn_config,
        )
        optim_future = await training_client.optim_step_async(adam_params)

        for i in range(len(batches)):
            if i + 1 < len(batches):
                next_fwd_bwd_future = await training_client.forward_backward_async(
                    [train_module._remove_mask(d) for d in batches[i + 1]],
                    loss_fn=loss_fn,
                    loss_fn_config=loss_fn_config,
                )
                next_optim_future = await training_client.optim_step_async(adam_params)
            else:
                next_fwd_bwd_future = None
                next_optim_future = None

            fwd_bwd_result = await fwd_bwd_future.result_async()
            if getattr(fwd_bwd_result, "metrics", None):
                fwd_bwd_metric_records.append(fwd_bwd_result.metrics)
            training_logprobs_D.extend(train_module._training_logprobs_from_fwd_bwd(fwd_bwd_result))
            optim_result = await optim_future.result_async()

            if next_fwd_bwd_future is not None and next_optim_future is not None:
                fwd_bwd_future = next_fwd_bwd_future
                optim_future = next_optim_future

        if metrics is not None and optim_result is not None and optim_result.metrics:
            metrics.update(optim_result.metrics)
        _merge_forward_backward_metrics(metrics, fwd_bwd_metric_records)

        return training_logprobs_D

    return train_step


def install_tinker_metric_augmentation() -> None:
    """Install local metric augmentation hooks for future Tinker runs."""

    from tinker_cookbook.rl import metric_util, train
    from tinker_cookbook.utils import ml_log

    if not getattr(train.train_step, "_dakota_metric_augmented", False):
        augmented_train_step = _make_augmented_train_step(train)
        setattr(augmented_train_step, "_dakota_metric_augmented", True)
        train.train_step = augmented_train_step

    if not getattr(train.compute_trajectory_metrics, "_dakota_metric_augmented", False):
        original_train_compute = train.compute_trajectory_metrics

        def compute_trajectory_metrics_with_reward_stats(trajectory_groups_P, taglist_P):
            metrics = original_train_compute(trajectory_groups_P, taglist_P)
            add_reward_distribution_metrics(metrics, trajectory_groups_P)
            return metrics

        setattr(compute_trajectory_metrics_with_reward_stats, "_dakota_metric_augmented", True)
        train.compute_trajectory_metrics = compute_trajectory_metrics_with_reward_stats

    if not getattr(metric_util.compute_trajectory_metrics, "_dakota_metric_augmented", False):
        original_metric_compute = metric_util.compute_trajectory_metrics

        def metric_util_compute_with_reward_stats(trajectory_groups_P, taglist_P):
            metrics = original_metric_compute(trajectory_groups_P, taglist_P)
            add_reward_distribution_metrics(metrics, trajectory_groups_P)
            return metrics

        setattr(metric_util_compute_with_reward_stats, "_dakota_metric_augmented", True)
        metric_util.compute_trajectory_metrics = metric_util_compute_with_reward_stats

    if not getattr(ml_log.MultiplexLogger.log_metrics, "_dakota_metric_augmented", False):
        original_log_metrics = ml_log.MultiplexLogger.log_metrics

        def log_metrics_with_dashboard_aliases(self, metrics: dict[str, Any], step: int | None = None):
            augment_dashboard_metrics(metrics)
            return original_log_metrics(self, metrics, step)

        setattr(log_metrics_with_dashboard_aliases, "_dakota_metric_augmented", True)
        ml_log.MultiplexLogger.log_metrics = log_metrics_with_dashboard_aliases
