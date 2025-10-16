#!/usr/bin/env python
"""Script to benchmark the performance of the AiiDA workflow engine on a given installation."""

import click

from aiida.cmdline.params import options
from aiida.cmdline.utils import decorators, echo


@click.command()
@options.CODE(required=False, help='A code that can run the ``ArithmeticAddCalculation``, for example bash.')
@click.option('-n', 'number', type=int, default=10, show_default=True, help='The number of processes to launch.')
@click.option('--daemon/--without-daemon', default=False, is_flag=True, help='Submit to daemon or run synchronously.')
@decorators.with_dbenv()
def main(code, number, daemon):
    """Submit a number of ``ArithmeticAddCalculation`` to the daemon and record time to completion.

    This command requires the daemon to be running.

    The script will submit a configurable number of ``ArithmeticAddCalculation`` jobs. By default, the jobs are executed
    using the ``bash`` executable of the system. If this executable cannot be found the script will exit. The jobs will
    be run on the localhost, which is automatically created and configured. At the end of the script, the created nodes
    will be deleted, as well as the code and computer, if they were automatically setup.
    """
    import shutil
    import tempfile
    import time
    import uuid

    from aiida import orm
    from aiida.engine import run_get_node, submit
    from aiida.engine.daemon.client import get_daemon_client
    from aiida.manage import get_manager
    from aiida.plugins import CalculationFactory
    from aiida.tools.graph.deletions import delete_nodes

    client = get_daemon_client()

    if daemon and not client.is_daemon_running:
        echo.echo_critical('The daemon is not running.')

    computer_created = False
    code_created = False

    echo.echo(f'Running on profile {get_manager().get_profile().name}')

    if not code:
        label = f'benchmark-{uuid.uuid4().hex[:8]}'
        computer = orm.Computer(
            label=label,
            hostname='localhost',
            transport_type='core.local',
            scheduler_type='core.direct',
            workdir=tempfile.gettempdir(),
        ).store()
        computer.configure(safe_interval=0.0, use_login_shell=False)
        echo.echo_success(f'Created and configured temporary `Computer` {label} for localhost.')
        computer_created = True

        executable = shutil.which('bash')

        if executable is None:
            echo.echo_critical('Could not determine the absolute path for the `bash` executable.')

        code = orm.InstalledCode(label='bash', computer=computer, filepath_executable=executable).store()
        echo.echo_success(f'Created temporary `Code` {code.label} for localhost.')
        code_created = True

    cls = CalculationFactory('core.arithmetic.add')
    builder = cls.get_builder()
    builder.code = code
    builder.x = orm.Int(1)
    builder.y = orm.Int(1)

    time_start = time.time()
    nodes = []

    if daemon:
        with click.progressbar(range(number), label=f'Submitting {number} calculations.') as bar:
            for iteration in bar:
                node = submit(builder)
                nodes.append(node)

        time_end = time.time()
        echo.echo(f'Submission completed in {(time_end - time_start):.2f} seconds.')

        completed = 0

        with click.progressbar(length=number, label='Waiting for calculations to complete') as bar:
            while True:
                time.sleep(0.2)

                terminated = [node.is_terminated for node in nodes]
                newly_completed = terminated.count(True) - completed
                completed = terminated.count(True)

                bar.update(newly_completed)

                if all(terminated):
                    break

    else:
        with click.progressbar(range(number), label=f'Running {number} calculations.') as bar:
            for iteration in bar:
                _, node = run_get_node(builder)
                nodes.append(node)

    if any(node.is_excepted or node.is_killed for node in nodes):
        echo.echo_warning('At least one submitted calculation excepted or was killed.')
    else:
        echo.echo_success('All calculations finished successfully.')

    time_end = time.time()
    echo.echo(f'Elapsed time: {(time_end - time_start):.2f} seconds.')

    echo.echo('Cleaning up...')
    delete_nodes([node.pk for node in nodes], dry_run=False)
    echo.echo_success('Deleted all calculations.')

    if code_created:
        code_label = code.full_label
        orm.Node.objects.delete(code.pk)
        echo.echo_success(f'Deleted the created code {code_label}.')

    if computer_created:
        computer_label = computer.label
        user = orm.User.objects.get_default()
        auth_info = computer.get_authinfo(user)
        orm.AuthInfo.objects.delete(auth_info.pk)
        orm.Computer.objects.delete(computer.pk)
        echo.echo_success(f'Deleted the created computer {computer_label}.')

    echo.echo(f'Performance: {(time_end - time_start) / number:.2f} s / process')


if __name__ == '__main__':
    main()
