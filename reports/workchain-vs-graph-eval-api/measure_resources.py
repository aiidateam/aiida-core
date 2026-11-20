###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Measure frozen workflow executions in fresh processes; retain unavailable perf diagnostics."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import shutil
import statistics
import subprocess
from pathlib import Path

REPORT = Path(__file__).resolve().parent
ROOT = REPORT.parents[1]
EVENTS = (
    ('L1_data', 'L1-dcache-loads:u', 'L1-dcache-load-misses:u'),
    ('L2', 'l2_rqsts.references:u', 'l2_rqsts.miss:u'),
    ('L3_LLC', 'LLC-loads:u', 'LLC-load-misses:u'),
)


def save(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + '\n')


def acceptance_cases(path: Path) -> list:
    """Read the existing literal acceptance matrix without importing workflow code."""
    module = ast.parse(path.read_text())
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != 'test_contract':
            continue
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                if decorator.func.attr == 'parametrize':
                    return ast.literal_eval(decorator.args[1])
    msg = 'acceptance test has no literal parametrization'
    raise ValueError(msg)


def parse_perf(path: Path, events: list[str]) -> dict:
    """Read perf's delimiter format, preserving unavailable counters instead of inventing zeroes."""
    result: dict = {event: {'count': None, 'status': 'not_reported', 'running_percent': None} for event in events}
    if not path.exists():
        return result
    for line in path.read_text().splitlines():
        fields = [field.strip() for field in line.split(';')]
        if len(fields) < 3 or fields[2] not in result:
            continue
        value, event = fields[0], fields[2]
        if value.startswith('<'):
            result[event]['status'] = value.strip('<>').replace(' ', '_')
            continue
        try:
            count = float(value)
        except ValueError:
            continue
        result[event]['count'] = int(count) if count.is_integer() else count
        result[event]['status'] = 'measured'
        if len(fields) > 4:
            try:
                result[event]['running_percent'] = float(fields[4])
            except ValueError:
                pass
    return result


def cache_levels(counters: dict, reason: str = '') -> dict:
    """Pair comparable accesses/misses without treating occupancy or hardware capacity as usage."""
    levels = {}
    for level, access_event, miss_event in EVENTS:
        accesses = counters.get(access_event, {}).get('count')
        misses = counters.get(miss_event, {}).get('count')
        measured = accesses is not None and misses is not None
        levels[level] = {
            'access_event': access_event,
            'miss_event': miss_event,
            'accesses': accesses,
            'misses': misses,
            'miss_rate_percent': 100 * misses / accesses if measured and accesses > 0 else None,
            'status': 'measured' if measured else 'unavailable',
            'reason': '' if measured else reason or 'counter unsupported, not counted, or not reported',
        }
    return levels


def probe_perf(output: Path, environment: dict[str, str]) -> dict:
    """Check permission first, then event support, without modifying host security configuration."""
    binary = shutil.which('perf')
    if binary is None:
        return {'status': 'unavailable', 'reason': 'perf executable is not installed', 'events': []}
    command = [binary, 'stat', '-e', 'cycles:u', '--', '/bin/true']
    result = subprocess.run(command, capture_output=True, text=True, env=environment, timeout=15, check=False)
    (output / 'perf-permission.log').write_text(result.stdout + result.stderr)
    if result.returncode:
        return {
            'status': 'unavailable',
            'reason': result.stderr.strip(),
            'events': [],
            'permission_probe': {'command': command, 'returncode': result.returncode},
        }
    events = [event for _, access_event, miss_event in EVENTS for event in (access_event, miss_event)]
    csv = output / 'perf-event-probe.csv'
    command = [binary, 'stat', '-x', ';', '-o', str(csv), '-e', ','.join(events), '--', '/bin/true']
    result = subprocess.run(command, capture_output=True, text=True, env=environment, timeout=15, check=False)
    (output / 'perf-events.log').write_text(result.stdout + result.stderr)
    counters = parse_perf(csv, events)
    usable = [event for event in events if counters[event]['status'] == 'measured']
    if result.returncode or not usable:
        return {
            'status': 'unavailable',
            'reason': result.stderr.strip() or 'requested cache events are unsupported',
            'events': [],
            'event_probe': {'command': command, 'returncode': result.returncode, 'counters': counters},
        }
    return {
        'status': 'available' if len(usable) == len(events) else 'partially_available',
        'reason': '',
        'events': usable,
        'counters': counters,
    }


