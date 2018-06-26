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
from aiida.cmdline.commands.data.list import _list
from aiida.cmdline.commands.data.export import _export
from aiida.cmdline.commands import verdi, verdi_data
from aiida.cmdline.params import arguments
from aiida.cmdline.params import options
from aiida.cmdline.utils import echo
from aiida.common.exceptions import DanglingLinkError
from aiida.cmdline.params.options.multivalue import MultipleValueOption
from aiida.backends.utils import load_dbenv, is_dbenv_loaded


def _show_ase(exec_name, structure_list):
    """
    Plugin to show the structure with the ASE visualizer
    """
    try:
        from ase.visualize import view
        for structure in structure_list:
            view(structure.get_ase())
    except ImportError:
        raise

def _show_jmol(exec_name, structure_list):
    """
    Plugin for jmol
    """
    import tempfile, subprocess

    with tempfile.NamedTemporaryFile() as f:
        for structure in structure_list:
            f.write(structure._exportstring('cif')[0])
        f.flush()

        try:
            subprocess.check_output([exec_name, f.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            echo.echo_info("the call to {} ended with an error.".format(
                exec_name))
        except OSError as e:
            if e.errno == 2:
                echo.echo_critical("No executable '{}' found. Add to the path, "
                        "or try with an absolute path.".format(
                    exec_name))
            else:
                raise
def _show_vesta(exec_name, structure_list):
    """
    Plugin for VESTA
    This VESTA plugin was added by Yue-Wen FANG and Abel Carreras
    at Kyoto University in the group of Prof. Isao Tanaka's lab

    """
    import sys
    import tempfile, subprocess

    with tempfile.NamedTemporaryFile(suffix='.cif') as f:
        for structure in structure_list:
            f.write(structure._exportstring('cif')[0])
        f.flush()

        try:
            subprocess.check_output([exec_name, f.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            echo.echo_info("the call to {} ended with an error.".format(
                exec_name))
        except OSError as e:
            if e.errno == 2:
                echo.echo_critical("No executable '{}' found. Add to the path, "
                        "or try with an absolute path.".format(exec_name))
            else:
                raise

def _show_vmd(exec_name, structure_list):
    """
    Plugin for vmd
    """
    import tempfile, subprocess

    if len(structure_list) > 1:
        raise MultipleObjectsError("Visualization of multiple objects "
                                    "is not implemented")
    structure = structure_list[0]

    with tempfile.NamedTemporaryFile(suffix='.xsf') as f:
        f.write(structure._exportstring('xsf')[0])
        f.flush()

        try:
            subprocess.check_output([exec_name, f.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            echo.echo_info("the call to {} ended with an error.".format(
                exec_name))
        except OSError as e:
            if e.errno == 2:
                echo.echo_critical ("No executable '{}' found. Add to the path, "
                        "or try with an absolute path.".format(
                    exec_name))
            else:
                raise
def _show_xcrysden(exec_name, structure_list):
    """
    Plugin for xcrysden
    """
    import sys
    import tempfile, subprocess

    if len(structure_list) > 1:
        raise MultipleObjectsError("Visualization of multiple objects "
                                    "is not implemented")
    structure = structure_list[0]

    with tempfile.NamedTemporaryFile(suffix='.xsf') as f:
        f.write(structure._exportstring('xsf')[0])
        f.flush()

        try:
            subprocess.check_output([exec_name, '--xsf', f.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            echo.echo_info("the call to {} ended with an error.".format(
                exec_name))
        except OSError as e:
            if e.errno == 2:
                echo_critical("No executable '{}' found. Add to the path, "
                        "or try with an absolute path.".format(
                    exec_name))
            else:
                raise

@verdi_data.group('structure')
@click.pass_context
def structure(ctx):
    """
    Manipulation of the structures
    """
    pass
    

@structure.command('show')
@arguments.NODES()
@click.option('-f', '--format', 'format',
              type=click.Choice(['ase', 'jmol', 'vesta', 'vmd', 'xcrysden']),
              default='ase',
              help="Type of the visualization format/tool")
def show(nodes, format):
    """
    Visualize structure objects
    """
    from aiida.orm.data.structure import StructureData
    for n in nodes:
        if not isinstance(n, StructureData):
            echo.echo_critical("Node {} is of class {} instead "
                                "of {}".format(n, type(n), StructureData))
    if format == "ase":
        _show_ase(format, nodes)
    elif format == "jmol":
        _show_jmol(format, nodes)
    elif format == "vesta":
        _show_vesta(format, nodes)
    elif format == "vmd":
        _show_vmd(format, nodes)
    elif format == "xcrysden":
        _show_xcrysden(format, nodes)
    else:
        raise

@structure.command('list')
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
def list_structures(elements, elements_only, formulamode, past_days, groups, all_users):
    """
    List stored StructureData objects
    """
    from aiida.orm.data.structure import StructureData
    from aiida.orm.data.structure import (get_formula, get_symbols_string)
    project = ["Id", "Label", "Kinds", "Sites"]
    lst = _list(StructureData, project, elements, elements_only, formulamode, past_days, groups, all_users)
    entry_list = []
    for [id, label, akinds, asites] in lst:
        # If symbols are defined there is a filtering of the structures
        # based on the element
        # When QueryBuilder will support this (attribute)s filtering,
        # it will be pushed in the query.
        if elements is not None:
            all_symbols = [_["symbols"][0] for _ in akinds]
            if not any([s in elements for s in all_symbols]):
                continue

            if elementonly:
                echo.echo_critical("Not implemented elementonly search")

        # We want only the StructureData that have attributes
        if akinds is None or asites is None:
            continue

        symbol_dict = {}
        for k in akinds:
            symbols = k['symbols']
            weights = k['weights']
            symbol_dict[k['name']] = get_symbols_string(symbols,
                                                        weights)

        try:
            symbol_list = []
            for s in asites:
                symbol_list.append(symbol_dict[s['kind_name']])
            formula = get_formula(symbol_list,
                                    mode=formulamode)
        # If for some reason there is no kind with the name
        # referenced by the site
        except KeyError:
            formula = "<<UNKNOWN>>"
        entry_list.append([str(id), str(formula), label])
    
    column_length = 19
    vsep = " "
    if entry_list:
        to_print = ""
        to_print += vsep.join([ s.ljust(column_length)[:column_length] for s in project]) + "\n"
        for entry in sorted(entry_list, key=lambda x: int(x[0])):
            to_print += vsep.join([ str(s).ljust(column_length)[:column_length] for s in entry]) + "\n"
        echo.echo(to_print)
    else:
        echo.echo_warning("No nodes of type {} where found in the database".format(datatype))

@structure.command('export')
@click.option('-y', '--format',
              type=click.Choice(['cif', 'tcod', 'xsf', 'xyz']),
              default='xyz',
              help="Type of the exported file.")
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
def export(format, reduce_symmetry, parameter_data, dump_aiida_database, exclude_external_contents, gzip, gzip_threshold, output, force, node):
    """
    Export structure
    """
    from aiida.orm.data.structure import StructureData
    args = {}
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

    if not isinstance(node, StructureData):
        echo.echo_critical("Node {} is of class {} instead of {}".format(node, type(node), StructureData))
    _export(node, output, format, other_args=args, overwrite=force)


def deposit_tcod(node, parameter_data=None, **kwargs):
    """
    Deposition plugin for TCOD.
    """
    from aiida.orm.data.structure import StructureData
    from aiida.tools.dbexporters.tcod import deposit
    parameters = None
    if parameter_data is not None:
        from aiida.orm import DataFactory
        ParameterData = DataFactory('parameter')
        parameters = load_node(parameter_data, sub_class=ParameterData)
    return deposit(node, StructureData, parameters, **kwargs)

@structure.command('deposit')
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
    Deposit data object
    """
    from aiida.orm.data.structure import StructureData
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

    if not isinstance(node, StructureData):
        echo.echo_critical("Node {} is of class {} instead of {}".format(node, type(node), StructureData))
    calc = deposit_tcod(node, parameter_data, **args)


def _import_xyz(filename, **kwargs):
    """
    Imports an XYZ-file.
    """
    from os.path import abspath
    from aiida.orm.data.structure import StructureData

    vacuum_addition = kwargs.pop('vacuum_addition')
    vacuum_factor = kwargs.pop('vacuum_factor')
    pbc = [bool(i) for i in kwargs.pop('pbc')]
    store = kwargs.pop('store')
    view_in_ase = kwargs.pop('view')

    echo.echo('importing XYZ-structure from: \n  {}'.format(abspath(filename)))
    filepath = abspath(filename)
    with open(filepath) as f:
        xyz_txt = f.read()
    new_structure = StructureData()
    try:
        new_structure._parse_xyz(xyz_txt)
        new_structure._adjust_default_cell(vacuum_addition=vacuum_addition,
                                            vacuum_factor=vacuum_factor,
                                            pbc=pbc)

        if store:
            new_structure.store()
        if view_in_ase:
            from ase.visualize import view
            view(new_structure.get_ase())
        echo.echo(
            '  Succesfully imported structure {}, '
            '(PK = {})'.format(new_structure.get_formula(), new_structure.pk)
        )

    except ValueError as e:
        echo.echo_critical(e)


def _import_pwi(filename, **kwargs):
    """
    Imports a structure from a quantumespresso input file.
    """
    from os.path import abspath
    try:
        from qe_tools.parsers.pwinputparser import PwInputFile
    except ImportError:
        echo.echo ("You have not installed the package qe-tools. \n"
                "You can install it with: pip install qe-tools")
        sys.exit(1)

    store = kwargs.pop('store')
    view_in_ase = kwargs.pop('view')

    echo.echo('importing structure from: \n  {}'.format(abspath(filename)))
    filepath = abspath(filename)

    try:
        inputparser = PwInputFile(filepath)
        new_structure = inputparser.get_structuredata()

        if store:
            new_structure.store()
        if view_in_ase:
            from ase.visualize import view
            view(new_structure.get_ase())
        echo.echo(
            '  Succesfully imported structure {}, '
            '(PK = {})'.format(new_structure.get_formula(), new_structure.pk)
        )

    except ValueError as e:
        echo.echo_critical(e)

def _import_ase(filename, **kwargs):
    """
    Imports a structure in a number of formats using the ASE routines.
    """
    from os.path import abspath
    from aiida.orm.data.structure import StructureData

    try:
        import ase.io
    except ImportError:
        echo.echo ("You have not installed the package ase. \n"
                "You can install it with: pip install ase")
        sys.exit(1)

    store = kwargs.pop('store')
    view_in_ase = kwargs.pop('view')

    echo.echo( 'importing structure from: \n  {}'.format(abspath(filename)))
    filepath = abspath(filename)

    try:
        asecell = ase.io.read(filepath)
        new_structure = StructureData(ase=asecell)

        if store:
            new_structure.store()
        if view_in_ase:
            from ase.visualize import view
            view(new_structure.get_ase())
        echo.echo(
            '  Succesfully imported structure {}, '
            '(PK = {})'.format(new_structure.get_formula(), new_structure.pk)
        )

    except ValueError as e:
        echo.echo_critical(e)

@structure.command('import')
@click.option('--file', 'filename',
              type=click.Path(exists=True, dir_okay=False, resolve_path=True),
              help="Path of the imported file. Reads from standard"
              " input if not specified")
@click.option('-f', '--format',
              type=click.Choice(['ase', 'pwi', 'xyz']),
              default='xyz',
              help="Type of the imported file.")
@click.option('--vacuum-factor', type=click.FLOAT,
              default=1.0,
              help="The factor by which the cell accomodating the"
              " structure should be increased, default: 1.0")
@click.option('--vacuum-addition', type=click.FLOAT,
              default=10.0,
              help="The distance to add to the unit cell after"
              " vacuum factor was applied to expand in each"
              " dimension, default: 10.0")
@click.option('--pbc', type=click.INT,
              nargs=3,
              default=[0, 0, 0],
              help="Set periodic boundary conditions for each"
              " lattice direction, 0 for no periodicity, any"
              " other integer for periodicity")
@click.option('--view', is_flag=True,
              default=False,
              help='View resulting structure using ASE.')
@click.option('--dont-store', 'store', is_flag=True,
              default=True,
              help='View resulting structure using ASE.')
def structure_import(filename, format, vacuum_factor, vacuum_addition, pbc, view, store):
    """
    Import structure
    """
    if not is_dbenv_loaded():
        load_dbenv()
    if not filename:
        filename = "/dev/stdin"
    
    args = {}
    if vacuum_factor is not None:
        args['vacuum_factor'] = vacuum_factor
    if vacuum_addition is not None:
        args['vacuum_addition'] = vacuum_addition
    if pbc is not None:
        args['pbc'] = pbc
    if view is not None:
        args['view'] = view
    if store is not None:
        args['store'] = store

    if format == "ase":
        _import_ase(filename, **args)
    elif format == "pwi":
        _import_pwi(filename, **args)
    elif format == "xyz":
        _import_xyz(filename, **args)
    else:
        raise
