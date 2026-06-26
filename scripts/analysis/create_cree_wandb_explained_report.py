#!/usr/bin/env python3
"""Publish an explained W&B report for the live Cree1865 run."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from wandb_workspaces.reports import v2 as wr


ROOT = Path(__file__).resolve().parents[2]


ENTITY = "christian-cooper-us"
PROJECT = "thinking-machines-qwen3-30b"
RUN_NAME = "cree1865-synthetic-expansion-v1"
RUN_ID = "hda2wqhl"
RUN_URL = f"https://wandb.ai/{ENTITY}/{PROJECT}/runs/{RUN_ID}"


def metric_panel(title: str, metrics: list[str], description: str, *, y: int) -> list[object]:
    """Return a chart plus a description panel on the same row."""
    return [
        wr.LinePlot(
            title=title,
            y=metrics,
            smoothing_type="exponential",
            smoothing_factor=0.6,
            title_x="Training step",
            layout=wr.Layout(x=0, y=y, w=16, h=8),
        ),
        wr.MarkdownPanel(
            markdown=description.strip(),
            layout=wr.Layout(x=16, y=y, w=8, h=8),
        ),
    ]


def build_report() -> wr.Report:
    runset = wr.Runset(
        entity=ENTITY,
        project=PROJECT,
        name="Live Cree synthetic expansion run",
        query=RUN_NAME,
        visible_columns=["Name", "State", "Created", "Runtime", "progress/done_frac", "reward/mean"],
    )

    overview = wr.MarkdownBlock(
        f"""
# Cree1865 Synthetic Expansion V1: Explained Dashboard

Live run: [{RUN_NAME}]({RUN_URL}) (`{RUN_ID}`)

This report is a readable companion to the W&B run. It does not start a new
run or log new metrics. Each chart is paired with a plain-language note about
what the value means and how to interpret movement during the 800-step Cree
dictionary RL experiment.

The core caution: a lookup-rubric reward is not fluency. Treat exact match,
target containment, character F1, orthography, and direction splits as separate
signals.
        """.strip()
    )

    progress_panels: list[object] = []
    y = 0
    for title, metrics, desc in [
        (
            "Run Progress",
            ["progress/done_frac", "progress/batch"],
            """
**What it means:** `progress/done_frac` is the fraction of the configured
800-step run completed. `progress/batch` is the current training iteration.

**How to read it:** this should increase monotonically. A flat line while the
process is alive means the run is probably sampling, checkpointing, or stalled
before the next metric write.
            """,
        ),
        (
            "Reward Distribution",
            ["reward/mean", "reward/std", "reward/min", "reward/max"],
            """
**What it means:** reward is the weighted Cree dictionary verifier score for
sampled completions in the current training batch. Mean is the headline, while
std/min/max show spread.

**How to read it:** rising mean with healthy spread means the model is finding
better answers without every sample collapsing to the same behavior. Do not
read the absolute scalar as fluency.
            """,
        ),
        (
            "Training Loss",
            ["loss:sum", "train/fwdbwd/loss:sum"],
            """
**What it means:** this is the RL optimizer objective reported by Tinker for
the forward/backward update, not ordinary cross-entropy.

**How to read it:** large early movement shows the optimizer is changing the
policy. It can cross zero and is not directly comparable to language-model
perplexity. Use it with reward, KL, and entropy.
            """,
        ),
        (
            "Entropy And KL",
            ["optim/entropy", "optim/kl_sample_train_v1", "optim/kl_sample_train_v2"],
            """
**What it means:** entropy measures output uncertainty/diversity; KL estimates
policy drift from the reference/sampling distribution.

**How to read it:** entropy falling is expected as the model becomes more
decisive. If entropy collapses while exact/containment stay flat, the model may
be learning answer style rather than lookup accuracy. KL spikes warn of
unstable policy drift.
            """,
        ),
        (
            "Exact And Containment By Direction",
            [
                "slice/english_to_cree/exact",
                "slice/english_to_cree/target_containment",
                "slice/cree_to_english/exact",
                "slice/cree_to_english/target_containment",
            ],
            """
**What it means:** exact match checks whether the normalized answer equals the
dictionary target. Target containment checks whether the target appears inside
the completion.

**How to read it:** these are the hard lookup-accuracy channels. They may lag
behind character F1. If they remain flat for hundreds of steps, the model is
improving surface shape but not reliably retrieving answers.
            """,
        ),
        (
            "Character F1 By Direction",
            ["slice/english_to_cree/char_f1", "slice/cree_to_english/char_f1"],
            """
**What it means:** character F1 measures spelling-level overlap with the target
answer, so partial forms and near misses receive partial credit.

**How to read it:** this is usually the first signal to improve in dictionary
training. It says the model is moving toward the right string shape; it does
not prove full lookup correctness.
            """,
        ),
        (
            "Orthography By Direction",
            ["slice/english_to_cree/orthography", "slice/cree_to_english/orthography"],
            """
**What it means:** orthography tracks whether required Cree marks, accents,
hyphens, and apostrophes are preserved.

