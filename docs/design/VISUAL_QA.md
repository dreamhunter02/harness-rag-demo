# Visual fidelity ledger

Browser rendering was checked with Playwright using local Google Chrome because the
integrated browser tool was unavailable in this environment.

| Check | Result |
| --- | --- |
| 1920×1080 stage layout | Pass; full-width presentation layout retains the complete research state |
| 1440×900 laptop layout | Pass; two-panel hierarchy retained with page and panel scrolling |
| 1366×768 projector layout | Pass; trajectory and individual Harness cells scroll independently |
| Slide palette | Warm off-white canvas, black editorial type, NVIDIA green accent, and thin grey rules retained |
| Approved hierarchy | Question/system/run controls, trajectory, five Harness cells, and bottom result/metrics strip retained |
| Evidence graph | Expanded across both rows with visible entity-to-document links |
| Live/replay clarity | Persistent black `DEMO REPLAY · NOT A LIVE MEASUREMENT` banner added |
| Metric correctness | Model result/reference comparison plus measured latency, model/retrieval split, tokens, throughput, and estimated cost |

Reference files:

- `approved-concept.png` — approved generated concept.
- `../screenshots/demo-ready.png` — ready state before execution.
- `../screenshots/demo-live-run.png` — populated live research state.
- `../screenshots/demo-completed.png` — verified result and measured telemetry.

The implementation uses explicit entity-to-document evidence links instead of
decorative graph geometry so live state updates remain legible and deterministic.
