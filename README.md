# Cree1865: A Dakota1890-Derived Grammar-to-RL Bootstrap Repo

This repository is a private bootstrap of the proven `Dakota1890` core pipeline, retargeted to a new historical source:

- [CreeDictionary.pdf](C:/Users/chris/Cree1865/CreeDictionary.pdf)

The goal is not to invent a second pipeline. The goal is to run the same chain again on a different origin document, learn where the schema and extraction assumptions break, and turn those breakpoints into the generalized template for future communities starting from scratch.

## Current Intent

This repo is the first-pass template for processing the Cree dictionary in the same way the recent Dakota1890 dictionary was processed:

1. source document ingestion
2. VLM-assisted page extraction
3. structured dictionary schema design
4. synthetic SFT dataset generation
5. grammar-task conversion for RL
6. remote RL training
7. Hugging Face publication and hosted inference

## Source Notes

This volume is not a clean one-to-one match with the Dakota source:

- the preface and basic grammar run only through page `24`
- the dictionary begins after page `24`
- there is at least one missing companion volume that still needs to be found

That means page-count exploration is part of the work, not a distraction from it. The extraction boundaries and schema will likely need to shift once the second volume is located and the dictionary structure is better understood.

See [SOURCE_NOTES.md](C:/Users/chris/Cree1865/SOURCE_NOTES.md).

## What Was Copied In

This repo carries the Dakota core as a starting template:

- `dakota_extraction/`
- `dakota_rl_training/`
- `environments/`
- `scripts/`
- `tests/`
- Hugging Face publication and inference surfaces
- OpenAI SFT baseline path

The names are still Dakota-flavored in many modules. That is intentional for the bootstrap phase. We are preserving the known-good control surface first, then generalizing names and schemas only where the Cree document forces the change.

## Immediate Next Steps

1. inspect `CreeDictionary.pdf` and confirm the exact page boundaries for grammar vs dictionary extraction
2. locate the second volume and record its bibliographic/source provenance
3. adapt the extraction prompt and JSON schema to the Cree dictionary structure
4. rerun the Dakota-style extraction pipeline on a small Cree page slice
5. preserve the full publication path: git -> W&B -> Tinker/remote RL -> Hugging Face

## Operator Docs

- [PIPELINE.md](C:/Users/chris/Cree1865/PIPELINE.md)
- [SETUP.md](C:/Users/chris/Cree1865/SETUP.md)
- [SOURCE_NOTES.md](C:/Users/chris/Cree1865/SOURCE_NOTES.md)
