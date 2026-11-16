###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Execute one frozen workflow once in an isolated profile and report Linux RSS peaks.

The caller selects the source snapshot through PYTHONPATH. No pytest, coding agent,
external broker or persistent user profile participates in this measurement.
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import tempfile
import time
from importlib import import_module
from pathlib import Path


def memory_status() -> dict[str, int]:
    """Read Linux resident memory counters, preserving their native KiB unit."""
    values = {}
    for line in Path('/proc/self/status').read_text().splitlines():
        key, _, value = line.partition(':')
        if key in {'VmRSS', 'VmHWM'}:
            values[key] = int(value.split()[0])
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-json', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--cpu', type=int)
    args = parser.parse_args()
    case = json.loads(args.case_json)
    if (
        not isinstance(case, list)
        or len(case) != 4
        or any(type(value) is not int for value in case[:3])
        or type(case[3]) is not bool
        or case[2] < 0
    ):
        parser.error('case must be [initial: int, target: int, budget: nonnegative int, fast: bool]')
    if args.cpu is not None:
        os.sched_setaffinity(0, {args.cpu})
    initial, target, budget, fast = case
    with tempfile.TemporaryDirectory(prefix='aiida-execution-resources-') as temporary:
        os.environ['AIIDA_PATH'] = temporary
        from aiida.common.links import LinkType
        from aiida.engine import run_get_node
        from aiida.manage.configuration import create_profile, get_config, profile_context
        from aiida.orm import Bool, Int

        workflow = import_module('tests.engine.processes.workflow_eval.solution').workflow
        config = get_config(create=True)
        profile = create_profile(
            config,
            name='execution-resources',
            email='resources@localhost',
            storage_backend='core.sqlite_dos',
            storage_config={'filepath': str(Path(temporary) / 'storage')},
            broker_backend=None,
            is_test_profile=True,
        )
        profile.set_option('warnings.development_version', False)
        config.set_default_profile(profile.name)
        config.store()
        with profile_context(profile):
            inputs = {'initial': Int(initial), 'target': Int(target), 'max_steps': Int(budget), 'fast': Bool(fast)}
            before = memory_status()
            before_usage = resource.getrusage(resource.RUSAGE_SELF)
            try:
                # Reset only this child process's RSS high-water mark, never a host setting.
                Path('/proc/self/clear_refs').write_text('5\n')
            except OSError as error:
                peak_reset = {'supported': False, 'error': str(error)}
            else:
                peak_reset = {'supported': True, 'error': None}
            started = time.monotonic()
            outputs, node = run_get_node(workflow, inputs=inputs)
            elapsed = time.monotonic() - started
            after = memory_status()
            after_usage = resource.getrusage(resource.RUSAGE_SELF)
            report = outputs['result'].get_dict()
            stride = 2 if fast else 1
            attempts = min(budget, (abs(target - initial) + stride - 1) // stride)
            distance = min(abs(target - initial), attempts * stride)
            value = initial + (distance if target > initial else -distance)
            converged = value == target
            expected = {
                'value': value,
                'target': target,
                'attempts': attempts,
                'converged': converged,
                'mode': 'square' if converged else 'unfinished',
                'score': value**2 if converged else -1,
            }
            assert node.is_finished_ok and report == expected
            assert len(node.called) == attempts + 1
            assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []
            finalizers = [child for child in node.called if child.process_label == 'FinalizeWorkChain']
            assert len(finalizers) == 1
            assert outputs['result'].uuid == finalizers[0].outputs.result.uuid
            assert all(child.is_finished_ok for child in node.called)
            result = {
                'case': {'initial': initial, 'target': target, 'max_steps': budget, 'fast': fast},
                'pid': os.getpid(),
                'cpu_affinity': sorted(os.sched_getaffinity(0)),
                'workflow_wall_seconds': elapsed,
                'workflow_user_cpu_seconds': after_usage.ru_utime - before_usage.ru_utime,
                'workflow_system_cpu_seconds': after_usage.ru_stime - before_usage.ru_stime,
                'rss_before_workflow_kib': before['VmRSS'],
                'rss_after_workflow_kib': after['VmRSS'],
                'rss_peak_reset': peak_reset,
                'workflow_peak_rss_kib': after['VmHWM'] if peak_reset['supported'] else None,
                'process_peak_rss_through_workflow_completion_kib': max(before['VmHWM'], after['VmHWM']),
                'kernel_ru_maxrss_after_kib': after_usage.ru_maxrss,
                'root_finished_ok': node.is_finished_ok,
                'report': report,
                'called_children': len(node.called),
                'provenance_verified': True,
            }
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
