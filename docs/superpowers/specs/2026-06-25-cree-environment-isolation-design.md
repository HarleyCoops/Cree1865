# Cree Environment Isolation Design

Date: 2026-06-25

## Goal

Build a Cree-specific Prime Intellect/verifiers environment in the Cree1865 repository and stop routing Cree training through Dakota-specific environment or rubric classes.

Dakota1890 remains the reference implementation for Dakota environments. Cree1865 may copy proven structure from Dakota1890, but Cree runtime code must not import Dakota language/rubric classes.

## Current Problem

The Cree Tinker run used `dakota_rl_training/tinker_integration/env.py`, which imports `DakotaGrammarRubric` and `DEFAULT_SYSTEM_PROMPT` from `dakota_grammar_translation.environment`. That means the Cree run inherited Dakota reward semantics:

- Dakota prompt defaults unless manually overridden.
- Dakota exact/character/pattern/affix/length channel names.
- Free `affix_raw = 1.0` reward whenever Cree tasks have no required affixes.
- Dakota-named package boundaries in Prime/verifiers integration.

This made the run a pipeline proof, not a valid Cree environment experiment.

## Boundary Rule

All Cree-specific runtime behavior belongs under Cree1865:

- `environments/cree1865_dictionary_qa/`
- `environments/cree1865_dictionary_qa/cree1865_dictionary_qa/environment.py`
- `environments/cree1865_dictionary_qa/configs/rl/*.toml`
- `tests/test_cree1865_environment.py`

Dakota-specific runtime behavior belongs under Dakota1890:

- `environments/adaption_dakota_qa/`
- `environments/dakota_grammar_translation/`
- Dakota rubric classes and Dakota prompt defaults.

Cree1865 may keep historical Dakota-derived filenames temporarily only when they are neutral wrappers. Any Cree training path must import Cree environment/rubric classes.

## Cree Environment Package

Create a new package named `cree1865_dictionary_qa` modeled on the Prime/verifiers pattern used by `adaption_dakota_qa`.

The package exposes:

- `load_environment(...)`
- `build_dataset(...)`
- `CreeDictionaryRubric`
- `DEFAULT_SYSTEM_PROMPT`

The environment is a single-turn chat environment for Watkins 1865 dictionary lookup tasks.

Default system prompt:

```text
You are a careful Cree language assistant working from Watkins' 1865 Cree dictionary. Answer the user's question directly and concisely. Preserve Cree orthography exactly, including macrons, acutes, circumflexes, hyphens, and apostrophes. Do not invent unsupported forms.
```

## Dataset Inputs

Primary local dataset:

```text
data/cree_goal_run_20260624_full_dictionary/training_datasets/rl_tasks_all.jsonl
```

Accepted fields:

- `id` or `task_id`
- `question` or `prompt`
- `answer`
- `task_type`
- `difficulty`
- `info`
- `metadata`

Dataset preparation must shuffle before applying `max_examples`, so a capped diagnostic run samples from the whole dictionary instead of the first page range.

The prepared dataset records should include:

- `id`
- `question`
- `answer`
- `task`
- `info`

The `info` payload should retain:

- `task_type`
- `difficulty`
- `verification_pattern`
- `hints`
- `special_chars`
- `orthography_chars`
- `direction`
- `entry_id`
- `page`
- related variants if present.

## Cree Rubric

`CreeDictionaryRubric` should be deterministic and continuous so GRPO has useful within-group reward variance.

Initial weighted channels:

- `exact_reward` at 0.20: normalized exact match.
- `target_containment_reward` at 0.25: expected form/gloss appears in the completion after Cree-aware normalization.
- `orthography_reward` at 0.20: expected Cree diacritics and punctuation are preserved when the target answer contains them.
- `char_f1_reward` at 0.20: character-level F1 against the answer using Cree-aware compaction.
- `length_reward` at 0.15: rewards concise answers close to the target length.

No affix channel should exist in the Cree dictionary rubric. Empty `required_affixes` must never award free reward.

Future channels can add variant matching and direction-specific scoring after the first verified environment passes.

## Tinker Integration

After the Prime/verifiers environment exists, update the Cree Tinker path to import from `cree1865_dictionary_qa.environment` or an explicit Cree adapter module.

The Tinker config for Cree should use the Cree package defaults unless a run explicitly overrides them:

- Cree system prompt.
- Cree rubric.
- Shuffle-before-cap dataset selection.
- Nonzero eval split for diagnostics.

The old Dakota integration can remain for Dakota runs, but Cree launch scripts must not import `DakotaGrammarRubric`.

## Training Defaults

For the next Cree diagnostic run, use a rollout budget comparable enough to measure signal:

- `batch_size`: 64 or 128.
- `rollouts_per_example` / `group_size`: 8 for dense Cree rubric, 16 if reward is still sparse.
- `max_steps`: 100 to 300 for diagnostics before longer runs.
- `lora_rank`: 32 unless there is a concrete memory reason to lower it.
- `eval_fraction`: 0.1.
- `eval_examples`: 128 or 256.

Do not compare runs by step count alone. Compare approximate sampled completions:

```text
max_steps * batch_size * rollouts_per_example
```

## Tests

Add tests before implementation changes:

- Dataset builder loads Cree records and preserves `question`, `answer`, `task_type`, and metadata.
- `max_examples` samples after shuffle, not before shuffle.
- Exact answer scores higher than an unrelated answer.
- Missing/empty affix metadata gives no free reward channel because the Cree rubric has no affix reward.
- `load_environment(...)` returns train and eval datasets when `eval_fraction > 0`.
- Tinker Cree adapter imports Cree rubric, not `DakotaGrammarRubric`.

## Migration Notes

This change does not delete Dakota reference code from Dakota1890.

In Cree1865, Dakota-named modules can be cleaned gradually after the Cree environment is working. The immediate blocker is runtime behavior, so the first implementation should focus on the new environment package, tests, and Cree training import path.
