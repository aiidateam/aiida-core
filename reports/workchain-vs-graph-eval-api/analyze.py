###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Audit paired eval sessions, compare the previous pair, and extract effort traces."""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree

REPORT = Path(__file__).resolve().parent
PREVIOUS = REPORT.parent / 'workchain-vs-graph-eval-after'
ARMS = ('workchain', 'graph')


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + '\n')


def passed(case: ElementTree.Element) -> bool:
    return all(case.find(tag) is None for tag in ('failure', 'error', 'skipped'))


def interval_seconds(intervals: list[tuple[float, float]]) -> float:
    """Merge tool intervals rather than double-counting any parallel execution."""
    if not intervals:
        return 0.0
    intervals.sort()
    total = 0.0
    start, end = intervals[0]
    for next_start, next_end in intervals[1:]:
        if next_start <= end:
            end = max(end, next_end)
        else:
            total += end - start
            start, end = next_start, next_end
    return (total + end - start) / 1000


def trace(folder: Path) -> dict:
    metrics = read_json(folder / 'metrics.json')
    session_paths = list((folder / 'sessions').glob('*.jsonl'))
    assert len(session_paths) == 1
    entries = [json.loads(line) for line in session_paths[0].read_text().splitlines()]
    totals = dict.fromkeys(metrics['usage'], 0)
    arguments = {}
    calls: list[dict] = []
    results = []
    intervals = []
    discovered = True
    for entry in entries:
        message = entry.get('message', {})
        if message.get('role') == 'assistant':
            usage = message.get('usage', {})
            for key in totals:
                totals[key] += usage.get(key, 0)
            tools = []
            for content in message.get('content', []):
                if content.get('type') != 'toolCall':
                    continue
                args = content.get('arguments', {})
                arguments[content['id']] = {
                    'name': content['name'],
                    'path': args.get('path'),
                    'command': args.get('command'),
                    'offset': args.get('offset'),
                    'limit': args.get('limit'),
                    'discovery': discovered,
                }
                if content['name'] in {'write', 'edit'}:
                    discovered = False
                    arguments[content['id']]['discovery'] = False
                tools.append(arguments[content['id']])
            calls.append(
                {
                    'turn': len(calls) + 1,
                    'timestamp': entry['timestamp'],
                    'usage': usage,
                    'tools': tools,
                    'stop_reason': message.get('stopReason'),
                }
            )
        elif message.get('role') == 'toolResult':
            args = arguments.get(message.get('toolCallId'), {})
            output = '\n'.join(
                content.get('text', '') for content in message.get('content', []) if content.get('type') == 'text'
            )
            duration = message.get('durationMs', 0)
            end = message.get('timestamp')
            if isinstance(end, (int, float)) and duration:
                intervals.append((end - duration, end))
            results.append(
                {
                    **args,
                    'duration_seconds': duration / 1000,
                    'output_chars': len(output),
                    'output_lines': len(output.splitlines()),
                    'is_error': message.get('isError', False),
                    'graph_language_error': 'GraphLanguageError:' in output,
                    'test_command': 'pytest' in (args.get('command') or ''),
                    'summary': [
                        line
                        for line in output.splitlines()
                        if (' passed' in line or ' failed' in line or 'FAILED ' in line)
                    ],
                }
            )
    assert totals == metrics['usage']
    cases = list(ElementTree.parse(folder / 'validation.xml').getroot().iter('testcase'))
    acceptance = [case for case in cases if 'test_acceptance' in case.get('classname', '')]
    test_results = [result for result in results if result['test_command']]
    return {
        'session_header': entries[0],
        'usage_matches_metrics': True,
        'model_turns': len(calls),
        'tool_calls': sum(len(call['tools']) for call in calls),
        'tool_names': dict(Counter(result.get('name') for result in results)),
        'tool_output_chars': sum(result['output_chars'] for result in results),
        'discovery_output_chars': sum(result['output_chars'] for result in results if result.get('discovery')),
        'discovery_tools': [result for result in results if result.get('discovery')],
        'all_tools_seconds_sum': sum(result['duration_seconds'] for result in results),
        'tool_interval_union_seconds': interval_seconds(intervals),
        'test_commands': test_results,
        'test_tool_seconds_sum': sum(result['duration_seconds'] for result in test_results),
        'graph_language_errors': sum(result['graph_language_error'] for result in results),
        'tool_errors': sum(result['is_error'] for result in results),
        'acceptance_passed': sum(passed(case) for case in acceptance),
        'acceptance_total': len(acceptance),
        'all_tests_passed': sum(passed(case) for case in cases),
        'all_tests_total': len(cases),
        'cache_zero_turns': [call for call in calls if call['usage'].get('cacheRead', 0) == 0],
        'model_calls': calls,
        'tool_results': results,
    }


