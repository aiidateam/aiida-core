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

@cif.command('export')
@click.option('-y', '--format',
              type=click.Choice(['cif', 'tcod', 'tcod_parameters']),
              default='json',
              help="Type of the exported file.")
@click.option('-o', '--output', type=click.STRING,
              default=None,
              help="If present, store the output directly on a file "
              "with the given name. It is essential to use this option "
              "if more than one file needs to be created.")
@options.FORCE(help="If passed, overwrite files without checking.")
@click.option('--prettify-format', default=None,
                type=click.Choice(Prettifier.get_prettifiers()),
                help='The style of labels for the prettifier')
@arguments.NODE()
def export(format, output, force, prettify_format, node):
    """
    Export the data node to a given format.
    """
    if format is None:
        print >> sys.stderr, (
            "Default format is not defined, please specify.\n"
            "Valid formats are:")
        for i in sorted(self.get_export_plugins().keys()):
            print >> sys.stderr, "  {}".format(i)
        sys.exit(1)

    output_fname = parsed_args.pop('output')
    if not output:
        output = ""

    overwrite = parsed_args.pop('overwrite')

    # if parsed_args:
    #    raise InternalError(
    #        "Some command line parameters were not properly parsed: {}".format(
    #            parsed_args.keys()
    #        ))

    try:
        func = self.get_export_plugins()[format]
    except KeyError:
        print >> sys.stderr, "Not implemented; implemented plugins are:"
        print >> sys.stderr, "{}.".format(
            ",".join(self.get_export_plugins()))
        sys.exit(1)

    if not is_dbenv_loaded():
        load_dbenv()

    n = load_node(data_id)

    try:
        if not isinstance(n, self.dataclass):
            print >> sys.stderr, ("Node {} is of class {} instead "
                                  "of {}".format(n, type(n), self.dataclass))
            sys.exit(1)
    except AttributeError:
        pass

    func(n, output_fname=output_fname, overwrite=force, **parsed_args)

def _export_cif(self, node, output_fname, overwrite, **kwargs):
    """
    Exporter to CIF.
    """
    self.print_or_store(node, output_fname, fileformat='cif', overwrite=overwrite,
                        other_args=kwargs)

def _export_tcod(self, node, output_fname, overwrite, parameter_data=None, **kwargs):
    """
    Plugin for TCOD
    """
    parameters = None
    if parameter_data is not None:
        from aiida.orm import DataFactory
        ParameterData = DataFactory('parameter')
        parameters = load_node(parameter_data, sub_class=ParameterData)
    self.print_or_store(node, output_fname, fileformat='tcod', overwrite=overwrite,
                        other_args=kwargs)

def _export_tcod_parameters(self, parser, **kwargs):
    """
    Command line parameters for TCOD
    """
    from aiida.tools.dbexporters.tcod import extend_with_cmdline_parameters
    extend_with_cmdline_parameters(parser, self.dataclass.__name__)