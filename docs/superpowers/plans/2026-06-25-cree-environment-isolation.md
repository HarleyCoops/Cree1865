# Cree Environment Isolation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Cree-specific Prime Intellect/verifiers environment in Cree1865 and wire Cree Tinker integration to the Cree rubric instead of Dakota runtime classes.

**Architecture:** Add a self-contained `cree1865_dictionary_qa` environment package under `environments/cree1865_dictionary_qa`, modeled on `adaption_dakota_qa` but with Cree dictionary lookup scoring. Add a small adapter in `dakota_rl_training/tinker_integration` so existing Tinker training code can import Cree rubric/default prompt without touching Dakota classes.

**Tech Stack:** Python, `datasets`, `verifiers`, root `pytest`, existing Tinker integration.

## Global Constraints

- Cree-specific runtime behavior belongs under Cree1865.
- Cree runtime code must not import Dakota language/rubric classes.
- Dakota-specific runtime behavior remains in Dakota1890.
- Empty `required_affixes` must never award free reward.
- Dataset preparation must shuffle before applying `max_examples`.
- Use TDD: write failing tests before production code.

---

### Task 1: Cree Environment Package

**Files:**
- Create: `environments/cree1865_dictionary_qa/pyproject.toml`
- Create: `environments/cree1865_dictionary_qa/README.md`
- Create: `environments/cree1865_dictionary_qa/cree1865_dictionary_qa/__init__.py`
- Create: `environments/cree1865_dictionary_qa/cree1865_dictionary_qa/environment.py`
- Create: `environments/cree1865_dictionary_qa/configs/rl/cree-smoke.toml`
- Test: `tests/test_cree1865_environment.py`

**Interfaces:**
- Produces: `cree1865_dictionary_qa.environment.CreeDictionaryRubric`
- Produces: `cree1865_dictionary_qa.environment.build_dataset(dataset_path=None, max_examples=-1, eval_fraction=0.1, eval_examples=128, seed=42, shuffle=True) -> datasets.Dataset`
- Produces: `cree1865_dictionary_qa.environment.load_environment(...) -> vf.Environment`

- [ ] **Step 1: Write failing package tests**

```python
def test_cree_rubric_scores_exact_answer_above_bad_answer() -> None:
    rubric = CreeDictionaryRubric()
    good = [{"role": "assistant", "content": "Wapi-nao"}]
    bad = [{"role": "assistant", "content": "I do not know."}]
    good_score = asyncio.run(_score_total(rubric, good, "Wapi-nao", {"special_chars": []}))
    bad_score = asyncio.run(_score_total(rubric, bad, "Wapi-nao", {"special_chars": []}))
    assert good_score > bad_score
```

- [ ] **Step 2: Run failing package tests**

Run: `python -m pytest tests/test_cree1865_environment.py -q`
Expected: FAIL because `cree1865_dictionary_qa` does not exist.

- [ ] **Step 3: Implement package and rubric**

Create a Prime/verifiers single-turn environment with normalization helpers, dataset loading, shuffle-before-cap, and `CreeDictionaryRubric` channels: exact, containment, orthography, char F1, length.

- [ ] **Step 4: Run package tests**

Run: `python -m pytest tests/test_cree1865_environment.py -q`
Expected: PASS.

### Task 2: Tinker Cree Adapter

**Files:**
- Create: `dakota_rl_training/tinker_integration/cree.py`
- Modify: `dakota_rl_training/tinker_integration/__init__.py`
- Modify: `dakota_rl_training/tinker_integration/env.py`
- Test: `tests/test_cree1865_environment.py`

**Interfaces:**
- Consumes: `CreeDictionaryRubric` and `DEFAULT_SYSTEM_PROMPT`
- Produces: `dakota_rl_training.tinker_integration.cree.CreeTinkerRubric`
- Produces: `dakota_rl_training.tinker_integration.env.DakotaTinkerEnv(..., rubric_factory=None)` where `rubric_factory` defaults to Dakota only for legacy runs.

- [ ] **Step 1: Write failing Tinker adapter test**

```python
def test_tinker_cree_adapter_uses_cree_rubric_not_dakota() -> None:
    from dakota_rl_training.tinker_integration.cree import create_cree_rubric
    rubric = create_cree_rubric()
    assert rubric.__class__.__name__ == "CreeDictionaryRubric"
```

- [ ] **Step 2: Run failing adapter test**

Run: `python -m pytest tests/test_cree1865_environment.py::test_tinker_cree_adapter_uses_cree_rubric_not_dakota -q`
Expected: FAIL because the adapter does not exist.

- [ ] **Step 3: Implement adapter and env injection**

Add `cree.py` and allow `DakotaTinkerEnv` to receive a rubric factory. Keep the legacy default unchanged for Dakota paths.

- [ ] **Step 4: Run adapter tests**

Run: `python -m pytest tests/test_cree1865_environment.py -q`
Expected: PASS.

### Task 3: Verification

**Files:**
- Modify only files from Tasks 1 and 2 unless tests expose a scoped issue.

**Interfaces:**
- Consumes all package and adapter interfaces.
- Produces a verified Cree environment package and tests.

- [ ] **Step 1: Run focused tests**

Run: `python -m pytest tests/test_cree1865_environment.py tests/test_cree_bootstrap.py tests/test_tinker_observability.py -q`
Expected: all selected tests pass.

- [ ] **Step 2: Run lint on changed Python files**

Run: `python -m ruff check environments/cree1865_dictionary_qa dakota_rl_training/tinker_integration/cree.py dakota_rl_training/tinker_integration/env.py tests/test_cree1865_environment.py`
Expected: no ruff errors.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/plans/2026-06-25-cree-environment-isolation.md environments/cree1865_dictionary_qa dakota_rl_training/tinker_integration tests/test_cree1865_environment.py
git commit -m "feat: add Cree dictionary RL environment"
```
