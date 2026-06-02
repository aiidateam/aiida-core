# Giovanni Pizzi
First version written on 10 Feb 2026

# Reaction–Diffusion Tutorial – Design Document

## 1. Choice of Example: Reaction–Diffusion (Gray–Scott Model)

### One-sentence explanation for users:
*"This code simulates how two diffusing and reacting substances on a 2D grid spontaneously form spatial patterns, starting from a nearly uniform initial state."*

#### Longer explanation
Note: this should probably be kept hidden/closed by default, but a curious user can open it and read a longer description. We can point e.g. to Wikipedia for more details. Something of this style (we can decide if we need to remove something, or add some more details).

*"Reaction-diffusion systems model two competing processes: chemicals spreading out (diffusion) and chemicals transforming into each other (reaction). In the Gray-Scott model specifically, we track two substances U and V on a grid. U is constantly fed into the system and both substances can decay, while V catalyzes its own production from U in a positive feedback loop. When diffusion, feeding, and decay are balanced just right, these simple local rules spontaneously create global patterns—the same mathematical framework explains everything from leopard spots to chemical oscillations in test tubes. The fascinating part is that identical starting conditions (nearly uniform concentrations everywhere) can produce wildly different patterns just by tweaking two parameters: the feed rate F and kill rate k."*

### Visual hook for learners:
Before diving into the technical details, the tutorial will show a gallery of example patterns (spots, stripes, labyrinthine structures) that emerge from different parameter combinations. This provides immediate visual motivation: "You will learn to generate and analyze these patterns using AiiDA."

### Why this example works for the tutorial:

- **Conceptually simple**: Users do not need to understand the full mathematics to follow the tutorial; the model provides a visually intuitive result.
- **Parameterizable**: The main parameters (feed rate F, kill rate k, diffusion constants du, dv) are scalars that are easy to sweep for high-throughput examples.
- **Deterministic and reproducible**: Simulations with the same seed always produce the same results, ideal for debugging and workflows.
- **Visual output**: Produces 2D arrays that can be visualized as patterns, providing immediate feedback.
- **Supports workflow concepts**: Can demonstrate workflow execution, error handling, retries, post-processing, and high-throughput scans.
- **Error-prone in a controlled way**: Numerical instabilities or trivial states allow natural introduction of exit codes, handlers, and debugging.

### Optional / maybe extensions:
- Multi-parameter scans (e.g., F and k)
- More sophisticated post-processing (dominant wavelength via FFT)
- MPI-friendly execution for larger grids (for advanced users)

---

## 2. Input / Output Overview

### User-facing inputs (YAML or Dict in AiiDA):

| Parameter | Type | Brief description |
|-----------|------|-------------------|
| `grid_size` | int | Size of the 2D grid (grid_size × grid_size) |
| `du`, `dv` | float | Diffusion rates of U and V |
| `F` | float | Feed rate (primary scan parameter) |
| `k` | float | Kill rate |
| `dt` | float | Time step for simulation |
| `n_steps` | int | Number of iterations |
| `seed` | int, optional | Random seed for reproducibility |

### Outputs:

| Output | Type | Notes | Typical values/ranges |
|--------|------|-------|----------------------|
| `U_final` | 2D array | Final distribution of U | Values between 0–1 |
| `V_final` | 2D array | Final distribution of V | Values between 0–1 |
| `variance_V` | float | Scalar measure of pattern "strength" | 0.0001–0.01 (low = uniform, high = structured patterns) |
| `mean_V` | float | Average value of V | 0.1–0.5 (depends on F and k) |
| `params` | Dict / JSON | Full simulation parameters used | Copy of input parameters |

### Success / failure signaling:
- **Success**: stdout prints `JOB DONE`, exit code 0
- **Failures**: non-zero exit code with `ERROR[code]: message`

This supports natural introduction of parsing, handlers, and debugging.

---

## 3. Key Design Principles for the Tutorial

### Start simple
Use the CLI or Python driver to run a single simulation and inspect outputs.

### Layered learning
Gradually introduce AiiDA concepts:
- Shell / Python execution
- Inspecting inputs/outputs (`verdi calcjob inputcat/outputcat`, `verdi process dump`)
- Parsing outputs
- Storing arrays and scalars in `ArrayData` / `Float` / `Dict`
- Optional: generating PNG images in post-processing

### Debugging & error handling
- Show users how to inspect failed jobs (exit_code, stderr)
- Demonstrate handlers to retry unstable jobs or trivial results

### High-throughput workflows
- Introduce parameter scans over F (~20–40 values)
- Collect and post-process results to produce variance vs F plots, mean vs F, and representative pattern images

### Provenance and organization
- Use Groups to organize runs
- Show exporting `.aiida` archives for reproducibility

### Pros of this example:
- **Immediate visual payoff** (patterns provide instant feedback and motivation)
- **Intuitive parameter sweeps** (changing F produces visibly different patterns)
- **Comprehensive AiiDA coverage** (supports all key features: CalcJob, WorkGraph, parser, data types, handlers, post-processing, querying, groups)
- **Authentic error scenarios** (controlled failure modes demonstrate real debugging workflows)
- **Low computational cost** (small 2D grids run quickly, suitable for hands-on tutorial environment)

### Cons / limitations:
- Limited to 2D, small grids for tutorial speed (no heavy HPC)
- Single-physics example; more abstract than domain-specific tools (e.g., QE)
- Advanced pattern analysis (FFT, multiple parameters) is optional / for later exploration

---

## 4. Proposed Tutorial Structure (Storyline / Sections)

### Section 1: Running a simulation in AiiDA shell

