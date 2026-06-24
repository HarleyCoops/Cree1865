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
datasets:
- local:cree_goal_run_20260624_full_dictionary
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

Completed smoke run:

- Base model: `Qwen/Qwen3.5-4B`
- Dataset: `data/cree_goal_run_20260624_full_dictionary/training_datasets/rl_tasks_all.jsonl`
- Renderer: `qwen3_5_disable_thinking`
- Steps: 4
- Final reward: `0.1894479405034325`
- Final parse success: `1.0`
- Tinker weights: `tinker://096ba4d7-bccc-5d33-9209-e1a1a8d746dc:train:0/weights/final`
- Ledger: `wandb_analysis/cree_reward_ledger_tinker_full_dictionary_smoke_20260624_qwen35_4b_no_think.csv`

Next run:

- 1200 training steps
- batch size 2
- group size 2
- max sampled tokens 64
- W&B enabled through `WANDB_API_KEY`

At the current small-model settings, 1200 steps is long but reasonable: the previous smoke timing suggests roughly 3-4 hours plus service overhead. It should not be treated as a final scale run.

## Reward Surface

The current environment reuses the Dakota1890 deterministic reward ledger. The Cree task export now provides Tinker-compatible fields:

- `question`
- `prompt`
- `answer`
- `task_type`
- `difficulty`
- `info.special_chars`
- `info.verification_pattern`
- `metadata.direction`

Reward channels include exact match, character overlap, pattern match, affix/default channel, and parse success. This is appropriate for a small audited run, but larger runs should first review long reverse-section English glosses and community-facing Q&A wording.

## Limitations

- The source is a missionary-era 1865 dictionary with historical orthography and colonial-era framing.
- The extraction may preserve source errors, scan artifacts, and model extraction mistakes.
- Many tasks are direct dictionary lookups, not natural dialogue.
- Long reverse-section glosses should be filtered or down-weighted before larger-scale training.
- Cree language work should be reviewed with appropriate community and linguistic expertise.

## Citation

Watkins, E. A. (1865). _A Dictionary of the Cree Language, as Spoken by the Indians of the Hudson's Bay Territories._ London: Society for Promoting Christian Knowledge.
