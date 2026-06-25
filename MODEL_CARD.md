---
language:
- crk
- en
license: apache-2.0
library_name: peft
pipeline_tag: text-generation
base_model: Qwen/Qwen3.5-4B
tags:
- cree
- indigenous-languages
- low-resource-language
- dictionary
- reinforcement-learning
- grpo
- tinker
- thinking-machines
---

# Cree1865 Tinker RL Adapter

This model card tracks the Cree1865 reinforcement-learning run built from Rev. E. A. Watkins' 1865 _A Dictionary of the Cree Language_. The repository is a Dakota1890-derived pipeline replayed on a new historical source.

This is a research artifact and a bootstrap pass. It is not a Cree language authority, a production translator, or a substitute for community review.

## Source

- Source: Watkins, E. A. (1865), _A Dictionary of the Cree Language_
- Local PDF: `CreeDictionary.pdf`
- Archive master: `sources/CreeDictionary_1865_cihm_41985_complete.pdf`
- Structure: one book with `Part I. English-Cree` and `Part II. Cree-English`

## Dataset Snapshot

Latest local full-dictionary build:

| Field | Value |
|---|---:|
| Extracted page JSON files | 463 |
| Raw entries | 19,607 |
| Deduplicated usable entries | 19,560 |
| Rejected incomplete entries | 125 |
| Multi-variant entries | 4,049 |
| SFT train / valid | 18,463 / 972 |
| RL task records | 38,870 |
| Plain Q&A records | 38,870 |
| English->Cree RL tasks | 19,435 |
| Cree->English RL tasks | 19,435 |
| Duplicate RL task IDs after normalization | 0 |

The generated data lives under `data/cree_goal_run_20260624_full_dictionary/` locally and is ignored by git. The extraction and dataset-building code is tracked so the artifacts can be regenerated.

## Current Training Status

Redesigned full-dictionary showcase run in progress:

- Launch date: `2026-06-25`
- Base model: `Qwen/Qwen3-30B-A3B-Instruct-2507`
- Dataset: `data/cree_goal_run_20260624_full_dictionary/training_datasets/rl_tasks_balanced_cree_showcase.jsonl`
- Weighted training rows: `70,040`
- Original rows covered: `38,870 / 38,870`
- Direction balance: `35,020 English->Cree / 35,020 Cree->English`
- Objective: grouped rollout RL with Tinker `importance_sampling`
- Batch size / group size: `32 / 8`
- Planned steps: `2,189`
- LoRA rank: `64`
- W&B run: [`4om7k9ao`](https://wandb.ai/christian-cooper-us/thinking-machines-qwen3-30b/runs/4om7k9ao)

Preliminary held-out eval snapshot from step 500:

| Eval metric | Step 0 | Step 500 | Delta |
|---|---:|---:|---:|
| Overall verifier reward | 0.2358 | 0.3628 | +0.1270 |
| Target-Cree reward | 0.2835 | 0.4233 | +0.1398 |
| Target-English reward | 0.1322 | 0.2316 | +0.0994 |
| Target-Cree exact match | 0.0029 | 0.0485 | +0.0456 |
| Target-Cree containment | 0.0913 | 0.1441 | +0.0528 |
| Target-Cree orthography | 0.4177 | 0.5400 | +0.1222 |
| Target-Cree character F1 | 0.3504 | 0.6020 | +0.2515 |
| Target-English character F1 | 0.2818 | 0.4003 | +0.1185 |

These numbers are preliminary verifier metrics, not evidence of fluency or community validation. The scalar reward is rubric-shaped; the more important signal is per-channel movement and the direction split between English->Cree and Cree->English.

Completed 1200-step run:

- Base model: `Qwen/Qwen3.5-4B`
- Dataset: `data/cree_goal_run_20260624_full_dictionary/training_datasets/rl_tasks_all.jsonl`
- Renderer: `qwen3_5_disable_thinking`
- Steps: `1200`
- Batch size / group size: `2 / 2`
- Max sampled tokens: `64`
- W&B run: [`kjn02ee4`](https://wandb.ai/christian-cooper-us/cree1865-tinker/runs/kjn02ee4)
- W&B project: `cree1865-tinker`
- Final reward: `0.21`
- Deduped mean reward: `0.18260238803447346`
- Final parse success: `1.0`
- Deduped mean parse success: `0.99875`
- Tinker weights: `tinker://bf25e2aa-6b3a-557c-8133-fadf5ebcba8f:train:0/weights/final`
- Tinker sampler weights: `tinker://bf25e2aa-6b3a-557c-8133-fadf5ebcba8f:train:0/sampler_weights/final`
- Raw ledger: `wandb_analysis/cree_reward_ledger_tinker_full_dictionary_1200step_20260624_qwen35_4b_no_think.csv`
- Deduped ledger: `wandb_analysis/cree_reward_ledger_tinker_full_dictionary_1200step_20260624_qwen35_4b_no_think_deduped.csv`

Resume note:

The first Tinker session stalled at local step 868 with `No progress made in 7200s`. The run was resumed under the same W&B run ID, `kjn02ee4`, from checkpoint `000800`. The final local raw ledger therefore has 1269 rows: 1200 unique steps plus 69 replay rows from steps 800-868. The deduped ledger keeps the last row per step for steps 0-1199.

Completed smoke run:

- Steps: `4`
- Final reward: `0.1894479405034325`
- Final parse success: `1.0`
- Tinker weights: `tinker://096ba4d7-bccc-5d33-9209-e1a1a8d746dc:train:0/weights/final`
- Ledger: `wandb_analysis/cree_reward_ledger_tinker_full_dictionary_smoke_20260624_qwen35_4b_no_think.csv`

At these small-model settings, 1200 steps is long but feasible; the practical risk is Tinker service stalling, not the step count itself. Future longer runs should use checkpointed chunks and preserve a single W&B run ID when continuing the same experiment.

## Reward Surface

The current Prime/Verifiers environment is Cree-specific: `harleycooper/cree1865-dictionary-qa` version `0.1.2`. It uses the Watkins dictionary QA export when repo data is present and ships a tiny packaged smoke dataset so Prime registry CI can load the environment in isolation.

The Cree task export provides Tinker-compatible fields:

- `question`
- `prompt`
- `answer`
- `task_type`
- `difficulty`
- `info.special_chars`
- `info.verification_pattern`
- `metadata.direction`

Reward channels are exact match, target containment, Cree orthography preservation, character F1, and concise answer length. There is no Dakota grammar rubric and no affix/default reward channel in the Cree verifier. Larger runs should still review long reverse-section English glosses and community-facing Q&A wording before making model-quality claims.

## Limitations

- The source is a missionary-era 1865 dictionary with historical orthography and colonial-era framing.
- The extraction may preserve source errors, scan artifacts, and model extraction mistakes.
- Many tasks are direct dictionary lookups, not natural dialogue.
- Long reverse-section glosses should be filtered or down-weighted before larger-scale training.
- Cree language work should be reviewed with appropriate community and linguistic expertise.

## Citation

Watkins, E. A. (1865). _A Dictionary of the Cree Language, as Spoken by the Indians of the Hudson's Bay Territories._ London: Society for Promoting Christian Knowledge.
