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

(tutorial:module8)=
# Module 8: Optional and Advanced Topics

:::{note}
This module covers extensions and advanced topics. It is not required for core tutorial completion — the main tutorial ends with {ref}`Module 7 <tutorial:module7>`.
:::

## Multi-parameter sweeps

Scan F and k simultaneously to map the full phase diagram of the Gray-Scott model.

<!-- TODO: 2D parameter scan over F and k -->
<!-- TODO: visualize the phase diagram as a heatmap of variance_V -->
<!-- TODO: identify different pattern regimes (spots, stripes, labyrinthine) -->

## MPI execution for larger grids

Run larger grids on HPC systems using MPI parallelization.

<!-- TODO: modify the simulation for MPI-friendly execution -->
<!-- TODO: configure AiiDA for remote HPC submission -->
<!-- TODO: compare performance across grid sizes -->

## Advanced post-processing: FFT analysis

Extract dominant pattern wavelength via Fourier transform.

<!-- TODO: write a calcfunction that computes the 2D FFT of V_final -->
<!-- TODO: extract the dominant wavelength -->
<!-- TODO: plot wavelength vs F -->

## Interactive exploration

<!-- TODO: optional: build a simple dashboard for exploring results -->
