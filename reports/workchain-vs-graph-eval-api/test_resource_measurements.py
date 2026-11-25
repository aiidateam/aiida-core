###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Validate counter parsing and unavailable-data handling independently of hardware permission."""

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('resource_measurements', HERE / 'measure_resources.py')
assert SPEC is not None and SPEC.loader is not None
MEASURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MEASURE)


def test_acceptance_matrix_is_reused() -> None:
    """The profiler takes its cases from the same evaluator used for the agent runs."""
    cases = MEASURE.acceptance_cases(HERE / 'test_acceptance.py')
    assert len(cases) == 13
    assert cases[0] == (0, 5, 8, False)
    assert cases[-1] == (2, 0, 1, True)


def test_perf_parser_distinguishes_zero_and_unavailable(tmp_path: Path) -> None:
    """Real zero counts remain numbers; unavailable and missing counters stay null."""
    csv = tmp_path / 'counters.csv'
    csv.write_text(
        '# perf stat delimiter output\n'
        '0;;L1-dcache-loads:u;1000000;100.00;;\n'
        '<not supported>;;L1-dcache-load-misses:u;0;0.00;;\n'
        '42;;l2_rqsts.references:u;2000000;50.00;;\n'
        '7;;l2_rqsts.miss:u;2000000;50.00;;\n'
        '<not counted>;;LLC-loads:u;0;0.00;;\n'
    )
    events = [event for _, accesses, misses in MEASURE.EVENTS for event in (accesses, misses)]
    counters = MEASURE.parse_perf(csv, events)
    assert counters['L1-dcache-loads:u'] == {'count': 0, 'status': 'measured', 'running_percent': 100.0}
    assert counters['L1-dcache-load-misses:u']['count'] is None
    assert counters['L1-dcache-load-misses:u']['status'] == 'not_supported'
    assert counters['LLC-loads:u']['status'] == 'not_counted'
    assert counters['LLC-load-misses:u']['status'] == 'not_reported'
    levels = MEASURE.cache_levels(counters)
    assert levels['L1_data']['status'] == 'unavailable'
    assert levels['L1_data']['miss_rate_percent'] is None
    assert levels['L2']['accesses'] == 42
    assert levels['L2']['misses'] == 7
    assert levels['L2']['miss_rate_percent'] == pytest.approx(100 / 6)
    assert counters['l2_rqsts.references:u']['running_percent'] == 50.0


def test_no_cache_events_does_not_mean_zero_usage() -> None:
    """Permission failures cannot be reported as zero misses or zero accesses."""
    for level in MEASURE.cache_levels({}, 'permission denied').values():
        assert level['accesses'] is None
        assert level['misses'] is None
        assert level['miss_rate_percent'] is None
        assert level['status'] == 'unavailable'
        assert level['reason'] == 'permission denied'


def test_zero_accesses_has_no_miss_rate(tmp_path: Path) -> None:
    """A measured zero denominator does not manufacture a percentage."""
    csv = tmp_path / 'zero.csv'
    csv.write_text('0;;L1-dcache-loads:u;1;100.00;;\n0;;L1-dcache-load-misses:u;1;100.00;;\n')
    counters = MEASURE.parse_perf(csv, ['L1-dcache-loads:u', 'L1-dcache-load-misses:u'])
    level = MEASURE.cache_levels(counters)['L1_data']
    assert level['status'] == 'measured'
    assert level['accesses'] == level['misses'] == 0
    assert level['miss_rate_percent'] is None


@pytest.mark.parametrize('case', [[0, 1, 1, 1], [0, 1, -1, True], [0.0, 1, 1, True]])
def test_invalid_case_rejected_before_workflow_import(case: list, tmp_path: Path) -> None:
    """The worker rejects invalid profiling inputs without touching any AiiDA profile."""
    output = tmp_path / 'unused.json'
    result = subprocess.run(
        [
            'uv',
            'run',
            '--no-sync',
            'python',
            str(HERE / 'profile_execution.py'),
            '--case-json',
            json.dumps(case),
            '--output',
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert 'case must be' in result.stderr
    assert not output.exists()
