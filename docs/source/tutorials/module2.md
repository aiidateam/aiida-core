---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.11.4
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

(tutorial:module2)=
# Module 2: Parsing Outputs

## What you will learn

After this module, you will be able to extract meaningful numerical results (`variance_V`, `mean_V`) from raw output files and understand how AiiDA determines job success or failure.

**Key concepts introduced:**

- Parser concept and implementation
- Exit codes (success = 0, various failure modes)
- Linking parsed outputs to the calculation node in the provenance graph

## What you will not learn yet

You cannot yet store arrays or generate visualizations — that comes in {ref}`Module 3 <tutorial:module3>`.

## Why do we need a parser?

In {ref}`Module 1 <tutorial:module1>`, we ran a calculation and looked at raw output files. But to use those results programmatically — query them, feed them into workflows, or compare across runs — we need to extract structured data.

A **parser** reads the output files of a calculation and:
1. Extracts relevant quantities as AiiDA data nodes
2. Checks for errors and sets appropriate exit codes
3. Links the parsed outputs to the calculation in the provenance graph

## Exit codes

Our simulation has well-defined failure modes:

| Exit code | Meaning | What to do |
|-----------|---------|-----------|
| 0 | Success (`JOB DONE`) | Parse outputs normally |
| 10 | Diffusion constants not positive | Fix input parameters |
| 11 | Time step not positive | Fix input parameters |
| 20 | Numerical instability | Reduce time step or change parameters |
| 30 | Trivial steady state | Change F or k to a pattern-forming regime |

## Writing a parser

<!-- TODO: define exit codes on the CalcJob spec -->
<!-- TODO: implement parser that reads .npz and extracts variance_V, mean_V as Float nodes -->
<!-- TODO: handle the various error exit codes -->

## Running with the parser

<!-- TODO: run a calculation that uses the custom parser -->
<!-- TODO: show the parsed outputs in verdi process show -->

## Triggering different exit codes

<!-- TODO: run with bad parameters to trigger exit code 30 (trivial solution) -->
<!-- TODO: run with bad dt to trigger numerical instability (exit code 20) -->
<!-- TODO: inspect the failed calculations -->

## Next steps

We can now extract scalars from our outputs and detect failures. In {ref}`Module 3 <tutorial:module3>`, you'll learn how to store richer data types — arrays, dictionaries, and visualizations — in AiiDA's provenance graph.
