# Cree 1865 Source Notes

## Governance, Authority, and Limits (read first)

This work is built on a 19th-century missionary dictionary of a living
Indigenous language. The technical pipeline is the easy part. The harder and
more important constraints are stated up front here so the rest of the document
is read in their light.

### What this is, and what it is not

This project is **not an attempt to extract value from Cree for the builder's
benefit.** The working hypothesis is the opposite of extraction: that a
structured historical source contains a *discoverable linguistic substrate* —
patterns of form, direction, orthography, and relation already latent in the
entries — and that this substrate can be taught to a small LoRA adapter. The
adapter is meant to be **handed over, not held.** The intended end state is that
Cree communities take the adapter, the correction data, and the authority to
decide what counts as better language behavior, and keep and maintain it for
themselves. Value is designed to flow *to* the community, not away from it.

That is the design intent. Whether the project actually succeeds at being
non-extractive is **not the builder's call to make** — only a Cree community,
with real authority over the artifact, can ratify that. Until such a partner is
in the loop, this should be described as a *technical demonstration* that one
historical volume can seed a model, offered in the hope a community will want to
carry it the rest of the way.

### Why a historical source, deliberately

Choosing an 1865 dictionary is a design decision, not a convenience. Training on
scraped *modern* Cree would mean collecting living speakers' language without
consent and producing an artifact that claims to be contemporary Cree — and gets
it wrong, competing with the very people who speak it. An old, public-domain
source avoids that failure mode in two concrete ways:

- **No consent-to-collect problem.** The source is a fixed, public-domain
  historical record. No living speaker's contributions are being harvested; there
  is nothing modern to take without permission.
- **Honest provenance.** The artifact is transparently archival. It is labeled
  1865 and does not impersonate current fluent Cree. A model that openly derives
  from a 160-year-old missionary record invites the right calibration and cannot
  easily be mistaken for a community's present-day authority.

In effect the dated source is the input-side analog of the visible reward
ledger: both choose *legible, bounded provenance* over smooth, source-hiding
confidence. The deliberate point is to avoid manufacturing a modern, incorrect
artifact, and instead surface a clearly-labeled historical one.

What the old source does **not** do: it does not make the content neutral (1865
is colonial, not unbiased), it does not make the model correct (only honestly
dated), and it does not by itself settle OCAP authority over the *derived*
weights — a Cree adapter still implicates the community even when the input text
was public domain. The old source resolves "whose living data did you take,"
softens "does it impersonate modern truth," and leaves "who governs what is built
from it" open for the community to decide.

### Indigenous data governance frameworks this work must answer to

- **OCAP®** — The First Nations Principles of **O**wnership, **C**ontrol,
  **A**ccess, and **P**ossession. A registered trademark of the First Nations
  Information Governance Centre (FNIGC), and the established standard for First
  Nations data in Canada. *Ownership:* a community collectively owns its cultural
  knowledge and information. *Control:* First Nations have the right to control
  how information about them is collected, used, and disclosed. *Access:*
  communities must be able to access information about themselves regardless of
  where it is held. *Possession:* physical control of the data is the mechanism
  that asserts and protects ownership. By these principles, the weights and
  correction data belong with the community, not in an individual's repository.

- **CARE Principles for Indigenous Data Governance** — from the Global
  Indigenous Data Alliance (GIDA). CARE complements the FAIR principles
  (Findable, Accessible, Interoperable, Reusable), which are purpose-agnostic, by
  adding the people-and-purpose layer. **C**ollective Benefit: data ecosystems
  must let Indigenous Peoples derive benefit. **A**uthority to Control:
  Indigenous Peoples' rights and authority over their data must be recognized and
  respected. **R**esponsibility: those working with the data are accountable for
  how it supports Indigenous self-determination. **E**thics: Indigenous Peoples'
  rights and wellbeing are the primary concern at every stage. The slogan is "be
  FAIR *and* CARE."

The honest current status against these frameworks: there is **no named
community partner with authority over this artifact yet.** Community involvement
is presently a roadmap item, which means the model was built before the people it
concerns were in the loop. That sequencing is a real limitation, not a
formality, and it is named here deliberately.

### Cree is not one language, and the source is one variety

"Cree" (autonym **Nēhiyawēwin** and related forms) is an Algonquian dialect
continuum, not a single standardized language. Major dialects are conventionally
distinguished by the reflex of the Proto-Algonquian sound, e.g.:

- **Plains Cree** — the "y" dialect — *Nēhiyawēwin* (Alberta, Saskatchewan)
- **Woods Cree** — the "th" dialect — *Nīhithawīwin* (northern Saskatchewan, Manitoba)
- **Swampy Cree** — the "n" dialect — *Nēhinawēwin* (Manitoba, Hudson Bay/James Bay coast)
- **Moose Cree** — the "l" dialect (around Moose Factory, Ontario)
- **East Cree / James Bay Cree** (Quebec)

Watkins 1865 is titled *as spoken by the Indians of the Hudson's Bay
Territories*, so it records a particular 19th-century variety (broadly the
eastern/Hudson Bay region) filtered through one missionary's ear and goals. The
exact dialect mapping should be confirmed with community speakers and linguists,
**not asserted by this repo.** A model trained on it speaks one historical
variety, and should never be presented as "the" Cree language.

### Orthography limitation

Cree is written in two main systems: **Cree syllabics** (an abugida, e.g.
ᓀᐦᐃᔭᐍᐏᐣ) and a **Roman / Standard Roman Orthography** using the Latin alphabet
with long-vowel marks. Watkins used his own 19th-century missionary Roman
orthography, which is **not** identical to modern SRO. The reward function in
this repo preserves Roman-orthography diacritics (macrons, circumflexes, hyphens,
apostrophes) and does **not** handle syllabics at all. Many Cree communities read
and write primarily in syllabics, so in its current form this tool may not serve
exactly the communities best positioned to judge it. This is a known gap, not a
design endorsement.

### The laundering risk to guard against

A model smooths uncertainty into fluent-sounding confidence. The source carries
scan errors, one missionary's mishearings, archaic forms, and colonial framing.
A system that emits those with the authority of "AI" can quietly displace living
speakers as the authority — re-teaching a colonial version of the language back
to the community it came from. The decomposed, visible reward ledger exists
partly to keep failures legible and inspectable so this does not happen silently.
The model is a starting point for correction, **never** a source of truth about
how Cree is spoken.

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
- how to keep long reverse-section English glosses useful for training without overweighting verbose definitions

## Full Extraction Status

The local 2026-06-24 full-dictionary extraction covers:

- PDF pages `29-210`: Part I English-Cree
- PDF pages `212-492`: Part II Cree-English
- total extracted page JSON files: `463`
- deduplicated usable entries: `19,560`
- RL tasks: `38,870`
- plain Q&A records: `38,870`

The reverse section is normalized to the same downstream schema as Part I: `cree_primary` always contains the Cree form, and `english_headword` always contains the English gloss or headword.

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
