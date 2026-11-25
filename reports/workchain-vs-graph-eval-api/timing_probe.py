###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Post-eval ABBA probe of unchanged graph tests; not included in agent solve metrics."""

import json
import os
import subprocess
import time
import typing as t
from pathlib import Path
from xml.etree import ElementTree

REPORT = Path(__file__).resolve().parent
ROOT = REPORT.parents[1]


class ProbeResult(t.TypedDict):
    """Measured execution of one fixed test suite."""

    label: str
    workers: int
    command: list[str]
    wall_seconds: float
    returncode: int
    tests_passed: int
    tests_total: int


def main() -> None:
    metrics = json.loads((REPORT / 'graph' / 'metrics.json').read_text())
    workspace = Path(metrics['workspace'])
    output = REPORT / 'test-timing-probe'
    output.mkdir(exist_ok=True)
    env = os.environ.copy()
    env.update(
        PYTHONPATH=f'{workspace / "src"}:{workspace}',
        UV_PROJECT_ENVIRONMENT=str(ROOT / '.venv'),
        AIIDA_PATH=str(output / 'aiida'),
    )
    results: list[ProbeResult] = []
    for index, workers in enumerate((0, 2, 2, 0), start=1):
        label = f'{index}-' + ('serial' if not workers else 'xdist-2')
        command = ['uv', 'run', '--no-sync', 'pytest', '--broker-backend=none', '-q']
        if workers:
            command += ['-n', str(workers)]
        xml_path = output / f'{label}.xml'
        command += ['tests/engine/processes/workflow_eval', f'--junitxml={xml_path}']
        started = time.monotonic()
        with (output / f'{label}.log').open('w') as log:
            completed = subprocess.run(
                command,
                cwd=workspace,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=240,
                check=False,
            )
        elapsed = time.monotonic() - started
        cases = list(ElementTree.parse(xml_path).getroot().iter('testcase'))
        passed = sum(all(case.find(tag) is None for tag in ('failure', 'error', 'skipped')) for case in cases)
        results.append(
            {
                'label': label,
                'workers': workers,
                'command': command,
                'wall_seconds': elapsed,
                'returncode': completed.returncode,
                'tests_passed': passed,
                'tests_total': len(cases),
            }
        )
        (output / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
        assert completed.returncode == 0 and passed == 30
    means = {
        str(workers): sum(row['wall_seconds'] for row in results if row['workers'] == workers) / 2 for workers in (0, 2)
    }
    summary = {
        'runs': results,
        'mean_wall_seconds': means,
        'reduction_percent': (1 - means['2'] / means['0']) * 100,
        'note': 'Post-hoc fixed-submission test execution, serial/parallel/parallel/serial order. '
        'No model calls or solution edits; excluded from agent solve times. '
        'Two repeats per mode are not a statistically powered benchmark.',
    }
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
