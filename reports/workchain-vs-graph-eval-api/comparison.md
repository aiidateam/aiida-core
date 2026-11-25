# Comparison with the immediately previous eval

Previous: `../workchain-vs-graph-eval-after/`, after the language improvements but before the private-IR/flat-input API and authoring guide changes.

| Arm | Solve seconds: previous → current | Total tokens | Reported USD | Model turns |
|---|---:|---:|---:|---:|
| workchain | 113.0 → 124.9 | 76,743 → 109,017 | $0.0697 → $0.0849 | 9 → 12 |
| graph | 151.5 → 116.5 | 207,414 → 91,193 | $0.1386 → $0.0529 | 14 → 9 |

Both arms pass the same 13 acceptance cases. Total tokens include cached context; detailed categories, percentage changes and effort traces are in `comparison.json`.

One run per style per revision cannot establish statistical significance or causation. Read `analysis.md` for evidence-backed remaining improvements and limitations.
