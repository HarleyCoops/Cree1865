---
language:
- crk
- en
license: apache-2.0
library_name: peft
pipeline_tag: text-generation
base_model: Qwen/Qwen3.6-35B-A3B
tags:
- cree
- nehiyawewin
- indigenous-languages
- low-resource-language
- dictionary
- grammar
- reinforcement-learning
- grpo
- tinker
- thinking-machines
- peft
- lora
datasets:
- HarleyCooper/cree1865-english-cree-qa
widget:
- text: "Translate 'a good man' to Cree, preserving the 1865 orthography. Return only the answer."
- text: "Give the Cree for 'abandon' from Watkins 1865. Return only the answer."
---

<!-- ╔══════════════════════════════════════════════════════════════════╗
     ║  HUGGING FACE MODEL CARD · Cree1865                               ║
     ║  Forward-looking showcase. Confirmed facts are live; values that  ║
     ║  exist only after training are marked  «PENDING FINAL RUN».       ║
     ║  Upload referenced images to the repo's /assets folder.           ║
     ╚══════════════════════════════════════════════════════════════════╝ -->

<div align="center">

<img src="./assets/cree_dictionary_hero_banner.png" alt="Cree1865 — one 1865 source book, two dictionary worlds" width="100%">

<h1>Cree1865 · Qwen3.6-35B-A3B-GRPO</h1>

<b>A reinforcement-learning fine-tune that read an 1865 Cree dictionary cover to cover.</b>

<br><br>

<img src="https://img.shields.io/badge/Base-Qwen3.6--35B--A3B-1a2a6c?style=flat-square">
<img src="https://img.shields.io/badge/Adapter-LoRA%20r32-7b1fa2?style=flat-square">
<img src="https://img.shields.io/badge/Method-GRPO-000000?style=flat-square">
<img src="https://img.shields.io/badge/Infra-Thinking%20Machines%20Tinker-b21f1f?style=flat-square">
<img src="https://img.shields.io/badge/Language-crk%20%C2%B7%20en-fdbb2d?style=flat-square">
<img src="https://img.shields.io/badge/License-Apache%202.0-2e7d32?style=flat-square">
<br>
<img src="https://img.shields.io/badge/Status-Extraction%20complete%20%C2%B7%20RL%20pending-orange?style=flat-square">
<img src="https://img.shields.io/badge/Lineage-Dakota1890%E2%86%92Cree1865-555?style=flat-square">

</div>

---

## Overview

This adapter is a **GRPO reinforcement-learning fine-tune** of `Qwen/Qwen3.6-35B-A3B`, optimized for **Cree (nēhiyawēwin) grammar, orthography, and translation** drawn from a single historical source: **Rev. E. A. Watkins' 1865 _A Dictionary of the Cree Language_**.

It is built with the proven **Dakota1890** pipeline, retargeted to Cree. The training environment is a **custom deterministic verifier** that turns dictionary entries into machine-checkable tasks and rewards short, correct, orthographically faithful Cree.

> **Scope, honestly stated.** This is an experimental research artifact, not a Cree language authority or a substitute for community expertise. It is the *first attempt* that contemporary Cree speakers are meant to correct — the community-in-the-loop second stage borrowed from the StoneyNakoda project.

---

## Model Details

| Field | Value |
|---|---|
| Base model | `Qwen/Qwen3.6-35B-A3B` |
| Adapter | LoRA, rank 32 (PEFT) |
| Method | GRPO (Group Relative Policy Optimization) |
| Verifier | Cree grammar/orthography rubric (deterministic, no LLM judge) |
| Infrastructure | Thinking Machines Tinker |
| Languages | Cree `crk`, English `en` |
| Source | Watkins 1865 — Internet Archive `cihm_41985` |
| License | Apache-2.0 (code) · Public Domain (1865 text) |

---

## Training Data & Methodology

Everything derives from **one public-domain book** — a bilingual, two-part 1865 dictionary:

<div align="center">
<img src="./assets/cree_dictionary_storyboard.png" alt="1865 original to 1938 revised companion" width="100%">
</div>

| Part | Direction | PDF pages | State |
|------|-----------|:---------:|-------|
| Front matter | pronunciation key + grammar notes | 1–28 | reference |
| **Part I** | **English → Cree** | 29–210 | extracted |
| **Part II** | **Cree → English** | 212–end | schema pending |

**Confirmed extraction (Part I · English → Cree):**

<div align="center">

