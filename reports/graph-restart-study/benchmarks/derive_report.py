###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Derive reports/graph-restart-study/benchmarks/report.json from raw pytest-benchmark JSON.

All timing numbers are read from ``raw-pytest-benchmark.json`` -- nothing is
hand-transcribed. Run from the repository root::

    uv run python reports/graph-restart-study/benchmarks/derive_report.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BENCH_DIR = REPO / 'reports' / 'graph-restart-study' / 'benchmarks'
RAW = BENCH_DIR / 'raw-pytest-benchmark.json'
RUN_LOG = BENCH_DIR / 'run.log'
VERIFY_LOG = BENCH_DIR.parent / 'validation.log'

EXPECTED_REVISION = '4ae87025e528f358f8194e4750334d247075ce6b'
EXPECTED_BRANCH = 'graph-benchmark-v6'


def _parse_summary_line(path: Path) -> dict[str, int | float | str]:
    """Parse the ``N passed, M skipped ... in S (H:MM:SS)`` line of a pytest log."""
    text = path.read_text(encoding='utf-8')
    match = re.search(
        r'=\s*((?:\d+ \w+,?\s*)+)in ([\d.]+)s \(([^)]+)\)\s*=',
        text,
    )
    if match is None:
        msg = f'no pytest summary line found in {path}'
        raise ValueError(msg)
    counts = {word: int(num) for num, word in re.findall(r'(\d+) (\w+)', match.group(1))}
    return {
        'passed': counts.get('passed', 0),
        'failed': counts.get('failed', 0),
        'skipped': counts.get('skipped', 0),
        'deselected': counts.get('deselected', 0),
        'errors': counts.get('error', 0) + counts.get('errors', 0),
        'duration_s': float(match.group(2)),
        'duration_hms': match.group(3),
    }


def _phase_of(fullname: str) -> tuple[str, str]:
    """Return (phase, timing_mode) for a benchmark fullname."""
    test = fullname.split('::')[1].split('[', maxsplit=1)[0]
    if test == 'test_benchmark_restart_ir':
        return 'IRserialization', 'restart-ir'
    if test == 'test_benchmark_restart_daemon':
        return 'submitted', 'restart-daemon'
    if test == 'test_benchmark_restart_local':
        return 'local', 'restart-local'
    if test == 'test_benchmark':
        return 'local', 'engine-matched'
    if test == 'test_benchmark_inline':
        return 'local', 'inline-matched'
    msg = f'unexpected benchmark test: {fullname}'
    raise ValueError(msg)


