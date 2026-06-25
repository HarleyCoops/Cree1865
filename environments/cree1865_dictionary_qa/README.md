# Cree1865 Dictionary QA Environment

Prime Intellect / Verifiers single-turn RL environment for Watkins 1865 Cree dictionary lookup tasks.

This environment is Cree-specific. It does not import Dakota runtime classes or Dakota reward functions.

The reward is deterministic and continuous: exact match, target containment, Cree orthography preservation, character F1, and concise answer length. There is no affix reward channel.

## Local Smoke

```bash
uv pip install -e .
uv run vf-eval cree1865_dictionary_qa -n 5 -r 1
```

## Hosted Training Starter

```bash
prime train configs/rl/cree-smoke.toml --plain -y
```
