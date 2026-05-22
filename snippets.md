# API Summary and Dogfooding Commands

## Current API

Two new CLI options work together on `verdi computer setup`, `verdi code create *`, and the legacy `verdi code setup`:

- `--config <file-or-url>` (existing option, now template-aware): accepts plain YAML or Jinja2-templated YAML. If templates are detected and the command runs interactively, prompts the user for each variable defined in the `metadata.template_variables` section.
- `--template-vars '<json>'` (new option): pre-supplies template variable values as a JSON object. Skips interactive prompting for those variables. Required in non-interactive mode (`-n`) when the config has templates.

The `metadata` section (used by AiiDAlab for tooltips and variable definitions) is always stripped before the config is applied. Plain YAML files without any templates or metadata continue to work identically.

## Dogfooding commands (real aiida-resource-registry files)

### Computer setup

```fish
# Interactive: merlin7 CPU (prompts for label, slurm_partition, multithreading)
verdi computer setup --config https://raw.githubusercontent.com/aiidateam/aiida-resource-registry/main/merlin7.psi.ch/cpu/computer-setup.yml

# Non-interactive: merlin7 CPU (all vars provided)
verdi computer setup -n \
  --config https://raw.githubusercontent.com/aiidateam/aiida-resource-registry/main/merlin7.psi.ch/cpu/computer-setup.yml \
  --template-vars '{"label": "merlin7-cpu", "slurm_partition": "daily", "multithreading": "nomultithread"}'

# Interactive: eiger MC (prompts for label, slurm_partition, slurm_account, multithreading)
# Note: slurm_account has no default, so prompt is mandatory for that one
verdi computer setup --config https://raw.githubusercontent.com/aiidateam/aiida-resource-registry/main/eiger.cscs.ch/mc/computer-setup.yml

# Non-interactive: eiger MC
verdi computer setup -n \
  --config https://raw.githubusercontent.com/aiidateam/aiida-resource-registry/main/eiger.cscs.ch/mc/computer-setup.yml \
  --template-vars '{"label": "eiger-mc", "slurm_partition": "normal", "slurm_account": "my_project", "multithreading": "nomultithread"}'
```

### Code creation (via dynamic command group)

```fish
# Interactive: merlin7 QE code (prompts for code_binary_name from list: pw, pp, ph, dos, projwfc, xspectra)
# NOTE: requires computer "merlin7-cpu" to already exist
verdi code create core.code.installed \
  --config https://raw.githubusercontent.com/aiidateam/aiida-resource-registry/main/merlin7.psi.ch/cpu/codes/QuantumESPRESSO-7.4.yml \
  --computer merlin7-cpu

# Non-interactive: merlin7 QE pw code
verdi code create core.code.installed -n \
  --config https://raw.githubusercontent.com/aiidateam/aiida-resource-registry/main/merlin7.psi.ch/cpu/codes/QuantumESPRESSO-7.4.yml \
  --template-vars '{"code_binary_name": "pw"}' \
  --computer merlin7-cpu

# Plain YAML (no templates): merlin7 phonopy -- works unchanged
# NOTE: requires computer "merlin7-cpu" to already exist
verdi code create core.code.containerized -n \
  --config https://raw.githubusercontent.com/aiidateam/aiida-resource-registry/main/merlin7.psi.ch/cpu/codes/phonopy-2.20.0.yml \
  --computer merlin7-cpu
```

### Error case testing

```fish
# Missing template vars in non-interactive mode -- should give clear error
verdi computer setup -n \
  --config https://raw.githubusercontent.com/aiidateam/aiida-resource-registry/main/eiger.cscs.ch/mc/computer-setup.yml

# Partial template vars (missing slurm_account) -- should error on missing var
verdi computer setup -n \
  --config https://raw.githubusercontent.com/aiidateam/aiida-resource-registry/main/eiger.cscs.ch/mc/computer-setup.yml \
  --template-vars '{"label": "eiger-mc", "slurm_partition": "normal"}'
```

## Offline dogfood results (template engine only, no AiiDA profile needed)

All four real-world registry files parsed successfully through `load_and_process_template`:

| File | Template vars | AiiDA placeholders preserved | metadata stripped |
|------|--------------|------------------------------|-------------------|
| merlin7 computer-setup.yml | label, slurm_partition, multithreading | `{username}` | yes |
| eiger computer-setup.yml | label, slurm_partition, slurm_account, multithreading | `{username}`, `{tot_num_mpiprocs}` | yes |
| merlin7 QE code (pw) | code_binary_name (multi-line `{{ }}`) | -- | yes |
| merlin7 phonopy (plain) | none | `{image_name}` | n/a (no metadata) |
