---
name: adding-a-calcjob
description: Use when creating a new CalcJob plugin that wraps an external executable. Covers the `define()` method, `prepare_for_submission()`, exit codes, entry point registration, and the companion Parser plugin.
---

# Adding a new CalcJob plugin

New CalcJob plugins are typically developed in **external plugin packages** via [aiida-plugin-cutter](https://github.com/aiidateam/aiida-plugin-cutter).

## Steps

1. Create a class inheriting from `CalcJob`:
   ```python
   from aiida.engine import CalcJob
   from aiida.orm import Dict, StructureData
   from aiida.common.datastructures import CalcInfo, CodeInfo

   class MyCalculation(CalcJob):
       ...
   ```
2. Implement `define()` to declare inputs, outputs, and exit codes:
   ```python
   @classmethod
   def define(cls, spec):
       super().define(spec)
       spec.input('parameters', valid_type=Dict)
       spec.input('structure', valid_type=StructureData)
       spec.output('result', valid_type=Dict)
       spec.exit_code(300, 'ERROR_MISSING_OUTPUT', message='Output file not found.')
   ```
3. Implement `prepare_for_submission(folder)`:
   - Write input files into `folder`.
   - Build and return a `CalcInfo` with the `CodeInfo` list, retrieve list, and local-copy / remote-copy lists.
4. Register as an entry point in `pyproject.toml`:
   ```toml
   [project.entry-points."aiida.calculations"]
   myplugin.mycalc = "myplugin.calculations.mycalc:MyCalculation"
   ```
5. Write a companion `Parser` plugin (see examples in `src/aiida/parsers/`) and register it under `aiida.parsers`.
6. Add tests: a minimal `prepare_for_submission` unit test plus an end-to-end test using the standard AiiDA test fixtures.

## Exit codes

Define explicit, numbered exit codes in `define()` for every expected failure mode.
WorkChains rely on exit codes to decide whether a step should retry, abort, or handle the failure gracefully.

## Relevant source

- Base class: `src/aiida/engine/processes/calcjobs/calcjob.py`
- File copying / submission / retrieval: `src/aiida/engine/daemon/execmanager.py`
- Minimal example: `src/aiida/calculations/arithmetic/add.py`
