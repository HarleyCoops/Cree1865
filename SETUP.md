# Setup

These instructions preserve the working Dakota1890 toolchain while this repo is still being generalized for Cree.

## Python

- Python `3.10+`
- consumer-hardware target for local checks
- Linux-first for long-running remote RL launch paths

## Install

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements_hf_inference.txt
python -m pip install -r requirements-tinker.txt
python -m pip install -e environments/dakota_grammar_translation
```

Important:

- the environment package name is still `dakota_grammar_translation`
- that is a bootstrap choice, not the intended long-term naming

## Environment Variables

Copy `.env.template` to `.env` and fill only the keys you need for the step you are running.

## Minimum Keys By Stage

- extraction: `ANTHROPIC_API_KEY`
- synthetic QA or comparison data generation: `GOOGLE_API_KEY`
- OpenAI SFT baseline: `OPENAI_API_KEY`
- HF publication / endpoint work: `HF_TOKEN`
- W&B telemetry: `WANDB_API_KEY`
- Tinker remote RL / sampler inference: `TINKER_API_KEY`

## First Smoke Goal

Before large-scale Cree extraction, the first success criterion should be small and boring:

1. verify dependency install
2. inspect the Cree PDF boundaries
3. run a tiny page-slice extraction
4. see where the Dakota schema assumptions fail

That failure surface is the real work of this repo.
