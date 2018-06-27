# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import click
from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.cmdline.commands import verdi, verdi_data
from aiida.cmdline.commands.data.export import _export
from aiida.cmdline.commands.data.deposit import deposit_tcod
from aiida.cmdline.params import arguments
from aiida.cmdline.params import options
from aiida.cmdline.utils import echo
from aiida.common.exceptions import DanglingLinkError
from aiida.cmdline.params.options.multivalue import MultipleValueOption
from aiida.cmdline.commands.data.list import _list
from aiida.backends.utils import load_dbenv, is_dbenv_loaded



        
@verdi_data.group('trajectory')
@click.pass_context
def trajectory(ctx):
    """
    View and manipulate TrajectoryData instances.
    """
    pass

@trajectory.command('list')
@click.option('-e', '--elements', type=click.STRING,
              cls=MultipleValueOption,
              default=None,
              help="Print all structures"
              "containing desired elements")
@click.option('-eo', '--elements-only', type=click.STRING,
              cls=MultipleValueOption,
              default=None,
              help="Print all structures "
              "containing only the selected elements")
@click.option('-f', '--formulamode',
              type=click.Choice(['hill', 'hill_compact', 'reduce', 'group', 'count', 'count_compact']),
              default='hill',
              help="Formula printing mode (if None, does not print the formula)")
@click.option('-p', '--past-days', type=click.INT,
              default=None,
              help="Add a filter to show only structures"
              " created in the past N days")
@options.GROUPS()
@click.option('-A', '--all-users', is_flag=True, default=False,
              help="show groups for all users, rather than only for the"
              "current user")
def list_trajections(elements, elements_only, formulamode, past_days, groups, all_users):
    """
    List trajectories stored in database.
    """
    from aiida.orm.data.array.trajectory import TrajectoryData
    project = ["Id"]
    lst = _list(TrajectoryData, project, elements, elements_only, formulamode, past_days, groups, all_users)
    column_length = 19
    vsep = " "
    if lst:
        to_print = ""
        to_print += vsep.join([ s.ljust(column_length)[:column_length] for s in project]) + "\n"
        for entry in sorted(lst, key=lambda x: int(x[0])):
            to_print += vsep.join([ str(s).ljust(column_length)[:column_length] for s in entry]) + "\n"
        echo.echo(to_print)
    else:
        echo.echo_warning("No nodes of type {} where found in the database".format(TrajectoryData))

