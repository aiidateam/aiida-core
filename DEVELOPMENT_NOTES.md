# feat/support-aiida-resource-registry — Development Notes

Branch: `feat/support-aiida-resource-registry` (fresh from `main`)
Worktree: `.../aiida-core.worktrees/feat/support-aiida-resource-registry`
Related PR: [#6918](https://github.com/aiidateam/aiida-core/pull/6918) (draft, stale, on branch `cli-placeholders-interactive`)
Old branches: `cli-placeholders-interactive`, `config-cli-placeholders-interactive` — can be deleted once this branch is pushed.

## Goal

Enable YAML config files from the [aiida-resource-registry](https://github.com/aiidateam/aiida-resource-registry) to be used directly with `verdi computer setup --config <file-or-url>` and `verdi code create --config <file-or-url>`. These files contain:

1. **Jinja2 placeholders** like `{{ slurm_account }}` in fields like `prepend_text`
2. A **`metadata` section** describing each placeholder (display name, description, type, defaults, allowed options)

Without this feature, `--config` rejects such files because (a) `{{ ... }}` makes the YAML invalid when parsed literally, and (b) `metadata` is flagged as an unknown parameter.

## What's implemented

### New file: `src/aiida/cmdline/utils/template_config.py`

Core engine for template processing:

- `load_and_process_template(content_or_path, *, interactive, template_vars, is_content)` — single entry point, accepts either raw YAML content (`is_content=True`) or a file path / URL (`is_content=False`, the default)
- Internally delegates to `_process_content` which: parses YAML, extracts `metadata.template_variables`, detects Jinja2 vars, resolves them (interactively or via `template_vars`), renders, strips `metadata`, returns config dict
- `_load_content(file_path_or_url)` — loads raw content from local file or URL (lazy `import requests`)

### Modified: `src/aiida/cmdline/params/options/config.py`

- Added `_template_aware_yaml_provider`: always reads content to string first (whether from file handle, path, or URL), then delegates to `load_and_process_template(content, is_content=True)`. This fixes the `FileOrUrl` bug where template processing was silently skipped for file handles.
- Added `TemplateAwareConfigFileOption`: like `ConfigFileOption` but uses the template-aware provider
- `metadata` stripping happens only in the provider (not in `configuration_callback`)

### Modified: `src/aiida/cmdline/params/options/main.py`

- `CONFIG_FILE` now uses `TemplateAwareConfigFileOption` instead of `ConfigFileOption` (transparent upgrade, plain YAML still works identically)
- Added `TEMPLATE_VARS` option (`--template-vars`, eager, stores parsed JSON on `ctx._template_vars`)
- Added `_set_template_vars_callback` for parsing the JSON

### Modified: `src/aiida/cmdline/commands/cmd_computer.py`

- `computer_setup` now has `@options.TEMPLATE_VARS()` decorator (before `@options.CONFIG_FILE()`)
- Transport/scheduler handling is defensive: checks `hasattr(val, 'name')` before calling `.name` (when loaded from a template config, these come as plain strings, not entry point objects)

### Modified: `src/aiida/cmdline/commands/cmd_code.py`

- `setup_code` (legacy command) now has `@options.TEMPLATE_VARS()` decorator

### Modified: `src/aiida/cmdline/groups/dynamic.py`

- `create_options` now applies `@options.TEMPLATE_VARS()` alongside `@options.CONFIG_FILE()` — this gives all dynamically generated commands (including `verdi code create core.code.installed`, `core.code.portable`, `core.code.containerized`) template support automatically

### Modified: `src/aiida/cmdline/params/options/__init__.py`

- Exports `TEMPLATE_VARS` and `TemplateAwareConfigFileOption`

## Usage

```bash
# Interactive — prompts for each placeholder defined in metadata.template_variables
verdi computer setup --config path/to/daint.yaml

# Interactive with URL (e.g. from aiida-resource-registry)
verdi computer setup --config https://raw.githubusercontent.com/aiidateam/aiida-resource-registry/main/computers/cscs-daint.yaml

# Non-interactive
verdi computer setup --config daint.yaml --template-vars '{"slurm_account": "my_proj"}' -n

# Same for code creation (all subcommands get template support via dynamic.py)
verdi code create core.code.installed --config path/to/qe-pw.yaml
verdi code create core.code.installed --config qe-pw.yaml --template-vars '{"code_path": "/usr/bin/pw.x"}' -n
```

## Design decisions made

- **Single `--config` handles everything.** No separate `--template` option. Users don't need to know whether their YAML has placeholders.
- **Provider always works on content.** Reads to string first regardless of whether click passes a file handle or path. This avoids the `FileOrUrl` handle-vs-path fragility.
- **`metadata` stripped in one place only** — inside the provider / `_process_content`, not in `configuration_callback`.
- **Single `load_and_process_template` function** with `is_content` flag to dispatch between raw content and file path/URL loading.

## What's been completed

- [x] **Dependencies**: Verified `jinja2` (line 44) and `requests` (line 54) are already explicit runtime deps in `pyproject.toml`.
- [x] **Tests**: 25 unit tests for `template_config.py` (all public helpers + `load_and_process_template`). 3 CLI integration tests for `verdi computer setup --config` with templated YAML. 1 CLI integration test for `verdi code create core.code.installed --config` with templated YAML. 3 integration tests for the config option provider in `test_config.py`.
- [x] **End-to-end tests with real registry content**: Tests include realistic merlin7 computer-setup YAML and QE code YAML (including multi-line `{{ }}` expressions and AiiDA-style `{username}` placeholders).
- [x] **Error messages**: Verified: missing template vars, invalid YAML, non-dict YAML, file not found all produce clear `click.BadParameter` messages.
- [x] **Bug fixes**: (a) `StrictUndefined` added to `_render_template` so missing vars raise instead of rendering empty. (b) `_process_content` now checks `template_vars` before `interactive` (explicit vars take priority over prompting). (c) `test_from_config_url` fixed to return `io.BytesIO` matching real `urlopen` behavior.

## What still needs to be done

### Must-have before merging

- [ ] **`computer duplicate`**: Add `@options.TEMPLATE_VARS()` there too if it makes sense.
- [ ] **Real-world dogfooding**: Test interactively with actual aiida-resource-registry URLs against a running AiiDA profile.

### Nice-to-have

- [ ] Consider whether `--template-vars` should also support `--template-vars key=value` syntax (not just JSON)
- [ ] Eventually bake `TEMPLATE_VARS` into `TemplateAwareConfigFileOption` itself so commands just do `@options.CONFIG_FILE()` and get everything — no per-command `@options.TEMPLATE_VARS()` needed
- [ ] Documentation update for `verdi computer setup` and `verdi code create`
- [ ] Close old PR #6918 once new PR is opened

## File layout

```
src/aiida/cmdline/
├── commands/
│   ├── cmd_code.py              # @options.TEMPLATE_VARS() on setup_code (legacy)
│   └── cmd_computer.py          # @options.TEMPLATE_VARS() on computer_setup
├── groups/
│   └── dynamic.py               # @options.TEMPLATE_VARS() on all dynamic commands (code create *)
├── params/
│   └── options/
│       ├── __init__.py           # exports TEMPLATE_VARS, TemplateAwareConfigFileOption
│       ├── config.py             # TemplateAwareConfigFileOption, _template_aware_yaml_provider
│       └── main.py               # CONFIG_FILE, TEMPLATE_VARS definitions
└── utils/
    └── template_config.py        # NEW: load_and_process_template, _process_content, _load_content
```
