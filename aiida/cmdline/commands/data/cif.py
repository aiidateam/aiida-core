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
from aiida.cmdline.commands import verdi, verdi_data
from aiida.cmdline.params import options
from aiida.cmdline.utils import echo
from aiida.orm.data.cif import CifData
from aiida.utils import timezone
import datetime
from aiida.common.exceptions import MultipleObjectsError
from aiida.common.utils import Prettifier
from aiida.cmdline.commands.data.export import _export
from aiida.cmdline.params import arguments

@verdi_data.group('cif')
@click.pass_context
def cif(ctx):
    """help"""
    pass
    

@click.option('--vseparator', default="\t",
    help="specify vertical separator for fields. Default '\\t'.")
@click.option('--header/--no-header', default=True,
    help="print a header with column names. Default option is with header "
         "enabled.")
@click.option('-p', '--past-days', type=click.INT,
             default=None,
             help="Add a filter to show only bandsdatas"
                  " created in the past N days")
@click.option('-A', '--all-users', is_flag=True, default=False,
             help="show groups for all users, rather than only for the"
                  "current user")
@options.GROUPS()
@cif.command('list')
def list(vseparator, header, past_days, all_users, groups):

    entry_list = query(past_days, all_users, groups)

    if entry_list:
        to_print = ""
        if header:
            to_print += vseparator.join(get_column_names()) + "\n"
        for entry in sorted(entry_list, key=lambda x: int(x[0])):
            to_print += vseparator.join(entry) + "\n"
        echo.echo(to_print)

def get_column_names():
    """
    Return the list with column names.

    :note: neither the number nor correspondence of column names and
        actual columns in the output from the query() are checked.
    """
    return ["ID", "formulae", "source_uri"]

def query(past_days, all_users, groups):
    """
    Perform the query and return information for the list.

    :param args: a namespace with parsed command line parameters.
    :return: table (list of lists) with information, describing nodes.
        Each row describes a single hit.
    """
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.implementation import Group
    from aiida.orm.user import User
    from aiida.orm.backend import construct_backend

    backend = construct_backend()

    qb = QueryBuilder()
    if all_users is False:
        user = backend.users.get_automatic_user()
        qb.append(User, tag="creator", filters={"email": user.email})
    else:
        qb.append(User, tag="creator")

    st_data_filters = {}

    if past_days is not None:
        now = timezone.now()
        n_days_ago = now - datetime.timedelta(days=past_days)
        st_data_filters.update({"ctime": {'>=': n_days_ago}})

    qb.append(CifData, tag="struc", created_by="creator",
              filters=st_data_filters,
              project=["*"])

    if groups is not None and len(groups) != 0:
        group_filters = {}
        group_filters.update({"name": {"in": [g.pk for g in groups]}})
        qb.append(Group, tag="group", filters=group_filters, group_of="struc")

    qb.order_by({CifData: {'ctime': 'asc'}})
    res = qb.distinct()

    entry_list = []
    if res.count() > 0:
        for [obj] in res.iterall():
            formulae = '?'
            try:
                formulae = ",".join(obj.get_attr('formulae'))
            except AttributeError:
                pass
            except TypeError:
                pass
            source_uri = '?'
            try:
                source_uri = obj.get_attr('source')['uri']
            except AttributeError:
                pass
            except KeyError:
                pass
            entry_list.append([str(obj.pk), formulae, source_uri])
    return entry_list

valid_formats = ['jmol', 'vesta']
@cif.command()
@arguments.NODES()
@click.option('-f', '--format', 'format',
              type=click.Choice(valid_formats),
              default='jmol',
              help="Type of the visualization format/tool.")
def show(nodes, format):
    """
    Show the data node with a visualization program.
    """

    args = list(args)
    parsed_args = vars(parser.parse_args(args))

    data_id = parsed_args.pop('data_id')
    format = parsed_args.pop('format')

    # Removing the keys, whose values are None
    for key in parsed_args.keys():
        if parsed_args[key] is None:
            parsed_args.pop(key)

    if format is None:
        echo.echo_critical(
            "Default format is not defined, please specify.\n"
            "Valid formats are: {}".format(valid_formats))

    for n in nodes:
        try:
            if not isinstance(n, CifData):
                echo.echo_critical("Node {} is of class {} instead "
                                      "of {}".format(n, type(n), CifData))
        except AttributeError:
            pass

    try:
        if format == 'jmol':
            _show_jmol(format, nodes)
        if format == 'vesta':
            _show_vesta(format, nodes)
    except MultipleObjectsError:
        echo.echo_critical(
            "Visualization of multiple objects is not implemented "
            "for '{}'".format(format))

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
            print "Note: the call to {} ended with an error.".format(
                exec_name)
        except OSError as e:
            if e.errno == 2:
                echo.echo_critical("No executable '{}' found. Add to the path, "
                       "or try with an absolute path.".format(
                    exec_name))
            else:
                raise