**How to read it:** English->Cree orthography is the important target-Cree
signal. Cree->English orthography can be less meaningful because the expected
target is often English and may contain few Cree marks.
            """,
        ),
        (
            "Answer Length By Direction",
            ["slice/english_to_cree/length", "slice/cree_to_english/length"],
            """
**What it means:** length reward favors concise lookup-style answers and
penalizes padded explanations.

**How to read it:** a high length score means the model is staying brief. That
is useful only if exact/containment and character F1 also improve; otherwise it
may just be getting terser.
            """,
        ),
        (
            "Held-Out Eval Reward",
            [
                "test/env/cree/reward/total",
                "test/env/direction/english_to_cree/reward/total",
                "test/env/direction/cree_to_english/reward/total",
            ],
            """
**What it means:** these are periodic eval scores on held-out diagnostic rows,
separate from the training batch.

**How to read it:** this is the best early generalization signal. Watch the
English->Cree and Cree->English split; target-Cree generation is usually the
harder and more important direction for this experiment.
            """,
        ),
        (
            "Held-Out Eval Components",
            [
                "test/env/cree/ledger/exact_raw",
                "test/env/cree/ledger/target_containment_raw",
                "test/env/cree/ledger/orthography_raw",
                "test/env/cree/ledger/char_f1_raw",
                "test/env/cree/ledger/length_raw",
            ],
            """
**What it means:** this decomposes held-out reward into exact answer,
containment, orthography, character overlap, and concise length.

**How to read it:** this tells why total eval reward moves. Character F1 and
length can rise before exact match. A convincing run eventually needs movement
in exact or containment, not only softer channels.
            """,
        ),
        (
            "Throughput",
            ["perf/tokens_per_sec", "perf/samples_per_sec", "perf/step_time"],
            """
**What it means:** token throughput, sampled completions per second, and wall
time per training step.

**How to read it:** falling throughput can reflect longer completions,
checkpointing, service variability, or load. It affects ETA, not model quality.
            """,
        ),
        (
            "Expert Token Utilization Internals",
            [
                "e_frac_with_tokens:mean",
                "train/fwdbwd/e_frac_with_tokens:mean",
                "e_frac_oversubscribed:mean",
                "train/fwdbwd/e_frac_oversubscribed:mean",
            ],
            """
**What it means:** `e_frac_with_tokens:mean` is the fraction of expert-parallel
token slots that contain real sampled tokens rather than padding/empty work.
For example, `0.7008` means about 70% of those slots are active. The
oversubscribed metric estimates how often capacity is over-requested.

**How to read it:** these are Tinker/MoE utilization diagnostics. They explain
compute density and routing pressure; they are not reward, accuracy, or Cree
quality metrics.
            """,
        ),
        (
            "Expert Capacity Violation Internals",
            [
                "e_min_violation:mean",
                "e_max_violation:mean",
                "e_max_violation:max",
                "train/fwdbwd/e_min_violation:mean",
                "train/fwdbwd/e_max_violation:mean",
            ],
            """
**What it means:** these internal diagnostics report how far expert/token
routing demand is from expected capacity bounds during the update.

**How to read it:** stable values are mostly operational. Large spikes can
coincide with inefficient or unstable steps, but they should not be interpreted
as language-learning metrics.
            """,
        ),
    ]:
        progress_panels.extend(metric_panel(title, metrics, desc, y=y))
        y += 8

    glossary = wr.MarkdownBlock(
        """
## Metric Glossary

- `reward/mean`: average Cree verifier score for the current training batch.
- `loss:sum`: Tinker RL objective for the update; useful as an optimization
  signal, not as perplexity.
- `optim/entropy`: output uncertainty. Falling entropy means the policy is
  becoming more decisive.
- `optim/kl_sample_train_v1`, `optim/kl_sample_train_v2`: KL drift estimates.
  Watch for spikes.
- `slice/*/exact`: normalized answer exactly matches the target.
- `slice/*/target_containment`: target answer appears inside the completion.
- `slice/*/char_f1`: spelling-level overlap with the target answer.
- `slice/*/orthography`: required Cree marks and punctuation are preserved.
- `slice/*/length`: response is concise enough for dictionary lookup.
- `test/env/*`: held-out eval metrics. Prefer these when judging
  generalization.
- `perf/*`: throughput and wall-clock diagnostics.
- `e_*`: low-level Tinker/MoE utilization and routing-capacity diagnostics.
  They explain compute behavior, not language quality.
        """.strip()
    )

    return wr.Report(
        entity=ENTITY,
        project=PROJECT,
        title="Cree1865 Synthetic Expansion V1 Explained Dashboard",
        description=(
            "Explained W&B report for the live Cree1865 synthetic expansion run. "
            "Every chart is paired with a description of what the value means."
        ),
        width="fluid",
        blocks=[
            overview,
            wr.TableOfContents(),
            wr.H2("Explained Charts"),
            wr.PanelGrid(runsets=[runset], panels=progress_panels),
            glossary,
        ],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", action="store_true", help="Save as a draft report.")
    args = parser.parse_args()
    _load_env(ROOT / ".env")
    report = build_report()
    report.save(draft=args.draft)
    print(report.url)
    return 0


def _load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key, value.strip().strip('"').strip("'"))


if __name__ == "__main__":
    raise SystemExit(main())
