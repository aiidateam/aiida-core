###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Orchestrate the isolated two-arm restart evaluation (NO agent runs on import).

Each arm gets a FRESH `pi` OS subprocess (`--mode json`, explicit
`--session-dir` + `--session-id`, never `--continue`/`--resume`/`--fork`),
a FRESH isolated git worktree at the same repository revision, and an identical
prompt except for the allowed implementation method. The harness:

1. records model/thinking/tools/timeout/token-cap/revision and `pi --version`;
2. creates one detached worktree per arm plus a fresh `eval-scratch-<arm>/`
   cwd containing ONLY the shared task files: the tracked `grading/` grader
   source and any root `reports/` checkout are physically removed from each
   fresh worktree (never from this checkout), and hidden tests are NEVER copied;
3. asserts no `.jsonl` report/session files and no `grading/`/`reports/` paths
   exist in either arm checkout (no leakage of prior runs or of this conversation);
4. pre-warms EVERY worktree (`.venv` via `uv sync`) BEFORE either agent
   launches, OUTSIDE the timed solve, identically for both arms;
5. launches `pi --mode json` with inherited tools/session context disabled
   (`--no-extensions -e builtin:codemode --no-mcp`, explicit `--tools`), a
   prefix-robust scrubbed child environment (every `PI_*` removed,
   credentials inherited but never logged), each child in its own process
   group (`start_new_session=True`, `killpg` on timeout/cap), streaming
   stdout (JSONL events) and stderr to per-arm files under `reports/`
   (outside both arm worktrees) while timing with `time.monotonic()`;
6. parses the authoritative `message_end` usage via :mod:`parse_events`;
7. writes a per-arm run card. It does NOT run the hidden acceptance tests —
   the operator runs `grading/verify_arm.py` AFTER both agents finish (see README).

Token budget policy: time is the enforced budget (`timeout_s_each_arm`,
monotonic wall clock). Tokens are measured post-hoc from authoritative
`message_end` usage and NEVER capped mid-run unless the operator sets a
positive `max_total_tokens_each_arm` in `config.json`, in which case the
harness terminates the whole child process group once the streamed total
exceeds it (both arms share the same cap, recorded on the run card). The cap
is sampled at assistant `message_end` boundaries, so the recorded total can
overshoot the cap by up to one response before the group is killed.

Process-group safety: every agent child starts with `start_new_session=True`
and any timeout/cap kill targets the entire subprocess group (`killpg`), so
orphaned tool children cannot survive the parent. Session logs persist under
`reports/` (outside both arm worktrees).

Usage (at GO, after filling `config.json`)::

    uv run python utils/benchmarks/graph_restart_eval/run_eval.py --config \
        utils/benchmarks/graph_restart_eval/config.json

No credentials are ever logged: the agent inherits the operator's environment
and no `--api-key` value is placed on any command line.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL_DIR))

from parse_events import parse_events_file  # noqa: E402

ARMS = {
    'a': {'name': 'BaseRestartWorkChain', 'arm_file': 'ARM_A_BRWC.md', 'solution_hint': 'RestartWrapper'},
    'b': {'name': 'GraphIR-direct', 'arm_file': 'ARM_B_GRAPHIR.md', 'solution_hint': 'build_restart_graph'},
}

SHARED_FILES = ['TASK_COMMON.md', 'fixtures/flaky_child.py']

SANITIZED_ENV_VARS = (
    'PI_SESSION_ID',
    'PI_SESSION_FILE',
    'PI_CODING_AGENT_SESSION_DIR',
    'PI_PROVIDER',
    'PI_MODEL',
    'PI_REASONING_LEVEL',
)
"""Parent-session variables always stripped from the agent child environment.

`--model`/`--thinking`/`--session-dir`/`--session-id` are passed explicitly
on the child command line, so inherited identity/continuation values must not
leak the parent session into the child. Provider credentials (e.g.
`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `CODEX_*`) are intentionally INHERITED
and never logged. The scrub is prefix-robust: every `PI_*` variable is
removed, not just the names above.
"""