| Pages | Entries | Avg confidence | Multi-variant | Rejected (QA gate) |
|:-----:|:-------:|:--------------:|:-------------:|:------------------:|
| **184** | **6,110** | **0.915** | **3,563** | **67** |

</div>

These structured entries become two downstream tracks: a **synthetic SFT dataset** of bilingual QA pairs, and a set of **verifiable RL tasks** (translation, reverse translation, morphology, orthography recall). Full-corpus dataset totals are **«PENDING FINAL RUN»** once the Part II Cree-headword schema lands.

<details>
<summary><b>Example extracted entry</b></summary>

```json
{
  "english_headword": "A",
  "part_of_speech": "art. indef.",
  "cree_variants": ["pātah minékwakunis", "ā meyosit napāo", "pāyuk"],
  "example_pairs": [
    {"english": "a good man", "cree": "ā meyosit napāo"}
  ],
  "usage_notes": "Usually not expressed in Cree; sometimes the numeral pāyuk ('one') is used.",
  "confidence": 0.95
}
```
</details>

---

## Reward Function

A **composite, deterministic** reward — every component is checkable by code, so the gradient is honest:

| Component | Weight | Verifies |
|---|:--:|---|
| **Orthography recall** | 40% | Macron/accent characters preserved (`ā ē ī ō ū`, `á é í ó ú`) |
| **Affix accuracy** | 40% | Cree morphology — correct prefixes/suffixes (`-num`, `-tum`, derivations) |
| **Semantic match** | 20% | Meaning vs. the 1865 gloss / ground truth |
| **Difficulty multiplier** | ×1.0–2.0 | Curriculum weighting after the component sum |

The verifier logs raw component values, weighted contributions, the reconstructed composite, and a `composite_diff` for full auditability.

---

## Performance

> **«PENDING FINAL RUN».** Final composite reward, orthography/affix accuracy, token efficiency, and W&B dashboards will appear here once the Cree GRPO run completes.

For precedent, the **same pipeline on Dakota** (Dakota1890) reached **100% affix accuracy**, strong character preservation, and a measurable composite-reward lift on its 30B/35B GRPO runs. Cree targets inherit that template.

<div align="center">
<img src="./assets/cree1865_structure_proof.png" alt="Source structure proof" width="90%">
<br><em>The two-part source structure that grounds the task design.</em>
</div>

---

## Usage

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

base_model_name = "Qwen/Qwen3.6-35B-A3B"
adapter_name    = "HarleyCooper/Cree1865-35B-A3B-GRPO"  # «pending publication»

model = AutoModelForCausalLM.from_pretrained(
    base_model_name, device_map="auto", torch_dtype="auto", trust_remote_code=True,
)
tokenizer = AutoTokenizer.from_pretrained(base_model_name)
model = PeftModel.from_pretrained(model, adapter_name)

messages = [
    {"role": "system", "content": "You are a Cree language assistant. Return only the answer."},
    {"role": "user",   "content": "Translate 'a good man' to Cree, preserving the 1865 orthography."},
]
text   = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=64, do_sample=False)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

---

## Limitations & Ethical Notes

The source is a **missionary-era dictionary published in 1865**. It reflects the orthography, analysis, and **colonial-era framing** of its time, recorded across the Hudson's Bay territories. Outputs can inherit mistakes, omissions, and outdated descriptions from both the source extraction and the base model.

- This is **not** a Cree language authority, a fluent-speaker replacement, or a production translation system.
- Cree language work should be reviewed with **appropriate community and linguistic expertise**.
- The model is designed to be **corrected**: it is the working endpoint for a community-in-the-loop stage, not a finished teacher.
- Nēhiyawēwin belongs to its communities. Treat this repository as a transparent technical artifact built *in service of* that work, not over it.

---

## Citation

> **Watkins, E. A. (1865).** *A Dictionary of the Cree Language, as Spoken by the Indians of the Hudson's Bay Territories.* London: Society for Promoting Christian Knowledge. Internet Archive: `cihm_41985`.

```bibtex
@misc{cree1865_model,
  title  = {Cree1865: A GRPO Cree Language Adapter from a Single 1865 Dictionary},
  author = {Cooper, Christian Harley},
  year   = {2026},
  note   = {Base: Qwen/Qwen3.6-35B-A3B. Source: Watkins 1865 (IA cihm_41985).
            Method derived from Dakota1890.}
}
```

**Infrastructure & lineage:** Thinking Machines Tinker (RL), PrimeIntellect (RL), Anthropic (VLM extraction), and the [Dakota1890](https://github.com/HarleyCoops/Dakota1890) pipeline this work replays.
