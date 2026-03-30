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

(tutorial:module7)=
# Module 7: Advanced Topics (Coming Soon)

:::{note}
This module is under development. Planned topics:

- Multi-parameter sweeps (2D phase diagrams)
- WorkGraph vs WorkChain comparison
- FFT analysis and advanced post-processing
- Interactive exploration of results

See {ref}`Module 3 <tutorial:module3>` for the latest completed module.
:::

<!-- Original content commented out for future development

This module covers extensions and advanced topics. It is not required for core
tutorial completion.

WorkGraph vs WorkChain:

Modules 3 used **WorkGraph** to build workflows — a declarative, graph-based approach
where you wire tasks together.
AiiDA also supports **WorkChains**, the traditional imperative approach where you define
an outline of steps, submit child processes, and pass data through a context dictionary.

Both are first-class AiiDA citizens: they use the same `engine.run()` / `engine.submit()`
API, produce the same provenance, and work with all `verdi process` commands.
The difference is in *how you author* the workflow, not in *how you run or inspect* it.

If you are developing an AiiDA **plugin** that other people will install and use,
WorkChains are the established convention — most existing plugins
(aiida-quantumespresso, aiida-cp2k, etc.) use them.
WorkGraph is better suited for composing and customizing workflows as a user.

## Multi-parameter sweeps

TODO: 2D parameter scan over F and k to map the full phase diagram
TODO: visualize the phase diagram as a heatmap of variance_V
TODO: identify different pattern regimes (spots, stripes, labyrinthine)

## FFT analysis

TODO: write a calcfunction that computes the 2D FFT of V_final
TODO: extract the dominant wavelength
TODO: plot wavelength vs F

## Interactive exploration

TODO: optional: build a simple dashboard for exploring results

-->
