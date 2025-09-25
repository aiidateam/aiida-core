###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi calcjob` commands."""

from __future__ import annotations

import os
import typing as t

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.params.types import CalculationParamType
from aiida.cmdline.utils import decorators, echo

if t.TYPE_CHECKING:
    from aiida import orm


@verdi.group('calcjob')
def verdi_calcjob():
    """Inspect and manage calcjobs."""


@verdi_calcjob.command('gotocomputer')
@arguments.CALCULATION('calcjob', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
def calcjob_gotocomputer(calcjob):
    """Open a shell in the remote folder on the calcjob.

    This command opens a ssh connection to the folder on the remote
    computer on which the calcjob is being/has been executed.
    """
    from aiida.common.exceptions import NotExistent

    try:
        transport = calcjob.get_transport()
    except NotExistent as exception:
        echo.echo_critical(repr(exception))

    remote_workdir = calcjob.get_remote_workdir()

    if not remote_workdir:
        echo.echo_critical('no remote work directory for this calcjob, maybe the daemon did not submit it yet')

    try:
        command = transport.gotocomputer_command(remote_workdir)
        echo.echo_report('going to the remote work directory...')
        os.system(command)
    except NotImplementedError:
        echo.echo_report(f'gotocomputer is not implemented for {transport}')
        echo.echo_report(f'remote work directory is {remote_workdir}')


@verdi_calcjob.command('res')
@arguments.CALCULATION('calcjob', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
@options.DICT_KEYS()
@options.DICT_FORMAT()
@decorators.with_dbenv()
def calcjob_res(calcjob, fmt, keys):
    """Print data from the result output Dict node of a calcjob."""
    from aiida.cmdline.utils.echo import echo_dictionary

    try:
        results = calcjob.res.get_results()
    except ValueError as exception:
        echo.echo_critical(str(exception))

    if keys is not None:
        try:
            result = {k: results[k] for k in keys}
        except KeyError as exc:
            echo.echo_critical(f"key '{exc.args[0]}' was not found in the results dictionary")
    else:
        result = results

    echo_dictionary(result, fmt=fmt)


@verdi_calcjob.command('inputcat')
@arguments.CALCULATION('calcjob', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
@click.argument('path', type=click.STRING, required=False)
@decorators.with_dbenv()
def calcjob_inputcat(calcjob, path):
    """Show the contents of one of the calcjob input files.

    You can specify the relative PATH in the raw input folder of the CalcJob.

    If PATH is not specified, the default input file path will be used, if defined by the calcjob plugin class.
    """
    import errno
    import sys
    from shutil import copyfileobj

    # Get path from the given CalcJobNode if not defined by user
    if path is None:
        path = calcjob.get_option('input_filename')

    # Get path from current process class of CalcJobNode if still not defined
    if path is None:
        fname = calcjob.process_class.spec_options.get('input_filename')
        if fname and fname.has_default():
            path = fname.default

    if path is None:
        # Still no path available
        echo.echo_critical(
            '"{}" and its process class "{}" do not define a default input file '
            '(option "input_filename" not found).\n'
            'Please specify a path explicitly.'.format(calcjob.__class__.__name__, calcjob.process_class.__name__)
        )

    try:
        # When we `cat`, it makes sense to directly send the output to stdout as it is
        with calcjob.base.repository.open(path, mode='rb') as fhandle:
            copyfileobj(fhandle, sys.stdout.buffer)
    except OSError as exception:
        # The sepcial case is breakon pipe error, which is usually OK.
        # It can happen if the output is redirected, for example, to `head`.
        if exception.errno != errno.EPIPE:
            # Incorrect path or file not readable
            echo.echo_critical(f'Could not open output path "{path}". Exception: {exception}')


@verdi_calcjob.command('remotecat')
@arguments.CALCULATION('calcjob', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
@click.argument('path', type=str, required=False)
@decorators.with_dbenv()
def calcjob_remotecat(calcjob: orm.CalcJobNode, path: str | None):
    """Show the contents of a file in the remote working directory.

    The file to show can be specified using the PATH argument. If PATH is not specified, the default output file path
    as defined by the `CalcJob` plugin class will be used instead.
    """
    import shutil
    import sys
    import tempfile

    remote_folder, path = get_remote_and_path(calcjob, path)

    with tempfile.NamedTemporaryFile() as tmp_path:
        try:
            remote_folder.getfile(path, tmp_path.name)
            with open(tmp_path.name, 'rb') as handle:
                shutil.copyfileobj(handle, sys.stdout.buffer)
        except OSError as exception:
            echo.echo_critical(str(exception))


@verdi_calcjob.command('outputcat')
@arguments.CALCULATION('calcjob', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
@click.argument('path', type=click.STRING, required=False)
@decorators.with_dbenv()
def calcjob_outputcat(calcjob, path):
    """Show the contents of one of the calcjob retrieved outputs.

    You can specify the relative PATH in the retrieved folder of the CalcJob.

    If PATH is not specified, the default output file path will be used, if defined by the calcjob plugin class.
    Content can only be shown after the daemon has retrieved the remote files.
    """
    import errno
    import sys
    from shutil import copyfileobj

    try:
        retrieved = calcjob.outputs.retrieved
    except AttributeError:
        echo.echo_critical("No 'retrieved' node found. Have the calcjob files already been retrieved?")

    # Get path from the given CalcJobNode if not defined by user
    if path is None:
        path = calcjob.get_option('output_filename')

    # Get path from current process class of CalcJobNode if still not defined
    if path is None:
        fname = calcjob.process_class.spec_options.get('output_filename')
        if fname and fname.has_default():
            path = fname.default

    if path is None:
        # Still no path available
        echo.echo_critical(
            '"{}" and its process class "{}" do not define a default output file '
            '(option "output_filename" not found).\n'
            'Please specify a path explicitly.'.format(calcjob.__class__.__name__, calcjob.process_class.__name__)
        )

    try:
        # When we `cat`, it makes sense to directly send the output to stdout as it is
        with retrieved.base.repository.open(path, mode='rb') as fhandle:
            copyfileobj(fhandle, sys.stdout.buffer)
    except OSError as exception:
        # The sepcial case is breakon pipe error, which is usually OK.
        # It can happen if the output is redirected, for example, to `head`.
        if exception.errno != errno.EPIPE:
            # Incorrect path or file not readable
            echo.echo_critical(f'Could not open output path "{path}". Exception: {exception}')


@verdi_calcjob.command('inputls')
@decorators.with_dbenv()
@arguments.CALCULATION('calcjob', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
@click.argument('path', type=click.STRING, required=False)
@click.option('-c', '--color', 'color', is_flag=True, default=False, help='color folders with a different color')
def calcjob_inputls(calcjob, path, color):
    """Show the list of the generated calcjob input files.

    You can specify a relative PATH in the raw input folder of the CalcJob.

    If PATH is not specified, the base path of the input folder will be used.
    """
    from aiida.cmdline.utils.repository import list_repository_contents

    try:
        list_repository_contents(calcjob, path, color)
    except FileNotFoundError:
        echo.echo_critical(f'the path `{path}` does not exist for the given node')


@verdi_calcjob.command('outputls')
@decorators.with_dbenv()
@arguments.CALCULATION('calcjob', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
@click.argument('path', type=click.STRING, required=False)
@click.option('-c', '--color', 'color', is_flag=True, default=False, help='color folders with a different color')
def calcjob_outputls(calcjob, path, color):
    """Show the list of the retrieved calcjob output files.

    You can specify a relative PATH in the retrieved folder of the CalcJob.

    If PATH is not specified, the base path of the retrieved folder will be used.
    Content can only be shown after the daemon has retrieved the remote files.
    """
    from aiida.cmdline.utils.repository import list_repository_contents

    try:
        retrieved = calcjob.outputs.retrieved
    except AttributeError:
        echo.echo_critical("No 'retrieved' node found. Have the calcjob files already been retrieved?")

    try:
        list_repository_contents(retrieved, path, color)
    except FileNotFoundError:
        echo.echo_critical(f'the path `{path}` does not exist for the given node')


@verdi_calcjob.command('cleanworkdir')
@decorators.with_dbenv()
@arguments.CALCULATIONS('calcjobs', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
@options.PAST_DAYS(default=None)
@options.OLDER_THAN(default=None)
@options.COMPUTERS(help='include only calcjobs that were ran on these computers')
@options.FORCE()
@options.EXIT_STATUS()
def calcjob_cleanworkdir(calcjobs, past_days, older_than, computers, force, exit_status):
    """Clean all content of all output remote folders of calcjobs.

    If no explicit calcjobs are specified as arguments, one or both of the -p and -o options has to be specified.
    If both are specified, a logical AND is done between the two, i.e. the calcjobs that will be cleaned have been
    modified AFTER [-p option] days from now, but BEFORE [-o option] days from now.
    """
    from aiida.orm.utils.remote import clean_mapping_remote_paths, get_calcjob_remote_paths

    if calcjobs:
        if past_days is not None and older_than is not None:
            echo.echo_critical('specify either explicit calcjobs or use the filtering options')
    elif past_days is None and older_than is None:
        echo.echo_critical('if no explicit calcjobs are specified, at least one filtering option is required')

    calcjobs_pks = [calcjob.pk for calcjob in calcjobs]
    path_mapping = get_calcjob_remote_paths(
        calcjobs_pks,
        past_days,
        older_than,
        computers,
        exit_status=exit_status,
        only_not_cleaned=True,
    )

    if path_mapping is None:
        echo.echo_critical('no calcjobs found with the given criteria')

    if not force:
        path_count = sum(len(paths) for paths in path_mapping.values())
        warning = f'Are you sure you want to clean the work directory of {path_count} calcjobs?'
        click.confirm(warning, abort=True)

    clean_mapping_remote_paths(path_mapping)


def get_remote_and_path(calcjob: orm.CalcJobNode, path: str | None = None) -> tuple[orm.RemoteData, str]:
    """Return the remote folder output node and process the path argument.

    :param calcjob: The ``CalcJobNode`` whose remote_folder to be returned.
    :param path: The relative path of file. If not defined, it is attempted to determine the default output file from
        the node options or otherwise from the associated process class. If neither are defined, a ``ValueError`` is
        raised.
    :returns: A tuple of the ``RemoteData`` and the path of the output file to be used.
    :raises ValueError: If path is not defined and no default output file is defined on the node nor its associated
        process class.
    """
    remote_folder_linkname = 'remote_folder'  # The `remote_folder` is the standard output of a calculation.

    try:
        remote_folder = getattr(calcjob.outputs, remote_folder_linkname)
    except AttributeError:
        echo.echo_critical(
            f'`CalcJobNode<{calcjob.pk}>` has no `{remote_folder_linkname}` output. '
            'It probably has not started running yet.'
        )

    if path is not None:
        return remote_folder, path

    # Try to get the default output filename from the node
    path = calcjob.get_option('output_filename')

    if path is not None:
        return remote_folder, path

    try:
        process_class = calcjob.process_class
    except ValueError as exception:
        raise ValueError(
            f'The process class of `CalcJobNode<{calcjob.pk}>` cannot be loaded and so the default output filename '
            'cannot be determined.\nPlease specify a path explicitly.'
        ) from exception

    # Try to get the default output filename from the node's associated process class spec
    port = process_class.spec_options.get('output_filename')  # type: ignore[attr-defined]
    if port and port.has_default():
        path = port.default

    if path is not None:
        return remote_folder, path

    raise ValueError(
        f'`CalcJobNode<{calcjob.pk}>` does not define a default output file (option "output_filename" not found) '
        f'nor does its associated process class `{calcjob.process_class.__class__.__name__}`\n'
        'Please specify a path explicitly.'
    )