def main() -> None:
    previous = read_json(PREVIOUS / 'results.json')
    current = read_json(REPORT / 'results.json')
    comparison = {}
    current_settings = read_json(REPORT / 'run.json')
    previous_settings = read_json(PREVIOUS / 'run.json')
    matching_settings = {
        key: current_settings[key] == previous_settings[key]
        for key in ('provider', 'model', 'thinking', 'pi_version', 'paired_concurrent')
    }
    assert all(matching_settings.values())
    for arm in ARMS:
        assert (REPORT / arm / 'prompt.md').read_bytes() == (PREVIOUS / arm / 'prompt.md').read_bytes()
        before, after = previous[arm], current[arm]
        before_trace = trace(PREVIOUS / arm)
        after_trace = trace(REPORT / arm)
        assert after_trace['session_header'].get('parentSession') is None
        assert after_trace['session_header']['id'] != before_trace['session_header']['id']
        assert all(after['fixed_files_unchanged'].values())
        assert after['validation_returncode'] == 0
        assert after_trace['acceptance_passed'] == after_trace['acceptance_total'] == 13
        changes = {}
        for key in ('wall_seconds', 'provider_reported_cost_usd', 'assistant_messages', 'tool_calls'):
            changes[key] = (after[key] / before[key] - 1) * 100
        for key in before['usage']:
            if before['usage'][key]:
                changes[key] = (after['usage'][key] / before['usage'][key] - 1) * 100
        comparison[arm] = {
            'previous': before,
            'current': after,
            'change_percent': changes,
            'previous_trace': before_trace,
            'current_trace': after_trace,
        }
        write_json(REPORT / arm / 'trace.json', after_trace)
        session = next((REPORT / arm / 'sessions').glob('*.jsonl'))
        exported = subprocess.run(
            ['pi', '--no-extensions', '--no-mcp', '--export', str(session), str(REPORT / arm / 'session.html')],
            capture_output=True,
            text=True,
            check=False,
        )
        (REPORT / arm / 'export.log').write_text(exported.stdout + exported.stderr)
        assert exported.returncode == 0
    assert (
        comparison['graph']['current_trace']['session_header']['id']
        != (comparison['workchain']['current_trace']['session_header']['id'])
    )
    artifacts = {}
    for name in ('task.md', 'collaborators.py', 'test_acceptance.py'):
        unchanged = (REPORT / name).read_bytes() == (PREVIOUS / name).read_bytes()
        assert unchanged
        artifacts[name] = unchanged
    write_json(REPORT / 'comparison.json', comparison)
    write_json(
        REPORT / 'audit.json',
        {
            'task_and_evaluator_identical': artifacts,
            'same_model_and_harness_settings': matching_settings,
            'per_arm_prompts_identical': True,
            'distinct_new_sessions': True,
            'persisted_usage_matches_stream_usage': True,
            'all_common_acceptance_passed': True,
            'fixed_files_unchanged': True,
        },
    )
    rows = []
    for arm in ARMS:
        data = comparison[arm]
        old, new = data['previous'], data['current']
        rows.append(
            f'| {arm} | {old["wall_seconds"]:.1f} → {new["wall_seconds"]:.1f} | '
            f'{old["usage"]["totalTokens"]:,} → {new["usage"]["totalTokens"]:,} | '
            f'${old["provider_reported_cost_usd"]:.4f} → ${new["provider_reported_cost_usd"]:.4f} | '
            f'{old["assistant_messages"]} → {new["assistant_messages"]} |'
        )
    (REPORT / 'comparison.md').write_text(
        '# Comparison with the immediately previous eval\n\n'
        'Previous: `../workchain-vs-graph-eval-after/`, after the language improvements but before '
        'the private-IR/flat-input API and authoring guide changes.\n\n'
        '| Arm | Solve seconds: previous → current | Total tokens | Reported USD | Model turns |\n'
        '|---|---:|---:|---:|---:|\n' + '\n'.join(rows) + '\n\n'
        'Both arms pass the same 13 acceptance cases. Total tokens include cached context; '
        'detailed categories, percentage changes and effort traces are in `comparison.json`.\n\n'
        'One run per style per revision cannot establish statistical significance or causation. '
        'Read `analysis.md` for evidence-backed remaining improvements and limitations.\n'
    )


if __name__ == '__main__':
    main()
