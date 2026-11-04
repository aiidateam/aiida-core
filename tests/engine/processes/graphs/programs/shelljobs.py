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
