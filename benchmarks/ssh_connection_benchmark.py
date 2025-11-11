#!/usr/bin/env python
"""Benchmark script to measure SSH connection reuse with different safe_open_interval values.

This script launches MultiplyAddWorkChain workflows with varying numbers of workers
to test how effectively AiiDA's TransportQueue reuses SSH connections.

Usage:
    python ssh_connection_benchmark.py --computer Thor --num-workchains 10 --num-workers 4
    python ssh_connection_benchmark.py --help

Requirements:
    - AiiDA profile must be loaded
    - Computer 'Thor' (or specified computer) must be configured
    - ArithmeticAdd code must be set up on the computer
"""

import argparse
import asyncio
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from aiida import orm
from aiida.engine import submit
from aiida.manage import get_manager
from aiida.workflows.arithmetic.multiply_add import MultiplyAddWorkChain


class SSHConnectionMonitor:
    """Monitor SSH connections opened during workflow execution."""

    def __init__(self):
        self.connections_opened = 0
        self.connections_closed = 0
        self.connection_times = []
        self.original_open = None
        self.original_close = None
        self.start_time = None
        self.transport_reuse_count = defaultdict(int)

    def patch_transport(self, transport_class):
        """Patch the transport class to monitor open/close calls."""
        self.original_open = transport_class.open
        self.original_close = transport_class.close

        monitor = self

        def monitored_open(self_transport):
            """Wrapped open method that tracks connection openings."""
            monitor.connections_opened += 1
            current_time = time.time() - monitor.start_time
            monitor.connection_times.append(
                {'time': current_time, 'action': 'open', 'count': monitor.connections_opened}
            )
            print(f'  [+] SSH connection opened (total: {monitor.connections_opened}) at t={current_time:.2f}s')
            return monitor.original_open(self_transport)

        def monitored_close(self_transport):
            """Wrapped close method that tracks connection closings."""
            monitor.connections_closed += 1
            current_time = time.time() - monitor.start_time
            monitor.connection_times.append(
                {'time': current_time, 'action': 'close', 'count': monitor.connections_closed}
            )
            print(f'  [-] SSH connection closed (total: {monitor.connections_closed}) at t={current_time:.2f}s')
            return monitor.original_close(self_transport)

        transport_class.open = monitored_open
        transport_class.close = monitored_close

    def unpatch_transport(self, transport_class):
        """Restore original transport methods."""
        if self.original_open:
            transport_class.open = self.original_open
        if self.original_close:
            transport_class.close = self.original_close

    def reset(self):
        """Reset counters for a new test run."""
        self.connections_opened = 0
        self.connections_closed = 0
        self.connection_times = []
        self.start_time = time.time()
        self.transport_reuse_count.clear()

    def get_stats(self) -> Dict:
        """Get statistics about connection usage."""
        return {
            'total_opened': self.connections_opened,
            'total_closed': self.connections_closed,
            'connection_timeline': self.connection_times,
        }


def get_or_create_code(computer_name: str, code_label: str = 'add') -> orm.AbstractCode:
    """Get or create an ArithmeticAdd code on the specified computer.

    Args:
        computer_name: Name of the computer
        code_label: Label for the code

    Returns:
        The code instance
    """
    from aiida.orm import InstalledCode, load_computer

    # Try to load existing code
    try:
        code = orm.load_code(f'{code_label}@{computer_name}')
        print(f'Using existing code: {code.full_label}')
        return code
    except Exception:
        pass

    # Create new code
    try:
        computer = load_computer(computer_name)
    except Exception as exc:
        print(f'Error: Could not load computer "{computer_name}": {exc}')
        print('\nAvailable computers:')
        for comp in orm.QueryBuilder().append(orm.Computer).all(flat=True):
            print(f'  - {comp.label}')
        sys.exit(1)

    print(f'Creating new ArithmeticAdd code on computer "{computer_name}"...')
    code = InstalledCode(
        label=code_label,
        computer=computer,
        filepath_executable='/bin/bash',
        default_calc_job_plugin='core.arithmetic.add',
    )
    code.store()
    print(f'Created code: {code.full_label}')
    return code


