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

(tutorial:module5)=
# Module 5: Remote Submission and the Daemon (Coming Soon)

:::{note}
This module is under development. Planned topics:

- `submit()` vs `run()` and the AiiDA daemon
- Setting up remote HPC computers (SSH transport, SLURM/PBS schedulers)
- Submitting calculations to remote clusters
- Monitoring and retrieving results

See {ref}`Module 3 <tutorial:module3>` for the latest completed module.
:::

<!-- Original content commented out for future development

## What you will learn

After this module, you will be able to:

- Understand the difference between `run()` (synchronous) and `submit()` (asynchronous)
- Start and manage the AiiDA daemon
- Set up a remote Computer with SSH transport and a job scheduler
- Submit calculations to remote HPC clusters
- Monitor running calculations and retrieve results

## submit() vs run() and the daemon

So far, every calculation has been **synchronous** — `launch_shell_job(...)` blocks until
the calculation finishes. This is fine for quick local runs, but for production use on
HPC clusters you'll want **asynchronous** execution:

- **`run()`** — blocks until the calculation completes. Simple, but ties up your Python session.
- **`submit()`** — sends the calculation to the AiiDA **daemon** and returns immediately.
  The daemon manages the calculation lifecycle in the background.

TODO: show submit() example
TODO: explain daemon start/stop/status
TODO: verdi daemon start, verdi daemon status

## Setting up remote computers

TODO: verdi computer setup with SSH transport and SLURM scheduler
TODO: verdi computer configure core.ssh
TODO: verdi computer test

## Submitting to remote clusters

TODO: submit a calculation to the remote computer
TODO: monitor with verdi process list
TODO: retrieve results

## Summary

In this module you learned to:

- **Distinguish** `run()` (synchronous) from `submit()` (asynchronous via daemon)
- **Set up** remote HPC computers
- **Submit** and monitor calculations on clusters

-->
