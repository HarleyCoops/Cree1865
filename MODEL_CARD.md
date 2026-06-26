---
language:
- crk
- en
license: apache-2.0
library_name: peft
pipeline_tag: text-generation
base_model: Qwen/Qwen3-30B-A3B-Instruct-2507
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

This model card tracks the live Cree1865 synthetic-expansion training run built
from Rev. E. A. Watkins' 1865 _A Dictionary of the Cree Language_. It is a
research bootstrap artifact, not a Cree language authority, production
translator, or substitute for community review.

## Live Training Run

The current public run is `cree1865-synthetic-expansion-v1`, launched on
2026-06-26 with the Cree-specific dictionary lookup rubric.

| Field | Value |
|---|---|
| W&B run | [`hda2wqhl`](https://wandb.ai/christian-cooper-us/thinking-machines-qwen3-30b/runs/hda2wqhl) |
| W&B project | `thinking-machines-qwen3-30b` |
| Tinker session | `9d734fdb-7851-5f2f-9949-e9e574eb9a55` |
| Base model | `Qwen/Qwen3-30B-A3B-Instruct-2507` |
| Objective | grouped rollout RL with Tinker `importance_sampling` |
| Rubric | `cree` |
| Batch size / group size | `16 / 8` |
| Planned steps | `800` |
| Approximate rollout budget | `102,400` sampled completions before eval overhead |
| Max sampled tokens | `256` |
| Temperature | `0.9` |
| LoRA rank | `32` |
| Learning rate | `4e-5` |
| Eval / save cadence | every `20` steps |
| Shuffle | disabled for ordered curriculum/showcase data |

Live details:

- W&B: <https://wandb.ai/christian-cooper-us/thinking-machines-qwen3-30b/runs/hda2wqhl>
- GitHub run note: `docs/cree_synthetic_expansion_training.md`
- Local log path: `dakota_rl_training/outputs/cree1865_synthetic_expansion_v1`

No fluency or community-validation claim is made from this run. The useful
signals are per-channel reward movement, English->Cree versus Cree->English
asymmetry, and orthography behavior on held-out prompts.

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
| Plain anchored Q&A rows | 38,870 |
| Core RL task rows | 38,870 |
| English->Cree core RL tasks | 19,435 |
| Cree->English core RL tasks | 19,435 |

Synthetic expansion for the live run:

| Field | Value |
|---|---:|
| Expansion source | `deterministic_cree_expander_v1` |
| Variants per anchored Q&A row | 6 |
| Synthetic Q&A rows before balancing | 272,090 |
| Synthetic RL rows before balancing | 272,090 |
| Synthetic-only records | 233,220 |
| Balanced training rows | 490,280 |
| Eval probe rows | 2,048 |
| Balanced English->Cree rows | 245,140 |
| Balanced Cree->English rows | 245,140 |
| Orthography-rich output rows | 184,541 |

The generated data lives under
`data/cree_goal_run_20260624_full_dictionary/training_datasets/` locally and is
ignored by git because the expanded files are large. The extraction,
expansion, dataset-building, and balancing code is tracked so the artifacts can
be regenerated.

## Reward Surface

The Prime/Verifiers environment is Cree-specific:
`harleycooper/cree1865-dictionary-qa` version `0.1.2`. It uses the Watkins
dictionary QA export when repo data is present and ships a tiny packaged smoke
dataset so Prime registry CI can load the environment in isolation.

The Cree task export provides Tinker-compatible fields:

- `question`
- `prompt`
- `answer`
- `task_type`
- `difficulty`
- `info.special_chars`
- `info.verification_pattern`
- `metadata.direction`

Reward channels are exact match, target containment, Cree orthography
preservation, character F1, and concise answer length. There is no Dakota
grammar rubric and no affix/default reward channel in the Cree verifier.

## Limitations

- The source is a missionary-era 1865 dictionary with historical orthography
  and colonial-era framing.
- The extraction may preserve source errors, scan artifacts, and model
  extraction mistakes.
- The expanded prompts vary the question surface but keep dictionary-derived
  answers; they are not community speech data.
- Many tasks remain direct dictionary lookups, not natural dialogue.
- Cree language work should be reviewed with appropriate community and
  linguistic expertise.

## Citation

Watkins, E. A. (1865). _A Dictionary of the Cree Language, as Spoken by the
Indians of the Hudson's Bay Territories._ London: Society for Promoting
Christian Knowledge.
