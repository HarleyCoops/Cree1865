# Cree 1865 Balanced Showcase Run

This run is designed to show whether the new Cree-specific dictionary rubric can produce a visible learning signal when the model is trained against the full synthetic Q&A surface from the 1865 dictionary.

Do not read scalar reward as the deliverable. A lookup rubric's absolute reward value is shaped by the verifier weights; it is not a direct fluency measure. The important signal is whether the rubric channels move in the right direction and whether the English-to-Cree target direction remains weaker than the Cree-to-English lookup direction.

## Training Dataset

Generate the weighted file and diagnostic eval probe:

```powershell
python scripts\cree\create_balanced_cree_showcase_rl.py
```

Generated local artifacts:

- `data/cree_goal_run_20260624_full_dictionary/training_datasets/rl_tasks_balanced_cree_showcase.jsonl`
- `data/cree_goal_run_20260624_full_dictionary/training_datasets/rl_tasks_balanced_cree_showcase_eval.jsonl`
- `data/cree_goal_run_20260624_full_dictionary/training_datasets/rl_tasks_balanced_cree_showcase_report.json`

The training file is intentionally ignored by git because it is about 87 MB and is reproducible from the committed generator.

Current generated stats:

| Metric | Value |
| --- | ---: |
| Source rows | 38,870 |
| Weighted train rows | 70,040 |
| Diagnostic eval rows | 1,024 |
| Missing original rows | 0 |
| Duplicate output IDs | 0 |
| Word translation rows | 35,020 |
| Reverse translation rows | 35,020 |
| Hard rows after weighting | 4,692 |
| Medium rows after weighting | 6,336 |
| Easy rows after weighting | 59,012 |

The first 512 ordered training rows are deliberately rich in harder examples:

| Tier | First 512 Rows |
| --- | ---: |
| hard_orthography | 128 |
| medium_orthography | 128 |
| hard | 64 |
| medium | 64 |
| easy_orthography | 64 |
| easy | 64 |

This gives the first phase of the run immediate reward contrast while preserving all original records and exact bidirectional task balance across the full epoch.

## Metrics To Watch

Primary dashboard signals:

| Question | Metrics |
| --- | --- |
| Is the model learning the lookup task? | `eval/slice/target_cree/reward_mean`, `eval/slice/target_english/reward_mean`, `eval/reward/mean` |
| Which verifier channel moved? | `eval/slice/target_cree/exact`, `eval/slice/target_cree/target_containment`, `eval/slice/target_cree/orthography`, `eval/slice/target_cree/char_f1`, `eval/slice/target_cree/length` |
| Is English-to-Cree still the failure mode? | `eval/slice/target_cree_gap`, `eval/slice/direction_gap` |
| Is the training stable? | `train/loss`, `loss/policy`, `loss/kl_penalty`, `optim/grad_norm`, `reward/std` |

`slice/target_cree_gap` is computed as:

```text
target-English reward - target-Cree reward
```

A positive gap means the model is doing better when the target is English than when the target is Cree. That is expected early. The showcase result would be more convincing if the target-Cree channel improves and the gap narrows without simply inflating length or target-containment reward.

The raw tagged Tinker metrics are also available for inspection:

- `env/direction/english_to_cree/...`
- `env/direction/cree_to_english/...`
- `env/target/cree/...`
- `env/target/english/...`
- `test/env/direction/english_to_cree/...`
- `test/env/direction/cree_to_english/...`
- `test/env/target/cree/...`
- `test/env/target/english/...`

## Confirming The Cree GRPO-Style Path

The launch must pass `--rubric-name cree`. That flag selects `create_cree_rubric()` in `dakota_rl_training/tinker_integration/cree.py`, which returns `CreeDictionaryRubric` from `environments/cree1865_dictionary_qa`.

The training stack uses Tinker cookbook RL with grouped rollouts:

- `--group-size` controls the number of sampled completions per prompt group.
- `DakotaGrammarEnvGroupBuilder.make_envs()` creates one `DakotaTinkerEnv` per rollout.
- `DakotaTinkerEnv.step()` scores each completion with the Cree rubric.
- `train.Config(loss_fn="importance_sampling")` uses the same modified GRPO-style grouped objective used in the earlier pipeline, rather than SFT or a plain cross-entropy objective.

