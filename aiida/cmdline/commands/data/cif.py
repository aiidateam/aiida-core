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
from aiida.cmdline.commands import verdi_data
from aiida.cmdline.commands.data.list import _list, list_options
from aiida.cmdline.commands.data.export import _export, export_options
from aiida.cmdline.commands.data.deposit import deposit_tcod, deposit_options
from aiida.cmdline.utils import echo
from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.cmdline.params import arguments

from aiida.orm.data.structure import StructureData


@verdi_data.group('cif')
@click.pass_context
def cif(ctx):
    """help"""
    pass

@cif.command('show')
@arguments.NODES()
@click.option('-f', '--format', 'given_format',
              type=click.Choice(['jmol', 'vesta']),
              default='jmol',
              help="Type of the visualization format/tool.")
def show(nodes, given_format):
    """
    Visualize CifData objects
    """
    from aiida.orm.data.cif import CifData
    from aiida.cmdline.commands.data.show import _show_jmol
    from aiida.cmdline.commands.data.show import _show_vesta

    for n in nodes:
        if not isinstance(n, CifData):
            echo.echo_critical("Node {} is of class {} instead "
                                "of {}".format(n, type(n), StructureData))
    if given_format == "jmol":
        _show_jmol(given_format, nodes)
    elif given_format == "vesta":
        _show_vesta(given_format, nodes)
    else:
        raise NotImplementedError ("The format {} is not yet implemented"
                                   .format(given_format))

@cif.command('list')
@list_options
def cif_list(elements, elements_only, raw, formulamode, past_days, groups,
             all_users):
    """
    List store CifData objects
    """
    from aiida.orm.data.cif import CifData
    from tabulate import tabulate

    project = ["Id", "Formulae", "Source.URI"]

    entry_list = _list(CifData, project, elements,
                elements_only, formulamode, past_days,
                groups, all_users)

    cif_list_data = list([project])
    for entry in entry_list:
        # Formulate Formulae (second column) for printing
        if entry[1] is None:
            entry[1] = '?'
        elif isinstance(entry[1], list):
            entry[1] = ",".join(entry[1])

        # Formulate Source.URI (third column) for printing
        if entry[2] is None:
            entry[2] = '?'
    cif_list_data.extend(entry_list)
    echo.echo(tabulate(cif_list_data, headers="firstrow"))


@cif.command('export')
@click.option('-y', '--format',
              type=click.Choice(['cif', 'tcod', 'tcod_parameters']),
              default='cif',
              help="Type of the exported file.")
@export_options
def export(**kwargs):
    """
    Export CifData object
    """
    from aiida.orm.data.cif import CifData

    node = kwargs.pop('node')
    output = kwargs.pop('output')
    format = kwargs.pop('format')
    force = kwargs.pop('force')

    for key,value in kwargs.items():
        if value is None:
            kwargs.pop(key)  

    if not isinstance(node, CifData):
        echo.echo_critical("Node {} is of class {} instead of {}".format(node, type(node), CifData))
    _export(node, output, format, other_args=kwargs, overwrite=force)


@cif.command('import')
@click.option('-f', '--format',
              type=click.Choice(['cif']),
              default='cif',
              help="Type of the imported file.")
@click.option('--file',
              type=click.STRING,
              default="/dev/stdin",
              help="Path of the imported file. Reads from standard input if "
                   "not specified.")
def importfile(format, file):
    """
    Import structure into CifData object
    """
    import os
    from aiida.orm.data.cif import CifData

    try:
        node, _ = CifData.get_or_create(os.path.abspath(file))
        echo.echo(str(node))
    except ValueError as e:
        echo.echo_critical(e)


@cif.command('deposit')
@deposit_options
def deposit(**kwargs):
    """
    Deposit CifData object
    """
    from aiida.orm.data.cif import CifData
    # if not is_dbenv_loaded():
    #     load_dbenv()
    node = kwargs.pop('node')
    deposition_type = kwargs.pop('deposition_type')
    parameter_data = kwargs.pop('parameter_data')

    #if kwargs['database'] is None:
        #echo.echo_critical("Default database is not defined, please specify.")
    kwargs.pop('database') # looks like a bug, but deposit function called inside deposit_tcod complains about the 'database' keywords argument
    
    for key,value in kwargs.items():
        if value is None:
            kwargs.pop(key) 

    if not isinstance(node, CifData):
        echo.echo_critical("Node {} is of class {} instead of {}".format(node, type(node), CifData))
    echo.echo(deposit_tcod(node, deposition_type, parameter_data, **kwargs))

#@cif.command('deposit')
#@arguments.NODE()
#@click.option('--database', '-d',
              #type=['', '  '],
              #default='',
              #help="Label of the database for deposition.")