**After this section, you will be able to:** Run a single reaction–diffusion calculation and inspect its input and output files using AiiDA's command-line tools.

**Key concepts introduced:**
- Using the CLI or minimal Python driver to submit a calculation
- Basic `verdi` commands: `verdi calcjob inputcat` and `verdi calcjob outputcat`
- Understanding job submission and completion

**What you will learn in this section:** You will learn how to submit your first AiiDA calculation and inspect what went in and what came out. However, you cannot yet automatically extract structured data from the outputs or handle errors—these capabilities will be introduced in the next sections.

---

### Section 2: Parsing outputs

**After this section, you will be able to:** Extract meaningful numerical results (`variance_V`, `mean_V`) from raw output files and understand how AiiDA determines job success or failure.

**Key concepts introduced:**
- Parser concept and implementation
- Exit codes (success = 0, various failure modes)
- Linking parsed outputs to the calculation

**What you will learn in this section:** You will learn how to automatically extract structured information from text output files and signal success or failure. However, you cannot yet store arrays or generate visualizations—that comes next.

---

### Section 3: Using Data types

**After this section, you will be able to:** Store arrays, scalars, and parameters in AiiDA's native data types and optionally generate PNG visualizations of your patterns.

**Key concepts introduced:**
- `ArrayData` for storing 2D arrays (U_final, V_final)
- `Float` for scalars (variance_V, mean_V)
- `Dict` for parameters
- Optional: simple post-processing function to generate PNG images

**What you will learn in this section:** You will learn how to properly store different types of scientific data in AiiDA's provenance graph. However, you cannot yet combine multiple calculations into automated workflows—that's the next step.

---

### Section 4: Workflow basics

**After this section, you will be able to:** Wrap a single calculation in a WorkGraph, understand workflow logic, and use context variables to pass data between steps.

**Key concepts introduced:**
- WorkGraph basics
- `run_calcjob` function
- Context (`ctx`) variables for data flow
- Simple workflow logic

**What you will learn in this section:** You will learn how to create simple automated workflows that chain calculations together. However, you cannot yet handle failures gracefully or debug complex workflow issues—error handling is covered next.

---

### Section 5: Error handling & debugging

**After this section, you will be able to:** Diagnose failed calculations, understand different failure modes, and implement handlers that automatically retry or adjust problematic jobs.

**Key concepts introduced:**
- Inspecting failed jobs with `verdi process dump`
- Understanding exit codes and stderr
- Implementing handlers for numerical instability
- Handling trivial solutions (no pattern formation)
- Re-submission strategies

**Common troubleshooting scenarios:**
- Wrong parameter ranges (F or k outside stable regime)
- Missing dependencies or incorrect environment setup
- Time step too large causing numerical blow-up

**What you will learn in this section:** You will learn how to debug failures and build resilient workflows that can recover from common errors. However, you cannot yet run systematic parameter sweeps or organize large numbers of calculations—high-throughput capabilities come next.

---

### Section 6: High-throughput scans & querying

**After this section, you will be able to:** Execute parameter sweeps over 20–40 values of F, collect all results, query the database for specific calculations, and organize your work using Groups.

**Key concepts introduced:**
- Loops in WorkGraphs for parameter sweeps
- Storing multiple calculation outputs
- Querying the AiiDA database (QueryBuilder)
- Groups for organization
- Provenance visualization

**What you will learn in this section:** You will learn how to run many calculations systematically, find specific results in your database, and organize them logically. However, you cannot yet analyze trends across your parameter sweep or create publication-quality figures—post-processing is the final step.

---

### Section 7: Post-processing & visualization

**After this section, you will be able to:** Analyze results across parameter sweeps, create plots showing how pattern characteristics vary with parameters, and export representative pattern images.

**Key concepts introduced:**
- Collecting results from multiple calculations
- Plotting variance vs F, mean vs F
- Selecting and exporting representative patterns
- Optional: FFT analysis for pattern wavelength
- Exporting `.aiida` archives for reproducibility

**What you will learn in this section:** You will learn how to extract scientific insights from your calculations and create publication-ready visualizations. At this point, you have completed the core tutorial and understand the full AiiDA workflow cycle.

---

### Section 8: Optional / advanced topics

**After this section, you will be able to:** Extend your knowledge to more complex scenarios including multi-parameter scans, parallel execution, and advanced pattern analysis.

**Topics covered:**
- Multi-parameter sweeps (F and k simultaneously)
- MPI execution for larger grids
- Advanced post-processing (FFT, wavelength extraction)
- Interactive dashboards (optional)

**Note:** These sections can be referenced or included as exercises, but are not required for core tutorial completion.

---

## 5. Key Storytelling / Teaching Points

- Demonstrate success and failure naturally using exit codes
- Start with single run, then expand to mid-throughput scans
- Introduce inspection commands (`inputcat/outputcat`, `process dump`) gradually
- Show provenance visualization in context of parameter sweeps
- Emphasize data handling and reproducibility with arrays, scalars, dictionaries, and PNG outputs

---

## 6. Next Steps / Optional Extensions

- FFT / pattern wavelength analysis
- Multi-parameter sweeps (F and k)
- Automated handler strategies for extreme parameters
- MPI / larger grids
- Interactive plots or dashboards (for advanced tutorials)

---

## Summary

Reaction–diffusion provides a visually intuitive, parameterizable, deterministic example that naturally supports all the main AiiDA tutorial goals: running calculations, inspecting inputs/outputs, handling errors, creating workflows with a WorkGraph, performing mid-throughput scans, storing structured outputs, post-processing results, and organizing them with Groups. Its simplicity avoids cognitive overload while still providing enough depth for hands-on exercises with real scientific workflows.
