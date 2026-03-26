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
# Module 2: Running External Codes

## What you will learn

After this module, you will be able to:

- Run an external code through AiiDA using `aiida-shell`
- Set up a Computer and Code in AiiDA
- Understand the CalcJob concept (input files → scheduler → output files)
- Run calculations on a remote computer
- Use `submit()` and the daemon for asynchronous execution
- Inspect calculation inputs and outputs with `verdi calcjob inputcat` / `outputcat`
- Write a parser to extract structured data from output files
- Handle exit codes for different failure modes

## What you will not learn yet

You cannot yet query the database, organize data into groups, or export archives — those capabilities come in {ref}`Module 3 <tutorial:module3>`.

## Running external codes with `aiida-shell`

<!-- TODO: introduce aiida-shell / ShellJob as the quickest way to run an external code -->
<!-- TODO: run reaction-diffusion.py via ShellJob -->
<!-- TODO: inspect the results -->

## Setting up a Computer and Code

<!-- TODO: explain the Computer + Code abstraction -->
<!-- TODO: verdi computer setup (or verdi presto) -->
<!-- TODO: verdi code setup -->

## The CalcJob concept

<!-- TODO: explain input files → scheduler → output files cycle -->
<!-- TODO: run the reaction-diffusion simulation as a CalcJob -->
<!-- TODO: verdi calcjob inputcat / outputcat to inspect files -->

## Remote execution

<!-- TODO: set up a remote Computer and Code -->
<!-- TODO: submit a calculation to a remote machine -->
<!-- TODO: explain submit() vs run() and the daemon (verdi daemon start) -->
<!-- TODO: monitor with verdi process list, retrieve results -->

## Writing a parser

<!-- TODO: why we need a parser: raw output files → structured AiiDA nodes -->
<!-- TODO: define exit codes on the CalcJob spec -->
<!-- TODO: implement parser that reads output and extracts variance_V, mean_V as Float nodes -->
<!-- TODO: handle the various error exit codes (0, 10, 11, 20, 30) -->

## Running with the parser

<!-- TODO: run a calculation that uses the custom parser -->
<!-- TODO: show the parsed outputs in verdi process show -->
<!-- TODO: trigger different exit codes with bad parameters -->

## Summary

In this module you learned to:

- **Run external codes** with `aiida-shell` and as CalcJobs
- **Set up** a Computer and Code in AiiDA
- **Run remotely** using `submit()` and the daemon
- **Inspect** calculation files with `verdi calcjob inputcat` / `outputcat`
- **Parse** output files into structured AiiDA nodes
- **Handle failures** with exit codes

## Next steps

We can now run external codes and parse their outputs. In {ref}`Module 3 <tutorial:module3>`, you'll learn how to work with AiiDA's data types, query the database, and organize your results.