def summarize(output: Path, metadata: dict, records: list[dict]) -> None:
    """Persist per-arm and per-case peaks without altering coding-agent metrics."""
    arms = {}
    for arm in ('workchain', 'graph'):
        rows = [row for row in records if row['arm'] == arm]
        peaks = [row['workflow_peak_rss_kib'] for row in rows if row['workflow_peak_rss_kib'] is not None]
        arms[arm] = {
            'executions': len(rows),
            'all_finished_ok': all(row['root_finished_ok'] for row in rows),
            'workflow_peak_rss_max_mib': max(peaks) / 1024 if peaks else None,
            'workflow_peak_rss_median_mib': statistics.median(peaks) / 1024 if peaks else None,
            'process_peak_rss_through_completion_max_mib': max(
                row['process_peak_rss_through_workflow_completion_kib'] for row in rows
            )
            / 1024,
            'cache_counters': cache_levels({}, metadata['perf']['reason']),
            'per_case': [],
        }
        for index in sorted({row['case_index'] for row in rows}):
            case_rows = [row for row in rows if row['case_index'] == index]
            case_peaks = [row['workflow_peak_rss_kib'] for row in case_rows if row['workflow_peak_rss_kib'] is not None]
            arms[arm]['per_case'].append(
                {
                    'case_index': index,
                    'case': case_rows[0]['case'],
                    'repetitions': len(case_rows),
                    'workflow_peak_rss_max_mib': max(case_peaks) / 1024 if case_peaks else None,
                    'workflow_peak_rss_median_mib': statistics.median(case_peaks) / 1024 if case_peaks else None,
                    'workflow_wall_seconds_median': statistics.median(
                        row['workflow_wall_seconds'] for row in case_rows
                    ),
                    'cache_samples': [row['cache_counters'] for row in case_rows],
                }
            )
        if any(row['perf_counters'] for row in rows):
            arms[arm]['cache_counters'] = {
                'status': 'per_execution_only',
                'reason': 'See per-run counters and per_case samples; no aggregate is inferred.',
            }
        if output == (REPORT / 'runtime-resources').resolve():
            save(REPORT / arm / 'execution-resources.json', arms[arm])
    save(output / 'summary.json', {'metadata': metadata, 'arms': arms})
    header = (
        '# Workflow execution memory and CPU caches\n\n'
        'New instrumented executions of the finished submissions, not retrospective agent measurements. '
        'Each case runs in a fresh Python process and temporary SQLite profile, pinned to the same logical CPU. '
        'The original coding-agent time/token/cost metrics are unchanged.\n\n'
        '| Arm | Executions | Maximum workflow-window RSS | Median per-run peak RSS | L1 data | L2 | L3/LLC |\n'
        '|---|---:|---:|---:|---|---|---|\n'
    )
    lines = []
    for arm, data in arms.items():
        maximum, median = data['workflow_peak_rss_max_mib'], data['workflow_peak_rss_median_mib']
        max_text = f'{maximum:.2f} MiB' if maximum is not None else 'Unavailable'
        median_text = f'{median:.2f} MiB' if median is not None else 'Unavailable'
        cache_status = 'Unavailable' if metadata['perf']['status'] == 'unavailable' else 'See per-run counters'
        lines.append(
            f'| {arm} | {data["executions"]} | {max_text} | {median_text} | '
            f'{cache_status} | {cache_status} | {cache_status} |'
        )
    cache_availability = (
        'Cache counters were collected where supported; see per-execution counters for partial availability.'
        if metadata['perf']['status'] != 'unavailable'
        else 'Hardware cache counters are unavailable. The perf probe failed; this host reports '
        f'`kernel.perf_event_paranoid={metadata["perf_event_paranoid"]}`. See `perf-permission.log` '
        'and `environment.json` for the exact diagnostic. No host security setting or privilege was changed.'
    )
    text = (
        header
        + '\n'.join(lines)
        + """

## Measurement boundaries

- RSS is the Linux resident-set high-water mark (`/proc/self/status: VmHWM`), not heap or summed ORM node sizes.
- The worker resets its own peak before `run_get_node` via `/proc/self/clear_refs` value 5.
  It reads the peak immediately on return, before checking results. This includes the Python/AiiDA resident baseline,
  graph compilation/serialization at first launch and scientific child WorkChains/calcfunctions in the same interpreter;
  it excludes earlier profile/import initialization and later validation/cleanup peaks. No task runs before this window.
- Preparation/final RSS, CPU times, process peak through completion and reset support are also recorded.
  If the reset is unavailable, workflow-window peaks are null rather than mislabeled lifetime measurements.
- Absolute RSS includes shared mapped pages; this is not proportional set size or incremental allocated memory.
- Maxima and medians summarize matched cases, but three repetitions are not a statistically powered comparison.
- All runs verify results, budgets, child counts, finished states, output identity and no root CREATE links.

## Cache availability

"""
        + cache_availability
        + """

Unavailable counter values are null, never zero. CPU cache capacities in `environment.json` are hardware metadata,
not workflow cache usage. Cache occupancy is not inferred from RSS, filesystem page cache or model-token caches.

The intended metrics are accesses, misses and miss rates for L1 **data**, L2 and L3/LLC.
L1 instruction cache capacity is recorded, but instruction-cache usage was not measured either.
On a permitted machine the runner checks event support and collects the supported events with perf;
those counters cover the whole profiling process (imports/setup/execution/verification/teardown),
not the narrower RSS workflow window. Raw counts and counter running percentages are retained per execution.
Do not compare those counters with a narrower execution-only scope without adapting the instrumentation.
The L2 aliases are specific to the detected Intel CPU and may require adaptation on other architectures.

## Reproduce

```bash
uv run --no-sync python reports/workchain-vs-graph-eval-api/measure_resources.py \\
  --repetitions 3 --output-dir /tmp/aiida-workflow-resources-new
```

The runner uses the frozen source workspaces recorded in the eval report and verifies their source hashes first.
A new output directory avoids overwriting results; use `--case-index 0 --repetitions 1` for a smoke run.
If perf access is granted by the machine administrator, the same command attempts cache counters automatically.
No agent/model calls occur. Per-run JSON, logs, source checks and environment details remain alongside this summary.
"""
    )
    (output / 'README.md').write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repetitions', type=int, default=3)
    parser.add_argument('--case-index', action='append', type=int)
    parser.add_argument('--cpu', type=int, default=min(os.sched_getaffinity(0)))
    parser.add_argument('--output-dir', type=Path, default=REPORT / 'runtime-resources')
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error('repetitions must be positive')
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if (output / 'runs.jsonl').exists():
        parser.error('output already contains measurements; use a fresh output directory')
    cases = acceptance_cases(REPORT / 'test_acceptance.py')
    selected = args.case_index if args.case_index is not None else list(range(len(cases)))
    if not selected or any(index < 0 or index >= len(cases) for index in selected):
        parser.error('case index is outside the acceptance matrix')
    if args.cpu not in os.sched_getaffinity(0):
        parser.error('selected CPU is outside the allowed affinity')
    environment = os.environ.copy()
    environment['LC_ALL'] = 'C'
    perf = probe_perf(output, environment)
    manifest = json.loads((REPORT / 'baseline-manifest.json').read_text())
    run = json.loads((REPORT / 'run.json').read_text())
    checks = {}
    for arm in ('workchain', 'graph'):
        workspace = Path(run['workspace_root']) / arm
        checked = 0
        for path, expected in manifest.items():
            if path.startswith('src/'):
                assert hashlib.sha256((workspace / path).read_bytes()).hexdigest() == expected, path
                checked += 1
        for name in ('solution.py', 'collaborators.py'):
            assert (workspace / 'tests/engine/processes/workflow_eval' / name).read_bytes() == (
                REPORT / arm / 'submission' / name
            ).read_bytes(), (arm, name)
        checks[arm] = {'source_files_verified': checked, 'submission_matches': True}
    caches = []
    for cache_path in sorted(Path(f'/sys/devices/system/cpu/cpu{args.cpu}/cache').glob('index*')):
        caches.append(
            {key: (cache_path / key).read_text().strip() for key in ('level', 'type', 'size', 'shared_cpu_list')}
        )
    lscpu = subprocess.run(['lscpu', '--json'], capture_output=True, text=True, check=True)
    (output / 'lscpu.json').write_text(lscpu.stdout)
    metadata = {
        'baseline_commit': run['baseline_commit'],
        'repetitions': args.repetitions,
        'cases': {str(index): cases[index] for index in selected},
        'cpu': args.cpu,
        'kernel': os.uname().release,
        'perf_event_paranoid': Path('/proc/sys/kernel/perf_event_paranoid').read_text().strip(),
        'cache_hardware_metadata_not_usage': caches,
        'perf': perf,
        'source_integrity': checks,
        'counter_scope_if_available': 'whole profiling process, user-mode events',
        'memory_scope': 'run_get_node window after process-local VmHWM reset, absolute RSS including resident baseline',
    }
    save(output / 'environment.json', metadata)
    records: list[dict] = []
    for repetition in range(args.repetitions):
        for index in selected:
            order = ('workchain', 'graph') if (repetition + index) % 2 == 0 else ('graph', 'workchain')
            for arm in order:
                label = f'{arm}-case-{index:02d}-repeat-{repetition + 1}'
                workspace = Path(run['workspace_root']) / arm
                env = {
                    **environment,
                    'PYTHONPATH': f'{workspace / "src"}:{workspace}',
                    'UV_PROJECT_ENVIRONMENT': str(ROOT / '.venv'),
                }
                result_path = output / f'{label}.json'
                command = [
                    'uv',
                    'run',
                    '--no-sync',
                    'python',
                    str(REPORT / 'profile_execution.py'),
                    '--case-json',
                    json.dumps(cases[index]),
                    '--output',
                    str(result_path),
                    '--cpu',
                    str(args.cpu),
                ]
                perf_csv = output / f'{label}.perf.csv'
                if perf['events']:
                    command = [
                        'perf',
                        'stat',
                        '-x',
                        ';',
                        '-o',
                        str(perf_csv),
                        '-e',
                        ','.join(perf['events']),
                        '--',
                        *command,
                    ]
                with (output / f'{label}.log').open('w') as log:
                    completed = subprocess.run(
                        command, cwd=workspace, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=120, check=False
                    )
                assert completed.returncode == 0 and result_path.exists(), label
                result = json.loads(result_path.read_text())
                counters = parse_perf(perf_csv, perf['events']) if perf['events'] else {}
                result.update(
                    arm=arm,
                    case_index=index,
                    repetition=repetition + 1,
                    perf_counters=counters,
                    cache_counters=cache_levels(counters, perf['reason']),
                    command=command,
                )
                save(result_path, result)
                records.append(result)
                with (output / 'runs.jsonl').open('a') as stream:
                    stream.write(json.dumps(result) + '\n')
                print(f'{label}: peak RSS {result["workflow_peak_rss_kib"]} KiB; finished OK', flush=True)
    summarize(output, metadata, records)


if __name__ == '__main__':
    main()
