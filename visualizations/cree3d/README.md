# Cree1865 3D Metrics Companion

This is an optional local companion for the `cree1865-synthetic-expansion-v1`
W&B run. The native W&B report remains the source of record for exact values;
this app turns selected metrics into normalized 3D ribbons so timing and shape
are easier to inspect.

Refresh the local metric snapshot from the run log:

```bash
python scripts/analysis/export_cree_3d_metrics.py
```

Run the app:

```bash
cd visualizations/cree3d
npm install
npm run dev
```

Production build and render check:

```bash
npm run build
npm run preview
npm run verify:render
```

The verifier captures desktop and mobile screenshots and samples pixels from
the WebGL canvas so a blank or badly framed render fails fast.