def main() -> None:
    raw = json.loads(RAW.read_text(encoding='utf-8'))
    benches = raw['benchmarks']
    if len(benches) != 32:
        msg = f'expected 32 timed cases, found {len(benches)}'
        raise ValueError(msg)

    machine = raw['machine_info']
    cpu = machine['cpu']
    # Deliberately omit machine_info['node'] (hostname): no host identifiers
    # and no credentials are serialized into the report.
    total_ram_gb = round(float(Path('/proc/meminfo').read_text().split()[1]) / 1024 / 1024, 1)

    cases = []
    for bench in benches:
        stats = bench['stats']
        phase, timing_mode = _phase_of(bench['fullname'])
        cases.append(
            {
                'id': bench['name'],
                'fullname': bench['fullname'],
                'group': bench['group'],
                'phase': phase,
                'timing_mode': timing_mode,
                'params': bench.get('params'),
                'stats_s': {
                    'mean': stats['mean'],
                    'median': stats['median'],
                    'stddev': stats['stddev'],
                    'min': stats['min'],
                    'max': stats['max'],
                    'rounds': stats['rounds'],
                },
                'times_s': list(stats['data']),
                'extra_info': bench.get('extra_info') or {},
            }
        )

    by_phase: dict[str, list[str]] = {}
    for case in cases:
        by_phase.setdefault(case['phase'], []).append(case['id'])

    run_summary = _parse_summary_line(RUN_LOG)
    verify_summary = _parse_summary_line(VERIFY_LOG)

    if raw['commit_info']['id'] != EXPECTED_REVISION:
        msg = f'raw commit {raw["commit_info"]["id"]} != {EXPECTED_REVISION}'
        raise ValueError(msg)

    report = {
        'title': 'Graph restart study: benchmark timing report (GO run)',
        'authoritative': 'report.json is authoritative; report.md is a brief human summary.',
        'revision': {
            'commit': raw['commit_info']['id'],
            'branch': EXPECTED_BRANCH,
            'dirty_tracked': raw['commit_info']['dirty'],
            'worktree_note': (
                'Tracked tree clean at the benchmark commit; the only untracked path is '
                'reports/ itself, created by this run to hold its output artifacts.'
            ),
        },
        'machine': {
            'cpu_brand': cpu['brand_raw'],
            'cpu_arch': cpu['arch_string_raw'],
            'cpu_count': cpu['count'],
            'cpu_freq_advertised': cpu['hz_advertised_friendly'],
            'total_ram_gb': total_ram_gb,
            'os': f'{machine["system"]} {machine["release"]}',
            'hostname': 'omitted (no host identifiers serialized)',
        },
        'backend': {
            'storage': 'core.sqlite_dos (temporary presto profile per test)',
            'broker': 'ZeroMQ in-process broker (presto default; no external RabbitMQ)',
            'local_modes_runner': 'local run_get_node, provenance always on',
            'submitted_modes_runner': (
                'started_daemon_client + submit_and_await fixtures; '
                'completion polling interval 0.1 s (time.sleep(0.1) in '
                'src/aiida/tools/pytest_fixtures/daemon.py), so each submitted '
                'round carries up to ~0.1 s of wait quantization plus broker/daemon scheduling'
            ),
            'python': machine['python_version'],
            'python_implementation': machine['python_implementation'],
            'aiida_version': '3.0.0.dev0',
            'pytest_version': '9.1.1',
            'pytest_benchmark_version': '4.0.0',
        },
        'command': (
            'uv run pytest -m presto tests/benchmark/test_graph_engine.py '
            'tests/benchmark/test_graph_engine_inline.py tests/benchmark/test_graph_restart.py '
            '--benchmark-only '
            '--benchmark-json=reports/graph-restart-study/benchmarks/raw-pytest-benchmark.json'
        ),
        'settings': {
            'markers': '-m presto (no external services)',
            'parallelism': 'serial, no xdist (-n not passed; single process)',
            'exclusivity': 'no other test or agent-eval runs concurrent with this timing run',
            'engine_matched': 'benchmark.pedantic(iterations=1, rounds=10, warmup_rounds=1); '
            'InstalledCode, launch kwargs and warmed handle.build() outside timing',
            'inline_matched': 'benchmark.pedantic(iterations=1, rounds=10, warmup_rounds=1); same warm setup',
            'restart_local': 'benchmark.pedantic(iterations=1, rounds=10, warmup_rounds=1); '
            'budget 5 (recover needs 3 FlakyStep runs); warmed handle.build() outside timing; '
            'graph-direct-ir reuses the same stored declaration Dict across rounds (relinked after warmup)',
            'restart_ir': 'benchmark.pedantic(iterations=1, rounds=10, warmup_rounds=1); each round = '
            'warmed handle.build() cache hit + to_dict/from_dict round trip (warm serialization, '
            'not cold compilation); equality check outside timing',
            'restart_daemon': 'benchmark.pedantic(iterations=1, rounds=5, warmup_rounds=1); per-round '
            'timeout 120 s; graph-submitted resolves get_launch_inputs from the authoring handle '
            'per round INSIDE timing; graph-submitted-direct-ir keeps the serialized payload template '
            'outside timing but builds a fresh declaration Dict per round inside timing',
            'provenance': 'always on for every timed case (supported graph execution always stores provenance)',
        },
        'counts': {
            'timed_cases_total': len(cases),
            'engine_matched': 10,
            'inline_matched': 15,
            'restart': 7,
            'restart_breakdown': {'local': 3, 'submitted_daemon': 3, 'ir_roundtrip': 1},
            'run_log_summary': run_summary,
            'skipped_note': (
                'The 57 skips are the non-benchmark (correctness) tests in the same files, '
                'auto-skipped by --benchmark-only; 0 failures, 0 deselected.'
            ),
        },
        'correctness_evidence': {
            'log': '/tmp/graph-exit-committed-verification.log',
            'attribution': (
                'PARENT RUN, not this timing run: independent verification on the same commit, '
                'do not attribute its 794 passes to this GO benchmark run.'
            ),
            'summary': verify_summary,
            'note': (
                'Parent run: correctness suite incl. graph exit-code, restart, daemon and inline '
                'tests; its 32 skips were the timing cases (--benchmark-skip active). '
                'This run is the complement: the 32 timing cases, with correctness deselected-by-skip '
                'via --benchmark-only. Per-case finished_ok and descendant counts are embedded in '
                'each case extra_info.provenance below.'
            ),
        },
        'restart_semantics': {
            'shared_child': 'Both implementations drive the same real FlakyStep child: two transient '
            'failures then success on recover; same attempt schedule (0, 1, 2); same result value 1.5.',
            'input_provenance_preserved': 'The shared FlakyStep forwards its already-stored ``result`` '
            'input Float unchanged on the successful run (step.outputs.value uuid == shared input '
            'uuid; no new Data created by the step, no CREATE link from any workflow node). The '
            'work-chain root returns that very node (root outputs.value uuid == shared uuid). '
            'Step-level computation provenance is therefore preserved on both sides.',
            'root_output_rewrap': 'The graph root ``result`` is NOT the shared input node: the '
            '``ensure_recovered`` calcfunction task consumes the recovered float value and creates '
            'a NEW Float node, and the graph root returns the ensure output. Root node identity '
            'therefore differs from the shared step node (uuid differs) while the value is '
            'identical (1.5) and the successful step runs keep shared-uuid provenance.',
            'no_exact_operation_equality': 'Workload-matched, not operation-identical: the graph runs '
            'exactly 7 extra helper calcfunctions with no work-chain counterpart (zero + 3 '
            'should_restart + 2 advance + ensure_recovered), carries graph declaration/loop '
            'plumbing, and uses a different failure vocabulary (below). Only the child-step count, '
            'attempt schedule, success value, and step-level provenance are matched.',
            'process_counts': 'Work-chain side per run: 3 FlakyStep WorkChains, 0 calcfunctions. '
            'Graph side per run: 3 FlakyStep WorkChains + exactly 7 helper calcfunctions '
            '(zero + 3 should_restart + 2 advance + ensure_recovered), 0 child graph nodes. '
            'Helper tasks are extra processes with no work-chain counterpart; see per-case provenance.',
            'failure_status_difference': 'Deliberate vocabulary split on failure paths (not timed): '
            'the work chain reports exit 401/402 while the graph reports 400 through its raising ensure.',
            'direct_ir_vs_authoring': 'Local graph-direct-ir reuses one warmed stored declaration Dict '
            '(no per-round serialization). Daemon graph-submitted pays authoring cost per round '
            '(get_launch_inputs inside timing); daemon direct-ir pays a fresh Dict construction per '
            'round from a pre-serialized template (stored-declaration path).',
            'ir_serialization_scope': 'Warmed build() cache hit + to_dict/from_dict round trip only; '
            'cold graph compilation cost is intentionally outside timing.',
        },
        'workload_mismatch_limitations': [
            'Graphs always declare outputs while the original WorkChains return nothing; loop benchmarks '
            'return their final counter and threaded benchmarks return collected results.',
            'Graph loop state rewinds through tasks: each loop benchmark spends one decrement plus one '
            'is_positive calcfunction task per iteration (plus one final check); the originals keep '
            'counter/iter in memory with zero tasks per no-op step.',
            'One GraphProcess executes the whole graph: nested graphs, loop iterations, branch arms and '
            'map elements run as scopes with hierarchical call labels, never as child graph nodes.',
            'Each par_map collection dispatches one collector calcfunction with no original counterpart; '
            'inline variants remove control tasks (expressions instead) but keep the collector.',
            'threaded-calcjob-loop is statically unrolled to exactly four placements on the graph side only.',
            'Graph calcjob placements require per-placement metadata.options (resources/withmpi) under '
            'task_metadata; WorkChain originals submit without explicit options. Both run the real '
            'ArithmeticAddCalculation (/bin/bash, sum == 3).',
            'Daemon submitted timing includes broker scheduling, daemon pickup and 0.1 s-granularity '
            'completion polling; it measures end-to-end submission latency, not engine speed alone.',
            'Single machine, single run, warm caches: numbers are comparative within this run, not '
            'absolute performance claims. Month-old idle orphan processes from other environments '
            'existed on the shared host (not test runs); load average at start was 0.85 on 28 cores.',
        ],
        'artifacts': {
            'raw_pytest_benchmark_json': 'reports/graph-restart-study/benchmarks/raw-pytest-benchmark.json',
            'run_log': 'reports/graph-restart-study/benchmarks/run.log',
            'report_json': 'reports/graph-restart-study/benchmarks/report.json',
            'report_md': 'reports/graph-restart-study/benchmarks/report.md',
            'derive_script': 'reports/graph-restart-study/benchmarks/derive_report.py',
            'env_snapshot': 'reports/graph-restart-study/benchmarks/env-snapshot.txt',
            'paths_relative_to': 'repository root',
        },
        'cases': cases,
    }

    (BENCH_DIR / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'wrote report.json with {len(cases)} cases; phases: {{k: len(v) for k, v in {by_phase!r}.items()}}')


if __name__ == '__main__':
    main()