def _show_vesta(exec_name, structure_list):
    """
    Plugin for VESTA, added by Yue-Wen FANG and Abel Carreras
    at Kyoto University in the group of Prof. Isao Tanaka's lab
    """
    import tempfile, subprocess

    with tempfile.NamedTemporaryFile(suffix='.cif') as f:
        for structure in structure_list:
            f.write(structure._exportstring('cif')[0])
        f.flush()

        try:
            subprocess.check_output([exec_name, f.name])
        except subprocess.CalledProcessError:
            # The program died: just print a message
            print "Note: the call to {} ended with an error.".format(exec_name)
        except OSError as e:
            if e.errno == 2:
                echo.echo_critical("No executable '{}' found. Add to the path, "
                       "or try with an absolute path.".format(exec_name))
            else:
                raise

export_formats = ['cif', 'tcod', 'tcod_parameters']
@cif.command('export')
@click.option('-y', '--format',
              type=click.Choice(export_formats),
              default='json',
              help="Type of the exported file.")
@click.option('-o', '--output', type=click.STRING,
              default=None,
              help="If present, store the output directly on a file "
              "with the given name. It is essential to use this option "
              "if more than one file needs to be created.")
@options.FORCE(help="If passed, overwrite files without checking.")
@arguments.NODE()
def export(format, output, force, prettify_format, node):
    """
    Export the data node to a given format.
    """
    try:
        if not isinstance(n, CifData):
            echo.echo_critical("Node {} is of class {} instead "
                                  "of {}".format(n, type(n), CifData))
    except AttributeError:
        pass

    if format == 'cif':
        func = _export_cif
    elif format == 'tcod':
        func = _export_tcod
    elif format == 'tcod_parameters':
        func = _export_tcod_parameters

    func(node, output_fname=output, overwrite=force)


def _export_cif(node, output_fname, overwrite, **kwargs):
    """
    Exporter to CIF.
    """
    _export(node, output_fname, fileformat='cif', overwrite=overwrite,
                        other_args=kwargs)

def _export_tcod(node, output_fname, overwrite, parameter_data=None, **kwargs):
    """
    Plugin for TCOD
    """
    parameters = None
    if parameter_data is not None:
        from aiida.orm import DataFactory
        ParameterData = DataFactory('parameter')
        parameters = load_node(parameter_data, sub_class=ParameterData)
    _export(node, output_fname, fileformat='tcod', overwrite=overwrite,
                        other_args=kwargs)

def _export_tcod_parameters(self, parser, **kwargs):
    """
    Command line parameters for TCOD
    """
    from aiida.tools.dbexporters.tcod import extend_with_cmdline_parameters
    extend_with_cmdline_parameters(parser, self.dataclass.__name__)


import_formats = ['cif']
@cif.command('import')
@click.option('-f', '--format',
              type=click.Choice(import_formats),
              default=import_formats[0],
              help="Type of the imported file.")
@click.option('--file',
              type=click.STRING,
              default="/dev/stdin",
              help="Path of the imported file. Reads from standard input if "
                   "not specified.")
def importfile(format, file):
    import os.path
    try:
        node, _ = CifData.get_or_create(os.path.abspath(file))
        print node
    except ValueError as e:
        print e


def _deposit_tcod(node, parameter_data=None, **kwargs):
    """
    Deposition plugin for TCOD.
    """
    from aiida.tools.dbexporters.tcod import deposit

    parameters = None
    if parameter_data is not None:
        from aiida.orm import DataFactory
        ParameterData = DataFactory('parameter')
        parameters = load_node(parameter_data, sub_class=ParameterData)
    return deposit(node, parameters=parameters, **kwargs)


def _deposit_tcod_parameters(self, parser, **kwargs):
    """
    Command line parameters deposition plugin for TCOD.
    """
    from aiida.tools.dbexporters.tcod import (deposition_cmdline_parameters,
                                              extend_with_cmdline_parameters)
    deposition_cmdline_parameters(parser, self.dataclass.__name__)
    extend_with_cmdline_parameters(parser, self.dataclass.__name__)


from aiida.tools.dbexporters.tcod import default_options
databases = {'tcod': _deposit_tcod, 'tcod_parameters': _deposit_tcod_parameters}
@cif.command('deposit')
@arguments.NODE()
@click.option('--database', '-d',
              type=click.Choice(databases.keys()),
              default=databases.keys()[0],
              help="Label of the database for deposition.")
