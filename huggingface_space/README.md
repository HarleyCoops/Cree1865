---
title: Cree1865 Tinker Endpoint
colorFrom: green
colorTo: gray
sdk: gradio
python_version: "3.12"
sdk_version: "5.28.0"
app_file: app.py
pinned: false
license: apache-2.0
base_model: Qwen/Qwen3-30B-A3B-Instruct-2507
tags:
  - cree
  - nlp
  - reinforcement-learning
  - grpo
  - lora
  - tinker
  - low-resource-language
language:
  - en
  - cr
pipeline_tag: text-generation
---

# Cree1865 Tinker Endpoint

This Space is a thin Gradio client for the final Cree1865 remote Tinker sampler:

`tinker://c71aadd1-8e48-51b0-b890-149a2889b4fa:train:0/sampler_weights/final`

It does not host the 30B model weights inside the Space. The UI sends prompts to
Thinking Machines/Tinker and displays the returned samples plus request metadata.

## Required Secret

Set this Hugging Face Space secret before running the app:

- `TINKER_API_KEY`

The key is read from the environment by the Tinker SDK. It is never committed to
the repository or shown in the interface.

## Research Status

This is an experimental 800-step endpoint trained with the Cree-specific rubric
and synthetic dictionary tasks. It is useful for inspection and prompt testing,
but it should not be treated as a validated fluent Cree model. Prior qualitative
checks showed repetition/collapse risk, especially on English-to-Cree generation.

## Suggested Prompts

- `Translate the Cree word maskihkiy into English.`
- `Give the Cree dictionary headword for 'medicine'. Return only the Cree form.`
- `Translate 'I speak Cree' into Cree. Return only the answer.`
- `What does the Cree suffix -win usually mark in dictionary entries?`

## Local Run

```bash
pip install -r requirements.txt
export TINKER_API_KEY=...
python app.py
```

On Windows PowerShell:

```powershell
$env:TINKER_API_KEY = "..."
python app.py
```
