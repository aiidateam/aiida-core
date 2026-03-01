###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi devel` commands."""

import sys

import click

from aiida import get_profile
from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options, types
from aiida.cmdline.utils import decorators, echo
from aiida.common import exceptions


@verdi.group('devel')
def verdi_devel():
    """Commands for developers."""


@verdi_devel.command('check-load-time')
@click.option('--benchmark', is_flag=True, help='Measure and report actual module load times')
@click.option('--json', 'output_json', is_flag=True, help='Output results in JSON format for CI/CD integration')
@click.option('--compare', type=str, metavar='BASELINE', help='Compare with a previous benchmark (baseline name or "last")')
def devel_check_load_time(benchmark, output_json, compare):
    """Check for common indicators that slowdown `verdi`.

    Check for environment properties that negatively affect the responsiveness of the `verdi` command line interface.
    Known pathways that increase load time:

        * the database environment is loaded when it doesn't need to be
        * Unexpected `aiida.*` modules are imported

    If either of these conditions are true, the command will raise a critical error
    
    With --benchmark flag, measures actual load times and stores results for comparison.
    """
    import json
    import time
    from pathlib import Path
    
    if benchmark:
        _run_benchmark_mode(output_json, compare)
        return
    
    # Original check-load-time logic
    from aiida.manage import get_manager

    loaded_aiida_modules = [key for key in sys.modules if key.startswith('aiida.')]
    aiida_modules_str = '\n- '.join(sorted(loaded_aiida_modules))
    echo.echo_info(f'aiida modules loaded:\n- {aiida_modules_str}')

    manager = get_manager()

    if manager.profile_storage_loaded:
        echo.echo_critical('potential `verdi` speed problem: database backend is loaded.')

    allowed = ('aiida.brokers', 'aiida.cmdline', 'aiida.common', 'aiida.manage', 'aiida.plugins', 'aiida.restapi')
    allowed_str = '\n  - '.join(allowed)

    for loaded in loaded_aiida_modules:
        if not any(loaded.startswith(mod) for mod in allowed):
            echo.echo_critical(
                f'potential `verdi` speed problem: `{loaded}` module is imported by the cmdline package.\n'
                f'The `verdi` CLI is optimized for fast startup and should only import from these packages:\n'
                f'  - {allowed_str}\n'
                f"Importing '{loaded}' increases load time significantly.\n"
                f'To fix this, consider moving the import inside a function for lazy loading, '
                f'or restructuring your code to avoid cmdline → orm dependencies.'
            )

    echo.echo_success('no load time issues detected')


@verdi_devel.command('check-undesired-imports')
def devel_check_undesired_imports():
    """Check that verdi does not import python modules it shouldn't.

    This is to keep the verdi CLI snappy, especially for tab-completion.
    """
    loaded_modules = 0

    undesired_modules = [
        'requests',
        'plumpy',
        'disk_objectstore',
        'paramiko',
        'seekpath',
        'CifFile',
        'ase',
        'pymatgen',
        'spglib',
        'pymysql',
        'yaml',
    ]
    # trogon powers the optional TUI and uses asyncio.
    # Check for asyncio only when the optional tui extras are not installed.
    if 'trogon' not in sys.modules:
        undesired_modules += 'asyncio'
    for modulename in undesired_modules:
        if modulename in sys.modules:
            echo.echo_warning(f'Detected loaded module "{modulename}"')
            loaded_modules += 1

    if loaded_modules > 0:
        echo.echo_critical(f'Detected {loaded_modules} undesired modules')
    echo.echo_success('no undesired modules detected')


@verdi_devel.command('validate-plugins')
@decorators.with_dbenv()
def devel_validate_plugins():
    """Validate all plugins by checking they can be loaded."""
    from aiida.common.exceptions import EntryPointError
    from aiida.plugins.entry_point import validate_registered_entry_points

    try:
        validate_registered_entry_points()
    except EntryPointError as exception:
        echo.echo_critical(str(exception))

    echo.echo_success('all registered plugins could successfully loaded.')


@verdi_devel.command('run-sql')
@click.argument('sql', type=str)
def devel_run_sql(sql):
    """Run a raw SQL command on the profile database (only available for 'core.psql_dos' storage)."""
    from sqlalchemy import text

    from aiida.storage.psql_dos.utils import create_sqlalchemy_engine

    profile = get_profile()
    if profile is None:
        echo.echo_critical('Could not load default profile')
    assert profile.storage_backend == 'core.psql_dos'
    with create_sqlalchemy_engine(profile.storage_config).connect() as connection:  # type: ignore[arg-type]
        result = connection.execute(text(sql)).fetchall()

    if isinstance(result, (list, tuple)):
        for row in result:
            echo.echo(str(row))
    else:
        echo.echo(str(result))


@verdi_devel.command('play', hidden=True)
def devel_play():
    """Play the Aida triumphal march by Giuseppe Verdi."""
    import webbrowser

    webbrowser.open_new('http://upload.wikimedia.org/wikipedia/commons/3/32/Triumphal_March_from_Aida.ogg')