def _show_jmol(exec_name, trajectory_list, **kwargs):
    """
    Plugin for jmol
    """
    import tempfile, subprocess

    with tempfile.NamedTemporaryFile() as f:
        for trajectory in trajectory_list:
            f.write(trajectory._exportstring('cif', **kwargs)[0])
        f.flush()

        try:
            subprocess.check_output([exec_name, f.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            print "Note: the call to {} ended with an error.".format(
                exec_name)
        except OSError as e:
            if e.errno == 2:
                echo.echo_critical ("No executable '{}' found. Add to the path, "
                        "or try with an absolute path.".format(
                    exec_name))
            else:
                raise


def _show_xcrysden(exec_name, trajectory_list, **kwargs):
    """
    Plugin for xcrysden
    """
    import tempfile, subprocess
    from aiida.common.exceptions import MultipleObjectsError

    if len(trajectory_list) > 1:
        raise MultipleObjectsError("Visualization of multiple trajectories "
                                    "is not implemented")
    trajectory = trajectory_list[0]

    with tempfile.NamedTemporaryFile(suffix='.xsf') as f:
        f.write(trajectory._exportstring('xsf', **kwargs)[0])
        f.flush()

        try:
            subprocess.check_output([exec_name, '--xsf', f.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            print "Note: the call to {} ended with an error.".format(
                exec_name)
        except OSError as e:
            if e.errno == 2:
                print ("No executable '{}' found. Add to the path, "
                        "or try with an absolute path.".format(
                    exec_name))
                sys.exit(1)
            else:
                raise

def _show_mpl_pos(exec_name, trajectory_list, **kwargs):
    """
    Produces a matplotlib plot of the trajectory
    """
    for t in trajectory_list:
        t.show_mpl_pos(**kwargs)


def _show_mpl_heatmap(exec_name, trajectory_list, **kwargs):
    """
    Produces a matplotlib plot of the trajectory
    """
    for t in trajectory_list:
        t.show_mpl_heatmap(**kwargs)

@trajectory.command('show')
@arguments.NODES()
@click.option('-f', '--format', 'format',
              type=click.Choice(['jmol', 'xcrysden', 'mpl_heatmap', 'mpl_pos']),
              default='jmol',
              help="Type of the visualization format/tool")
@click.option('--step', type=click.INT,
              default=None,
              help="ID of the trajectory step. If none is supplied, all"
              " steps are explored.")
@click.option('-c', '--contour', type=click.FLOAT,
              cls=MultipleValueOption,
              default=None,
              help="Isovalues to plot")
@click.option('--sampling-stepsize', type=click.INT,
              default=None,
              help="Sample positions in plot every sampling_stepsize"
              " timestep")
@click.option('--stepsize', type=click.INT,
              default=None,
              help="The stepsize for the trajectory, set it higher"
              " to reduce number of points")
@click.option('--mintime', type=click.INT,
              default=None,
              help="The time to plot from")
@click.option('--maxtime', type=click.INT,
              default=None,
              help="The time to plot to")
@click.option('-e', '--elements', type=click.STRING,
              cls=MultipleValueOption,
              default=None,
              help="Show only atoms of that species")
@click.option('--indices', type=click.INT,
              cls=MultipleValueOption,
              default=None,
              help="Show only these indices")
@click.option('--dont-block', 'block', is_flag=True,
              default=True,
              help="Don't block interpreter when showing plot.")
def show(nodes, format, step, contour, sampling_stepsize, stepsize, mintime, maxtime, elements, indices, block):
    """
    Visualize trajectory
    """
    from aiida.orm.data.array.trajectory import TrajectoryData
    for n in nodes:
        if not isinstance(n, TrajectoryData):
            echo.echo_critical("Node {} is of class {} instead "
                                "of {}".format(n, type(n), TrajectoryData))
    args = {}
    if step is not None:
        args['step'] = step
    if contour is not None:
        args['contour'] = contour
    if sampling_stepsize is not None:
        args['sampling_stepsize'] = sampling_stepsize
    if stepsize is not None:
        args['stepsize'] = stepsize
    if mintime is not None:
        args['mintime'] = mintime
    if maxtime is not None:
        args['maxtime'] = maxtime
    if elements is not None:
        args['elements'] = elements
    if indices is not None:
        args['indices'] = indices



    if format == "jmol":
        _show_jmol(format, nodes, **args)
    elif format == "xcrysden":
        _show_xcrysden(format, nodes, **args)
    elif format == "mpl_pos":
        _show_mpl_pos(format, nodes, **args)
    elif format == "mpl_heatmap":
        _show_mpl_heatmap(format, nodes, **args)
    else:
        raise


@trajectory.command('export')
@click.option('-y', '--format',
              type=click.Choice(['cif', 'tcod', 'xsf']),
              default='cif',
              help="Type of the exported file.")
@click.option('--step', type=click.INT,
              default=None,
              help="ID of the trajectory step. If none is supplied, all"
              " steps are explored.")
@click.option('--reduce-symmetry/--no-reduce-symmetry', 'reduce_symmetry', is_flag=True,
              default=None,
              help='Do (default) or do not perform symmetry reduction.')
@click.option('--parameter-data', type=click.INT,
              default=None,
              help="ID of the ParameterData to be exported alongside the"
                    " StructureData instance. By default, if StructureData"
                    " originates from a calculation with single"
                    " ParameterData in the output, aforementioned"
                    " ParameterData is picked automatically. Instead, the"
                    " option is used in the case the calculation produces"
                    " more than a single instance of ParameterData.")
@click.option('--dump-aiida-database/--no-dump-aiida-database', 'dump_aiida_database', is_flag=True,
              default=None,
              help='Export (default) or do not export AiiDA database to the CIF file.')
@click.option('--exclude-external-contents/--no-exclude-external-contents', 'exclude_external_contents', is_flag=True,
              default=None,
              help='Do not (default) or do save the contents for external resources even if URIs are provided')
@click.option('--gzip/--no-gzip', is_flag=True,   
              default=None,
              help='Do or do not (default) gzip large files.')
@click.option('--gzip-threshold', type=click.INT,
              default=None,
              help="Specify the minimum size of exported file which should"
              " be gzipped.")
@click.option('-o', '--output', type=click.STRING,
              default=None,
              help="If present, store the output directly on a file "
              "with the given name. It is essential to use this option "
              "if more than one file needs to be created.")
@options.FORCE(help="If passed, overwrite files without checking.")
@arguments.NODE()
def export(format, step, reduce_symmetry, parameter_data, dump_aiida_database, exclude_external_contents, gzip, gzip_threshold, output, force, node):
    """
    Export trajectory
    """
    from aiida.orm.data.array.trajectory import TrajectoryData
    args = {}
    if reduce_symmetry is not None:
        args['reduce_symmetry'] = reduce_symmetry
    if step is not None:
        args['step'] = step
    if parameter_data is not None:
        args['parameter_data'] = parameter_data
    if dump_aiida_database is not None:
        args['dump_aiida_database'] = dump_aiida_database
    if exclude_external_contents is not None:
        args['exclude_external_contents'] = exclude_external_contents
    if gzip is not None:
        args['gzip'] = gzip
    if gzip_threshold is not None:
        args['gzip_threshold'] = gzip_threshold

    if not isinstance(node, TrajectoryData):
        echo.echo_critical("Node {} is of class {} instead of {}".format(node, type(node), TrajectoryData))
    _export(node, output, format, other_args=args, overwrite=force)


@trajectory.command('deposit')
@click.option('-d', '--database', 'database',
              type=click.Choice(['tcod']),
              default='tcod',
              help="Label of the database for deposition.")
@click.option('--deposition-type',
              type=click.Choice(['published', 'prepublication', 'personal']),
              default='published',
              help="Type of the deposition.")
@click.option('-u', '--username', type=click.STRING,
              default=None,
              help="Depositor's username.")
@click.option('-p', '--password', type=click.STRING,
              default=None,
              help="Depositor's password.")
@click.option('--user-email', type=click.STRING,
              default=None,
              help="Depositor's e-mail address.")
@click.option('--title', type=click.STRING,
              default=None,
              help="Title of the publication.")
@click.option('--author-name', type=click.STRING,
              default=None,
              help="Full name of the publication author.")
@click.option('--author-email', type=click.STRING,
              default=None,
              help="E-mail address of the publication author.")
@click.option('--url', type=click.STRING,
              default=None,
              help="URL of the deposition API.")
@click.option('--code', type=click.STRING,
              default=None,
              help="Label of the code to be used for the deposition."
              " Default: cif_cod_deposit.")
@click.option('--computer', type=click.STRING,
              default=None,
              help="Name of the computer to be used for deposition.")
@click.option('--replace', type=click.INT,
              default=None,
              help="ID of the structure to be redeposited (replaced), if any.")
@click.option('-m', '--message', type=click.STRING,
              default=None,
              help="Description of the change (relevant for redepositions only).")
@click.option('--reduce-symmetry/--no-reduce-symmetry', 'reduce_symmetry', is_flag=True,
              default=None,
              help='Do (default) or do not perform symmetry reduction.')
@click.option('--parameter-data', type=click.INT,
              default=None,
              help="ID of the ParameterData to be exported alongside the"
                    " StructureData instance. By default, if StructureData"
                    " originates from a calculation with single"
                    " ParameterData in the output, aforementioned"
                    " ParameterData is picked automatically. Instead, the"
                    " option is used in the case the calculation produces"
                    " more than a single instance of ParameterData.")
@click.option('--dump-aiida-database/--no-dump-aiida-database', 'dump_aiida_database', is_flag=True,
              default=None,
              help='Export (default) or do not export AiiDA database to the CIF file.')
@click.option('--exclude-external-contents/--no-exclude-external-contents', 'exclude_external_contents', is_flag=True,
              default=None,
              help='Do not (default) or do save the contents for external resources even if URIs are provided')
@click.option('--gzip/--no-gzip', 'gzip', is_flag=True,   
              default=None,
              help='Do or do not (default) gzip large files.')
@click.option('--gzip-threshold', type=click.INT,
              default=None,
              help="Specify the minimum size of exported file which should"
              " be gzipped.")
@arguments.NODE()
def deposit(database, deposition_type, username, password, user_email, title, author_name, author_email, url, code, computer, replace, message, reduce_symmetry, parameter_data, dump_aiida_database, exclude_external_contents, gzip, gzip_threshold, node):
    """
    Deposit trajectory object
    """
    from aiida.orm.data.array.trajectory import TrajectoryData
    if not is_dbenv_loaded():
        load_dbenv()
    if database is None:
        echo_critical("Default database is not defined, please specify.")
    
    args = {}
    if deposition_type is not None:
        args['deposition_type'] = deposition_type
    if username is not None:
        args['username'] = username
    if password is not None:
        args['password'] = password
    if user_email is not None:
        args['user_email'] = user_email
    if title is not None:
        args['title'] = title
    if author_name is not None:
        args['author_name'] = author_name
    if author_email is not None:
        args['author_email'] = author_email
    if url is not None:
        args['url'] = url
    if code is not None:
        args['code'] = code
    if code is not None:
        args['computer'] = computer
    if replace is not None:
        args['replace'] = replace
    if message is not None:
        args['message'] = message
    if reduce_symmetry is not None:
        args['reduce_symmetry'] = reduce_symmetry
    if parameter_data is not None:
        args['parameter_data'] = parameter_data
    if dump_aiida_database is not None:
        args['dump_aiida_database'] = dump_aiida_database
    if exclude_external_contents is not None:
        args['exclude_external_contents'] = exclude_external_contents
    if gzip is not None:
        args['gzip'] = gzip
    if gzip_threshold is not None:
        args['gzip_threshold'] = gzip_threshold
    
    if not isinstance(node, TrajectoryData):
        echo.echo_critical("Node {} is of class {} instead of {}".format(node, type(node), TrajectoryData))
    calc = deposit_tcod(node, parameter_data, **args)
