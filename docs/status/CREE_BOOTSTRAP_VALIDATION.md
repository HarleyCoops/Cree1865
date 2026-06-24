# Cree Bootstrap Validation

## Current Validated Facts

- `CreeDictionary.pdf` resolves locally and contains `492` PDF pages.
- The front matter, pronunciation guidance, and early grammar notes run through PDF page `28`.
- The first confirmed dictionary page is PDF page `29`.
- The reverse-section transition sits around printed page `183`, which lands at PDF page `211` in the local scan.
- The first full Cree-English entry page is printed page `184`, which lands at PDF page `212`.
- The current structured extraction path is visually validated for **English -> Cree** pages in a two-column layout.

## Implemented Validation Surface

### Offline bootstrap

```bash
python scripts/cree/validate_cree_bootstrap.py
```

This validates:

1. PDF page-count assumptions
2. PDF -> rendered image conversion
3. Part I Cree sample extraction JSON shape
4. SFT dataset materialization
5. RL task generation in both directions from Part I structured entries:
   - `english_to_cree`
   - `cree_to_english`

### Live page runner

```bash
python scripts/cree/run_cree_pipeline.py --dictionary-pages 29 40 100
```

This replays the Dakota control-surface shape on Cree for `Part I. English-Cree`:

1. render selected grammar and dictionary pages from the PDF
2. optionally call Anthropic on dictionary pages using the Cree prompt
3. build Cree SFT and RL artifacts from the extracted JSON
4. emit a compact pipeline report under `data/cree_pipeline/`

## New Cree-Specific Surfaces

- `dakota_extraction/core/cree_extraction_prompt.py`
- `dakota_extraction/core/cree_grammar_extraction_prompt.py`
- `dakota_extraction/schemas/cree_dictionary_schema.py`
- `dakota_extraction/datasets/cree_training_dataset_builder.py`
- `dakota_extraction/datasets/cree_task_generator.py`
- `dakota_extraction/profiles/cree1865.py`
- `dakota_extraction/tools/pdf_ingest.py`

## Remaining Blockers

- `Part II. Cree-English` still needs a Cree-headword structured extraction schema and live validation pass.
- Grammar extraction is prepared at the prompt level, but still needs a Cree-native structured rule surface and live API pass.
- The copied package names remain Dakota-flavored by design; renaming is not the priority until the Cree extraction surface stabilizes.
