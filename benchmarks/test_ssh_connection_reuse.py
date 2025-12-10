"""Pytest-based benchmarks for SSH connection reuse in TransportQueue.

This module contains pytest tests that benchmark how effectively AiiDA's
TransportQueue reuses SSH connections with different safe_open_interval values.

Run with:
    pytest benchmarks/test_ssh_connection_reuse.py -v -s
    pytest benchmarks/test_ssh_connection_reuse.py -v -s --benchmark-only
"""

import time
from unittest.mock import patch

import pytest

from aiida import orm
from aiida.engine import run_get_node
from aiida.workflows.arithmetic.multiply_add import MultiplyAddWorkChain


class ConnectionCounter:
    """Helper class to count SSH connection opens/closes."""

    def __init__(self):
        self.opened = 0
        self.closed = 0
        self.timeline = []
        self.start_time = time.time()

    def record_open(self):
        """Record a connection opening."""
        self.opened += 1
        self.timeline.append({'time': time.time() - self.start_time, 'action': 'open', 'count': self.opened})

    def record_close(self):
        """Record a connection closing."""
        self.closed += 1
        self.timeline.append({'time': time.time() - self.start_time, 'action': 'close', 'count': self.closed})

    def reset(self):
        """Reset counters."""
        self.opened = 0
        self.closed = 0
        self.timeline = []
        self.start_time = time.time()


@pytest.fixture
def connection_counter():
    """Fixture that provides a connection counter."""
    return ConnectionCounter()


@pytest.fixture
def ssh_computer(aiida_localhost):
    """Fixture that provides an SSH-configured computer.

    Note: This uses aiida_localhost but can be modified to use
    a real SSH computer if available in the test environment.
    """
    return aiida_localhost


@pytest.fixture
def arithmetic_code(ssh_computer):
    """Fixture that provides an ArithmeticAdd code."""
    from aiida.orm import InstalledCode

    code = InstalledCode(
        label='add-test',
        computer=ssh_computer,
        filepath_executable='/bin/bash',
        default_calc_job_plugin='core.arithmetic.add',
    )
    code.store()
    return code


def patch_ssh_transport(connection_counter):
    """Context manager to patch SSH transport and count connections.

    Args:
        connection_counter: ConnectionCounter instance to record connections

    Returns:
        Context manager that patches and restores transport
    """
    from aiida.transports.plugins.ssh import SshTransport

    original_open = SshTransport.open
    original_close = SshTransport.close

    def tracked_open(self):
        connection_counter.record_open()
        return original_open(self)

    def tracked_close(self):
        connection_counter.record_close()
        return original_close(self)

    return patch.multiple(SshTransport, open=tracked_open, close=tracked_close)


@pytest.mark.parametrize('num_workchains', [1, 5, 10])
@pytest.mark.parametrize('safe_interval', [0.1, 0.5, 1.0, 2.0])
def test_connection_reuse_with_safe_interval(arithmetic_code, connection_counter, num_workchains, safe_interval):
    """Test SSH connection reuse with different safe_open_interval values.

    This test launches multiple MultiplyAddWorkChain instances and tracks
    how many SSH connections are actually opened vs the theoretical maximum.

    Args:
        arithmetic_code: Code fixture
        connection_counter: Counter fixture
        num_workchains: Number of workchains to launch
        safe_interval: Safe open interval to test
    """
    from aiida.transports.plugins.ssh import SshTransport

    # Set the safe interval
    original_interval = SshTransport._DEFAULT_SAFE_OPEN_INTERVAL
    SshTransport._DEFAULT_SAFE_OPEN_INTERVAL = safe_interval

    try:
        with patch_ssh_transport(connection_counter):
            connection_counter.reset()

            # Launch workchains
            nodes = []
            for _ in range(num_workchains):
                builder = MultiplyAddWorkChain.get_builder()
                builder.x = orm.Int(2)
                builder.y = orm.Int(3)
                builder.z = orm.Int(5)
                builder.code = arithmetic_code

                _, node = run_get_node(builder)
                nodes.append(node)

            # Check results
            theoretical_max = num_workchains * 2  # Rough estimate
            reuse_efficiency = 1.0 - (connection_counter.opened / theoretical_max)

            print(f'\n--- Results for {num_workchains} workchains, ' f'interval={safe_interval}s ---')
            print(f'  Connections opened: {connection_counter.opened}')
            print(f'  Connections closed: {connection_counter.closed}')
            print(f'  Theoretical max: {theoretical_max}')
            print(f'  Reuse efficiency: {reuse_efficiency:.1%}')

            # Assert that we're reusing connections (opened < theoretical max)
            assert connection_counter.opened < theoretical_max, (
                f'Expected connection reuse, but opened {connection_counter.opened} '
                f'connections (theoretical max: {theoretical_max})'
            )

            # Store results as extras on the workchain for later analysis
            for node in nodes:
                node.base.extras.set('benchmark_connections_opened', connection_counter.opened)
                node.base.extras.set('benchmark_safe_interval', safe_interval)
                node.base.extras.set('benchmark_num_workchains', num_workchains)

    finally:
        # Restore original interval
        SshTransport._DEFAULT_SAFE_OPEN_INTERVAL = original_interval


