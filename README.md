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

This source is not a clean one-to-one match with the Dakota source:

- the front matter, pronunciation key, and early grammar notes run through PDF page `28`
- `Part I. English-Cree` begins at PDF page `29`
- the `Part II. Cree-English` transition sits around printed page `183`, which lands at PDF page `211` in the local scan
- the first full `Part II. Cree-English` entry page is printed page `184`, which lands at PDF page `212`
- the title page explicitly identifies the book as a two-part dictionary inside a single volume
- a fuller archive master scan now lives at [sources/CreeDictionary_1865_cihm_41985_complete.pdf](C:/Users/chris/Cree1865/sources/CreeDictionary_1865_cihm_41985_complete.pdf)
- a later revised companion now lives at [sources/CreeDictionary_1938_companion.pdf](C:/Users/chris/Cree1865/sources/CreeDictionary_1938_companion.pdf)

That means the real engineering task is not hunting a missing second volume. It is handling one historical book with two extraction surfaces: `English -> Cree` and `Cree -> English`.

The archival story now has two anchors:

- the 1865 original on Internet Archive as `cihm_41985`
- the 1938 revised companion on Internet Archive as `dictionaryofcree0000reve`

Current pipeline state:

- the automated structured extraction path now supports both `Part I. English-Cree` and `Part II. Cree-English`
- reverse-section pages are normalized into the same downstream fields: `cree_primary` remains Cree and `english_headword` remains the English gloss
- the full local 1865 dictionary run produced 463 page JSON files, 19,560 deduplicated usable entries, and balanced English->Cree / Cree->English task exports

See [SOURCE_NOTES.md](C:/Users/chris/Cree1865/SOURCE_NOTES.md).
See also the visual/source package in [docs/source_dossier/CREE1865_SOURCE_DOSSIER.md](C:/Users/chris/Cree1865/docs/source_dossier/CREE1865_SOURCE_DOSSIER.md).
The fastest visual entrypoint is [cree_dictionary_hero_banner.png](C:/Users/chris/Cree1865/docs/source_dossier/cree_dictionary_hero_banner.png).

## Source Story

This book is not just a vocabulary dump. It is a bilingual bridge object from 1865: front matter, a pronunciation key, `Part I. English-Cree`, and `Part II. Cree-English` in one historical volume. That matters culturally because it preserves translation work, orthographic compromise, and lexical contact under missionary print conditions across the Hudson's Bay territories. It also matters technically because those same structures give the pipeline enough shape to bootstrap extraction, SFT datasets, and RL tasks from a single archival source.

The Internet Archive companion story is now also explicit in-repo. The later item `dictionaryofcree0000reve` is identifiable, its metadata and preview surfaces are downloadable, and its full borrow path is auth-gated rather than missing. The clearest visuals are:

- [cree_dictionary_hero_banner.png](C:/Users/chris/Cree1865/docs/source_dossier/cree_dictionary_hero_banner.png)
- [cree_dictionary_storyboard.png](C:/Users/chris/Cree1865/docs/source_dossier/cree_dictionary_storyboard.png)
- [cree_second_volume_ia_access_story.png](C:/Users/chris/Cree1865/docs/source_dossier/cree_second_volume_ia_access_story.png)

The exact blocker state is also preserved in machine-readable form:

- [dictionaryofcree0000reve_authentication_document.json](C:/Users/chris/Cree1865/docs/source_dossier/internet_archive/dictionaryofcree0000reve_authentication_document.json)
- [dictionaryofcree0000reve_browse_probe.json](C:/Users/chris/Cree1865/docs/source_dossier/internet_archive/dictionaryofcree0000reve_browse_probe.json)

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

## Full-Corpus Dataset Snapshot

Latest local full-dictionary build:

- extraction root: `data/cree_goal_run_20260624_full_dictionary`
- extracted dictionary JSON pages: `463`
- raw entries: `19,607`
- deduplicated usable entries: `19,560`
- rejected incomplete entries: `125`
- multi-variant entries: `4,049`
- RL task records: `38,870`
- plain Q&A records: `38,870`
- SFT split: `18,463` train / `972` validation
- RL directions: `19,435` English->Cree and `19,435` Cree->English

The generated `data/` artifacts are intentionally ignored by git; the code and docs describe how to regenerate them from the local extraction JSON.

## Immediate Next Steps

1. run the 1200-step small-model Tinker pass on the audited full-dictionary RL tasks
2. inspect reward ledgers for orthography and exact-answer behavior before scaling batch size or model size
3. publish the selected checkpoint/model card once a non-smoke run is complete
4. keep the community-review framing explicit: this is a transparent bootstrap artifact, not a language authority

## Bootstrap Validation

The first offline end-to-end Cree validation path now exists:

```bash
python scripts/cree/validate_cree_bootstrap.py
```

That command validates:

1. source PDF page-count assumptions
2. PDF -> page image rendering
3. Cree sample extraction schema
4. SFT dataset materialization
5. RL task generation

The live extraction runner supports forward, reverse, and grammar page slices:

```bash
python scripts/cree/run_cree_pipeline.py --dictionary-pages 29 40 100 --reverse-pages 212 220
```

That command reuses the Dakota control surface shape while swapping in Cree-specific page rendering, prompt/schema expectations, and dataset materialization for both dictionary directions.

## Operator Docs

- [PIPELINE.md](C:/Users/chris/Cree1865/PIPELINE.md)
- [SETUP.md](C:/Users/chris/Cree1865/SETUP.md)
- [SOURCE_NOTES.md](C:/Users/chris/Cree1865/SOURCE_NOTES.md)
