###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Run two independent, matched Pi processes and retain auditable evaluation artifacts.

Run from the repository root: uv run --no-sync python reports/workchain-vs-graph-eval/run_eval.py
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).resolve().parent
REL = Path('tests/engine/processes/workflow_eval')
STYLES = {
    'workchain': 'Use a conventional WorkChain subclass with define/spec.outline, self.ctx, '
    'while_/if_ as appropriate, self.submit and ToContext for child execution. '
    'Export the class as workflow. Do not import/use graph, task or graph IR APIs.',
    'graph': 'Use the public graph authoring layer: @graph and task(TrialWorkChain), '
    'task(FinalizeWorkChain) from aiida.engine. Express counters/comparisons/branches/loop '
    'in the @graph body, using inline orchestration and normal supported Python syntax. '
    'Export the decorated graph as workflow. Do not implement a new WorkChain or use low-level graph IR.',
}


def command(argv: list[str], cwd: Path = ROOT, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=cwd, check=True, text=True, capture_output=True, **kwargs)


def save_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2) + '\n')


def snapshot(workspace: Path) -> dict[str, str]:
    tracked = command(['git', 'ls-files', '-z']).stdout.split('\0')
    extra = command(
        ['git', 'ls-files', '--others', '--exclude-standard', '-z', '--', 'src', 'tests', 'docs', '.agents']
    ).stdout.split('\0')
    hashes = {}
    for name in sorted(set(tracked + extra)):
        if not name or name.startswith(('reports/', '.benchmarks/')):
            continue
        source = ROOT / name
        if not source.is_file() and not source.is_symlink():
            continue
        destination = workspace / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            destination.symlink_to(os.readlink(source))
        else:
            shutil.copy2(source, destination)
            hashes[name] = hashlib.sha256(source.read_bytes()).hexdigest()
    (workspace / '.venv').symlink_to(ROOT / '.venv', target_is_directory=True)
    package = workspace / REL
    package.mkdir(parents=True, exist_ok=True)
    (package / '__init__.py').write_text('')
    for filename in ('collaborators.py', 'test_acceptance.py'):
        shutil.copy2(REPORT / filename, package / filename)
    command(['git', 'init', '-q'], workspace)
    command(['git', 'add', '.'], workspace)
    command(
        [
            'git',
            '-c',
            'user.name=Eval',
            '-c',
            'user.email=eval@localhost',
            'commit',
            '-qm',
            'Identical starting snapshot',
        ],
        workspace,
    )
    return hashes