This is not a generic Dakota grammar run when launched with `--rubric-name cree`; the Dakota names remain in shared adapter classes, but the reward function is Cree dictionary lookup.

## Recommended Full Run

One weighted epoch with `batch_size=32` is:

```text
ceil(70040 / 32) = 2189 training steps
```

With `group_size=8`, that is roughly:

```text
2189 steps * 32 prompts/step * 8 rollouts/prompt = 560,384 sampled completions
```

Recommended command:

```powershell
python dakota_rl_training\tinker_train.py `
  --rubric-name cree `
  --model-name Qwen/Qwen3-30B-A3B-Instruct-2507 `
  --renderer-name qwen3_instruct `
  --dataset-path data\cree_goal_run_20260624_full_dictionary\training_datasets\rl_tasks_balanced_cree_showcase.jsonl `
  --eval-path data\cree_goal_run_20260624_full_dictionary\training_datasets\rl_tasks_balanced_cree_showcase_eval.jsonl `
  --batch-size 32 `
  --group-size 8 `
  --max-steps 2189 `
  --eval-examples 1024 `
  --max-tokens 192 `
  --temperature 1.0 `
  --learning-rate 1e-5 `
  --lora-rank 64 `
  --loss-fn importance_sampling `
  --num-substeps 1 `
  --eval-every 50 `
  --save-every 100 `
  --seed 1865 `
  --no-shuffle `
  --wandb-project thinking-machines-qwen3-30b `
  --wandb-name cree1865-balanced-showcase-v1 `
  --log-path dakota_rl_training\outputs\cree_balanced_showcase_v1 `
  --ledger-csv wandb_analysis\cree_balanced_showcase_reward_ledger.csv `
  --sync-metrics-to-wandb
```

This should be a fresh run, not a resume into the previous Cree W&B trace. The earlier run used the wrong experimental surface for the question we are asking now; keeping this as a clean restart makes the redesigned rubric, ordered full-dictionary dataset, and direction-sliced metrics interpretable.

## Why These Settings

`group_size=8` is the right first full-run setting because the Cree rubric has several partially continuous channels: exact match, target containment, orthography, character F1, and length control. The model does not need a huge rollout group just to discover reward variance, but it does need enough alternatives per prompt for group-relative advantages to be meaningful. If `remove_constant_reward_groups` drops too many groups, the next run should increase this to `group_size=16`.

`batch_size=32` gives 256 completions per optimizer step at `group_size=8`. That is large enough for stable reward estimates while still giving about 2,189 optimizer updates per weighted epoch. A larger batch would reduce update count and can make the learning curve look flatter even when total sampled tokens are high.

`lora_rank=64` is the right showcase setting: larger than the earlier narrow adapter, but not so large that the run mostly demonstrates memorization capacity. If the reward signal is strong and stable, rank 128 is a later capacity test, not the first proof run.

`learning_rate=1e-5` is intentionally lower than the current script default. The previous Cree result was not a clear win, and this run is testing a redesigned reward/data surface. A lower rate gives cleaner evidence about whether reward improves before risking adapter drift.

`--no-shuffle` matters because the generated file is an ordered curriculum. If this flag is omitted, the weighting still helps, but the early hard/orthography pressure is lost.

## Is 1200 Steps Too Long?

No, not for this redesigned file. At `batch_size=32`, `1200` steps is only about 55% of one weighted epoch:

```text
1200 / 2189 = 0.55 epoch
```

It is still a large rollout budget:

```text
1200 * 32 * 8 = 307,200 sampled completions
```

The practical sequence should be:

1. Run a 200-step canary with the same command but `--max-steps 200`.
2. If reward variance, parse success, and eval reward look sane, continue the same run plan to 1200 steps.
3. If the 1200-step curve is still improving without eval collapse, run the full 2189-step one-epoch showcase.

Do not interpret this as community validation or fluency. It is a verifier-learning test: can the model learn to satisfy the Cree dictionary rubric over the expanded synthetic Q&A surface?
