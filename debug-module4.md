# Debugging module 4 timeout

The timeout hits the `launch_shell_job(load_code('gsrd@slurm-ssh'), ...)` cell.
To isolate, reproduce the steps manually.

## 1. Start the SLURM container

```fish
docker run -d --name slurm-tutorial -p 5001:22 xenonmiddleware/slurm:17
```

## 2. Install gsrd inside the container

```fish
# Copy uv binary into the container
docker cp (realpath (which uv)) slurm-tutorial:/usr/local/bin/uv

# Create venv + install gsrd (--only-binary numpy because container has no C compiler)
docker exec slurm-tutorial bash -c "\
  export UV_PYTHON_INSTALL_DIR=/opt/uv-python && \
  uv venv /opt/gsrd --python 3.12 && \
  uv pip install --python /opt/gsrd/bin/python --only-binary numpy \
    'gsrd @ https://github.com/aiidateam/gsrd/archive/refs/heads/main.zip' && \
  chmod -R a+rX /opt/gsrd /opt/uv-python"
```

Verify it works:

```fish
docker exec slurm-tutorial /opt/gsrd/bin/gsrd --help
```

## 3. Set up SSH

The container's SSH user is `xenon`, password `javagat`. The pre-generated
key is in `.github/config/slurm_rsa`.

```fish
set REPO_ROOT (git rev-parse --show-toplevel)
cp $REPO_ROOT/.github/config/slurm_rsa ~/.ssh/slurm_rsa
chmod 600 ~/.ssh/slurm_rsa
```

Check if the SSH config entry already exists:

```fish
grep -c "AiiDA tutorial" ~/.ssh/config
```

If it prints `0`, add it:

```fish
printf '\n# --- AiiDA tutorial (slurm-ssh) ---
Host slurm-ssh
    HostName localhost
    User xenon
    Port 5001
    IdentityFile ~/.ssh/slurm_rsa
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR\n' >> ~/.ssh/config
```

Test raw SSH works:

```fish
ssh slurm-ssh echo "SSH OK"
```

## 4. Set up AiiDA computer + code

Use whatever tutorial profile you have (or `verdi presto`).

```fish
# Register the computer
verdi computer setup \
    --label slurm-ssh \
    --hostname slurm-ssh \
    --transport core.ssh_async \
    --scheduler core.slurm \
    --work-dir '/home/{username}/workdir' \
    --mpiprocs-per-machine 1 \
    --non-interactive

# Configure transport (try asyncssh first, fall back to openssh if needed)
verdi computer configure core.ssh_async slurm-ssh --safe-interval 0 --non-interactive

# Test the connection
verdi computer test slurm-ssh
```

Register the code:

```fish
verdi code create core.code.installed \
    --label gsrd \
    --computer slurm-ssh \
    --filepath-executable /opt/gsrd/bin/gsrd \
    --default-calc-job-plugin core.shell \
    --non-interactive
```

## 5. Run the job manually (Python)

```fish
uv run python -c "
from pathlib import Path
from aiida import load_profile
from aiida.orm import load_code, load_computer

load_profile()

# Speed up polling
comp = load_computer('slurm-ssh')
comp.set_minimum_job_poll_interval(1)

from aiida_shell import launch_shell_job

input_path = Path('docs/source/tutorials/include/input.yaml').resolve()

print('Launching...')
results, node = launch_shell_job(
    load_code('gsrd@slurm-ssh'),
    arguments='{input}',
    nodes={'input': input_path},
    outputs=['results.npz'],
)

print(f'PK:     {node.pk}')
print(f'State:  {node.process_state}')
print(f'Exit:   {node.exit_status}')
print(f'Comp:   {node.computer.label}')
"
```

## 6. If it hangs, debug the transport layer

In a separate terminal while step 5 is running:

```fish
# Check if the job was actually submitted to SLURM
docker exec slurm-tutorial squeue -u xenon

# Check if there are any jobs at all
docker exec slurm-tutorial squeue

# Check SLURM controller status
docker exec slurm-tutorial scontrol show node

# Check if files were uploaded
docker exec slurm-tutorial ls -la /home/xenon/workdir/

# Check SLURM logs
docker exec slurm-tutorial cat /var/log/slurm-llnl/slurmctld.log | tail -30
```

## 7. Cleanup

```fish
docker stop slurm-tutorial && docker rm slurm-tutorial

# Remove SSH config entry
# (manually remove the "AiiDA tutorial (slurm-ssh)" block from ~/.ssh/config)

# Remove AiiDA computer (if you want a clean slate)
verdi computer delete slurm-ssh
```