def _utcnow() -> str:
    """Return the current UTC time in ISO 8601 format."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    """Return the hex SHA-256 of a file."""
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(65536), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command, raising with context on failure."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=True, **kwargs)
    except subprocess.CalledProcessError as exc:
        msg = f'command failed: {" ".join(cmd)}\nstdout: {exc.stdout}\nstderr: {exc.stderr}'
        raise RuntimeError(msg) from exc


def build_prompt(scratch: Path, arm_file: str) -> str:
    """Assemble the single first-prompt message for one arm."""
    common = (EVAL_DIR / 'TASK_COMMON.md').read_text(encoding='utf-8')
    arm = (EVAL_DIR / arm_file).read_text(encoding='utf-8')
    header = (
        '# Isolated evaluation run\n\n'
        f'Your scratch directory is `{scratch}`. Work ONLY inside it. '
        'The shared task is below, followed by YOUR arm-specific method rules.\n\n'
        '## Strict isolation rules (violations invalidate the run)\n\n'
        '- Work ONLY inside your scratch directory. You may READ repository sources '
        '  outside the scratch for reference (e.g. `src/aiida/...`, '
        '  `tests/engine/processes/graphs/...`), but NEVER write outside it.\n'
        '- FORBIDDEN to read, list, glob, or grep: any other `eval-scratch-*` '
        '  directory, any `ARM_*.md` file other than the one in your scratch, '
        '  any `reports/` directory, any `grading/` path, any `*.jsonl` '
        '  transcript/metrics/session file, any `tests_hidden/` path or file '
        '  with `hidden`/`verify` in its name.\n'
        '- FORBIDDEN to inspect git history or other checkouts: no `git log/show/diff/blame`, '
        '  no other worktrees or branches, no stash/reflog. The current checkout is all there is.\n'
        '- This is a fresh session: there is no prior conversation to resume and no other '
        '  agent to coordinate with. Do NOT attempt to discover the hidden acceptance '
        '  tests; implement exactly the behaviour specified below.\n\n'
    )
    return f'{header}{common}\n\n---\n\n{arm}\n'


def _solver_worktree_leak_paths(worktree: Path) -> list[Path]:
    """Paths that must never be visible inside a fresh solver worktree."""
    return [
        worktree / 'utils' / 'benchmarks' / 'graph_restart_eval' / 'grading',
        worktree / 'reports',
    ]


def _scrub_solver_worktree(worktree: Path) -> list[str]:
    """Remove grader source and reports from a NEW disposable worktree only.

    `grading/` is tracked grader source (committed after the original solves)
    and root `reports/` may hold committed run cards — a fresh `git worktree
    add` would otherwise expose both to the solver. Every removal is joined
    under `worktree` (the disposable detached checkout for one arm); the main
    checkout and the repository are never touched. Raises if either leak path
    is still present afterwards.
    """
    removed: list[str] = []
    for path in _solver_worktree_leak_paths(worktree):
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
            removed.append(str(path))
        elif path.is_file() or path.is_symlink():
            path.unlink()
            removed.append(str(path))
    leaks = [str(p) for p in _solver_worktree_leak_paths(worktree) if p.exists()]
    if leaks:
        msg = f'solver worktree still exposes grader/report paths: {leaks}'
        raise RuntimeError(msg)
    return removed


def prepare_arm(repo_root: Path, revision: str, arm: str, worktree_root: Path, reports_dir: Path) -> dict:
    """Create an isolated worktree + scratch dir with only shared task files.

    The fresh detached worktree is scrubbed of the tracked `grading/` grader
    and any root `reports/` checkout BEFORE the scratch dir is staged and long
    before the solver starts; the main checkout is never modified.
    """
    info = ARMS[arm]
    worktree = worktree_root / f'graph-restart-eval-arm-{arm}'
    if worktree.exists():
        msg = f'worktree path already exists (remove it for a fresh run): {worktree}'
        raise RuntimeError(msg)
    _run(['git', 'worktree', 'add', '--detach', str(worktree), revision], cwd=repo_root)
    scrubbed = _scrub_solver_worktree(worktree)

    scratch = worktree / f'eval-scratch-{arm}'
    scratch.mkdir(parents=True)
    for rel in SHARED_FILES + [info['arm_file']]:
        src = EVAL_DIR / rel
        dst = scratch / Path(rel).name if rel == info['arm_file'] else scratch / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    # Isolation pre-flight: no JSONL artefacts, no hidden tests, and no
    # grader/report paths in arm reach.
    jsonl = sorted(str(p) for p in scratch.rglob('*.jsonl'))
    hidden = sorted(str(p) for p in scratch.rglob('*hidden*')) + sorted(str(p) for p in scratch.rglob('*verify*'))
    staged = sorted(str(p) for p in scratch.rglob('*') if p.name in ('grading', 'reports'))
    if jsonl or hidden or staged:
        msg = f'isolation pre-flight failed for arm {arm}: jsonl={jsonl} hidden={hidden} staged={staged}'
        raise RuntimeError(msg)

    prompt = build_prompt(scratch, info['arm_file'])
    prompt_path = reports_dir / f'prompt-arm-{arm}.md'
    prompt_path.write_text(prompt, encoding='utf-8')
    return {
        'worktree': worktree,
        'scratch': scratch,
        'prompt': prompt,
        'prompt_path': prompt_path,
        'scrubbed': scrubbed,
    }


def _sanitized_child_env() -> tuple[dict[str, str], list[str]]:
    """Copy the operator environment minus parent-session continuation variables.

    Credentials are inherited untouched (the child must authenticate); they are
    never written to logs — only the redacted argv is recorded. Returns the
    scrubbed env plus the sorted list of removed `PI_*` names for the run card.
    """
    env = dict(os.environ)
    stripped = sorted(k for k in env if k.startswith('PI_') or k in SANITIZED_ENV_VARS)
    for var in stripped:
        env.pop(var, None)
    return env, stripped


def prewarm_worktree(worktree: Path) -> dict:
    """Run `uv sync` inside a fresh worktree OUTSIDE the timed solve.

    Called identically for both arms BEFORE either agent launches, so neither
    arm pays environment-install time inside its measured budget.
    """
    start = time.monotonic()
    proc = subprocess.run(['uv', 'sync'], cwd=worktree, capture_output=True, text=True, check=False)
    wall_s = time.monotonic() - start
    if proc.returncode != 0:
        msg = f'`uv sync` prewarm failed in {worktree}:\n{proc.stderr[-2000:] or proc.stdout[-2000:]}'
        raise RuntimeError(msg)
    return {'exit_code': proc.returncode, 'wall_s': wall_s}


def _streamed_total_tokens(line: str, running: int) -> int:
    """Add one JSONL line's assistant `message_end` total to the running count.

    Mirrors the authoritative rule in :mod:`parse_events` (sum of assistant
    `message_end` usage); used only for live cap enforcement, never reported.
    """
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return running
    if event.get('type') != 'message_end':
        return running
    message = event.get('message') or {}
    if message.get('role') != 'assistant':
        return running
    try:
        return running + int((message.get('usage') or {}).get('totalTokens') or 0)
    except (TypeError, ValueError):
        return running


def _kill_process_group(proc: subprocess.Popen, sig: int) -> None:
    """Signal the whole child process group so tool children cannot outlive `pi`.

    Falls back to killing the parent when group signalling is unavailable.
    """
    try:
        os.killpg(os.getpgid(proc.pid), sig)
    except (ProcessLookupError, PermissionError, OSError):
        with contextlib.suppress(ProcessLookupError, OSError):
            proc.send_signal(sig)


def session_files(session_dir: Path) -> list[dict]:
    """List persisted raw session logs (`*.jsonl`) with SHA-256."""
    entries = []
    if session_dir.is_dir():
        for path in sorted(session_dir.rglob('*.jsonl')):
            entries.append({'path': str(path), 'sha256': _sha256(path), 'bytes': path.stat().st_size})
    return entries


def launch_pi(
    pi_bin: str,
    prompt: str,
    cwd: Path,
    session_dir: Path,
    session_id: str,
    model: str,
    thinking: str,
    provider: str | None,
    tools: str,
    exclude_tools: str,
    no_mcp: bool,
    no_extensions: bool,
    codemode_extension: str,
    extra_args: list[str],
    timeout_s: int,
    max_total_tokens: int | None,
    events_path: Path,
    stderr_path: Path,
) -> dict:
    """Launch one fresh `pi --mode json` run; return harness timing metadata.

    Streams stdout line-by-line to `events_path` (full raw JSONL transcript)
    so an optional equal token cap can terminate the whole child process group
    mid-run; wall time is measured with `time.monotonic()` around the whole
    child lifetime. The child starts with `start_new_session=True` and any
    timeout/cap kill targets the entire group (`killpg`). The cap is sampled
    at `message_end` boundaries and can overshoot by up to one response.
    """
    session_dir.mkdir(parents=True, exist_ok=True)
    cmd = [pi_bin, '--mode', 'json']
    if no_extensions:
        # Codemode ships as a built-in extension: disabling all extensions
        # removes inherited agent/session context, so re-enable just it.
        cmd += ['--no-extensions', '-e', codemode_extension]
    cmd += [
        '--session-dir',
        str(session_dir),
        '--session-id',
        session_id,
        '--model',
        model,
        '--thinking',
        thinking,
        '--tools',
        tools,
        '--exclude-tools',
        exclude_tools,
    ]
    if provider:
        cmd += ['--provider', provider]
    if no_mcp:
        cmd.append('--no-mcp')
    cmd += extra_args
    # Deliberately no --continue/--resume/--fork: the explicit --session-id in a
    # fresh --session-dir guarantees an isolated, fresh session. `--` ends option
    # parsing so the prompt is always a positional message, never a flag.
    cmd += ['--', prompt]
    # Never log the environment (it may carry credentials); never pass --api-key.
    redacted = [c if not c.startswith('sk-') else '<redacted>' for c in cmd]
    start = time.monotonic()
    timed_out = False
    token_cap_exceeded = False
    exit_code: int | None = None
    child_env, env_stripped = _sanitized_child_env()
    with open(events_path, 'w', encoding='utf-8') as out, open(stderr_path, 'w', encoding='utf-8') as err:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=err,
            text=True,
            env=child_env,
            start_new_session=True,
        )
        assert proc.stdout is not None
        watchdog_fired = False

        def _kill() -> None:
            nonlocal watchdog_fired
            watchdog_fired = True
            _kill_process_group(proc, signal.SIGKILL)

        timer = threading.Timer(timeout_s, _kill)
        timer.start()
        try:
            streamed_tokens = 0
            for line in proc.stdout:
                out.write(line)
                streamed_tokens = _streamed_total_tokens(line, streamed_tokens)
                if max_total_tokens is not None and streamed_tokens > max_total_tokens:
                    token_cap_exceeded = True
                    _kill_process_group(proc, signal.SIGTERM)
                    break
            exit_code = proc.wait()
        finally:
            timer.cancel()
            with contextlib.suppress(ProcessLookupError, OSError):
                if proc.poll() is None:
                    _kill_process_group(proc, signal.SIGKILL)
                    proc.wait(timeout=10)
    timed_out = watchdog_fired
    end = time.monotonic()
    return {
        'cmd_redacted': redacted,
        'cwd': str(cwd),
        'timeout_s': timeout_s,
        'max_total_tokens': max_total_tokens,
        'timed_out': timed_out,
        'token_cap_exceeded': token_cap_exceeded,
        'pi_exit_code': exit_code,
        'wall_s_monotonic': end - start,
        'env_stripped': env_stripped,
        'start_new_session': True,
    }


def _self_check() -> None:
    """Offline harness smoke test: prepare-arm safety without any model run.

    Uses a tempfile fake worktree only — no `pi` binary, no git worktree, no
    network, no agent. Validates that the solver-worktree scrub removes the
    tracked grader and reports while leaving task files alone, that the prompt
    forbids `grading/`, and that the tracked grader hashes cleanly. Raises
    `RuntimeError` on the first failure; prints a PASS summary otherwise.
    Run via `run_eval.py --self-check`.
    """
    import tempfile

    checks: list[str] = []
    with tempfile.TemporaryDirectory(prefix='graph-restart-self-check-') as tmp:
        fake = Path(tmp) / 'arm-worktree'
        grader = fake / 'utils' / 'benchmarks' / 'graph_restart_eval' / 'grading'
        grader.mkdir(parents=True)
        (grader / 'test_acceptance.py').write_text('# fake tracked grader\n', encoding='utf-8')
        committed_reports = fake / 'reports' / 'graph-restart-study'
        committed_reports.mkdir(parents=True)
        (committed_reports / 'report.json').write_text('{}\n', encoding='utf-8')
        scratch = fake / 'eval-scratch-a'
        scratch.mkdir(parents=True)
        (scratch / 'TASK_COMMON.md').write_text('task\n', encoding='utf-8')

        removed = _scrub_solver_worktree(fake)
        checks.append(f'scrub removed {len(removed)} leak path(s)')
        if grader.exists() or (fake / 'reports').exists():
            msg = 'self-check failed: scrub left grader/report paths behind'
            raise RuntimeError(msg)
        checks.append('grading/ + reports/ absent from fake solver worktree')
        if not (scratch / 'TASK_COMMON.md').is_file():
            msg = 'self-check failed: scrub touched the scratch task files'
            raise RuntimeError(msg)
        checks.append('scratch task files untouched')
        if not (EVAL_DIR / 'run_eval.py').is_file():
            msg = 'self-check failed: main checkout layout unexpected'
            raise RuntimeError(msg)
        checks.append('main checkout untouched (fake worktree lived under tempfile)')

    prompt = build_prompt(EVAL_DIR / 'eval-scratch-self-check', ARMS['a']['arm_file'])
    if '`grading/`' not in prompt:
        msg = 'self-check failed: prompt does not forbid grading/'
        raise RuntimeError(msg)
    checks.append('prompt forbids grading/')
    tracked = sorted((EVAL_DIR / 'grading').glob('*.py')) if (EVAL_DIR / 'grading').is_dir() else []
    if not tracked:
        msg = 'self-check failed: tracked grading/*.py missing'
        raise RuntimeError(msg)
    checks.append(f'tracked grader present ({len(tracked)} file(s); manifest annotates grader_version v2)')
    for check in checks:
        print(f'self-check PASS: {check}')


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default=str(EVAL_DIR / 'config.json'))
    parser.add_argument('--model', default=None)
    parser.add_argument('--thinking', default=None)
    parser.add_argument('--timeout-s', type=int, default=None)
    parser.add_argument('--revision', default=None, help='Git revision for both worktrees (default: HEAD).')
    parser.add_argument('--arms', default='a,b')
    parser.add_argument('--worktree-root', default=None)
    parser.add_argument('--reports-dir', default=str(EVAL_DIR / 'reports'))
    parser.add_argument(
        '--self-check',
        action='store_true',
        help='Run the offline harness smoke test (tempfile only; no model, no `pi`, no git worktree).',
    )
    args = parser.parse_args()
    if args.self_check:
        _self_check()
        return

    config = json.loads(Path(args.config).read_text(encoding='utf-8'))
    model = args.model or config['model']
    thinking = args.thinking or config['thinking']
    provider = config.get('provider')
    timeout_s = args.timeout_s or int(config['timeout_s_each_arm'])
    max_total_tokens = config.get('max_total_tokens_each_arm')
    if max_total_tokens is not None:
        max_total_tokens = int(max_total_tokens)
        if max_total_tokens <= 0:
            msg = '`max_total_tokens_each_arm` must be a positive integer or null (null = no hard cap).'
            raise SystemExit(msg)
    if 'REPLACE_WITH' in model:
        msg = 'config model is still a placeholder; set --model or fill config.json at GO time.'
        raise SystemExit(msg)

    repo_root = Path(_run(['git', 'rev-parse', '--show-toplevel']).stdout.strip())
    revision = args.revision or _run(['git', 'rev-parse', 'HEAD'], cwd=repo_root).stdout.strip()
    pi_bin = shutil.which('pi')
    if pi_bin is None:
        msg = 'no `pi` binary on PATH'
        raise SystemExit(msg)
    pi_version = _run([pi_bin, '--version']).stdout.strip()
    reports_dir = Path(args.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    worktree_root = Path(args.worktree_root) if args.worktree_root else repo_root.parent

    # Authoritative hidden tests for FUTURE runs: the tracked v2 grader in
    # `grading/` (committed after the original solves; physically removed from
    # solver worktrees by `prepare_arm`). The original v1 `tests_hidden/`
    # snapshot stays frozen and git-ignored; its results are preserved in the
    # completed study report, not re-hashed here.
    hidden_tests: dict[str, str] = {}
    hidden_dir = EVAL_DIR / 'grading'
    if hidden_dir.is_dir():
        hidden_tests = {p.name: _sha256(p) for p in sorted(hidden_dir.glob('*.py'))}
    manifest = {
        'eval_id': config.get('eval_id'),
        'grader_version': 'v2',
        'grader_dir': 'grading',
        'started_utc': _utcnow(),
        'model': model,
        'thinking': thinking,
        'provider': provider,
        'tools': config['tools'],
        'exclude_tools': config['exclude_tools'],
        'no_mcp': config['no_mcp'],
        'no_extensions': config.get('no_extensions', True),
        'codemode_extension': config.get('codemode_extension', 'builtin:codemode'),
        'extra_args': config.get('extra_args', []),
        'timeout_s_each_arm': timeout_s,
        'max_total_tokens_each_arm': max_total_tokens,
        'token_policy': (
            'no hard token cap; authoritative message_end usage measured post-hoc'
            if max_total_tokens is None
            else (
                f'hard cap of {max_total_tokens} total tokens per arm, enforced by stream parser '
                'at message_end boundaries (recorded total can overshoot by up to one response)'
            )
        ),
        'revision': revision,
        'pi_version': pi_version,
        'repo_status': _run(['git', 'status', '--short'], cwd=repo_root).stdout,
        # Frozen inputs: identical requirement/provenance for both arms.
        'fixture_sha256': _sha256(EVAL_DIR / 'fixtures' / 'flaky_child.py'),
        'task_common_sha256': _sha256(EVAL_DIR / 'TASK_COMMON.md'),
        'arm_files_sha256': {arm: _sha256(EVAL_DIR / info['arm_file']) for arm, info in ARMS.items()},
        'hidden_tests_sha256': hidden_tests,
        'env_stripped_from_child': 'all PI_* (incl. PI_SESSION_ID, PI_SESSION_FILE, '
        'PI_CODING_AGENT_SESSION_DIR, PI_PROVIDER, PI_MODEL, PI_REASONING_LEVEL)',
        'arms': {},
    }
    (reports_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')

    arms = [a.strip() for a in args.arms.split(',') if a.strip()]
    # Phase 1: isolate worktrees, then pre-warm EVERY arm (`uv sync`) BEFORE
    # any solve starts, so neither arm pays install time in its measured budget.
    preps: dict[str, dict] = {}
    prewarms: dict[str, dict] = {}
    for arm in arms:
        preps[arm] = prepare_arm(repo_root, revision, arm, worktree_root, reports_dir)
    for arm in arms:
        prewarms[arm] = prewarm_worktree(preps[arm]['worktree'])

    # Phase 2: timed solves, one fresh process group per arm.
    for arm in arms:
        prep = preps[arm]
        prewarm = prewarms[arm]
        session_dir = reports_dir / f'sessions-arm-{arm}'
        events_path = reports_dir / f'events-arm-{arm}.jsonl'
        stderr_path = reports_dir / f'stderr-arm-{arm}.log'
        run_meta = launch_pi(
            pi_bin,
            prep['prompt'],
            prep['scratch'],
            session_dir,
            f'graph-restart-eval-{arm}-v1',
            model,
            thinking,
            provider,
            config['tools'],
            config['exclude_tools'],
            bool(config['no_mcp']),
            bool(config.get('no_extensions', True)),
            str(config.get('codemode_extension', 'builtin:codemode')),
            list(config.get('extra_args', [])),
            timeout_s,
            max_total_tokens,
            events_path,
            stderr_path,
        )
        summary = parse_events_file(events_path)
        summary['wall_s_monotonic'] = run_meta['wall_s_monotonic']
        (reports_dir / f'metrics-arm-{arm}.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
        card = {
            'eval_id': config.get('eval_id'),
            'arm': arm,
            'method': ARMS[arm]['name'],
            'model': model,
            'thinking': thinking,
            'provider': provider,
            'revision': revision,
            'pi_version': pi_version,
            'started_utc': manifest['started_utc'],
            'worktree': str(prep['worktree']),
            'scratch': str(prep['scratch']),
            'scrubbed_worktree_paths': prep['scrubbed'],
            'prewarm_uv_sync': prewarm,
            'session_dir': str(session_dir),
            'session_files': session_files(session_dir),
            'transcript': str(events_path),
            'transcript_sha256': _sha256(events_path),
            'metrics_sha256': _sha256(reports_dir / f'metrics-arm-{arm}.json'),
            'prompt_sha256': _sha256(prep['prompt_path']),
            'harness': run_meta,
            'metrics': summary,
            'verify': 'NOT RUN — run the hidden acceptance tests only after BOTH arms finish.',
        }
        (reports_dir / f'run-card-arm-{arm}.json').write_text(json.dumps(card, indent=2) + '\n', encoding='utf-8')
        manifest['arms'][arm] = {'run_card': f'run-card-arm-{arm}.json'}
        (reports_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        print(
            f'arm {arm}: timed_out={run_meta["timed_out"]} cap_exceeded={run_meta["token_cap_exceeded"]} '
            f'wall_s={run_meta["wall_s_monotonic"]:.1f} stop={summary["stop_reason"]} '
            f'in={summary["usage_tokens"]["input"]} out={summary["usage_tokens"]["output"]}'
        )

    print('DONE. Hidden acceptance tests were NOT run. Verify afterwards, e.g.:')
    print('  uv run python utils/benchmarks/graph_restart_eval/grading/verify_arm.py \\')
    print('    --solution-dir <arm-a worktree>/eval-scratch-a/restart_solution --arm a')


if __name__ == '__main__':
    main()
