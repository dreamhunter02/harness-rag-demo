# Visual fidelity ledger

Browser rendering was checked with Playwright using local Google Chrome because the
integrated browser tool was unavailable in this environment.

| Check | Result |
| --- | --- |
| 1920×1080 stage layout | Pass; complete UI and footer fit without page scrolling |
| 1440×900 laptop layout | Pass; two-panel hierarchy retained |
| 1366×768 projector layout | Pass after compact-height tuning; populated replay fits without page scrolling |
| Slide palette | Warm off-white canvas, black editorial type, NVIDIA green accent, and thin grey rules retained |
| Approved hierarchy | Question/system/run controls, trajectory, six Harness cells, and bottom result/metrics strip retained |
| Live/replay clarity | Persistent black `DEMO REPLAY · NOT A LIVE MEASUREMENT` banner added |
| Metric correctness | Illustrative labels replaced with measured total, first action, model/retrieval split, tokens, throughput, and estimated cost |

Reference files:

- `approved-concept.png` — approved generated concept.
- `implemented-1920x1080.png` — populated deterministic recovery state at stage resolution.
- `implemented-1366x768.png` — populated compact projector state.

Remaining visual difference is intentional: the implementation uses text-based
evidence-graph bridges instead of decorative graph geometry so live state can update
legibly and deterministically.