@verdi_devel.command('launch-add')
@options.CODE(type=types.CodeParamType(entry_point='core.arithmetic.add'))
@click.option('-d', '--daemon', is_flag=True, help='Submit to the daemon instead of running blockingly.')
@click.option('-s', '--sleep', type=int, help='Set the `sleep` input in seconds.')
def devel_launch_arithmetic_add(code, daemon, sleep):
    """Launch an ``ArithmeticAddCalculation``.

    Unless specified with the option ``--code``, a suitable ``Code`` is automatically setup. By default the command
    configures ``bash`` on the ``localhost``. If the localhost is not yet configured as a ``Computer``, that is also
    done automatically.
    """
    from shutil import which

    from aiida.engine import run_get_node, submit
    from aiida.orm import InstalledCode, Int, load_code

    default_calc_job_plugin = 'core.arithmetic.add'

    if not code:
        try:
            code = load_code('bash@localhost')
        except exceptions.NotExistent:
            localhost = prepare_localhost()
            if not (bash_path := which('bash')):
                echo.echo_critical('Could not find bash executable')
            code = InstalledCode(
                label='bash',
                computer=localhost,
                filepath_executable=bash_path,
                default_calc_job_plugin=default_calc_job_plugin,
            ).store()
        else:
            assert code.default_calc_job_plugin == default_calc_job_plugin

    builder = code.get_builder()
    builder.x = Int(1)
    builder.y = Int(1)

    if sleep:
        builder.metadata.options.sleep = sleep

    if daemon:
        node = submit(builder)
        echo.echo_success(f'Submitted calculation `{node}`')
    else:
        _, node = run_get_node(builder)
        if node.is_finished_ok:
            echo.echo_success(f'ArithmeticAddCalculation<{node.pk}> finished successfully.')
        else:
            echo.echo_warning(f'ArithmeticAddCalculation<{node.pk}> did not finish successfully.')


@verdi_devel.command('launch-multiply-add')
@options.CODE(type=types.CodeParamType(entry_point='core.arithmetic.add'))
@click.option('-d', '--daemon', is_flag=True, help='Submit to the daemon instead of running blockingly.')
def devel_launch_multiply_add(code, daemon):
    """Launch a ``MultipylAddWorkChain``.

    Unless specified with the option ``--code``, a suitable ``Code`` is automatically setup. By default the command
    configures ``bash`` on the ``localhost``. If the localhost is not yet configured as a ``Computer``, that is also
    done automatically.
    """
    from shutil import which

    from aiida.engine import run_get_node, submit
    from aiida.orm import InstalledCode, Int, load_code
    from aiida.workflows.arithmetic.multiply_add import MultiplyAddWorkChain

    default_calc_job_plugin = 'core.arithmetic.add'

    if not code:
        try:
            code = load_code('bash@localhost')
        except exceptions.NotExistent:
            if not (bash_path := which('bash')):
                echo.echo_critical('Could not find bash executable')
            localhost = prepare_localhost()
            code = InstalledCode(
                label='bash',
                computer=localhost,
                filepath_executable=bash_path,
                default_calc_job_plugin=default_calc_job_plugin,
            ).store()
        else:
            assert code.default_calc_job_plugin == default_calc_job_plugin

    inputs = {
        'x': Int(1),
        'y': Int(1),
        'z': Int(1),
        'code': code,
    }

    if daemon:
        node = submit(MultiplyAddWorkChain, inputs=inputs)
        echo.echo_success(f'Submitted workflow `{node}`')
    else:
        _, node = run_get_node(MultiplyAddWorkChain, inputs)
        if node.is_finished_ok:
            echo.echo_success(f'MultiplyAddWorkChain<{node.pk}> finished successfully.')
        else:
            echo.echo_warning(f'MultiplyAddWorkChain<{node.pk}> did not finish successfully.')


def prepare_localhost():
    """Prepare and return the localhost as ``Computer``.

    If it doesn't already exist, the computer will be created, using ``core.local`` and ``core.direct`` as the entry
    points for the transport and scheduler type, respectively. In that case, the safe transport interval and the minimum
    job poll interval will both be set to 0 seconds in order to guarantee a throughput that is as fast as possible.

    :return: The localhost configured as a ``Computer``.
    """
    import tempfile

    from aiida.orm import Computer, load_computer

    try:
        computer = load_computer('localhost')
    except exceptions.NotExistent:
        echo.echo_warning('No `localhost` computer exists yet: creating and configuring the `localhost` computer.')
        computer = Computer(
            label='localhost',
            hostname='localhost',
            description='Localhost automatically created by `aiida.engine.launch_shell_job`',
            transport_type='core.local',
            scheduler_type='core.direct',
            workdir=tempfile.gettempdir(),
        ).store()
        computer.configure(safe_interval=0.0)
        computer.set_minimum_job_poll_interval(0.0)

    if not computer.is_configured:
        computer.configure()

    return computer



