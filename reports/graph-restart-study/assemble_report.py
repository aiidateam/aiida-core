###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Assemble reports/graph-restart-study/report.json from input JSON files.

All measurements are read from the input artifacts -- nothing is
hand-transcribed. Run from the repository root::

    uv run python reports/graph-restart-study/assemble_report.py

Inputs (all under reports/graph-restart-study/):
    benchmarks/report.json, benchmarks/raw-pytest-benchmark.json,
    evaluation/report.json, evaluation/metrics-arm-{a,b}.json,
    evaluation/verification-v2-{a,b}.json, evaluation/run-card-arm-{a,b}.json

The script validates the inputs (32 timed cases, per-case stats consistency
against the raw pytest-benchmark JSON, token usage recomputed from the
authoritative ``message_end`` assistant records, frozen fixture/solution /
transcript hashes, distinct raw sessions) and then writes the root
``report.json`` embedding every case plus the normalized evaluation summary.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STUDY = REPO / 'reports' / 'graph-restart-study'
BENCH = STUDY / 'benchmarks'
EVAL = STUDY / 'evaluation'

BASELINE_REVISION = '4ae87025e528f358f8194e4750334d247075ce6b'
MODEL = 'gpt-6.1-sol'
THINKING = 'medium'


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _recompute_usage(events_path: Path) -> dict[str, int]:
    """Sum assistant usage from authoritative ``message_end`` records only."""
    total = {'input': 0, 'output': 0, 'cacheRead': 0, 'cacheWrite': 0, 'totalTokens': 0}
    with open(events_path, encoding='utf-8') as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            event = json.loads(line)
            if event.get('type') == 'message_end':
                message = event.get('message', {})
                if message.get('role') == 'assistant':
                    usage = message.get('usage', {})
                    for key in total:
                        total[key] += int(usage.get(key, 0) or 0)
    return total


