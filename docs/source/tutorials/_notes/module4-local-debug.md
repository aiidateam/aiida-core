# Module 4 local debug commands

Use these against the running `slurm-ssh` container to figure out where the `launch_shell_job` round-trip is spending its time. Run them in the tutorial profile (`source ~/.aiidarc` or `verdi profile setdefault tutorial-...`) from a shell with `uv run` available.

## 1. Container & SSH sanity

```fish
# Container is up?
docker ps --filter name=slurm-ssh

# SSH itself works (no AiiDA in the way)?
ssh slurm-ssh hostname
ssh slurm-ssh whoami
ssh slurm-ssh ls /opt/gsrd/bin/gsrd
```

If any of those fail, the problem is below AiiDA — fix that first.

## 2. SLURM inside the container

```fish
# Daemon up? Partition visible?
ssh slurm-ssh sinfo
ssh slurm-ssh squeue

# Submit a trivial job by hand and time it end-to-end:
ssh slurm-ssh bash -c '"sbatch --wrap=\"sleep 2; echo done\" --output=/tmp/test.out"'
ssh slurm-ssh squeue          # may need to run a couple of times until empty
ssh slurm-ssh cat /tmp/test.out
```

If `sbatch → squeue empty → output file present` takes more than ~10s, the SLURM scheduler tick inside `xenonmiddleware/slurm:17` is the bottleneck. Note the rough wall time.

## 3. AiiDA against the container

```fish
# Print the full traceback for `verdi computer test`. If it's still just
# the "[FAILED]: Error while trying to connect to the computer" warning
# without a stack, drop to the Python-level test below.
uv run verdi -v debug computer test slurm-ssh --print-traceback

# Python-level fallback that ALWAYS raises with a real traceback if the
# transport refuses to open:
uv run python -c '
from aiida import load_profile
from aiida.orm import load_computer
load_profile()
comp = load_computer("slurm-ssh")
with comp.get_transport() as t:
    print("connected:", t.whoami())
    print("listdir:", t.listdir("/"))
'

# Time a single launch_shell_job round-trip:
time uv run python -c '
from pathlib import Path
from aiida import load_profile
from aiida.orm import load_code
from aiida_shell import launch_shell_job

load_profile()
input_path = Path("docs/source/tutorials/include/input.yaml").resolve()
_, node = launch_shell_job(
    load_code("gsrd@slurm-ssh"),
    arguments="{input}",
    nodes={"input": input_path},
    outputs=["results.npz"],
)
print(f"Process PK:  {node.pk}")
print(f"Exit status: {node.exit_status}")
'
```

That is exactly what the failing notebook cell does, just outside the cell. If it finishes in (say) 90s, the notebook timeout was the only problem and the bump to `timeout: 600` in `module4.md` frontmatter is enough. If it hangs much longer than the SLURM hand-test in §2, AiiDA's polling loop is the culprit.

## 4. If the AiiDA call is the slow one

Watch the daemon-less inline state machine in real time. Pull the verbose logs:

```fish
# In one shell, follow the running process:
uv run verdi process list -a -p 1
uv run verdi process status <PK>

# In another, follow what state the CalcJob is in. The interesting transition
# is Submitted -> Waiting -> Retrieving. If it sits in Waiting much longer
# than the SLURM hand-test, the scheduler-poll loop is too lazy.
uv run verdi process watch <PK>
```

Knobs we already set (already in `module4.md`):

- `--safe-interval 0` on `verdi computer configure`
- `slurm_computer.set_minimum_job_poll_interval(1)` in the hidden cell

If polling is still the issue, two more things to try:

```python
# Even shorter poll interval (default minimum is 10s; we already set 1):
slurm_computer.set_minimum_job_poll_interval(0)

# AiiDA-side: lower the CalcJob "intermediate step" interval. This is a
# global config, so reset after the tutorial:
from aiida.manage.configuration import get_config
get_config().set_option("transport.task_retry_initial_interval", 1)
get_config().set_option("transport.task_maximum_attempts", 3)
```

## 5. Cleanup

```fish
docker stop slurm-ssh
```

Report back: §2 hand-submit wall time, §3 `time ... launch_shell_job` wall time, and §4 process state durations if it never finishes. That triangulates whether the slowdown is SLURM, SSH, or AiiDA's polling.
