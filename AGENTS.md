# AGENTS.md - AI Coding Assistant Guide for AiiDA Core

This file provides context for AI coding assistants (Claude Code, GitHub Copilot, etc.) working on the `aiida-core` codebase.

**IMPORTANT**: Always use the project's tooling. Use `uv run` to run Python, tests, and tools (e.g., `uv run pytest`, `uv run pre-commit`). Never use bare `python` or `pip`. Check `pyproject.toml` and `.pre-commit-config.yaml` for the full configuration.

## Project overview

AiiDA is a workflow manager for computational science with a strong focus on provenance, performance, and extensibility.
It is written in Python (see `pyproject.toml` for supported versions) and uses PostgreSQL/SQLite for metadata storage, [`disk-objectstore`](https://github.com/aiidateam/disk-objectstore) for file storage, and RabbitMQ as a message broker.

## Key design concepts

- **Provenance:** all data and computations are tracked as nodes in a directed acyclic graph (DAG). Nodes are immutable once stored, except extras (always mutable) and `ProcessNode._updatable_attributes` (process state, exit status, checkpoint, etc., mutable until `seal()`).
- **Process/Node duality:** processes (`CalcJob`, `WorkChain`, `calcfunction`, `workfunction`) define *how* to run; process nodes record *that* something ran.
- **CREATE vs RETURN links:** calculations *create* new data nodes; workflows *return* existing data nodes. Workflows orchestrate but don't create data themselves.
- **Don't break provenance:** never circumvent the link system or modify stored nodes in ways that would break the DAG.
- **Public API:** anything importable from a second-level package (e.g., `from aiida.orm import ...`) is public API with deprecation guarantees. Deeper internal modules may change without notice.
- **Plugin system:** entry points (`pyproject.toml` `[project.entry-points]`) allow extending AiiDA with new calculation types, data types, schedulers, transports, and storage backends.
- **Daemon signal handling:** the daemon captures `SIGINT`/`SIGTERM` for graceful shutdown. Subprocesses in daemon code must pass `start_new_session=True`.

### Process / Node duality

Each process class has a corresponding node class that records its execution:

| Process class | Node class | Link types |
|--------------|------------|------------|
| `@calcfunction` | `CalcFunctionNode` | INPUT_CALC → CREATE |
| `CalcJob` | `CalcJobNode` | INPUT_CALC → CREATE |
| `@workfunction` | `WorkFunctionNode` | INPUT_WORK → RETURN/CALL |
| `WorkChain` | `WorkChainNode` | INPUT_WORK → RETURN/CALL |

## Code style

Code style is enforced via **pre-commit hooks** (`.pre-commit-config.yaml`). Always run `uv run pre-commit` before pushing.
Formatting: `ruff`. Type checking: `mypy`. Write new code following ruff conventions with proper type hints.
Typing is progressively strict: modules listed under `[[tool.mypy.overrides]]` in `pyproject.toml` require full annotations, and a module joins that list once it is fully typed.
Docstrings: Sphinx-style (`:param:`, `:return:`, `:raises:`), types in annotations not docstrings.
Comments and docstrings explain *why*, not *what*.
New source files should include the standard copyright header (copy from any existing `.py` file).
In `cmdline/`: delay `aiida` imports to function level (keeps `verdi` CLI responsive, see the `adding-a-cli-command` skill).
See the `linting-and-ci` skill for details.

### Error handling

Use `aiida.common.exceptions` for AiiDA-specific exceptions, `aiida.common.warnings` for non-fatal issues.
Assign exception messages to a variable before raising: `msg = f'...'; raise TypeError(msg)`

## Design principles

Useful frameworks:

- **SOLID:** single responsibility, open/closed, Liskov, interface segregation, dependency inversion.
- **GRASP:** assign each responsibility to the class that already holds the information; low coupling, high cohesion.
- **CUPID:** composable, does one thing well, predictable, idiomatic, domain-based.

Design patterns are deliberately not listed here.
Where a problem genuinely calls for one, fetch [refactoring.guru/design-patterns](https://refactoring.guru/design-patterns) and work from it rather than from memory.
Don't force code into a pattern it does not need.

### Heuristics

- **Reuse what exists:** search the codebase before writing a helper, and call `super()` rather than restating base-class logic.
- **YAGNI:** build what is needed now, not what might be needed later.
- **Redesign rather than document:** logic needing a paragraph of comments to follow is too complex.
- **Chesterton's fence:** don't remove or rewrite code whose purpose you haven't established.
- **Changing observable behaviour is a breaking change** (Hyrum's law), even where the signature stays the same.
- **DRY, but rule of three:** duplication is cheaper than the wrong abstraction, so wait for the third occurrence.
- **Principle of least astonishment:** where two designs are defensible, pick the one the name already implies.

### API design

- **Flat over nested:** re-export at package level. File layout is an implementation detail.
- **Keep dependencies acyclic:** needing a `TYPE_CHECKING` guard or a function-level import to break a cycle means the layering is wrong.
- **Don't repeat context in names:** `kpoints.set_mesh()`, not `kpoints.set_kpoints_mesh()`.
- **Keyword-only (`*`) arguments** for several or same-typed parameters, and always for booleans.
- **Progressive disclosure:** simple things simple, complex things possible. Don't front-load complexity.
- **Pit of success:** safe defaults, unsafe behaviour behind explicit opt-in. Make wrong code look wrong.
- **Permissive at the boundary, strict inside:** parse messy external input at the edge; internal code passes domain types, not generic containers.
- **Fail fast:** reject bad input where it enters, naming the offending value.
- **Prefer pure functions:** no side effects, no mutation of inputs, same output for the same arguments.
- **Minimize mutable state:** return new values over mutating inputs, and a copy or read-only view over an alias to your own container.
- **No global mutable state:** keyword arguments with defaults, state on a class instance, or `ContextVar`.
- **Raise exceptions rather than returning `None` or a sentinel;** status values are for failures that must persist or cross a process boundary.
- **Context managers** for acquire/release and setup/teardown, since cleanup the caller must remember gets skipped.

### Object-oriented design

- **Composition over inheritance:** delegate to a collaborator; inheritance means is-a, and using it to share code risks coupling conceptually unrelated classes.
- **Depend on abstractions:** shape the interface around what callers need, so it does not simply mirror one concrete implementation.
- **Prefer `Protocol`,** where no inheritance should be imposed; use an **ABC** when the contract needs runtime enforcement or shared base behaviour.
- **Liskov substitution:** never narrow a parameter type in a subclass override, and mark overrides with `@override`.
- **Encapsulate:** needing another object's underscore-prefixed members means the API is missing something.
- **Adapt at the boundary:** conversion into our abstractions belongs on the incoming type or in a dedicated adapter, not spread through the consuming code.
- **Command-query separation:** a method either does something or answers something, not both.
- **Law of Demeter:** talk to immediate collaborators, since `a.b.c.d()` couples the caller to the whole chain.
- **Overload an operator** only when a reader can predict what it does from the types involved.
- **Keep attribute access cheap:** attribute syntax reads as free, so an expensive lookup belongs behind a method or a `cached_property`.

### Types

- **Annotate as you write:** a suspiciously broad return type signals a missing abstraction.
- **The signature is the contract:** types and names alone should convey what to pass and what comes back.
- **Avoid `Any`:** it is contagious, and unlike `type: ignore` it leaves no marker that a decision was made.
- **Every `type: ignore` is a decision:** fix the design or record the debt.
- **Make illegal states unrepresentable:** a type should admit exactly the valid values and nothing more, so invalid states and calls cannot be written.
- **`TypedDict`/`dataclass` over plain dicts:** a dict key typo is silent; a field name typo is a type error.
- **`Literal`/`Enum` over bare strings** for constrained value sets. `assert_never` for exhaustiveness.
- **Sensible default values over `None` as a default,** where one exists: `None` hides the real default and widens the type for every caller.
- **Postel's law:** accept broad types (`Sequence`, `Mapping`), return narrow ones (`list`, `dict`).
- **`TypeAlias`** to name any complex type that appears more than once.
- **Generics (`TypeVar`)** to carry type information across function boundaries.
- **`@overload`** to narrow return types statically, **`@singledispatch`** over `isinstance` chains.
- **`Final`** for constants, **`@final`** for classes that must not be subclassed.
- **`TypeGuard`/`TypeIs`** for narrowing in validation functions, **`Self`** for fluent APIs, **`ParamSpec`** to carry signatures through decorators.
- **A type that is hard to write** is a sign the design needs work, not that the annotation needs loosening.

### Python idioms

- **Guard clauses** over deep nesting: edge case first, main path at low indentation.
- **`is None` / `is not None`** over truthiness for optionals, and `isinstance()` rather than `type()`.
- **No mutable default arguments:** default `None`, assign in the body.
- **Modern stdlib idioms:** `pathlib.Path` over `os.path`, f-strings over `.format()`/`%`.
- **Catch specific exceptions,** never bare `except:` or blanket `except Exception:`, which swallow `KeyboardInterrupt` and genuine bugs.
- **`contextlib.suppress(...)`** over `except ...: pass`.
- **Preserve the cause when re-raising:** `raise ValueError(msg) from err`.
- **Comprehensions** over `map`/`filter` with lambdas, and `itertools` and generators over large materialized lists.
- **Let the container do the work:** `defaultdict`, `Counter`, `deque`, `dict.get(key, default)` over hand-written equivalents.
- **`functools.cached_property` / `lru_cache`** for expensive computed values.
- **Timezone-aware datetimes:** `datetime.now(tz=timezone.utc)`, never naive `datetime.now()`.
- **Never call blocking I/O from async code:** it stalls the event loop, and in the daemon every other process with it.

## Claude Code skills

The following Claude Code skills (under `.claude/skills/`) provide task-specific guidance. Listed here as a reference for all agents:

- `adding-a-cli-command`: `verdi` subcommands and import-time constraints
- `adding-dependencies`: third-party dependency checklist
- `architecture-overview`: codebase structure, key files, ABCs
- `commit-conventions`: branching, commit style, PR requirements
- `debugging-processes`: diagnosing failed or stuck processes and the daemon
- `deprecating-api`: deprecation warnings and removal timeline
- `linting-and-ci`: pre-commit, CI checks
- `running-tests`: pytest cheatsheet, plugins, fixtures
- `writing-and-building-docs`: documentation style and building
- `writing-tests`: test philosophy, markers, parametrization

## AI assistant guidelines

When working on this codebase:

- **Read before writing**: Always read existing code and understand patterns before proposing changes.
  Don't guess how AiiDA works.
- **Match existing style**: Follow patterns you see in surrounding code.
- **Don't modify code you weren't asked to change**: If fixing a bug in function A, don't also "improve" functions B and C nearby.
- **Don't add docstrings/type hints to unchanged code**: Only add to code you're actively modifying.

## Key dependencies

Key dependencies (all under [github.com/aiidateam](https://github.com/aiidateam)): `plumpy` (process state machine), `kiwipy` (message broker interface), `disk-objectstore` (file storage).
