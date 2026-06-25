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
- peft
- lora
datasets:
- local:cree_goal_run_20260624_full_dictionary
widget:
- text: "Translate 'a good man' to Cree, preserving the 1865 orthography. Return only the answer."
- text: "Give the English meaning of the Cree word Pāsooch. Return only the answer."
---

<div align="center">

# Cree1865

**A 1200-step GRPO/Tinker bootstrap run from Rev. E. A. Watkins' 1865 Cree dictionary.**

<img src="https://img.shields.io/badge/Base-Qwen3.5--4B-1a2a6c?style=flat-square">
<img src="https://img.shields.io/badge/Method-GRPO-000000?style=flat-square">
<img src="https://img.shields.io/badge/Infra-Thinking%20Machines%20Tinker-b21f1f?style=flat-square">
<img src="https://img.shields.io/badge/Language-crk%20%2B%20en-fdbb2d?style=flat-square">
<img src="https://img.shields.io/badge/Status-1200%20steps%20complete-2e7d32?style=flat-square">
<img src="https://img.shields.io/badge/Lineage-Dakota1890%20to%20Cree1865-555?style=flat-square">

</div>

## Overview

Cree1865 is a research bootstrap artifact built from a single public-domain source: Rev. E. A. Watkins' 1865 _A Dictionary of the Cree Language_. The repo replays the Dakota1890 extraction-to-RL pipeline on Cree, producing structured dictionary entries, SFT/Q&A pairs, and deterministic reward-ledger RL tasks.

This is not a Cree language authority, a production translator, or a substitute for community review. It is a transparent technical starting point for inspection and correction.

## Source And Dataset

| Field | Value |
|---|---:|
| Source | Watkins 1865, _A Dictionary of the Cree Language_ |
| Internet Archive ID | `cihm_41985` |
| Extracted page JSON files | 463 |
| Raw entries | 19,607 |
| Deduplicated usable entries | 19,560 |
| Rejected incomplete entries | 125 |
| Multi-variant entries | 4,049 |
| SFT train / validation | 18,463 / 972 |
| RL task records | 38,870 |
| Plain Q&A records | 38,870 |
| English-to-Cree RL tasks | 19,435 |
| Cree-to-English RL tasks | 19,435 |

The local dataset root is `data/cree_goal_run_20260624_full_dictionary/`. Generated data is ignored by git; the extraction and dataset-building code is tracked in the repository.

## Training Run

| Field | Value |
|---|---|
| Base model | `Qwen/Qwen3.5-4B` |
| Renderer | `qwen3_5_disable_thinking` |
| Method | GRPO with deterministic reward ledger |
| Steps | `1200` |
| Batch size / group size | `2 / 2` |
| Max sampled tokens | `64` |
| W&B project | `cree1865-tinker` |
| W&B run | [`kjn02ee4`](https://wandb.ai/christian-cooper-us/cree1865-tinker/runs/kjn02ee4) |
| Final reward | `0.21` |
| Deduped mean reward | `0.18260238803447346` |
| Final parse success | `1.0` |
| Deduped mean parse success | `0.99875` |
| Final Tinker weights | `tinker://bf25e2aa-6b3a-557c-8133-fadf5ebcba8f:train:0/weights/final` |
| Final sampler weights | `tinker://bf25e2aa-6b3a-557c-8133-fadf5ebcba8f:train:0/sampler_weights/final` |

The first Tinker session stalled at local step 868 with `No progress made in 7200s`. It was resumed under the same W&B run ID, `kjn02ee4`, from checkpoint `000800`. The raw local ledger therefore has 1269 rows: 1200 unique training steps plus 69 replay rows from steps 800-868. The deduped ledger keeps the last row per step for steps 0-1199.

## Reward Ledger

Tracked ledgers:

- Raw: `wandb_analysis/cree_reward_ledger_tinker_full_dictionary_1200step_20260624_qwen35_4b_no_think.csv`
- Deduped: `wandb_analysis/cree_reward_ledger_tinker_full_dictionary_1200step_20260624_qwen35_4b_no_think_deduped.csv`

Reward channels include exact match, character overlap, pattern match, an affix/default channel, length penalty, difficulty multiplier, and parse success. The verifier is deterministic; there is no LLM judge in the reward path.

## Usage

The final Tinker checkpoint is recorded above. Once an adapter is published, it should load with PEFT on top of `Qwen/Qwen3.5-4B`.

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

base_model_name = "Qwen/Qwen3.5-4B"
adapter_name = "HarleyCooper/Cree1865"  # replace with the published adapter id

model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    device_map="auto",
    torch_dtype="auto",
    trust_remote_code=True,
)
tokenizer = AutoTokenizer.from_pretrained(base_model_name)
model = PeftModel.from_pretrained(model, adapter_name)

messages = [
    {"role": "system", "content": "You are a Cree language assistant. Return only the answer."},
    {"role": "user", "content": "Translate 'a good man' to Cree, preserving the 1865 orthography."},
]
text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=64, do_sample=False)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## Limitations

- The source is a missionary-era 1865 dictionary with historical orthography and colonial-era framing.
- The extraction may preserve source errors, scan artifacts, and model extraction mistakes.
- The current task set is primarily direct dictionary lookup Q&A, not conversational Cree competence.
- Long reverse-section English glosses should be reviewed or filtered before larger runs.
- Cree language work should be reviewed with appropriate community and linguistic expertise.

## Citation

Watkins, E. A. (1865). _A Dictionary of the Cree Language, as Spoken by the Indians of the Hudson's Bay Territories._ London: Society for Promoting Christian Knowledge. Internet Archive: `cihm_41985`.

```bibtex
@misc{cree1865_model,
  title  = {Cree1865: A GRPO Cree Language Adapter from a Single 1865 Dictionary},
  author = {Cooper, Christian Harley},
  year   = {2026},
  note   = {Base: Qwen/Qwen3.5-4B. Source: Watkins 1865, IA cihm_41985.
            Method derived from Dakota1890.}
}
```
