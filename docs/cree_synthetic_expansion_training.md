# Cree Synthetic Expansion Training Plan

This note defines how to turn the anchored Cree dictionary Q&A file into a larger GRPO training dataset without changing the ground-truth answers.

## Live Run

The current run launched on 2026-06-26:

| Field | Value |
|---|---|
| W&B run | [`hda2wqhl`](https://wandb.ai/christian-cooper-us/thinking-machines-qwen3-30b/runs/hda2wqhl) |
| W&B run name | `cree1865-synthetic-expansion-v1` |
| Tinker session | `9d734fdb-7851-5f2f-9949-e9e574eb9a55` |
| Local process ID at launch | `19556` |
| Local log path | `dakota_rl_training/outputs/cree1865_synthetic_expansion_v1` |
| Model | `Qwen/Qwen3-30B-A3B-Instruct-2507` |
| Rubric | `cree` |
| Batch size / group size | `16 / 8` |
| Planned steps | `800` |
| Approximate rollout budget | `102,400` sampled completions before eval overhead |

## Source Contract

The source file is:

```text
data/cree_goal_run_20260624_full_dictionary/training_datasets/qa_pairs_all.jsonl
```

Each row has one dictionary-backed `question`, one `answer`, one `direction`, and source metadata. The expansion step may vary the question surface, but it must not synthesize a new answer. The answer remains anchored to the extracted dictionary entry.

## Expansion Step

Generate deterministic synthetic prompt variants:

```powershell
python scripts\cree\create_cree_synthetic_qa_expansion.py `
  --qa-input data\cree_goal_run_20260624_full_dictionary\training_datasets\qa_pairs_all.jsonl `
  --qa-output data\cree_goal_run_20260624_full_dictionary\training_datasets\synthetic_qa_pairs_all.jsonl `
  --rl-output data\cree_goal_run_20260624_full_dictionary\training_datasets\rl_tasks_synthetic_expanded.jsonl `
  --report data\cree_goal_run_20260624_full_dictionary\training_datasets\synthetic_qa_expansion_report.json `
  --variants-per-record 6
```

With the current `38,870` anchored Q&A rows, `--variants-per-record 6` plus original anchors yields `272,090` Q&A rows and the same number of RL task rows. Each expanded row carries:

- `metadata.anchor_qa_id`: original Q&A row ID
- `metadata.synthetic_expansion`: whether the row is synthetic or the original anchor
- `metadata.answer_anchor`: `dictionary_extraction`
- `metadata.expansion_template` and `metadata.expansion_family`

## Balancing Step

Run the existing Cree balancer on the synthetic RL file:

```powershell
python scripts\cree\create_balanced_cree_showcase_rl.py `
  --input data\cree_goal_run_20260624_full_dictionary\training_datasets\rl_tasks_synthetic_expanded.jsonl `
  --output data\cree_goal_run_20260624_full_dictionary\training_datasets\rl_tasks_synthetic_expanded_balanced.jsonl `
  --eval-output data\cree_goal_run_20260624_full_dictionary\training_datasets\rl_tasks_synthetic_expanded_balanced_eval.jsonl `
  --report data\cree_goal_run_20260624_full_dictionary\training_datasets\rl_tasks_synthetic_expanded_balanced_report.json `
  --eval-records 2048
```

This keeps the existing hard/medium/orthography weighting and direction balancing. The goal is not to make the scalar reward bigger by construction; the goal is to expose the model to many more ways of asking the same dictionary-grounded task while keeping the verifier anchored.

## First Training Run

Use the synthetic balanced file with the Cree rubric:

```powershell
python dakota_rl_training\tinker_train.py `
  --rubric-name cree `
  --dataset-path data\cree_goal_run_20260624_full_dictionary\training_datasets\rl_tasks_synthetic_expanded_balanced.jsonl `
  --eval-path data\cree_goal_run_20260624_full_dictionary\training_datasets\rl_tasks_synthetic_expanded_balanced_eval.jsonl `
  --log-path dakota_rl_training\outputs\cree1865_synthetic_expansion_v1 `
  --wandb-project thinking-machines-qwen3-30b `
  --wandb-name cree1865-synthetic-expansion-v1 `
  --model-name Qwen/Qwen3-30B-A3B-Instruct-2507 `
  --batch-size 16 `
  --group-size 8 `
  --max-steps 800 `
  --no-shuffle `
  --max-tokens 256 `
  --temperature 0.9 `
  --learning-rate 4e-5 `
  --lora-rank 32 `
  --loss-fn importance_sampling `
  --eval-every 20 `
  --save-every 20 `
  --sync-metrics-to-wandb
```

The first run should be `800` steps rather than `1200`. At `batch-size 16` and `group-size 8`, each step asks for `128` completions, so `800` steps gives about `102,400` rollouts before eval and logging overhead. If the per-channel rewards improve without orthography collapse, the next run can move to `1200` steps or increase `group-size` to `16`.

## What To Watch

Track direction-specific and channel-specific learning, not only mean reward:

- `reward/mean`, `eval/reward/mean`
- exact answer match or answer containment channels
- orthography channel, especially macrons and accented vowels
- `direction/english_to_cree` versus `direction/cree_to_english`
- KL, entropy, and gradient norm
- eval reward gaps between original anchors and synthetic prompt families

The expected improvement is not fluency by itself. The expected improvement is stronger dictionary lookup behavior under varied question forms, especially English-to-Cree prompts that require producing Cree as the target language.
