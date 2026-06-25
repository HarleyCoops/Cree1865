# Cree RL Observability

Date: 2026-06-25

## What Changed

Future `dakota_rl_training/tinker_train.py` runs install a local Tinker metrics augmentation hook before entering the cookbook training loop.

The hook does three things:

1. It merges `ForwardBackwardOutput.metrics` into the per-step metric dict before optimizer metrics are logged. This surfaces backend loss metrics when Tinker emits them.
2. It normalizes raw metric names into stable dashboard names for W&B and `metrics.jsonl`.
3. It adds reward distribution, eval aliases, and throughput aliases from metrics already available in the RL rollout loop.

## New Canonical Metric Names

Loss and objective aliases, when the backend emits the underlying metric:

- `train/loss`
- `loss/total`
- `loss/policy`
- `loss/kl_penalty`
- `loss/value`
- `loss/reward`
- `loss/cross_entropy`
- `loss/nll`
- `train/perplexity`

Stability aliases:

- `optim/grad_norm`
- `optim/grad_norm_clipped`
- `optim/param_norm`
- `optim/clip_frac`

Reward health:

- `reward/mean`
- `reward/std`
- `reward/min`
- `reward/max`
- `reward/kl_coef`, if present in raw metrics

Task-level eval aliases from the built-in held-out RL evaluator:

- `eval/reward/mean`
- `eval/reward/std`
- `eval/exact_match`
- `eval/char_overlap`
- `eval/parse_success`

Throughput aliases:

- `perf/step_time`
- `perf/tokens_per_sec`
- `perf/samples_per_sec`

## Caveat

The Tinker cookbook optimizer path always exposed optimizer internals, but the installed GRPO/importance-sampling backend did not visibly expose a named total loss in the completed 1200-step Cree run. The new hook will log `train/loss` as soon as Tinker emits a loss-like forward/backward metric such as `loss`, `total_loss`, or `mean_loss`. It does not relabel reward or KL as loss.

Perplexity is only logged when a cross-entropy or NLL metric exists. For the current GRPO dictionary-lookup setup, reward, exact match, character overlap, parse success, KL, and gradient health are the reliable live signals until a separate CE/NLL eval path is added.