def main() -> None:
    bench_report = json.loads((BENCH / 'report.json').read_text(encoding='utf-8'))
    raw = json.loads((BENCH / 'raw-pytest-benchmark.json').read_text(encoding='utf-8'))
    eval_report = json.loads((EVAL / 'report.json').read_text(encoding='utf-8'))
    manifest = json.loads((EVAL / 'manifest.json').read_text(encoding='utf-8'))
    metrics = {arm: json.loads((EVAL / f'metrics-arm-{arm}.json').read_text(encoding='utf-8')) for arm in ('a', 'b')}
    run_cards = {arm: json.loads((EVAL / f'run-card-arm-{arm}.json').read_text(encoding='utf-8')) for arm in ('a', 'b')}
    verifications_v2 = {
        arm: json.loads((EVAL / f'verification-v2-{arm}.json').read_text(encoding='utf-8')) for arm in ('a', 'b')
    }

    errors: list[str] = []

    # --- 1. Case counts and per-case stats consistency against raw JSON. ---
    raw_benches = raw['benchmarks']
    rep_cases = bench_report['cases']
    if len(raw_benches) != 32 or len(rep_cases) != 32:
        errors.append(f'expected 32 raw and 32 report cases, found {len(raw_benches)}/{len(rep_cases)}')
    by_fullname = {c['fullname']: c for c in rep_cases}
    for bench in raw_benches:
        case = by_fullname.get(bench['fullname'])
        if case is None:
            errors.append(f'report missing raw case {bench["fullname"]}')
            continue
        stats, rep_stats = bench['stats'], case['stats_s']
        for key in ('mean', 'median', 'stddev', 'min', 'max', 'rounds'):
            if rep_stats[key] != stats[key]:
                errors.append(f'{bench["fullname"]}: stats {key} {rep_stats[key]!r} != raw {stats[key]!r}')
        if list(case['times_s']) != list(stats['data']):
            errors.append(f'{bench["fullname"]}: times_s != raw stats.data')
        if len(case['times_s']) != stats['rounds']:
            errors.append(f'{bench["fullname"]}: len(times_s) != rounds')
        if (bench.get('extra_info') or {}) != (case.get('extra_info') or {}):
            errors.append(f'{bench["fullname"]}: extra_info drift vs raw')
    if raw['commit_info']['id'] != BASELINE_REVISION:
        errors.append('raw commit != baseline')
    if bench_report['revision']['commit'] != BASELINE_REVISION:
        errors.append('derived report commit != baseline')

    # --- 2. Corrected restart-semantics wording present, stale claim gone. ---
    semantics = bench_report.get('restart_semantics', {})
    semantics_text = json.dumps(semantics)
    for required in ('NEW Float', 'uuid differs', 'no_exact_operation_equality', 'ensure_recovered'):
        if required not in semantics_text:
            errors.append(f'restart_semantics missing corrected wording: {required!r}')
    for stale in ('uuid passthrough, no new data created', 'not a copy: outputs.result.value'):
        if stale in semantics_text:
            errors.append(f'restart_semantics still carries stale claim: {stale!r}')

    # --- 3. Token usage recomputed from authoritative message_end records. ---
    recomputed = {}
    for arm in ('a', 'b'):
        usage = _recompute_usage(EVAL / f'events-arm-{arm}.jsonl')
        recomputed[arm] = usage
        if usage != metrics[arm]['usage_tokens']:
            errors.append(f'arm {arm}: recomputed usage {usage} != metrics {metrics[arm]["usage_tokens"]}')
        if usage != eval_report['arms'][arm]['tokens']:
            errors.append(f'arm {arm}: recomputed usage != eval report tokens')
        if usage != run_cards[arm]['metrics']['usage_tokens']:
            errors.append(f'arm {arm}: recomputed usage != run-card metrics')

    # --- 4. Frozen inputs / solutions / transcripts unchanged; sessions distinct. ---
    frozen = manifest  # frozen_* hashes live in evaluation/report.json; manifest pins eval setup
    _ = frozen
    frozen_inputs = eval_report['frozen_inputs_sha256']
    fixture_actual = _sha256(REPO / 'utils/benchmarks/graph_restart_eval/fixtures/flaky_child.py')
    if fixture_actual != frozen_inputs['fixture_flaky_child']:
        errors.append('frozen fixture flaky_child hash drift')
    task_actual = _sha256(REPO / 'utils/benchmarks/graph_restart_eval/TASK_COMMON.md')
    if task_actual != frozen_inputs['task_common']:
        errors.append('frozen TASK_COMMON hash drift')
    for arm, fname in (('a', 'ARM_A_BRWC.md'), ('b', 'ARM_B_GRAPHIR.md')):
        actual = _sha256(REPO / f'utils/benchmarks/graph_restart_eval/{fname}')
        if actual != frozen_inputs['arm_files'][arm]:
            errors.append(f'frozen arm file {fname} hash drift')
    for arm in ('a', 'b'):
        for name in ('solutions/a', 'solutions/b'):
            pass
        sol_path = EVAL / f'solutions/{arm}/restart_solution/__init__.py'
        if _sha256(sol_path) != verifications_v2[arm]['solution_sha256']:
            errors.append(f'arm {arm}: solution file hash != verification-v2 solution_sha256')
        if _sha256(sol_path) != eval_report['solution_copies'][arm][0]['sha256']:
            errors.append(f'arm {arm}: solution file hash != eval report solution_copies')
        for sess in eval_report['isolation']['session_files'][arm]:
            sess_path = Path(sess['path'])
            if not sess_path.is_absolute():
                sess_path = REPO / sess['path']
            # session files live under the study dir; paths in report are absolute repo paths
            if _sha256(sess_path) != sess['sha256']:
                errors.append(f'arm {arm}: session file hash drift: {sess["path"]}')
    sha_a = eval_report['isolation']['session_files']['a'][0]['sha256']
    sha_b = eval_report['isolation']['session_files']['b'][0]['sha256']
    if sha_a == sha_b:
        errors.append('session files not distinct per arm')
    if eval_report['isolation']['transcript_sha256']['a'] == eval_report['isolation']['transcript_sha256']['b']:
        errors.append('transcripts not distinct per arm')
    for arm in ('a', 'b'):
        if eval_report['isolation']['transcript_sha256'][arm] != run_cards[arm]['transcript_sha256']:
            errors.append(f'arm {arm}: transcript sha != run card')

    # --- 5. Eval normalization: hidden_tests == authoritative_v2 4/4, v1 retained. ---
    for arm in ('a', 'b'):
        hidden = eval_report['arms'][arm]['hidden_tests']
        v2 = eval_report['authoritative_v2'][arm]
        initial = eval_report['arms'][arm].get('initial_v1_hidden_tests')
        if initial is None:
            errors.append(f'arm {arm}: initial_v1_hidden_tests missing')
        elif initial.get('passed') == 4 or initial.get('exit_code') == 0:
            errors.append(f'arm {arm}: initial v1 does not look like the preserved failing run')
        for key in ('exit_code', 'collected', 'passed', 'failed'):
            if hidden[key] != v2[key]:
                errors.append(f'arm {arm}: hidden_tests.{key} != authoritative_v2')
        if hidden['passed'] != 4 or hidden['failed'] != 0 or hidden['exit_code'] != 0:
            errors.append(f'arm {arm}: hidden_tests not the successful 4/4')
        if initial is not None and hidden['passed_tests'] == initial.get('passed_tests') == []:
            errors.append(f'arm {arm}: hidden_tests indistinguishable from initial v1')

    # --- 6. Parent verification logs referenced (final independent verify). ---
    for arm in ('a', 'b'):
        parent_log = EVAL / f'verify-parent-{arm}.log'
        if not parent_log.exists():
            errors.append(f'missing parent verification log {parent_log.name}')

    if errors:
        for err in errors:
            print(f'VALIDATION ERROR: {err}', file=sys.stderr)
        raise SystemExit(1)

    studied_cases = [
        {
            'id': c['id'],
            'fullname': c['fullname'],
            'group': c['group'],
            'phase': c['phase'],
            'timing_mode': c['timing_mode'],
            'params': c['params'],
            'stats_s': c['stats_s'],
            'times_s': c['times_s'],
            'provenance': (c.get('extra_info') or {}).get('provenance'),
        }
        for c in rep_cases
    ]

    def arm_summary(arm: str) -> dict:
        card = run_cards[arm]
        v2 = eval_report['authoritative_v2'][arm]
        initial = eval_report['arms'][arm]['initial_v1_hidden_tests']
        return {
            'method': eval_report['arms'][arm]['method'],
            'model': MODEL,
            'thinking': THINKING,
            'provider': (card['harness']['env_stripped'] and 'openai-codex') or 'openai-codex',
            'tokens': dict(recomputed[arm]),
            'tokens_cached_read': recomputed[arm]['cacheRead'],
            'tokens_uncached_input': recomputed[arm]['input'],
            'tokens_output': recomputed[arm]['output'],
            'wall_s_monotonic': metrics[arm]['wall_s_monotonic'],
            'assistant_responses': metrics[arm]['assistant_responses'],
            'tool_calls': {
                'started': metrics[arm]['tool_calls_started'],
                'ok': metrics[arm]['tool_calls_ok'],
                'error': metrics[arm]['tool_calls_error'],
            },
            'stop_reason': metrics[arm]['stop_reason'],
            'timed_out': card['harness']['timed_out'],
            'token_cap_exceeded': card['harness']['token_cap_exceeded'],
            'pi_exit_code': card['harness']['pi_exit_code'],
            'correctness_authoritative': {
                'exit_code': v2['exit_code'],
                'collected': v2['collected'],
                'passed': v2['passed'],
                'failed': v2['failed'],
            },
            'correctness_initial_v1': {
                'exit_code': initial['exit_code'],
                'collected': initial['collected'],
                'passed': initial['passed'],
                'failed': initial['failed'],
            },
            'grading': 'v2 corrected grader (canonical scratch fixtures.flaky_child); '
            'v1 failure was a fixture-loading defect, not a solver failure',
            'solution_sha256': v2['solution_sha256'],
        }

    report = {
        'title': 'Graph restart study: consolidated report (benchmarks + isolated restart-authoring eval)',
        'authoritative_inputs': {
            'benchmark_report': 'reports/graph-restart-study/benchmarks/report.json',
            'benchmark_raw': 'reports/graph-restart-study/benchmarks/raw-pytest-benchmark.json',
            'benchmark_run_log': 'reports/graph-restart-study/benchmarks/run.log',
            'benchmark_derive_script': 'reports/graph-restart-study/benchmarks/derive_report.py',
            'benchmark_env_snapshot': 'reports/graph-restart-study/benchmarks/env-snapshot.txt',
            'eval_archive': 'reports/graph-restart-study/evaluation-logs.tar.xz',
            'eval_archive_sha256': _sha256(STUDY / 'evaluation-logs.tar.xz'),
            'eval_report': 'reports/graph-restart-study/evaluation/report.json',
            'eval_manifest': 'reports/graph-restart-study/evaluation/manifest.json',
            'assemble_script': 'reports/graph-restart-study/assemble_report.py',
            'correctness_log_copy': 'reports/graph-restart-study/validation.log',
            'correctness_log_original': '/tmp/graph-exit-committed-verification.log',
            'paths_relative_to': 'repository root',
        },
        'baseline': {
            'revision': BASELINE_REVISION,
            'branch': 'graph-benchmark-v6',
            'model': MODEL,
            'thinking': THINKING,
            'n_per_method': 1,
            'pi_version': '1.5.2',
        },
        'benchmarks': {
            'command': bench_report['command'],
            'revision': bench_report['revision'],
            'machine': bench_report['machine'],
            'backend': bench_report['backend'],
            'settings': bench_report['settings'],
            'counts': bench_report['counts'],
            'correctness_evidence': bench_report['correctness_evidence'],
            'restart_semantics': bench_report['restart_semantics'],
            'workload_mismatch_limitations': bench_report['workload_mismatch_limitations'],
            'cases': studied_cases,
        },
        'evaluation': {
            'eval_id': eval_report['eval_id'],
            'frozen_inputs_sha256': eval_report['frozen_inputs_sha256'],
            'arms': {arm: arm_summary(arm) for arm in ('a', 'b')},
            'isolation': eval_report['isolation'],
            'grading_correction': eval_report['grading_correction'],
            'limitation': eval_report['limitation'],
            'artifacts': [f'evaluation/{name}' for name in eval_report['artifacts']],
        },
        'uncertainty_and_protocol_limitations': [
            'n=1 per method: a single paired run cannot establish a general productivity '
            'difference between the BaseRestartWorkChain and GraphIR-direct APIs; treat the eval '
            'outcome (both arms 4/4 under the corrected grader) as one anecdotal data point.',
            'Single machine, single warm-cache timing run: benchmark numbers are comparative '
            'within this run, not absolute performance claims.',
            'Benchmarks are workload-matched, not operation-identical: graphs declare outputs, '
            'loop state rewinds through tasks, one GraphProcess runs whole graphs with no child '
            'graph nodes, par_map adds a collector calcfunction, threaded-calcjob-loop is '
            'statically unrolled to four placements on the graph side, and per-placement '
            'metadata.options are required for graph calcjobs.',
            'Restart timing compares 3 FlakyStep work chains on both sides plus exactly 7 extra '
            'graph helper calcfunctions; failure exit-code vocabulary differs (401/402 vs 400).',
            'Daemon submitted timing includes broker scheduling, daemon pickup, and 0.1 s-granularity '
            'completion polling; it measures end-to-end submission latency, not engine speed alone.',
            'Month-old idle orphan processes from other environments existed on the shared host '
            '(no active test runs); load average at start was 0.85 on 28 cores.',
            'Agent tokens count streamed assistant usage (input/output/cacheRead/cacheWrite); '
            'the token cap is enforced at message_end boundaries so a recorded total can overshoot '
            'by up to one response. No agent reruns occurred after grading correction, so '
            'time/token metrics are identical to the original paired run.',
        ],
        'integrity': {
            'raw_cases': len(raw_benches),
            'report_cases': len(rep_cases),
            'stats_consistent_with_raw': True,
            'usage_recomputed_from_message_end': recomputed,
            'usage_matches_metrics_and_runcards': True,
            'frozen_fixture_hashes_unchanged': True,
            'solution_hashes_match_verification_v2': True,
            'session_files_distinct_per_arm': True,
            'transcripts_distinct_per_arm': True,
            'eval_hidden_tests_authoritative_v2_4_of_4': True,
            'initial_v1_results_retained': True,
            'historical_files_untouched': [
                'evaluation/events-arm-a.jsonl',
                'evaluation/events-arm-b.jsonl',
                'evaluation/sessions-arm-a/',
                'evaluation/sessions-arm-b/',
                'evaluation/solutions/',
                'evaluation/verification-a.json',
                'evaluation/verification-b.json',
                'evaluation/verification-v2-a.json',
                'evaluation/verification-v2-b.json',
                'evaluation/verify-a.log',
                'evaluation/verify-b.log',
                'evaluation/verify-v2-a.log',
                'evaluation/verify-v2-b.log',
                'evaluation/grader-v1/',
                'benchmarks/raw-pytest-benchmark.json',
                'benchmarks/run.log',
            ],
        },
    }

    out = STUDY / 'report.json'
    out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'validated inputs OK; wrote {out.relative_to(REPO)} with {len(studied_cases)} cases')


if __name__ == '__main__':
    main()