def launch_workchains(
    code: orm.AbstractCode, num_workchains: int, x: int = 2, y: int = 3, z: int = 5
) -> List[orm.WorkChainNode]:
    """Launch multiple MultiplyAddWorkChain instances.

    Args:
        code: The code to use for calculations
        num_workchains: Number of workchains to launch
        x, y, z: Input values for the workchains

    Returns:
        List of submitted workchain nodes
    """
    nodes = []
    print(f'\nLaunching {num_workchains} workchains...')

    for i in range(num_workchains):
        builder = MultiplyAddWorkChain.get_builder()
        builder.x = orm.Int(x)
        builder.y = orm.Int(y)
        builder.z = orm.Int(z)
        builder.code = code

        node = submit(builder)
        nodes.append(node)
        print(f'  Submitted workchain {i+1}/{num_workchains}: {node.pk}')

    return nodes


async def wait_for_completion(nodes: List[orm.WorkChainNode], timeout: int = 600):
    """Wait for all workchains to complete.

    Args:
        nodes: List of workchain nodes to monitor
        timeout: Maximum time to wait in seconds
    """
    print(f'\nWaiting for {len(nodes)} workchains to complete (timeout: {timeout}s)...')
    start_time = time.time()

    while True:
        # Check completion status
        statuses = {}
        for node in nodes:
            node = orm.load_node(node.pk)  # Reload to get fresh state
            statuses[node.process_state.value] = statuses.get(node.process_state.value, 0) + 1

        print(f'  Status: {statuses}', end='\r')

        # Check if all are finished
        all_finished = all(orm.load_node(node.pk).is_terminated for node in nodes)

        if all_finished:
            print(f'\n  All workchains completed in {time.time() - start_time:.2f}s')
            break

        # Check timeout
        if time.time() - start_time > timeout:
            print(f'\n  Warning: Timeout reached after {timeout}s')
            break

        await asyncio.sleep(1)


def run_benchmark(
    computer_name: str, num_workchains: int, num_workers: int, safe_interval: float, timeout: int = 600
) -> Dict:
    """Run a single benchmark test.

    Args:
        computer_name: Name of the computer to use
        num_workchains: Number of workchains to launch
        num_workers: Number of daemon workers to use
        safe_interval: Safe open interval to test
        timeout: Maximum time to wait for completion

    Returns:
        Dictionary with benchmark results
    """
    print('\n' + '=' * 80)
    print(f'BENCHMARK: {num_workchains} workchains, {num_workers} workers, ' f'safe_interval={safe_interval}s')
    print('=' * 80)

    # Get or create code
    code = get_or_create_code(computer_name)

    # Set up monitoring
    monitor = SSHConnectionMonitor()
    from aiida.transports.plugins.ssh import SshTransport

    # Temporarily modify the safe interval
    original_interval = SshTransport._DEFAULT_SAFE_OPEN_INTERVAL
    SshTransport._DEFAULT_SAFE_OPEN_INTERVAL = safe_interval

    # Patch transport to monitor connections
    monitor.patch_transport(SshTransport)
    monitor.reset()

    try:
        # Launch workchains
        start_time = time.time()
        nodes = launch_workchains(code, num_workchains)

        # Wait for completion
        asyncio.run(wait_for_completion(nodes, timeout))

        end_time = time.time()
        elapsed_time = end_time - start_time

        # Collect results
        results = {
            'num_workchains': num_workchains,
            'num_workers': num_workers,
            'safe_interval': safe_interval,
            'elapsed_time': elapsed_time,
            'connections_opened': monitor.connections_opened,
            'connections_closed': monitor.connections_closed,
            'workchains': [node.pk for node in nodes],
            'connection_timeline': monitor.connection_times,
        }

        # Calculate efficiency metrics
        theoretical_max = num_workchains * 2  # Each workchain does one CalcJob (could open connection)
        reuse_efficiency = 1.0 - (monitor.connections_opened / theoretical_max) if theoretical_max > 0 else 0
        results['theoretical_max_connections'] = theoretical_max
        results['reuse_efficiency'] = reuse_efficiency

        print('\n--- Results ---')
        print(f'  Elapsed time: {elapsed_time:.2f}s')
        print(f'  SSH connections opened: {monitor.connections_opened}')
        print(f'  SSH connections closed: {monitor.connections_closed}')
        print(f'  Theoretical max connections: {theoretical_max}')
        print(f'  Connection reuse efficiency: {reuse_efficiency:.1%}')

        return results

    finally:
        # Restore original settings
        monitor.unpatch_transport(SshTransport)
        SshTransport._DEFAULT_SAFE_OPEN_INTERVAL = original_interval


