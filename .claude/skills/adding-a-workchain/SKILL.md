---
name: adding-a-workchain
description: Use when creating a new WorkChain to orchestrate CalcJobs, calcfunctions, or other WorkChains. Covers `define()` with inputs/outputs/outline, step methods, context usage, exit codes, and entry point registration.
---

# Adding a new WorkChain

New WorkChains are typically developed in **external plugin packages**.

## Steps

1. Create a class inheriting from `WorkChain`:
   ```python
   from aiida.engine import WorkChain, ToContext, if_, while_
   from aiida.orm import Int
   ```
2. Implement `define()` with inputs, outputs, an outline, and exit codes:
   ```python
   @classmethod
   def define(cls, spec):
       super().define(spec)
       spec.input('x', valid_type=Int)
       spec.input('y', valid_type=Int)
       spec.outline(
           cls.add,
           cls.inspect_add,
           cls.multiply,
           cls.finalize,
       )
       spec.output('result', valid_type=Int)
       spec.exit_code(400, 'ERROR_ADD_FAILED', message='The add step failed.')
   ```
3. Implement each outline step as a method:
   ```python
   def add(self):
       future = self.submit(AddCalculation, x=self.inputs.x, y=self.inputs.y)
       return ToContext(add_node=future)

   def inspect_add(self):
       if not self.ctx.add_node.is_finished_ok:
           return self.exit_codes.ERROR_ADD_FAILED
   ```
4. Pass state between steps via `self.ctx`. Await submitted processes with `ToContext(...)`.
5. Workflows *return* existing data nodes &mdash; they do **not** create new data nodes themselves.
   Only `CalcJob` / `calcfunction` can create data. If a step needs to produce new data, wrap the transformation in a `@calcfunction`.
6. Register as an entry point:
   ```toml
   [project.entry-points."aiida.workflows"]
   myplugin.addmultiply = "myplugin.workflows.addmultiply:AddMultiplyWorkChain"
   ```
7. Add tests using `run_get_node` against `presto`-compatible fixtures where possible.

## Relevant source

- Base class: `src/aiida/engine/processes/workchains/workchain.py`
- Context helpers: `src/aiida/engine/processes/workchains/context.py`
- Minimal example: `src/aiida/workflows/arithmetic/multiply_add.py`