## deposition_cmdline_parameters
## Provides descriptions of command line options, that are used to control
## the process of deposition to TCOD.
##
## :param parser: an argparse.Parser instance
## :param expclass: name of the exported class to be shown in help string
##     for the command line options
##
## .. note:: This method must not set any default values for command line
##     options in order not to clash with any other data deposition plugins.
#@click.option('--type', '--deposition-type', '§',
              #type=click.Choice(['published','prepublication','personal']),
              #help="Type of the deposition.")
#@click.option('-u', '--username', type=click.STRING, default=None,
              #help="Depositor's username.")
#@click.option('-p', '--password', is_flag=True, default=None,
              #help="Depositor's password.")
#@click.option('--user-email', 'user_email', type=click.STRING, default=None,
              #help="Depositor's e-mail address.")
#@click.option('--title', type=click.STRING, default=None,
              #help="Title of the publication.")
#@click.option('--author-name', 'author_name', type=click.STRING, default=None,
              #help="Full name of the publication author.")
#@click.option('--author-email', type=click.STRING, default=None,
              #help="E-mail address of the publication author.")
#@click.option('--url', type=click.STRING,
              #help="URL of the deposition API.")
#@click.option('--code', 'code_label', type=click.STRING, default=None,
              #help="Label of the code to be used for the deposition. "
                   #"Default: cif_cod_deposit.")
#@click.option('--computer', 'computer_name', type=click.STRING,
              #help="Name of the computer to be used for deposition. Default "
                   #"computer is used if not specified.")
#@click.option('--replace', type=click.STRING,
              #help="ID of the structure to be redeposited replaced), if any.")
#@click.option('-m', '--message', type=click.STRING,
              #help="Description of the change (relevant for redepositions "
                   #"only.")
## extend_with_cmdline_parameters
## Provides descriptions of command line options, that are used to control
## the process of exporting data to TCOD CIF files.
##
## :param parser: an argparse.Parser instance
## :param expclass: name of the exported class to be shown in help string
##     for the command line options
##
## .. note:: This method must not set any default values for command line
##     options in order not to clash with any other data export plugins.
#@click.option('--no-reduce-symmetry', '--dont-reduce-symmetry',
              #'reduce_symmetry', is_flag=True, default=True,
              #help="Do not perform symmetry reduction.")
##@click.option('--parameter-data', type=click.INT, default=None,
              ##help="ID of the ParameterData to be exported alongside the {} "
                   ##"instance. By default, if {} originates from a calculation "
                   ##"with single ParameterData in the output, aforementioned "
                   ##"ParameterData is picked automatically. Instead, the "
                   ##"option is used in the case the calculation produces more "
                   ##"than a single instance of ParameterData."
              ##.format(CifData, CifData))
#@click.option('--no-dump-aiida-database', '--dont-dump-aiida-database',
              #'dump_aiida_database', is_flag=True, default=True,
              #help="Do not export AiiDA database to the CIF file.")
#@click.option('--no-exclude-external-contents', '--dont-exclude-external-contents',
              #'exclude_external_contents', is_flag=True, default=True,
              #help="Do not export AiiDA database to the CIF file.")
#@click.option('--gzip', is_flag=True, default=True,
              #help="Gzip large files.")
#@click.option('--gzip-threshold', type=click.INT, default=None,
              #help="Specify the minimum size of exported file which should be "
                   #"gzipped. Default 1024.")
#def deposit(node, parameter_data, deposition_type,  **kwargs):


    #print kwargs
    #echo.echo("node: " + str(node))
    ## echo.echo("database: " + str(database))
    ## echo.echo("deposition_type: " + str(deposition_type))
    ## echo.echo("username: " + str(username))
    ## echo.echo("password: " + str(password))
    ## echo.echo("user_email: " + str(user_email))
    ## echo.echo("title: " + str(title))
    ## echo.echo("author_name: " + str(author_name))
    ## echo.echo("author_email: " + str(author_email))
    ## echo.echo("url: " + str(url))
    ## echo.echo("code_label: " + str(code_label))
    ## echo.echo("computer_name: " + str(computer_name))
    ## echo.echo("replace: " + str(replace))
    ## echo.echo("message: " + str(message))
    ##
    ## echo.echo("reduce_symmetry: " + str(reduce_symmetry))
    #echo.echo("parameter_data: " + str(parameter_data))
    ## echo.echo("dump_aiida_database: " + str(dump_aiida_database))
    ## echo.echo("exclude_external_contents: " + str(exclude_external_contents))
    ## echo.echo("gzip: " + str(gzip))
    ## echo.echo("gzip_threshold: " + str(gzip_threshold))

    #try:
        #if not isinstance(node, CifData):
            #echo.echo_critical("Node {} is of class {} instead "
                                  #"of {}".format(node, type(node), CifData))
    #except AttributeError:
        #pass

    #from aiida.cmdline.commands.data.deposit import deposit_tcod

    #print deposit_tcod(node, deposition_type , kwargs)