# deposition_cmdline_parameters
# Provides descriptions of command line options, that are used to control
# the process of deposition to TCOD.
#
# :param parser: an argparse.Parser instance
# :param expclass: name of the exported class to be shown in help string
#     for the command line options
#
# .. note:: This method must not set any default values for command line
#     options in order not to clash with any other data deposition plugins.
@click.option('--type', '--deposition-type', 'deposition_type',
              type=click.Choice(['published','prepublication','personal']),
              help="Type of the deposition.")
@click.option('-u', '--username', type=click.STRING, default=None,
              help="Depositor's username.")
@click.option('-p', '--password', is_flag=True, default=None,
              help="Depositor's password.")
@click.option('--user-email', 'user_email', type=click.STRING, default=None,
              help="Depositor's e-mail address.")
@click.option('--title', type=click.STRING, default=None,
              help="Title of the publication.")
@click.option('--author-name', 'author_name', type=click.STRING, default=None,
              help="Full name of the publication author.")
@click.option('--author-email', type=click.STRING, default=None,
              help="E-mail address of the publication author.")
@click.option('--url', type=click.STRING,
              help="URL of the deposition API.")
@click.option('--code', 'code_label', type=click.STRING, default=None,
              help="Label of the code to be used for the deposition. "
                   "Default: cif_cod_deposit.")
@click.option('--computer', 'computer_name', type=click.STRING,
              help="Name of the computer to be used for deposition. Default "
                   "computer is used if not specified.")
@click.option('--replace', type=click.STRING,
              help="ID of the structure to be redeposited replaced), if any.")
@click.option('-m', '--message', type=click.STRING,
              help="Description of the change (relevant for redepositions "
                   "only.")
# extend_with_cmdline_parameters
# Provides descriptions of command line options, that are used to control
# the process of exporting data to TCOD CIF files.
#
# :param parser: an argparse.Parser instance
# :param expclass: name of the exported class to be shown in help string
#     for the command line options
#
# .. note:: This method must not set any default values for command line
#     options in order not to clash with any other data export plugins.
@click.option('--no-reduce-symmetry', '--dont-reduce-symmetry',
              'reduce_symmetry', is_flag=True, default=True,
              help="Do not perform symmetry reduction.")
@click.option('--parameter-data', type=click.INT, default=None,
              help="ID of the ParameterData to be exported alongside the {} "
                   "instance. By default, if {} originates from a calculation "
                   "with single ParameterData in the output, aforementioned "
                   "ParameterData is picked automatically. Instead, the "
                   "option is used in the case the calculation produces more "
                   "than a single instance of ParameterData."
              .format(CifData, CifData))
@click.option('--no-dump-aiida-database', '--dont-dump-aiida-database',
              'dump_aiida_database', is_flag=True, default=True,
              help="Do not export AiiDA database to the CIF file.")
@click.option('--no-exclude-external-contents', '--dont-exclude-external-contents',
              'exclude_external_contents', is_flag=True, default=True,
              help="Do not export AiiDA database to the CIF file.")
@click.option('--gzip', is_flag=True, default=True,
              help="Gzip large files.")
@click.option('--gzip-threshold', type=click.INT, default=None,
              help="Specify the minimum size of exported file which should be "
                   "gzipped. Default {}."
              .format(default_options['gzip_threshold']))
def deposit(node, database, deposition_type, username, password, user_email,
            title, author_name, author_email, url, code_label, computer_name,
            replace, message, reduce_symmetry, parameter_data,
            dump_aiida_database, exclude_external_contents, gzip,
            gzip_threshold):
    echo.echo("node: " + str(node))
    echo.echo("database: " + str(database))
    echo.echo("deposition_type: " + str(deposition_type))
    echo.echo("username: " + str(username))
    echo.echo("password: " + str(password))
    echo.echo("user_email: " + str(user_email))
    echo.echo("title: " + str(title))
    echo.echo("author_name: " + str(author_name))
    echo.echo("author_email: " + str(author_email))
    echo.echo("url: " + str(url))
    echo.echo("code_label: " + str(code_label))
    echo.echo("computer_name: " + str(computer_name))
    echo.echo("replace: " + str(replace))
    echo.echo("message: " + str(message))
    
    echo.echo("reduce_symmetry: " + str(reduce_symmetry))
    # echo.echo(node, database, deposition_type, username, password, user_email,
    #         title, author_name, author_email, url, code_label, computer_name, replace,
    #         message, reduce_symmetry)


    # try:
    #     if not isinstance(n, CifData):
    #         echo.echo_critical("Node {} is of class {} instead "
    #                               "of {}".format(node, type(node), CifData))
    # except AttributeError:
    #     pass
    #
    # calc = databases[database](n, **parsed_args)
    # echo.echo(calc)