def run_arm(arm: str, workspace: Path, provider: str, model: str, thinking: str) -> dict:
    output = REPORT / arm
    output.mkdir()
    prompt = (REPORT / 'task.md').read_text() + '\n## Assigned style\n\n' + STYLES[arm] + '\n'
    (output / 'prompt.md').write_text(prompt)
    env = os.environ.copy()
    for key in list(env):
        if key.startswith('PI_SESSION'):
            del env[key]
    env.update(
        PYTHONPATH=str(workspace / 'src') + ':' + str(workspace),
        UV_PROJECT_ENVIRONMENT=str(ROOT / '.venv'),
        AIIDA_PATH=str(output / 'aiida'),
    )
    argv = [
        'pi',
        '--print',
        '--mode',
        'json',
        '--provider',
        provider,
        '--model',
        model,
        '--thinking',
        thinking,
        '--no-extensions',
        '--no-mcp',
        '--no-prompt-templates',
        '--tools',
        'read,bash,edit,write',
        '--session-id',
        str(uuid.uuid4()),
        '--session-dir',
        str(output / 'sessions'),
        prompt,
    ]
    save_json(
        output / 'invocation.json',
        {
            'argv': argv,
            'cwd': str(workspace),
            'environment_overrides': {key: env[key] for key in ('PYTHONPATH', 'UV_PROJECT_ENVIRONMENT', 'AIIDA_PATH')},
        },
    )
    started = time.monotonic()
    started_utc = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    timed_out = False
    with (output / 'events.jsonl').open('w') as stdout, (output / 'stderr.log').open('w') as stderr:
        process = subprocess.Popen(
            argv, cwd=workspace, env=env, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, start_new_session=True
        )
        try:
            returncode = process.wait(timeout=900)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                returncode = process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                returncode = process.wait()
    elapsed = time.monotonic() - started
    usage = {'input': 0, 'output': 0, 'cacheRead': 0, 'cacheWrite': 0, 'totalTokens': 0}
    cost = 0.0
    turns = 0
    tool_calls = 0
    errors = []
    final = []
    for line in (output / 'events.jsonl').read_text().splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            errors.append('Non-JSON stdout record: ' + line[:200])
            continue
        if event.get('type') != 'message_end':
            continue
        message = event.get('message', {})
        if message.get('role') != 'assistant':
            continue
        turns += 1
        for key in usage:
            usage[key] += message.get('usage', {}).get(key, 0)
        cost += message.get('usage', {}).get('cost', {}).get('total', 0)
        for content in message.get('content', []):
            if content.get('type') == 'toolCall':
                tool_calls += 1
            if content.get('type') == 'text':
                final.append(content['text'])
        if message.get('errorMessage'):
            errors.append(message['errorMessage'])
    (output / 'assistant-text.md').write_text('\n\n'.join(final))
    integrity = {
        name: (workspace / REL / name).read_bytes() == (REPORT / name).read_bytes()
        for name in ('collaborators.py', 'test_acceptance.py')
    }
    # Restore evaluator-owned tests/collaborators before independent validation.
    for filename in integrity:
        shutil.copy2(REPORT / filename, workspace / REL / filename)
    validation_argv = [
        'uv',
        'run',
        '--no-sync',
        'pytest',
        '--broker-backend=none',
        '-q',
        str(REL),
        '--junitxml=' + str(output / 'validation.xml'),
    ]
    validation_started = time.monotonic()
    with (output / 'validation.log').open('w') as log:
        try:
            validation = subprocess.run(
                validation_argv, cwd=workspace, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=240, check=False
            )
            validation_returncode = validation.returncode
        except subprocess.TimeoutExpired:
            validation_returncode = 124
    command(['git', 'add', '-N', '.'], workspace)
    (output / 'solution.patch').write_text(command(['git', 'diff', '--binary', 'HEAD'], workspace).stdout)
    shutil.copytree(workspace / REL, output / 'submission', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    metrics = {
        'arm': arm,
        'provider': provider,
        'model': model,
        'thinking': thinking,
        'started_utc': started_utc,
        'wall_seconds': elapsed,
        'timed_out': timed_out,
        'agent_returncode': returncode,
        'usage': usage,
        'provider_reported_cost_usd': cost,
        'assistant_messages': turns,
        'tool_calls': tool_calls,
        'errors': errors,
        'fixed_files_unchanged': integrity,
        'validation_command': validation_argv,
        'validation_returncode': validation_returncode,
        'validation_seconds': time.monotonic() - validation_started,
        'workspace': str(workspace),
        'git_status': command(['git', 'status', '--short'], workspace).stdout,
    }
    save_json(output / 'metrics.json', metrics)
    return metrics


def main() -> None:
    provider = os.environ.get('PI_PROVIDER', 'openai-codex')
    model = os.environ.get('PI_MODEL', 'gpt-6.1-sol')
    thinking = os.environ.get('PI_REASONING_LEVEL', 'medium')
    base = Path(tempfile.mkdtemp(prefix='aiida-paired-workflow-eval-'))
    workspaces = {}
    manifests = {}
    for arm in STYLES:
        workspaces[arm] = base / arm
        workspaces[arm].mkdir()
        manifests[arm] = snapshot(workspaces[arm])
    assert manifests['workchain'] == manifests['graph']
    save_json(REPORT / 'baseline-manifest.json', manifests['workchain'])
    save_json(
        REPORT / 'run.json',
        {
            'baseline_commit': command(['git', 'rev-parse', 'HEAD']).stdout.strip(),
            'baseline_status': command(['git', 'status', '--short']).stdout,
            'pi_version': command(['pi', '--version']).stdout.strip(),
            'provider': provider,
            'model': model,
            'thinking': thinking,
            'workspace_root': str(base),
            'paired_concurrent': True,
            'note': 'Snapshot includes current tracked working-tree contents and untracked source/tests/docs. '
            'No parent conversation/session supplied. No report folders copied. Shared installed dependencies only.',
        },
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = {
            arm: pool.submit(run_arm, arm, workspace, provider, model, thinking)
            for arm, workspace in workspaces.items()
        }
        results = {arm: future.result() for arm, future in futures.items()}
    save_json(REPORT / 'results.json', results)
    print(json.dumps(results, indent=2), flush=True)


if __name__ == '__main__':
    main()
