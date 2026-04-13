---
name: adding-a-data-type
description: Use when creating a new Data node subclass (derived from `Data`, `ArrayData`, `SinglefileData`, etc.) for aiida-core or an external plugin. Covers base class selection, pre/post-storage mutability, and entry point registration.
---

# Adding a new Data node type

New data types are typically developed in **external plugin packages** via [aiida-plugin-cutter](https://github.com/aiidateam/aiida-plugin-cutter), not inside `aiida-core` itself.

## Steps

1. Create a new class inheriting from the most appropriate base:
   - `Data` &mdash; generic base, store arbitrary attributes plus repository files.
   - `ArrayData` &mdash; numpy arrays.
   - `SinglefileData` &mdash; a single file in the repository.
   - `Dict`, `List`, `Str`, `Int`, `Float`, `Bool` &mdash; simple value wrappers.
2. Override the constructor to accept the domain-specific inputs and validate them.
3. Store payload via `self.base.attributes.set()` and/or `self.base.repository.put_object_from_*()` **before** the node is stored.
   After `node.store()`, attributes are immutable (only extras can change).
4. Expose typed accessors (`@property`) for user-facing fields.
5. Register as an entry point in `pyproject.toml`:
   ```toml
   [project.entry-points."aiida.data"]
   myplugin.mydata = "myplugin.data.mydata:MyData"
   ```
6. Add tests covering construction, round-trip (store &rarr; load), and error cases.
   Use `@pytest.mark.presto` where possible so the tests run without PostgreSQL / RabbitMQ.

## Relevant source

- Base: `src/aiida/orm/nodes/data/data.py`
- Array example: `src/aiida/orm/nodes/data/array/array.py`
- Entry point system: `src/aiida/plugins/factories.py`