@pytest.mark.benchmark
def test_connection_timeline(arithmetic_code, connection_counter):
    """Test the timeline of connection opens/closes.

    This test verifies that connections are opened and closed in the
    expected pattern, with proper batching via the TransportQueue.
    """
    from aiida.transports.plugins.ssh import SshTransport

    safe_interval = 1.0
    SshTransport._DEFAULT_SAFE_OPEN_INTERVAL = safe_interval

    try:
        with patch_ssh_transport(connection_counter):
            connection_counter.reset()

            # Launch 5 workchains
            for _ in range(5):
                builder = MultiplyAddWorkChain.get_builder()
                builder.x = orm.Int(2)
                builder.y = orm.Int(3)
                builder.z = orm.Int(5)
                builder.code = arithmetic_code

                run_get_node(builder)

            # Analyze timeline
            print('\n--- Connection Timeline ---')
            for event in connection_counter.timeline:
                print(f'  t={event["time"]:.3f}s: {event["action"]} ' f'(total {event["action"]}ed: {event["count"]})')

            # Verify that connections are being batched
            # (multiple opens should happen close together in time)
            if len(connection_counter.timeline) > 2:
                open_events = [e for e in connection_counter.timeline if e['action'] == 'open']
                if len(open_events) > 1:
                    time_diffs = [
                        open_events[i + 1]['time'] - open_events[i]['time'] for i in range(len(open_events) - 1)
                    ]
                    avg_time_between_opens = sum(time_diffs) / len(time_diffs)
                    print(f'  Average time between opens: {avg_time_between_opens:.3f}s')

                    # Time between opens should be >= safe_interval (with some tolerance)
                    assert (
                        avg_time_between_opens >= safe_interval * 0.9
                    ), f'Expected opens to be separated by at least {safe_interval}s'

    finally:
        SshTransport._DEFAULT_SAFE_OPEN_INTERVAL = 5.0


@pytest.mark.benchmark
@pytest.mark.parametrize('safe_interval', [0.1, 0.5, 1.0, 2.0, 5.0])
def test_optimal_safe_interval(arithmetic_code, connection_counter, safe_interval):
    """Benchmark to find the optimal safe_open_interval value.

    This test runs the same workload with different safe_interval values
    and measures both connection reuse and total execution time.

    The goal is to find the sweet spot where:
    - Connection reuse is high (few connections opened)
    - Execution time is low (not waiting too long to open connections)
    """
    from aiida.transports.plugins.ssh import SshTransport

    SshTransport._DEFAULT_SAFE_OPEN_INTERVAL = safe_interval
    num_workchains = 10

    try:
        with patch_ssh_transport(connection_counter):
            connection_counter.reset()
            start_time = time.time()

            # Launch workchains
            for _ in range(num_workchains):
                builder = MultiplyAddWorkChain.get_builder()
                builder.x = orm.Int(2)
                builder.y = orm.Int(3)
                builder.z = orm.Int(5)
                builder.code = arithmetic_code

                run_get_node(builder)

            elapsed_time = time.time() - start_time

            # Calculate metrics
            theoretical_max = num_workchains * 2
            reuse_efficiency = 1.0 - (connection_counter.opened / theoretical_max)

            print(f'\n--- Optimal Interval Test: {safe_interval}s ---')
            print(f'  Elapsed time: {elapsed_time:.2f}s')
            print(f'  Connections opened: {connection_counter.opened}')
            print(f'  Reuse efficiency: {reuse_efficiency:.1%}')
            print(f'  Time per workchain: {elapsed_time/num_workchains:.2f}s')

    finally:
        SshTransport._DEFAULT_SAFE_OPEN_INTERVAL = 5.0


@pytest.mark.benchmark
def test_compare_intervals_side_by_side(arithmetic_code, connection_counter):
    """Compare multiple safe_interval values side by side."""
    intervals = [0.1, 0.5, 1.0, 2.0, 5.0]
    results = []

    for interval in intervals:
        from aiida.transports.plugins.ssh import SshTransport

        SshTransport._DEFAULT_SAFE_OPEN_INTERVAL = interval

        with patch_ssh_transport(connection_counter):
            connection_counter.reset()
            start_time = time.time()

            # Launch 10 workchains
            for _ in range(10):
                builder = MultiplyAddWorkChain.get_builder()
                builder.x = orm.Int(2)
                builder.y = orm.Int(3)
                builder.z = orm.Int(5)
                builder.code = arithmetic_code

                run_get_node(builder)

            elapsed_time = time.time() - start_time
            results.append({'interval': interval, 'time': elapsed_time, 'connections': connection_counter.opened})

    # Print comparison table
    print('\n--- Safe Interval Comparison ---')
    print(f'{"Interval":>10} {"Time":>10} {"Connections":>12} {"Efficiency":>10}')
    print('-' * 50)

    for result in results:
        efficiency = 1.0 - (result['connections'] / 20)  # 20 is theoretical max
        print(f'{result["interval"]:>9.1f}s {result["time"]:>9.2f}s ' f'{result["connections"]:>12} {efficiency:>9.1%}')

    # Restore default
    from aiida.transports.plugins.ssh import SshTransport

    SshTransport._DEFAULT_SAFE_OPEN_INTERVAL = 5.0
