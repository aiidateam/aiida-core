###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Corrected (v2) hidden verification CLI for the restart evaluation.

Tracked grader source (committed) — never copy into solver worktrees, never
show to solvers. The harness physically removes this directory from every
fresh solver checkout before the solve starts. Run only after both agents finish::

    uv run python utils/benchmarks/graph_restart_eval/grading/verify_arm.py \\
        --solution-dir <arm worktree>/eval-scratch-a/restart_solution --arm a

Uses the repository's `presto` setup (SQLite storage, ZeroMQ broker: no
external services) with the AiiDA pytest fixtures plugin explicitly loaded.
Exits non-zero when any acceptance test fails.

Grading correction v2 (fixture-loading infrastructure ONLY): runs the
corrected `grading/test_acceptance.py`, which validates the scratch
`fixtures/flaky_child.py` SHA-256 against the frozen eval fixture and imports
the canonical scratch `fixtures.flaky_child` module (under both legal import
aliases) before loading the solution. Acceptance semantics are unchanged.
"""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parents[1]
TEST_FILE = EVAL_DIR / 'grading' / 'test_acceptance.py'


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solution-dir', required=True, help='Path to the arm restart_solution/ package.')
    parser.add_argument('--arm', required=True, choices=('a', 'b'))
    parser.add_argument('--broker-backend', default='zmq', choices=('rmq', 'zmq', 'none'))
    parser.add_argument('--db-backend', default='sqlite', choices=('sqlite', 'psql'))
    args = parser.parse_args()

    solution_dir = Path(args.solution_dir)
    if not (solution_dir / '__init__.py').is_file():
        msg = f'missing restart_solution package: {solution_dir}/__init__.py'
        raise SystemExit(msg)
    repo_root = Path(
        subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True, check=True
        ).stdout.strip()
    )
    env = dict(os.environ)
    env['ARM_SOLUTION_DIR'] = str(solution_dir)
    env['ARM_ID'] = args.arm
    cmd = [
        'uv',
        'run',
        'python',
        '-m',
        'pytest',
        '-p',
        'aiida.tools.pytest_fixtures',
        '--broker-backend',
        args.broker_backend,
        '--db-backend',
        args.db_backend,
        '-m',
        'presto',
        str(TEST_FILE),
    ]
    proc = subprocess.run(cmd, cwd=repo_root, env=env, check=False)
    raise SystemExit(proc.returncode)


if __name__ == '__main__':
    main()
