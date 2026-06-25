# Cree1865

Cree1865 is a research repo for building a Cree language RL adapter from one source: Rev. E. A. Watkins' 1865 _A Dictionary of the Cree Language_. The model work described here is grounded in the 1865 Watkins dictionary and the datasets generated from it.

The repo is a Dakota1890-derived pipeline replayed on Cree: extract structured dictionary entries, convert them into supervised and reinforcement-learning tasks, run GRPO training, and publish the resulting adapter/checkpoint artifacts when the runs are ready.

## Source

- Source text: Watkins, E. A. (1865), _A Dictionary of the Cree Language_
- Local source PDF: `CreeDictionary.pdf`
- Archive master PDF: `sources/CreeDictionary_1865_cihm_41985_complete.pdf`
- Language directions in the 1865 dictionary:
  - English -> Cree
  - Cree -> English

The source is one historical dictionary volume. The pipeline treats its English-to-Cree and Cree-to-English sections as extraction directions, not as separate sources.

## What this repo contains

- `dakota_extraction/` — inherited extraction pipeline components adapted for Cree
- `dakota_rl_training/` — RL/Tinker training code and run outputs
- `scripts/cree/` — Cree-specific validation and dataset tooling
- `scripts/conversion/` — dataset conversion utilities
- `wandb_analysis/` — reward ledgers and run-analysis outputs
- `MODEL_CARD.md` — current model/run status
- `SOURCE_NOTES.md` — source-document notes and page-boundary details

Generated full-corpus data under `data/` is intentionally ignored by git. The tracked code and documentation describe how to regenerate it from the local source/extraction artifacts.

## Dataset snapshot

Latest local full-dictionary build:

| Field | Value |
|---|---:|
| Extracted page JSON files | 463 |
| Raw entries | 19,607 |
| Deduplicated usable entries | 19,560 |
| Rejected incomplete entries | 125 |
| Multi-variant entries | 4,049 |
| SFT train / validation | 18,463 / 972 |
| RL task records | 38,870 |
| Plain Q&A records | 38,870 |
| English -> Cree RL tasks | 19,435 |
| Cree -> English RL tasks | 19,435 |
| Duplicate RL task IDs after normalization | 0 |

Dataset root used locally:

`data/cree_goal_run_20260624_full_dictionary/`

Main RL task file used for the current Tinker run path:

`data/cree_goal_run_20260624_full_dictionary/training_datasets/rl_tasks_all.jsonl`

## Current model status

Completed smoke run:

- Base model: `Qwen/Qwen3.5-4B`
- Renderer: `qwen3_5_disable_thinking`
- Steps: 4
- Final reward: `0.1894479405034325`
- Final parse success: `1.0`
- Tinker weights: `tinker://096ba4d7-bccc-5d33-9209-e1a1a8d746dc:train:0/weights/final`
- Reward ledger: `wandb_analysis/cree_reward_ledger_tinker_full_dictionary_smoke_20260624_qwen35_4b_no_think.csv`

Planned/active training path:

- 1200 training steps
- batch size 2
- group size 2
- max sampled tokens 64
- W&B enabled through `WANDB_API_KEY`

The smoke run proves the end-to-end path executes. It is not a final model-quality claim.

## Reward surface

The current RL environment reuses the Dakota1890 deterministic reward-ledger pattern. Cree tasks export Tinker-compatible fields such as:

- `question`
- `prompt`
- `answer`
- `task_type`
- `difficulty`
- `info.special_chars`
- `info.verification_pattern`
- `metadata.direction`

Reward channels include exact match, character overlap, pattern match, an affix/default channel, and parse success.

This is intentionally deterministic. There is no LLM-as-judge claim in the current reward path.

## Validation

Run the offline bootstrap validator:

```bash
python scripts/cree/validate_cree_bootstrap.py
```

Run the project test suite:

```bash
pytest
```

## Important limitations

- This is a research/bootstrap artifact, not a Cree language authority.
- The source is a missionary-era 1865 dictionary with historical orthography and colonial-era framing.
- Extraction can preserve source errors, scan artifacts, and model extraction mistakes.
- Many tasks are dictionary lookups rather than natural dialogue.
- Larger training runs should review long reverse-direction glosses and community-facing Q&A wording before scale-up.
- Cree language work should be reviewed with appropriate community and linguistic expertise.

## Citation

```bibtex
@misc{cree1865,
  title        = {Cree1865: Reinforcement Learning from an 1865 Cree Dictionary},
  author       = {Cooper, Christian Harley},
  year         = {2026},
  howpublished = {\url{https://github.com/HarleyCoops/Cree1865}},
  note         = {Source: Watkins, E. A. (1865). A Dictionary of the Cree Language.}
}
```

Watkins, E. A. (1865). _A Dictionary of the Cree Language, as Spoken by the Indians of the Hudson's Bay Territories._ London: Society for Promoting Christian Knowledge.

## License

Code is Apache-2.0. The 1865 source text is public domain.
