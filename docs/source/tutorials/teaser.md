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

(tutorial:teaser)=
# AiiDA in Action

<!-- This page gives you a quick preview of what you will be able to do after completing the tutorial. -->
<!-- Don't worry about understanding every detail -- the modules will teach you each piece step by step. -->
<!---->
<!-- ## The scenario -->
<!---->
<!-- Imagine you want to scan 20 values of an input parameter, collect the results, and analyze how an output quantity varies across the scan. -->
<!---->
<!-- Without AiiDA, this typically means a script full of `subprocess` calls, temporary directories, manual file bookkeeping, and no record of what ran or why. -->
<!-- If a few runs fail, you notice only when you parse the results -- if you notice at all. -->
<!---->
<!-- With AiiDA, you get **monitoring**, **automatic error recovery**, **queryable results**, and **full provenance** -- for free. -->
<!---->
<!-- ## Monitoring running processes -->
<!---->
<!-- Once you submit a parameter sweep, you can check its status at any time from the command line: -->
<!---->
<!-- ```console -->
<!-- $ verdi process list -->
<!--   PK  Created    Process label         State             Process status -->
<!-- ----  ---------  --------------------  ----------------  -------------------------- -->
<!--  142  2m ago     GrayScottSweep        ⏵ Waiting         Waiting for 20 sub-processes -->
<!--  143  2m ago     run_simulation         ✓ Finished [0] -->
<!--  144  2m ago     run_simulation         ✓ Finished [0] -->
<!--  145  1m ago     run_simulation         ⏵ Running -->
<!--  ... -->
<!---->
<!-- Total results: 22 -->
<!-- ``` -->
<!---->
<!-- You can drill into any process to see its inputs, outputs, and log messages: -->
<!---->
<!-- ```console -->
<!-- $ verdi process show 145 -->
<!-- Process label:   run_simulation -->
<!-- Process state:   Running -->
<!-- Exit code:       None -->
<!---->
<!-- Inputs: -->
<!--     F         0.042 -->
<!--     k         0.065 -->
<!--     n_steps   5000 -->
<!--     ... -->
<!-- ``` -->
<!---->
<!-- Even if you close your terminal and come back the next day, all processes and their results are safely stored in the database. -->
<!---->
<!-- ## Automatic error recovery -->
<!---->
<!-- Some parameter combinations cause the calculation to fail. -->
<!-- A plain script would just skip these and move on, losing information. -->
<!---->
<!-- With AiiDA workflows, you can register **error handlers** that automatically respond to specific exit codes. -->
<!-- For instance, when a calculation fails, the workflow can adjust inputs and retry: -->
<!---->
<!-- ```console -->
<!-- $ verdi process status 142 -->
<!-- GrayScottSweep<142> [Waiting] -->
<!--     ├── run_simulation<143> [Finished] [0] -->
<!--     ├── run_simulation<144> [Finished] [0] -->
<!--     ├── run_simulation<145> [Finished] [30]: Trivial steady state -->
<!--     │       └── [handler: retry_with_more_steps] → retrying with n_steps=10000 -->
<!--     ├── run_simulation<146> [Finished] [0]   ← retry succeeded -->
<!--     ... -->
<!-- ``` -->
<!---->
<!-- The failure, the handler decision, and the retry are all recorded in the provenance -- nothing is lost or hidden. -->
<!---->
<!-- ## Querying your results -->
<!---->
<!-- After the sweep finishes, you don't need to remember file paths or dig through directories. -->
<!-- AiiDA stores everything in a database that you can query with Python: -->
<!---->
<!-- ```python -->
<!-- from aiida import orm -->
<!---->
<!-- qb = orm.QueryBuilder() -->
<!-- qb.append(orm.CalcFunctionNode, filters={'label': 'run_simulation'}) -->
<!-- qb.append(orm.Float, filters={'label': 'variance_V'}, with_incoming='*') -->
<!---->
<!-- for node, in qb.iterall(): -->
<!--     calc = node.creator -->
<!--     F = calc.inputs.parameters.get_dict()['F'] -->
<!--     print(f"F = {F:.3f}  →  variance(V) = {node.value:.4e}") -->
<!-- ``` -->
<!---->
<!-- ```text -->
<!-- F = 0.035  →  variance(V) = 1.2345e-03 -->
<!-- F = 0.037  →  variance(V) = 2.8901e-03 -->
<!-- F = 0.039  →  variance(V) = 5.1234e-03 -->
<!-- ... -->
<!-- ``` -->
<!---->
<!-- This works whether the data was produced five minutes ago or five months ago. -->
<!-- You can filter, sort, and join across any combination of inputs, outputs, and process metadata. -->
<!---->
<!-- ## Full provenance -->
<!---->
<!-- Every piece of data in AiiDA is connected to a **provenance graph** that records exactly how it was produced: -->
<!---->
<!-- ```console -->
<!-- $ verdi node graph generate 146 -->
<!-- ``` -->
<!---->
<!-- <!-- TODO: Add a pre-generated provenance graph image here showing: -->
<!--      parameters → run_simulation → variance_V / mean_V -->
<!--      with the retry chain visible --> -->
<!---->
<!-- The graph answers questions that are otherwise impossible to reconstruct: -->
<!-- - *"What parameters produced this outlier?"* -->
<!-- - *"Did this result come from the original run or a retry?"* -->
<!-- - *"Which version of the simulation script was used?"* -->
<!---->
<!-- ## Sharing and reproducing results -->
<!---->
<!-- You can export any set of nodes -- including their full provenance -- to an archive file that a colleague can import into their own AiiDA database: -->
<!---->
<!-- ```console -->
<!-- $ verdi archive create sweep_results.aiida --all -->
<!-- $ verdi archive import sweep_results.aiida   # on another machine -->
<!-- ``` -->
<!---->
<!-- The imported data carries its complete history: every input, every intermediate step, every output. -->
<!-- Reproducibility is not an afterthought -- it is built into the data model. -->
<!---->
<!-- ## Extending a workflow -->
<!---->
<!-- Suppose you later realize you need an additional analysis step -- for example, a post-processing calculation that extracts a derived quantity from the raw output. -->
<!-- With WorkGraph, extending the workflow is just adding a task and connecting it: -->
<!---->
<!-- ```python -->
<!-- from aiida_workgraph import task -->
<!---->
<!-- @task -->
<!-- def post_process(raw_output): -->
<!--     """Derive a new quantity from the calculation output.""" -->
<!--     # ... your analysis code ... -->
<!--     return derived_quantity -->
<!---->
<!-- # Add the new step to an existing workflow — one line: -->
<!-- wg.add_task(post_process, raw_output=wg.tasks.calculate.outputs.result) -->
<!-- ``` -->
<!---->
<!-- No class hierarchies to subclass, no `define()` to override, no outline to restructure. -->
<!-- You compose tasks like functions -- and AiiDA tracks the provenance of the new step automatically. -->
<!---->
<!-- ## What this tutorial will teach you -->
<!---->
<!-- The modules below will take you from zero to everything shown on this page: -->
<!---->
<!-- | What you saw above | Where you'll learn it | -->
<!-- |---|---| -->
<!-- | The simulation code and its interface | {ref}`Module 0 <tutorial:module0>` | -->
<!-- | Running and tracking simulations | {ref}`Module 1 <tutorial:module1>` | -->
<!-- | Richer data types, calcfunctions, parameter sweeps | {ref}`Module 2 <tutorial:module2>` | -->
<!-- | Building workflows | {ref}`Module 3 <tutorial:module3>` | -->
<!-- | Error handlers, remote HPC, and more | Coming soon | -->
<!---->
<!-- Ready? Start with {ref}`Module 0 <tutorial:module0>` to meet the running example, then head to {ref}`Module 1 <tutorial:module1>`. -->
