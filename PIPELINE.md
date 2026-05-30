# Cree1865 Pipeline Template

This repository starts from the same core chain used in `Dakota1890`, but applies it to a different historical origin document.

## Template Path

```mermaid
flowchart TD
    A["Historical source<br/>CreeDictionary.pdf"] --> B["Page ingest / image conversion<br/>dakota_extraction.tools.image_converter"]
    B --> C["Early grammar extraction<br/>scripts/extraction/extract_grammar_pages.py"]
    B --> D["Dictionary extraction<br/>python -m dakota_extraction.run_extraction"]
    C --> E["Organize grammar rules<br/>scripts/rl/organize_grammar_for_rl.py"]
    E --> F["Generate RL tasks<br/>scripts/conversion/convert_rules_to_primeintellect.py"]
    D --> G["Structured extraction JSONs"]
    G --> H["Synthetic SFT dataset path<br/>OpenAIFineTune + conversion scripts"]
    F --> I["Packaged RL environment<br/>environments/dakota_grammar_translation"]
    I --> J["Local RL checks"]
    I --> K["Remote RL training / Tinker"]
    K --> L["Published adapter + HF inference surfaces"]
```

## Important Constraint

The code surface is still Dakota-derived:

- package names still use `dakota_*`
- the packaged environment is still `dakota_grammar_translation`
- several scripts still encode Dakota assumptions in prompts and schemas

That is acceptable at bootstrap time. The rule for this repo is:

- preserve the known-good pipeline shape
- generalize only where the Cree source actually requires it

## Cree-Specific Starting Assumptions

- pages `1-24` are likely preface/basic grammar
- pages after `24` are likely dictionary-focused
- a second volume is missing and may affect schema design

## First Adaptation Targets

1. page-boundary verification
2. Cree dictionary entry schema
3. orthography and prompt updates
4. grammar extraction schema for the shorter front matter
5. publication path reuse for the eventual Cree model