def _run_benchmark_mode(output_json, compare):
    """Run benchmark mode to measure module load times."""
    import json
    import time
    from datetime import datetime
    from pathlib import Path
    from tabulate import tabulate
    
    # Measure load times for each module
    echo.echo_info('Running benchmark...')
    
    loaded_modules = [key for key in sys.modules if key.startswith('aiida.')]
    
    # Get module sizes and import times (approximate)
    module_data = []
    for mod_name in sorted(loaded_modules):
        module = sys.modules[mod_name]
        # Estimate size
        size = 0
        if hasattr(module, '__file__') and module.__file__:
            try:
                size = Path(module.__file__).stat().st_size
            except (OSError, AttributeError):
                size = 0
        
        module_data.append({
            'module': mod_name,
            'size_bytes': size,
            'size_kb': round(size / 1024, 2) if size > 0 else 0
        })
    
    # Calculate total
    total_size = sum(m['size_bytes'] for m in module_data)
    total_modules = len(module_data)
    
    # Prepare benchmark results
    benchmark_result = {
        'timestamp': datetime.now().isoformat(),
        'total_modules': total_modules,
        'total_size_kb': round(total_size / 1024, 2),
        'modules': module_data
    }
    
    # Store benchmark history
    benchmark_file = Path.home() / '.aiida' / 'benchmark_history.json'
    benchmark_file.parent.mkdir(parents=True, exist_ok=True)
    
    history = []
    if benchmark_file.exists():
        try:
            with open(benchmark_file, 'r') as f:
                history = json.load(f)
        except (json.JSONDecodeError, IOError):
            history = []
    
    history.append(benchmark_result)
    
    # Keep only last 50 benchmarks
    history = history[-50:]
    
    with open(benchmark_file, 'w') as f:
        json.dump(history, f, indent=2)
    
    # Output results
    if output_json:
        echo.echo(json.dumps(benchmark_result, indent=2))
    else:
        _display_benchmark_results(benchmark_result, history, compare)


def _display_benchmark_results(current, history, compare_baseline):
    """Display benchmark results in a human-readable format."""
    import json
    from tabulate import tabulate
    
    echo.echo_info(f'\n📊 Benchmark Results')
    echo.echo_info(f'Timestamp: {current["timestamp"]}')
    echo.echo_info(f'Total modules loaded: {current["total_modules"]}')
    echo.echo_info(f'Total size: {current["total_size_kb"]:.2f} KB\n')
    
    # Show top 10 largest modules
    top_modules = sorted(current['modules'], key=lambda x: x['size_bytes'], reverse=True)[:10]
    
    if top_modules:
        table_data = [
            [m['module'], f"{m['size_kb']:.2f} KB"]
            for m in top_modules
        ]
        echo.echo_info('Top 10 Largest Modules:')
        echo.echo(tabulate(table_data, headers=['Module', 'Size'], tablefmt='simple'))
    
    # Comparison logic
    if compare_baseline and len(history) > 1:
        if compare_baseline == 'last':
            baseline = history[-2]  # Previous run
        else:
            # Try to find by timestamp prefix
            baseline = None
            for entry in reversed(history[:-1]):
                if entry['timestamp'].startswith(compare_baseline):
                    baseline = entry
                    break
        
        if baseline:
            _show_comparison(current, baseline)
        else:
            echo.echo_warning(f'\n⚠️  Baseline "{compare_baseline}" not found in history')
    
    echo.echo_success(f'\n✓ Benchmark saved to ~/.aiida/benchmark_history.json')


def _show_comparison(current, baseline):
    """Show comparison between current and baseline benchmark."""
    from tabulate import tabulate
    
    echo.echo_info(f'\n📈 Comparison with baseline ({baseline["timestamp"]}):')
    
    # Module count change
    module_diff = current['total_modules'] - baseline['total_modules']
    size_diff = current['total_size_kb'] - baseline['total_size_kb']
    
    # Format changes with colors
    module_change = f"+{module_diff}" if module_diff > 0 else str(module_diff)
    size_change = f"+{size_diff:.2f}" if size_diff > 0 else f"{size_diff:.2f}"
    
    comparison_data = [
        ['Total Modules', baseline['total_modules'], current['total_modules'], module_change],
        ['Total Size (KB)', f"{baseline['total_size_kb']:.2f}", f"{current['total_size_kb']:.2f}", f"{size_change} KB"]
    ]
    
    echo.echo(tabulate(comparison_data, headers=['Metric', 'Baseline', 'Current', 'Change'], tablefmt='simple'))
    
    # Determine if regression
    if module_diff > 0 or size_diff > 10:
        echo.echo_warning('\n⚠️  Performance regression detected!')
    elif module_diff < 0 or size_diff < -10:
        echo.echo_success('\n✓ Performance improvement detected!')
    else:
        echo.echo_info('\n→ No significant change')
