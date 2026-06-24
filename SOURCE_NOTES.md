# Cree 1865 Source Notes

## Current Source

- Local file: [CreeDictionary.pdf](C:/Users/chris/Cree1865/CreeDictionary.pdf)
- Fuller archive master: [CreeDictionary_1865_cihm_41985_complete.pdf](C:/Users/chris/Cree1865/sources/CreeDictionary_1865_cihm_41985_complete.pdf)
- Later revised companion: [CreeDictionary_1938_companion.pdf](C:/Users/chris/Cree1865/sources/CreeDictionary_1938_companion.pdf)

## Known Structure

- Front matter, pronunciation key, and early grammar notes run through PDF page `28`
- `Part I. English-Cree` begins at PDF page `29`
- the `Part II. Cree-English` transition sits around printed page `183`, which lands at PDF page `211` in the local scan
- the first full `Part II. Cree-English` entry page is printed page `184`, which lands at PDF page `212`
- The dictionary entries in `Part I` are arranged as **English headword -> Cree realization**
- The entries in `Part II` reverse direction to **Cree headword -> English gloss**
- The local 492-page PDF already contains both internal parts of the 1865 book
- The recovered 501-page archive master is a fuller scan of the same book, not a separate second volume
- The later 1938 companion is a revised dictionary based on Watkins' 1865 foundation, not volume two of the 1865 edition

## Why This Matters

The Dakota pipeline assumes that:

1. the extraction boundaries can be stated clearly
2. the grammar section can be separated from the dictionary section
3. the downstream schema can be inferred from a stable entry pattern

This Cree source may preserve those assumptions only partially. Before large-scale extraction, we need to verify:

- whether the early grammar pages are enough to seed an RL task schema
- whether dictionary entries are consistent across both internal parts
- whether the Cree orthography and entry layout require prompt or schema upgrades
- whether examples and cross-references are stable enough to generate reverse Cree -> English tasks without manual repair
- how the Cree-headword schema for `Part II` should differ from the current English-headword extraction schema

## Working Rule

Do not over-generalize before the document forces it. Start by replaying the Dakota core on small slices of this source, then promote only the changes that are actually required.

## Archive Anchors

- 1865 Internet Archive identifier: `cihm_41985`
- 1938 companion Internet Archive identifier: `dictionaryofcree0000reve`

The archived metadata for both items is preserved under [docs/source_dossier/internet_archive](C:/Users/chris/Cree1865/docs/source_dossier/internet_archive). The 1938 companion PDF on disk was recovered via a public mirror after the direct Internet Archive `download/` paths returned `401` / `403` in this environment; the probe evidence is preserved in [dictionaryofcree0000reve_access_probe.json](C:/Users/chris/Cree1865/docs/source_dossier/internet_archive/dictionaryofcree0000reve_access_probe.json).

Archive's own OPDS authentication document is also preserved at [dictionaryofcree0000reve_authentication_document.json](C:/Users/chris/Cree1865/docs/source_dossier/internet_archive/dictionaryofcree0000reve_authentication_document.json). That response makes the current state precise: the item is real, the public preview surfaces are real, and the remaining barrier to the official IA full-file borrow/download path is Archive authentication.

There is now a second protocol-level proof file as well: [dictionaryofcree0000reve_browse_probe.json](C:/Users/chris/Cree1865/docs/source_dossier/internet_archive/dictionaryofcree0000reve_browse_probe.json). It records that Archive's anonymous `grant_access` cookie can be obtained, but that `browse_book` and `create_token` still fail without login and that hidden leaves still resolve to the same limited-preview placeholder.

The second-volume visuals worth opening first are:

- [cree_second_volume_ia_access_story.png](C:/Users/chris/Cree1865/docs/source_dossier/cree_second_volume_ia_access_story.png)
- [dictionaryofcree0000reve_cover_large.jpg](C:/Users/chris/Cree1865/docs/source_dossier/internet_archive/thumbs/dictionaryofcree0000reve_cover_large.jpg)
- [dictionaryofcree0000reve_leaf005_ia_preview.png](C:/Users/chris/Cree1865/docs/source_dossier/screens/ia_preview_pages/dictionaryofcree0000reve_leaf005_ia_preview.png)
- [leaf17_grant.jpg](C:/Users/chris/Cree1865/docs/source_dossier/internet_archive/preview_probe/leaf17_grant.jpg)

Archive's reader surfaces were still usable. The repo now also contains:

- the BookReader payload: [dictionaryofcree0000reve_bookreader.jsonp](C:/Users/chris/Cree1865/docs/source_dossier/internet_archive/dictionaryofcree0000reve_bookreader.jsonp)
- the webpub manifest: [dictionaryofcree0000reve_webpub_manifest.json](C:/Users/chris/Cree1865/docs/source_dossier/internet_archive/dictionaryofcree0000reve_webpub_manifest.json)
- directly downloaded IA preview leaves under [ia_preview_pages](C:/Users/chris/Cree1865/docs/source_dossier/screens/ia_preview_pages)
