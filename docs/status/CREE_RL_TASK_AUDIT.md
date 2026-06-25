# Cree RL Task Audit

Audit date: 2026-06-24

Dataset root: `data/cree_goal_run_20260624_full_dictionary/training_datasets`

## Counts

| Field | Value |
|---|---:|
| RL records | 38,870 |
| Q&A records | 38,870 |
| English->Cree tasks | 19,435 |
| Cree->English tasks | 19,435 |
| Word-translation tasks | 19,435 |
| Reverse-translation tasks | 19,435 |
| Easy / medium / hard | 36,910 / 1,408 / 552 |
| Missing `question` fields | 0 |
| Missing `task_type` fields | 0 |
| Missing `info` payloads | 0 |
| Missing direction metadata | 0 |
| Duplicate RL task IDs | 0 |

## Answer Shape

| Metric | Value |
|---|---:|
| Minimum answer length | 1 word |
| Median answer length | 1 word |
| 95th percentile answer length | 8 words |
| Maximum answer length | 29 words |

## Orthography Signal

Rows with non-ASCII Cree orthography tracked in `info.special_chars`: `11,388`.

Most common tracked characters:

| Character class | Count |
|---|---:|
| macron a | 9,892 |
| acute u | 1,070 |
| acute e | 808 |
| acute o | 600 |
| macron e | 385 |
| acute a | 135 |
| circumflex e | 74 |
| circumflex u | 45 |
| macron u | 40 |
| acute i | 36 |
| macron o | 24 |
| macron i | 24 |

## Readiness Notes

The dataset is ready for the requested small 1200-step run. It is balanced by direction, has no missing Tinker task fields, and has no duplicate task IDs after page-scoped ID normalization.

For larger runs, review or filter the longest reverse-section English glosses. The current task set is primarily direct dictionary lookup Q&A, which is useful for reward debugging but should not be presented as conversational Cree competence.

## Training Follow-Up

The requested 1200-step Tinker run completed under W&B run `kjn02ee4`; see `docs/status/CREE_1200STEP_TINKER_RUN.md` for the final checkpoint, reward ledger paths, and resume note.
