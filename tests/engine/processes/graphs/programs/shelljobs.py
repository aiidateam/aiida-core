###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`ShellJob` tasks with declared dynamic ports, shared by the graph behavior suites."""

from aiida.calculations.shell import ShellJob
from aiida.engine.processes.exit_code import ExitCode, ExitCodeEnum
from aiida.engine.processes.graphs.lowering import graph, task
from aiida.orm import Code, SinglefileData

cat = task(ShellJob, inputs={'nodes': {'text': SinglefileData}}, outputs={'stdout': SinglefileData})
count_words = task(ShellJob, inputs={'nodes': {'text': SinglefileData}}, outputs={'stdout': SinglefileData})


@graph
def copy_and_count(
    text: SinglefileData, cat_code: Code, wc_code: Code, cat_arguments: list[str], wc_arguments: list[str]
) -> SinglefileData:
    """Copy a file through `cat`, then count the words of the copy with `wc`."""
    copied = cat(code=cat_code, arguments=cat_arguments, nodes={'text': text})
    counted = count_words(code=wc_code, arguments=wc_arguments, nodes={'text': copied.stdout})
    return counted.stdout


unproduced = task(ShellJob, inputs={'nodes': {'text': SinglefileData}}, outputs={'missing_txt': SinglefileData})


@graph
def expect_unproduced(text: SinglefileData, code: Code, arguments: list[str]) -> SinglefileData:
    """Read an output the command never writes."""
    produced = unproduced(code=code, arguments=arguments, nodes={'text': text})
    return produced.missing_txt


@task
def number() -> int:
    """Return an integer, which a file port cannot take."""
    return 1


@graph
def mistyped(code: Code, arguments: list[str]) -> SinglefileData:
    """Wire an integer into a declared file port."""
    value = number()
    copied = cat(code=code, arguments=arguments, nodes={'text': value})
    return copied.stdout


def double(x: int) -> int:
    """Double a number; registered as a task only by the tests."""
    return 2 * x


rerun = task(ShellJob, inputs={'nodes': {'text': SinglefileData}}, outputs={'stdout': SinglefileData})


@graph
def run_remote_none_in_task_call(text: SinglefileData, code: Code, arguments: list[str]) -> SinglefileData:
    """Run without the optional remote folder; the input is left out of the launch."""
    reran = rerun(code=code, arguments=arguments, nodes={'text': text}, remote_folder=None)
    return reran.stdout


@graph
def run_remote_none_in_graph_signature(
    text: SinglefileData, code: Code, arguments: list[str], remote=None
) -> SinglefileData:
    """Run with the remote input passed as `None`; the port stays out of the launch."""
    reran = rerun(code=code, arguments=arguments, nodes={'text': text}, remote_folder=remote)
    return reran.stdout


@graph
def run_remote_from_previous_task(text: SinglefileData, code: Code, arguments: list[str]) -> SinglefileData:
    """Run with the previous remote folder as the optional remote folder."""
    first = cat(code=code, arguments=arguments, nodes={'text': text})
    reran = rerun(code=code, arguments=arguments, nodes={'text': text}, remote_folder=first.remote_folder)
    return reran.stdout


class ShellErrors(ExitCodeEnum):
    """Mapped failures of the `fail` task."""

    COMMAND_FAILED = ExitCode(400, 'The command failed.')


fail = task(
    ShellJob,
    inputs={'nodes': {'text': SinglefileData}},
    outputs={'stdout': SinglefileData},
    errors=ShellErrors,
)


@task
def recover_shell(error: ShellErrors) -> str:
    """Recover from a failed shell command."""
    return f'recovered from {error.value.status}'


@task
def read_stdout(content: SinglefileData) -> str:
    """Read command output."""
    return content.get_content()


@graph
def recover_failing(text: SinglefileData, code: Code, arguments: list[str]) -> str:
    """Run a command that may fail, recovering with `recover_shell` when it does."""
    ran = fail(code=code, arguments=arguments, nodes={'text': text})
    if ran.error is not None:
        selected = recover_shell(error=ran.error)
    else:
        selected = read_stdout(content=ran.stdout)
    return selected