def save_results(all_results: List[Dict], output_file: str):
    """Save benchmark results to a file.

    Args:
        all_results: List of result dictionaries
        output_file: Path to output file
    """
    import json

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump({'timestamp': datetime.now().isoformat(), 'results': all_results}, f, indent=2)

    print(f'\nResults saved to: {output_path}')


def print_summary(all_results: List[Dict]):
    """Print a summary table of all benchmark results.

    Args:
        all_results: List of result dictionaries
    """
    print('\n' + '=' * 100)
    print('BENCHMARK SUMMARY')
    print('=' * 100)
    print(f'{"WorkChains":>12} {"Workers":>8} {"Interval":>10} {"Time":>10} ' f'{"Opened":>10} {"Efficiency":>12}')
    print('-' * 100)

    for result in all_results:
        print(
            f'{result["num_workchains"]:>12} {result["num_workers"]:>8} '
            f'{result["safe_interval"]:>10.1f}s {result["elapsed_time"]:>9.1f}s '
            f'{result["connections_opened"]:>10} {result["reuse_efficiency"]:>11.1%}'
        )


def main():
    """Main entry point for the benchmark script."""
    parser = argparse.ArgumentParser(
        description='Benchmark SSH connection reuse in AiiDA with different safe_open_interval values',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with default settings
  python ssh_connection_benchmark.py --computer Thor

  # Test multiple configurations
  python ssh_connection_benchmark.py --computer Thor \\
      --num-workchains 1 10 100 \\
      --num-workers 1 2 4 8 \\
      --safe-intervals 0.5 1.0 2.0 5.0

  # Quick test with single configuration
  python ssh_connection_benchmark.py --computer Thor \\
      --num-workchains 10 \\
      --num-workers 4 \\
      --safe-intervals 2.0
        """,
    )

    parser.add_argument('--computer', type=str, required=True, help='Name of the computer to use (e.g., Thor)')
    parser.add_argument(
        '--num-workchains',
        type=int,
        nargs='+',
        default=[1, 10, 100],
        help='Number of workchains to launch (default: 1 10 100)',
    )
    parser.add_argument(
        '--num-workers',
        type=int,
        nargs='+',
        default=[1, 2, 4, 8],
        help='Number of daemon workers to test (default: 1 2 4 8)',
    )
    parser.add_argument(
        '--safe-intervals',
        type=float,
        nargs='+',
        default=[0.5, 1.0, 2.0, 5.0],
        help='Safe open intervals to test in seconds (default: 0.5 1.0 2.0 5.0)',
    )
    parser.add_argument(
        '--timeout', type=int, default=600, help='Timeout for workchain completion in seconds (default: 600)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='ssh_benchmark_results.json',
        help='Output file for results (default: ssh_benchmark_results.json)',
    )
    parser.add_argument('--skip-summary', action='store_true', help='Skip running all combinations, just test once')

    args = parser.parse_args()

    # Check AiiDA is loaded
    try:
        get_manager()
    except Exception as exc:
        print(f'Error: Could not load AiiDA: {exc}')
        print('Make sure you have loaded an AiiDA profile (verdi status)')
        sys.exit(1)

    all_results = []

    if args.skip_summary:
        # Run single test
        result = run_benchmark(
            args.computer, args.num_workchains[0], args.num_workers[0], args.safe_intervals[0], args.timeout
        )
        all_results.append(result)
    else:
        # Run all combinations
        total_tests = len(args.num_workchains) * len(args.num_workers) * len(args.safe_intervals)
        print(f'\nRunning {total_tests} benchmark tests...')

        test_num = 0
        for num_wc in args.num_workchains:
            for num_workers in args.num_workers:
                for interval in args.safe_intervals:
                    test_num += 1
                    print(f'\n[Test {test_num}/{total_tests}]')

                    result = run_benchmark(args.computer, num_wc, num_workers, interval, args.timeout)
                    all_results.append(result)

    # Print summary and save results
    print_summary(all_results)
    save_results(all_results, args.output)

    print('\nBenchmark complete!')


if __name__ == '__main__':
    main()
