# Cree 1200-Step Tinker Run

Run date: 2026-06-24 to 2026-06-25

## Outcome

The full-dictionary Cree1865 Tinker run completed 1200 training steps on `Qwen/Qwen3.5-4B` with the `qwen3_5_disable_thinking` renderer.

- W&B project: `cree1865-tinker`
- W&B run ID: `kjn02ee4`
- W&B run: <https://wandb.ai/christian-cooper-us/cree1865-tinker/runs/kjn02ee4>
- Final Tinker weights: `tinker://bf25e2aa-6b3a-557c-8133-fadf5ebcba8f:train:0/weights/final`
- Final sampler weights: `tinker://bf25e2aa-6b3a-557c-8133-fadf5ebcba8f:train:0/sampler_weights/final`

## Metrics

Metrics are from the deduped reward ledger, keeping the last row for each step.

- Unique steps: `1200` (`0` through `1199`)
- Final reward: `0.21`
- Mean reward: `0.18260238803447346`
- Final parse success: `1.0`
- Mean parse success: `0.99875`
- Final character-overlap score: `0.37499999999999994`
- Mean character-overlap score: `0.36454791208131276`
- Final exact-match score: `0.0`
- Mean exact-match score: `0.0014583333333333334`

## Artifacts

- Raw reward ledger: `wandb_analysis/cree_reward_ledger_tinker_full_dictionary_1200step_20260624_qwen35_4b_no_think.csv`
- Deduped reward ledger: `wandb_analysis/cree_reward_ledger_tinker_full_dictionary_1200step_20260624_qwen35_4b_no_think_deduped.csv`
- Local output directory: `dakota_rl_training/outputs/cree_tinker_full_dictionary_1200step_20260624_qwen35_4b_no_think/`

The raw ledger has 1269 rows because the run resumed from checkpoint `000800` after the first session stalled at step 868. The resumed section replayed steps 800-868 locally before continuing to step 1199. The deduped ledger has one row per training step.

## Operational Note

The first Tinker session failed after `No progress made in 7200s`. The corrected resume used `WANDB_RUN_ID=kjn02ee4` and `WANDB_RESUME=must`, so all public W&B data stayed in the original run. A brief accidental second W&B run was stopped and deleted before it accumulated training metrics.

For this setup, 1200 steps is not inherently too long, but it is long enough to expose service-stall risk. Future longer training should be chunked around checkpoints while preserving a single W&B run ID for one experiment.
