"""`verdi process` command."""

import click

from aiida.cmdline.params import arguments, options
from aiida.cmdline.utils import decorators, echo
from aiida.workgraph.cli.cmd_workgraph import workgraph

REPAIR_INSTRUCTIONS = """\
If one ore more processes are unreachable, you can run the following commands to try and repair them:

    verdi daemon stop
    verdi process repair
    verdi daemon start
"""


@workgraph.group('task')
def workgraph_task():
    """Inspect and manage processes."""


@workgraph_task.command('list')
@arguments.PROCESS()
@options.TIMEOUT()
@decorators.with_dbenv()
def task_show(process, timeout):
    """List the tasks for one or multiple work graphs."""
    from aiida.workgraph import WorkGraph

    wg = WorkGraph.load(process.pk)
    wg.show()


@workgraph_task.command('pause')
@arguments.PROCESS()
@click.argument('tasks', nargs=-1)
@options.TIMEOUT()
@decorators.with_dbenv()
def task_pause(process, tasks, timeout):
    """Pause task."""
    from aiida.engine.processes import control
    from aiida.workgraph.utils.control import pause_tasks

    try:
        _, msg = pause_tasks(process.pk, tasks, timeout)
    except control.ProcessTimeoutException as exception:
        echo.echo_critical(f'{exception}\n{REPAIR_INSTRUCTIONS}')


@workgraph_task.command('play')
@arguments.PROCESS()
@click.argument('tasks', nargs=-1)
@options.TIMEOUT()
@decorators.with_dbenv()
def task_play(process, tasks, timeout):
    """Play task."""
    from aiida.engine.processes import control
    from aiida.workgraph.utils.control import play_tasks

    try:
        _, msg = play_tasks(process.pk, tasks, timeout)
    except control.ProcessTimeoutException as exception:
        echo.echo_critical(f'{exception}\n{REPAIR_INSTRUCTIONS}')


@workgraph_task.command('kill')
@arguments.PROCESS()
@click.argument('tasks', nargs=-1)
@options.TIMEOUT()
@decorators.with_dbenv()
def task_kill(process, tasks, timeout):
    """Kill task."""
    from aiida.engine.processes import control
    from aiida.workgraph.utils.control import kill_tasks

    print('tasks', tasks)
    try:
        kill_tasks(process.pk, tasks, timeout)
    except control.ProcessTimeoutException as exception:
        echo.echo_critical(f'{exception}\n{REPAIR_INSTRUCTIONS}')
