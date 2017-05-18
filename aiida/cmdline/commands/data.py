# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import sys

from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.cmdline import delayed_load_node as load_node
from aiida.cmdline.baseclass import (
    VerdiCommandRouter, VerdiCommandWithSubcommands)
from aiida.cmdline.commands.node import _Label, _Description
from aiida.common.exceptions import MultipleObjectsError



class Data(VerdiCommandRouter):
    """
    Setup and manage data specific types

    There is a list of subcommands for managing specific types of data.
    For instance, 'data upf' manages pseudopotentials in the UPF format.
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        ## Add here the classes to be supported.
        self.routed_subcommands = {
            'upf': _Upf,
            'structure': _Structure,
            'bands': _Bands,
            'cif': _Cif,
            'trajectory': _Trajectory,
            'parameter': _Parameter,
            'array': _Array,
            'label': _Label,
            'description': _Description,
        }


class Listable(object):
    """
    Provides shell completion for listable data nodes.

    .. note:: classes, inheriting Listable, MUST define value for property
        ``dataclass`` (preferably in ``__init__``), which
        has to point to correct \*Data class.
    """

    def list(self, *args):
        """
        List all instances of given data class.

        :param args: a list of command line arguments.
        """
        import argparse

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='List {} objects.'.format(self.dataclass.__name__))

        self.append_list_cmdline_arguments(parser)

        parser.add_argument('--vseparator', default="\t",
                            help="specify vertical separator for fields. "
                                 "Default '\\t'.",
                            type=str, action='store')
        parser.add_argument('--header', default=True,
                            help="print a header with column names. "
                                 "Default option.",
                            dest="header", action='store_true')
        parser.add_argument('--no-header', '-H',
                            help="do not print a header with column names.",
                            dest="header", action='store_false')

        args = list(args)
        parsed_args = parser.parse_args(args)

        entry_list = self.query(parsed_args)

        vsep = parsed_args.vseparator
        if entry_list:
            to_print = ""
            if parsed_args.header:
                to_print += vsep.join(self.get_column_names()) + "\n"
            for entry in sorted(entry_list, key=lambda x: int(x[0])):
                to_print += vsep.join(entry) + "\n"
            sys.stdout.write(to_print)

    def query(self, args):
        """
        Perform the query and return information for the list.

        :param args: a namespace with parsed command line parameters.
        :return: table (list of lists) with information, describing nodes.
            Each row describes a single hit.
        """
        if not is_dbenv_loaded():
            load_dbenv()
        from django.db.models import Q
        from aiida.backends.utils import get_automatic_user

        q_object = None
        if args.all_users is False:
            q_object = Q(user=get_automatic_user())
        else:
            q_object = Q()

        self.query_past_days(q_object, args)
        self.query_group(q_object, args)

        object_list = self.dataclass.query(q_object).distinct().order_by('ctime')

        entry_list = []
        for obj in object_list:
            entry_list.append([str(obj.pk)])
        return entry_list

    def query_past_days_qb(self, filters, args):
        """
        Subselect to filter data nodes by their age.

        :param filters: the filters to be enriched.
        :param args: a namespace with parsed command line parameters.
        """
        from aiida.utils import timezone
        import datetime
        if args.past_days is not None:
            now = timezone.now()
            n_days_ago = now - datetime.timedelta(days=args.past_days)
            filters.update({"ctime": {'>=': n_days_ago}})
        return filters

    def query_past_days(self, q_object, args):
        """
        Subselect to filter data nodes by their age.

        :param q_object: a query object
        :param args: a namespace with parsed command line parameters.
        """
        from aiida.utils import timezone
        from django.db.models import Q
        import datetime
        if args.past_days is not None:
            now = timezone.now()
            n_days_ago = now - datetime.timedelta(days=args.past_days)
            q_object.add(Q(ctime__gte=n_days_ago), Q.AND)

    def query_group_qb(self, filters, args):
        """
        Subselect to filter data nodes by their group.

        :param q_object: a query object
        :param args: a namespace with parsed command line parameters.
        """
        if args.group_name is not None:
            filters.update({"name": {"in": args.group_name}})
        if args.group_pk is not None:
            filters.update({"id": {"in": args.group_pk}})

    def query_group(self, q_object, args):
        """
        Subselect to filter data nodes by their group.

        :param q_object: a query object
        :param args: a namespace with parsed command line parameters.
        """
        from django.db.models import Q
        if args.group_name is not None:
            q_object.add(Q(dbgroups__name__in=args.group_name), Q.AND)
        if args.group_pk is not None:
            q_object.add(Q(dbgroups__pk__in=args.group_pk), Q.AND)

    def append_list_cmdline_arguments(self, parser):
        """
        Append additional command line parameters, that are later parsed and
        used in the query construction.

        :param parser: instance of argparse.ArgumentParser
        """
        parser.add_argument('-p', '--past-days', metavar='N',
                            help="add a filter to show only objects created in the past N days",
                            type=int, action='store')
        parser.add_argument('-g', '--group-name', metavar='N', nargs="+", default=None,
                            help="add a filter to show only objects belonging to groups",
                            type=str, action='store')
        parser.add_argument('-G', '--group-pk', metavar='N', nargs="+", default=None,
                            help="add a filter to show only objects belonging to groups",
                            type=int, action='store')
        parser.add_argument('-A', '--all-users', action='store_true', default=False,
                            help="show groups for all users, rather than only for the"
                                 "current user")

    def get_column_names(self):
        """
        Return the list with column names.

        .. note:: neither the number nor correspondence of column names and
            actual columns in the output from the :py:meth:`query` are checked.
        """
        return ["ID"]


class Visualizable(object):
    """
    Provides shell completion for visualizable data nodes.

    .. note:: classes, inheriting Visualizable, MUST NOT contain
        attributes, starting with ``_show_``, which are not plugins for
        visualization.

    In order to specify a default visualization format, one has to override
    ``_default_show_format`` property (preferably in
    ``__init__``), setting it to the name of default visualization tool.
    """
    show_prefix = '_show_'
    show_parameters_postfix = '_parameters'

    def get_show_plugins(self):
        """
        Get the list of all implemented plugins for visualizing the structure.
        """
        method_names = dir(self)  # get list of class methods names
        valid_formats = [i[len(self.show_prefix):] for i in method_names
                         if i.startswith(self.show_prefix) and \
                         not i.endswith(self.show_parameters_postfix)]  # filter

        return {k: getattr(self, self.show_prefix + k) for k in valid_formats}

    def show(self, *args):
        """
        Show the data node with a visualization program.
        """
        # DEVELOPER NOTE: to add a new plugin, just add a _show_xxx() method.
        import argparse, os

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Visualize data object.')
        parser.add_argument('data_id', type=int, default=None, nargs="+",
                            help="ID of the data object to be visualized.")

        default_format = None
        try:
            default_format = self._default_show_format
        except AttributeError:
            if len(self.get_show_plugins().keys()) == 1:
                default_format = self.get_show_plugins().keys()[0]
            else:
                default_format = None

        parser.add_argument('--format', '-f', type=str, default=default_format,
                            help="Type of the visualization format/tool.",
                            choices=sorted(self.get_show_plugins().keys()))

        # Augmenting the command line parameters with ones, that are used by
        # individual plugins
        for cmd in dir(self):
            if not cmd.startswith(self.show_prefix) or \
                    not cmd.endswith(self.show_parameters_postfix):
                continue
            getattr(self, cmd)(parser)

        args = list(args)
        parsed_args = vars(parser.parse_args(args))

        data_id = parsed_args.pop('data_id')
        format = parsed_args.pop('format')

        # Removing the keys, whose values are None
        for key in parsed_args.keys():
            if parsed_args[key] is None:
                parsed_args.pop(key)

        if format is None:
            print >> sys.stderr, (
                "Default format is not defined, please specify.\n"
                  "Valid formats are:")
            for i in self.get_show_plugins().keys():
                print >> sys.stderr, "  {}".format(i)
            sys.exit(1)

        # I can give in input the whole path to executable
        code_name = os.path.split(format)[-1]

        try:
            func = self.get_show_plugins()[code_name]
        except KeyError:
            print >> sys.stderr, "Not implemented; implemented plugins are:"
            print >> sys.stderr, "{}.".format(
                ",".join(self.get_show_plugins()))
            sys.exit(1)

        if not is_dbenv_loaded():
            load_dbenv()

        n_list = [load_node(id) for id in data_id]

        for n in n_list:
            try:
                if not isinstance(n, self.dataclass):
                    print >> sys.stderr, ("Node {} is of class {} instead "
                          "of {}".format(n, type(n), self.dataclass))
                    sys.exit(1)
            except AttributeError:
                pass

        try:
            func(format, n_list, **parsed_args)
        except MultipleObjectsError:
            print >> sys.stderr, (
                "Visualization of multiple objects is not implemented "
                "for '{}'".format(format))
            sys.exit(1)


class Exportable(object):
    """
    Provides shell completion for exportable data nodes.

    .. note:: classes, inheriting Exportable, MUST NOT contain attributes,
        starting with ``_export_``, which are not plugins for exporting.
    """
    export_prefix = '_export_'
    export_parameters_postfix = '_parameters'

    def append_export_cmdline_arguments(self, parser):
        """
        Function (to be overloaded in a subclass) to add custom export command
        line arguments.

        :param parser: a ArgParse parser object
        :return: change the parser in place
        """
        pass

    def get_export_plugins(self):
        """
        Get the list of all implemented exporters for data class.
        """
        method_names = dir(self)  # get list of class methods names
        valid_formats = [i[len(self.export_prefix):] for i in method_names
                         if i.startswith(self.export_prefix) and \
                         not i.endswith(self.export_parameters_postfix)]  # filter

        return {k: getattr(self, self.export_prefix + k) for k in valid_formats}

    def export(self, *args):
        """
        Export the data node to a given format.
        """
        # DEVELOPER NOTE: to add a new plugin, just add a _export_xxx() method.
        import argparse

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Export data object.')
        parser.add_argument('-o','--output', type=str, default='',
                            help="If present, store the output directly on a file "
                                 "with the given name. It is essential to use this option "
                                 "if more than one file needs to be created.")
        parser.add_argument('-y', '--overwrite', action='store_true',
                            help="If passed, overwrite files without checking.")
        parser.add_argument('data_id', type=int, default=None,
                            help="ID of the data object to be visualized.")

        self.append_export_cmdline_arguments(parser)

        default_format = None
        try:
            default_format = self._default_export_format
        except AttributeError:
            if len(self.get_export_plugins().keys()) == 1:
                default_format = self.get_export_plugins().keys()[0]
            else:
                default_format = None

        parser.add_argument('--format', '-f', type=str, default=default_format,
                            help="Type of the exported file.",
                            choices=sorted(self.get_export_plugins().keys()))

        # Augmenting the command line parameters with ones, that are used by
        # individual plugins
        for cmd in dir(self):
            if not cmd.startswith(self.export_prefix) or \
                    not cmd.endswith(self.export_parameters_postfix):
                continue
            getattr(self, cmd)(parser)

        args = list(args)
        parsed_args = vars(parser.parse_args(args))

        format = parsed_args.pop('format')
        data_id = parsed_args.pop('data_id')

        # Removing the keys, whose values are None
        for key in parsed_args.keys():
            if parsed_args[key] is None:
                parsed_args.pop(key)

        if format is None:
            print >> sys.stderr, (
                "Default format is not defined, please specify.\n"
                  "Valid formats are:")
            for i in sorted(self.get_export_plugins().keys()):
                print >> sys.stderr, "  {}".format(i)
            sys.exit(1)

        output_fname = parsed_args.pop('output')
        if not output_fname:
            output_fname = ""

        overwrite = parsed_args.pop('overwrite')

        #if parsed_args:
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

        func(n, output_fname=output_fname, overwrite=overwrite, **parsed_args)

    def print_or_store(self, node, output_fname, fileformat, other_args={}, overwrite=False):
        """
        Depending on the parameters, either print the (single) output file on screen, or
        stores the file(s) on disk.

        :param node: the Data node to print or store on disk
        :param output_fname: The filename to store the main file. If empty or None, print
             instead
        :param fileformat: a string to pass to the _exportstring method
        :param other_args: a dictionary with additional kwargs to pass to _exportstring
        :param overwrite: if False, stops if any file already exists (when output_fname
             is not empty

        :note: this function calls directly sys.exit(1) when an error occurs (or e.g. if
            check_overwrite is True and a file already exists).
        """
        try:
            if output_fname:
                try:
                    node.export(
                        output_fname, fileformat=fileformat, overwrite=overwrite, **other_args)
                except OSError as e:
                    print >> sys.stderr, "verdi: ERROR while exporting file:"
                    print >> sys.stderr, e.message
                    sys.exit(1)
            else:
                filetext, extra_files = node._exportstring(
                    fileformat, main_file_name=output_fname, **other_args)
                if extra_files:
                    print >> sys.stderr, "This format requires to write more than one file."
                    print >> sys.stderr, "You need to pass the -o option to specify a file name."
                    sys.exit(1)
                else:
                    print filetext
        except TypeError as e:
            # This typically occurs for parameters that are passed down to the
            # methods in, e.g., BandsData, but they are not accepted
            print >> sys.stderr, "verdi: ERROR, probably a parameter is not supported by the specific format."
            print >> sys.stderr, "Error message: {}".format(e.message)
            raise

            sys.exit(1)


class Importable(object):
    """
    Provides shell completion for importable data nodes.

    .. note:: classes, inheriting Importable, MUST NOT contain attributes,
        starting with ``_import_``, which are not plugins for importing.
    """
    import_prefix = '_import_'
    import_parameters_postfix = '_parameters'

    def get_import_plugins(self):
        """
        Get the list of all implemented importers for data class.
        """
        method_names = dir(self)  # get list of class methods names
        valid_formats = [i[len(self.import_prefix):] for i in method_names
                         if i.startswith(self.import_prefix) and \
                         not i.endswith(self.import_parameters_postfix)]  # filter

        return {k: getattr(self, self.import_prefix + k) for k in valid_formats}

    def importfile(self, *args):
        import argparse, sys

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Import data object.')
        parser.add_argument('--file', type=str, default=None,
                            help="Path of the imported file. Reads from "
                                 "standard input if not specified.")

        default_format = None
        try:
            default_format = self._default_import_format
        except AttributeError:
            if len(self.get_import_plugins().keys()) == 1:
                default_format = self.get_import_plugins().keys()[0]
            else:
                default_format = None

        parser.add_argument('--format', '-f', type=str, default=default_format,
                            help="Type of the imported file.",
                            choices=sorted(self.get_import_plugins().keys()))

        # Augmenting the command line parameters with ones, that are used by
        # individual plugins
        for cmd in dir(self):
            if not cmd.startswith(self.import_prefix) or \
                    not cmd.endswith(self.import_parameters_postfix):
                continue
            getattr(self, cmd)(parser)

        args = list(args)
        parsed_args = vars(parser.parse_args(args))

        format = parsed_args.pop('format')
        filename = parsed_args.pop('file')

        if format is None:
            print >> sys.stderr, (
                "Default format is not defined, please specify.\n"
                  "Valid formats are:")
            for i in self.get_import_plugins().keys():
                print >> sys.stderr, "  {}".format(i)
            sys.exit(1)

        if not filename:
            filename = "/dev/stdin"

        try:
            func = self.get_import_plugins()[format]
        except KeyError:
            print >> sys.stderr, "Not implemented; implemented plugins are:"
            print >> sys.stderr, "{}.".format(
                ",".join(self.get_import_plugins()))
            sys.exit(1)

        if not is_dbenv_loaded():
            load_dbenv()

        func(filename, **parsed_args)


class Depositable(object):
    """
    Provides shell completion for depositable data nodes.

    .. note:: classes, inheriting Depositable, MUST NOT contain
        attributes, starting with ``_deposit_``, which are not plugins for
        depositing.
    """
    deposit_prefix = '_deposit_'
    deposit_parameters_postfix = '_parameters'

    def get_deposit_plugins(self):
        """
        Get the list of all implemented deposition methods for data class.
        """
        method_names = dir(self) # get list of class methods names
        valid_formats = [ i[len(self.deposit_prefix):] for i in method_names
                         if i.startswith(self.deposit_prefix) and \
                            not i.endswith(self.deposit_parameters_postfix)] # filter

        return {k: getattr(self,self.deposit_prefix + k) for k in valid_formats}

    def deposit(self, *args):
        """
        Deposit the data node to a given database.

        :param args: a namespace with parsed command line parameters.
        """
        # DEVELOPER NOTE: to add a new plugin, just add a _deposit_xxx() method.
        import argparse
        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Deposit data object.')
        parser.add_argument('data_id', type=int, default=None,
                            help="ID of the data object to be deposited.")

        default_database = None
        try:
            default_database = self._default_deposition_database
        except AttributeError:
            if len(self.get_deposit_plugins().keys()) == 1:
                default_database = self.get_deposit_plugins().keys()[0]
            else:
                default_database = None

        parser.add_argument('--database', '-d', type=str, default=default_database,
                            help="Label of the database for deposition.",
                            choices=self.get_deposit_plugins().keys())

        # Augmenting the command line parameters with ones, that are used by
        # individual plugins
        for cmd in dir(self):
            if not cmd.startswith(self.deposit_prefix) or \
               not cmd.endswith(self.deposit_parameters_postfix):
                continue
            getattr(self,cmd)(parser)

        args = list(args)
        parsed_args = vars(parser.parse_args(args))

        database = parsed_args.pop('database')
        data_id = parsed_args.pop('data_id')

        # Removing the keys, whose values are None
        for key in parsed_args.keys():
            if parsed_args[key] is None:
                parsed_args.pop(key)

        if database is None:
            print >> sys.stderr, (
                "Default database is not defined, please specify.\n"
                  "Valid databases are:")
            for i in self.get_deposit_plugins().keys():
                print >> sys.stderr, "  {}".format(i)
            sys.exit(1)

        try:
            func = self.get_deposit_plugins()[database]
        except KeyError:
            print >> sys.stderr, "Not implemented; implemented plugins are:"
            print >> sys.stderr, "{}.".format(
                ",".join(self.get_deposit_plugins()))
            sys.exit(1)

        if not is_dbenv_loaded():
            load_dbenv()

        n = load_node(data_id)

        try:
            if not isinstance(n,self.dataclass):
                print >> sys.stderr, ("Node {} is of class {} instead "
                      "of {}".format(n,type(n),self.dataclass))
                sys.exit(1)
        except AttributeError:
            pass

        calc = func(n,**parsed_args)
        print calc


# Note: this class should not be exposed directly in the main module,
# otherwise it becomes a command of 'verdi'. Instead, we want it to be a
# subcommand of verdi data.
class _Upf(VerdiCommandWithSubcommands, Importable):
    """
    Setup and manage upf to be used

    This command allows to list and configure upf.
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        if not is_dbenv_loaded():
            load_dbenv()
        from aiida.orm.data.upf import UpfData

        self.dataclass = UpfData
        self.valid_subcommands = {
            'uploadfamily': (self.uploadfamily, self.complete_auto),
            'listfamilies': (self.listfamilies, self.complete_none),
            'import': (self.importfile, self.complete_none),
            'exportfamily': (self.exportfamily, self.complete_auto)
        }

    def uploadfamily(self, *args):
        """
        Upload a new pseudopotential family.

        Returns the numbers of files found and the number of nodes uploaded.

        Call without parameters to get some help.
        """
        import os.path

        if not len(args) == 3 and not len(args) == 4:
            print >> sys.stderr, ("After 'upf uploadfamily' there should be three "
                                  "arguments:")
            print >> sys.stderr, ("folder, group_name, group_description "
                                  "[OPTIONAL: --stop-if-existing]\n")
            sys.exit(1)

        folder = os.path.abspath(args[0])
        group_name = args[1]
        group_description = args[2]
        stop_if_existing = False

        if len(args) == 4:
            if args[3] == "--stop-if-existing":
                stop_if_existing = True
            else:
                print >> sys.stderr, 'Unknown directive: ' + args[3]
                sys.exit(1)

        if (not os.path.isdir(folder)):
            print >> sys.stderr, 'Cannot find directory: ' + folder
            sys.exit(1)

        import aiida.orm.data.upf as upf

        files_found, files_uploaded = upf.upload_upf_family(folder, group_name,
                                                            group_description, stop_if_existing)

        print "UPF files found: {}. New files uploaded: {}".format(files_found, files_uploaded)

    def listfamilies(self, *args):
        """
        Print on screen the list of upf families installed
        """
        # note that the following command requires that the upfdata has a
        # key called element. As such, it is not well separated.
        import argparse

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='List AiiDA upf families.')
        parser.add_argument('-e', '--element', nargs='+', type=str, default=None,
                            help="Filter the families only to those containing "
                                 "a pseudo for each of the specified elements")
        parser.add_argument('-d', '--with-description',
                            dest='with_description', action='store_true',
                            help="Show also the description for the UPF family")
        parser.set_defaults(with_description=False)

        args = list(args)
        parsed_args = parser.parse_args(args)

        from aiida.orm import DataFactory
        from aiida.orm.data.upf import UPFGROUP_TYPE

        UpfData = DataFactory('upf')
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.group import Group
        qb = QueryBuilder()
        qb.append(UpfData, tag='upfdata')
        if parsed_args.element is not None:
            qb.add_filter(UpfData, {'attributes.element': {'in': parsed_args.element}})
        qb.append(
            Group,
            group_of='upfdata', tag='group',
            project=["name", "description"],
            filters={"type": {'==': UPFGROUP_TYPE}}
        )

        qb.distinct()
        if qb.count() > 0:
            for res in qb.dict():
                group_name = res.get("group").get("name")
                group_desc = res.get("group").get("description")
                qb = QueryBuilder()
                qb.append(
                    Group,
                    tag='thisgroup',
                    filters={"name":  {'like': group_name}}
                )
                qb.append(
                    UpfData,
                    project=["id"],
                    member_of='thisgroup'
                )

                if parsed_args.with_description:
                    description_string = ": {}".format(group_desc)
                else:
                    description_string = ""

                print "* {} [{} pseudos]{}".format(group_name, qb.count(),
                                                   description_string)

        else:
            print "No valid UPF pseudopotential family found."

    def exportfamily(self, *args):
        """
        Export a pseudopotential family into a folder.
        Call without parameters to get some help.
        """
        import os
        from aiida.common.exceptions import NotExistent
        from aiida.orm import DataFactory

        if not len(args) == 2:
            print >> sys.stderr, ("After 'upf export' there should be two "
                                  "arguments:")
            print >> sys.stderr, ("folder, upf_family_name\n")
            sys.exit(1)

        folder = os.path.abspath(args[0])
        group_name = args[1]

        UpfData = DataFactory('upf')
        try:
            group = UpfData.get_upf_group(group_name)
        except NotExistent:
            print >> sys.stderr, ("upf family {} not found".format(group_name))

        for u in group.nodes:
            dest_path = os.path.join(folder,u.filename)
            if not os.path.isfile(dest_path):
                with open(dest_path,'w') as dest:
                    with u._get_folder_pathsubfolder.open(u.filename) as source:
                        dest.write(source.read())
            else:
                print >> sys.stdout, ("File {} is already present in the "
                                      "destination folder".format(u.filename))

    def _import_upf(self, filename, **kwargs):
        """
        Importer from UPF.
        """
        try:
            node, _ = self.dataclass.get_or_create(filename)
            print node
        except ValueError as e:
            print e


class _Bands(VerdiCommandWithSubcommands, Listable, Visualizable, Exportable):
    """
    Manipulation on the bands
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        if not is_dbenv_loaded():
            load_dbenv()
        from aiida.orm.data.array.bands import BandsData

        self.dataclass = BandsData
        self.valid_subcommands = {
            'show': (self.show, self.complete_none),
            'list': (self.list, self.complete_none),
            'export': (self.export, self.complete_none),
        }

    def query(self, args):
        """
        Perform the query and return information for the list.

        :param args: a namespace with parsed command line parameters.
        :return: table (list of lists) with information, describing nodes.
            Each row describes a single hit.
        """
        if not is_dbenv_loaded():
            load_dbenv()

        from aiida.orm.querybuilder import QueryBuilder
        from aiida.backends.utils import get_automatic_user
        from aiida.orm.implementation import User
        from aiida.orm.implementation import Group
        from aiida.orm.data.structure import (get_formula, get_symbols_string)
        from aiida.orm.data.array.bands import BandsData
        from aiida.orm.data.structure import StructureData

        qb = QueryBuilder()
        if args.all_users is False:
            au = get_automatic_user()
            user = User(dbuser=au)
            qb.append(User, tag="creator", filters={"email": user.email})
        else:
            qb.append(User, tag="creator")

        bdata_filters = {}
        self.query_past_days_qb(bdata_filters, args)
        qb.append(BandsData, tag="bdata", created_by="creator",
                  filters=bdata_filters,
                  project=["id", "label", "ctime"]
                  )

        group_filters = {}
        self.query_group_qb(group_filters, args)
        if group_filters:
            qb.append(Group, tag="group", filters=group_filters,
                      group_of="bdata")

        qb.append(StructureData, tag="sdata", ancestor_of="bdata",
                  # We don't care about the creator of StructureData
                  project=["id", "attributes.kinds", "attributes.sites"])

        qb.order_by({StructureData: {'ctime': 'desc'}})

        list_data = qb.distinct()

        entry_list = []
        already_visited_bdata = set()
        if list_data.count() > 0:
            for [bid, blabel, bdate, sid, akinds, asites] in list_data.all():

                # We process only one StructureData per BandsData.
                # We want to process the closest StructureData to
                # every BandsData.
                # We hope that the StructureData with the latest
                # creation time is the closest one.
                # This will be updated when the QueryBuilder supports
                # order_by by the distance of two nodes.
                if already_visited_bdata.__contains__(bid):
                    continue
                already_visited_bdata.add(bid)

                if args.element is not None:
                    all_symbols = [_["symbols"][0] for _ in akinds]
                    if not any([s in args.element for s in all_symbols]
                               ):
                        continue

                if args.element_only is not None:
                    all_symbols = [_["symbols"][0] for _ in akinds]
                    if not all(
                            [s in all_symbols for s in args.element_only]
                            ):
                        continue

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
                                          mode=args.formulamode)
                # If for some reason there is no kind with the name
                # referenced by the site
                except KeyError:
                    formula = "<<UNKNOWN>>"
                entry_list.append([str(bid), str(formula),
                                   bdate.strftime('%d %b %Y'), blabel])

        return entry_list

    def append_list_cmdline_arguments(self, parser):
        """
        Append additional command line parameters, that are later parsed and
        used in the query construction.

        :param parser: instance of argparse.ArgumentParser
        """
        parser.add_argument('-e', '--element', nargs='+', type=str, default=None,
                            help="Print all bandsdatas from structures "
                                 "containing desired elements")
        parser.add_argument('-eo', '--element-only', nargs='+', type=str, default=None,
                            help="Print all bandsdatas from structures "
                                 "containing only the selected elements")
        parser.add_argument('-f', '--formulamode', metavar='FORMULA_MODE',
                            type=str, default='hill',
                            help="Formula printing mode (hill, hill_compact,"
                                 " reduce, group, count, or count_compact)"
                                 " (if None, does not print the formula)",
                            action='store')
        parser.add_argument('-p', '--past-days', metavar='N',
                            help="Add a filter to show only bandsdatas created in the past N days",
                            type=int, action='store')
        parser.add_argument('-g', '--group-name', metavar='N', nargs="+", default=None,
                            help="add a filter to show only objects belonging to groups",
                            type=str, action='store')
        parser.add_argument('-G', '--group-pk', metavar='N', nargs="+", default=None,
                            help="add a filter to show only objects belonging to groups",
                            type=int, action='store')
        parser.add_argument('-A', '--all-users', action='store_true', default=False,
                            help="show groups for all users, rather than only for the"
                                 "current user")

    def append_export_cmdline_arguments(self, parser):
        """
        Additional command line arguments for the 'export' command

        :param parser: instance of argparse.ArgumentParser
        """
        from aiida.common.utils import Prettifier

        parser.add_argument('--prettify-format', type=str, default=None,
                            choices=Prettifier.get_prettifiers(),
                            help = 'The style of labels for the prettifier')
        parser.add_argument('--y-min-lim', type=float, default=None,
                            help = 'The minimum value for the y axis. Default: minimum of all bands')
        parser.add_argument('--y-max-lim', type=float, default=None,
                            help = 'The maximum value for the y axis. Default: maximum of all bands')


    def get_column_names(self):
        """
        Return the list with column names.

        :note: neither the number nor correspondence of column names and
            actual columns in the output from the query() are checked.
        """
        return ["ID", "formula", "ctime", "label"]

    def _export_agr(self, node, output_fname, overwrite, **kwargs):
        """
        Export a .agr file, to be visualized with the XMGrace plotting software.
        """
        self.print_or_store(node, output_fname, fileformat='agr', overwrite=overwrite,
                            other_args=kwargs)


    def _export_agr_batch(self, node, output_fname, overwrite, **kwargs):
        """
        Export a .agr batch file, to be visualized with the XMGrace plotting software.
        """
        self.print_or_store(node, output_fname, fileformat='agr_batch', overwrite=overwrite,
                            other_args=kwargs)

    def _export_gnuplot(self, node, output_fname, overwrite, **kwargs):
        """
        Export a Gnuplot file, together with the corresponding .dat file,
        to be visualized with the Gnuplot plotting software.

        Run with 'gnuplot -p filename' to see the plot (and keep the window with
        the plot open).
        """
        self.print_or_store(node, output_fname, fileformat='gnuplot', overwrite=overwrite,
                            other_args=kwargs)

    def _export_dat_multicolumn(self, node, output_fname, overwrite, **kwargs):
        """
        Export a .dat file with one line per kpoint, with multiple energy values
        on the same line separated by spaces.
        """
        self.print_or_store(node, output_fname, fileformat='dat_multicolumn', overwrite=overwrite,
                            other_args=kwargs)

    def _export_dat_blocks(self, node, output_fname, overwrite, **kwargs):
        """
        Export a .dat file with one line per datapoint (kpt, energy),
        with multiple bands separated in stanzas (i.e. having at least an empty
        newline inbetween).
        """
        self.print_or_store(node, output_fname, fileformat='dat_blocks', overwrite=overwrite,
                            other_args=kwargs)

    def _export_json(self, node, output_fname, overwrite, **kwargs):
        """
        Export a .dat file with one line per datapoint (kpt, energy),
        with multiple bands separated in stanzas (i.e. having at least an empty
        newline inbetween).
        """
        self.print_or_store(node, output_fname, fileformat='json', overwrite=overwrite,
                            other_args=kwargs)


    def _export_mpl_singlefile(self, node, output_fname, overwrite, **kwargs):
        """
        Export a .py file that would produce the plot using matplotlib
        when run with python (with data dumped within the same python file)
        """
        self.print_or_store(node, output_fname, fileformat='mpl_singlefile', overwrite=overwrite,
                            other_args=kwargs)

    def _export_mpl_withjson(self, node, output_fname, overwrite, **kwargs):
        """
        Export a .py file that would produce the plot using matplotlib
        when run with python (with data dumped in an external json filee)
        """
        self.print_or_store(node, output_fname, fileformat='mpl_withjson', overwrite=overwrite,
                            other_args=kwargs)


    def _export_mpl_png(self, node, output_fname, overwrite, **kwargs):
        """
        Export a .png file generated using matplotlib
        """
        if not output_fname:
            print >> sys.stderr, "To export to PNG please always specify the filename with the -o option"
            sys.exit(1)
        self.print_or_store(node, output_fname, fileformat='mpl_png', overwrite=overwrite,
                            other_args=kwargs)

    def _export_mpl_pdf(self, node, output_fname, overwrite, **kwargs):
        """
        Export a .pdf file generated using matplotlib
        """
        if not output_fname:
            print >> sys.stderr, "To export to PDF please always specify the filename with the -o option"
            sys.exit(1)
        self.print_or_store(node, output_fname, fileformat='mpl_pdf', overwrite=overwrite,
                            other_args=kwargs)

    def _show_xmgrace(self, exec_name, list_bands):
        """
        Plugin for show the bands with the XMGrace plotting software.
        """
        import tempfile, subprocess, numpy
        from aiida.orm.data.array.bands import max_num_agr_colors

        list_files = []
        current_band_number = 0
        for iband, bands in enumerate(list_bands):
            # extract number of bands
            nbnds = bands.get_bands().shape[1]
            text, _ = bands._exportstring('agr', setnumber_offset=current_band_number,
                                       color_number=numpy.mod(iband + 1, max_num_agr_colors))
            # write a tempfile
            f = tempfile.NamedTemporaryFile(suffix='.agr')
            f.write(text)
            f.flush()
            list_files.append(f)
            # update the number of bands already plotted
            current_band_number += nbnds

        try:
            subprocess.check_output([exec_name] + [f.name for f in list_files])
            _ = [f.close() for f in list_files]
        except subprocess.CalledProcessError:
            # The program died: just print a message
            print "Note: the call to {} ended with an error.".format(
                exec_name)
            _ = [f.close() for f in list_files]
        except OSError as e:
            _ = [f.close() for f in list_files]
            if e.errno == 2:
                print ("No executable '{}' found. Add to the path, "
                       "or try with an absolute path.".format(
                    exec_name))
                sys.exit(1)
            else:
                raise


class _Structure(VerdiCommandWithSubcommands,
                 Listable,
                 Visualizable,
                 Exportable,
                 Importable,
                 Depositable):
    """
    Visualize AiIDA structures
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        if not is_dbenv_loaded():
            load_dbenv()
        from aiida.orm.data.structure import StructureData

        self.dataclass = StructureData
        self.valid_subcommands = {
            'show': (self.show, self.complete_none),
            'list': (self.list, self.complete_none),
            'export': (self.export, self.complete_none),
            'deposit': (self.deposit, self.complete_none),
            'import': (self.importfile, self.complete_none),
        }

    def query(self, args):
        """
        Perform the query
        """
        if not is_dbenv_loaded():
            load_dbenv()

        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.data.structure import StructureData
        from aiida.backends.utils import get_automatic_user
        from aiida.orm.implementation import User
        from aiida.orm.implementation import Group
        from aiida.orm.data.structure import (get_formula, get_symbols_string)

        qb = QueryBuilder()
        if args.all_users is False:
            au = get_automatic_user()
            user = User(dbuser=au)
            qb.append(User, tag="creator", filters={"email": user.email})
        else:
            qb.append(User, tag="creator")

        st_data_filters = {}
        self.query_past_days_qb(st_data_filters, args)
        qb.append(StructureData, tag="struc", created_by="creator",
                  filters=st_data_filters,
                  project=["id", "label", "attributes.kinds",
                           "attributes.sites"])

        group_filters = {}
        self.query_group_qb(group_filters, args)
        if group_filters:
            qb.append(Group, tag="group", filters=group_filters,
                      group_of="struc")

        struc_list_data = qb.distinct()

        entry_list = []
        if struc_list_data.count() > 0:
            for [id, label, akinds, asites] in struc_list_data.all():

                # If symbols are defined there is a filtering of the structures
                # based on the element
                # When QueryBuilder will support this (attribute)s filtering,
                # it will be pushed in the query.
                if args.element is not None:
                    all_symbols = [_["symbols"][0] for _ in akinds]
                    if not any([s in args.element for s in all_symbols]
                               ):
                        continue

                    if args.elementonly:
                        print "Not implemented elementonly search"
                        sys.exit(1)

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
                                          mode=args.formulamode)
                # If for some reason there is no kind with the name
                # referenced by the site
                except KeyError:
                    formula = "<<UNKNOWN>>"
                entry_list.append([str(id), str(formula), label])

        return entry_list

    def append_list_cmdline_arguments(self, parser):
        parser.add_argument('-e', '--element', nargs='+', type=str, default=None,
                            help="Print all structures containing desired elements")
        parser.add_argument('-eo', '--elementonly', action='store_true',
                            help="If set, structures do not contain different "
                                 "elements (to be used with -e option)")
        parser.add_argument('-f', '--formulamode', metavar='FORMULA_MODE',
                            type=str, default='hill',
                            help="Formula printing mode (hill, hill_compact,"
                                 " reduce, group, count, or count_compact)"
                                 " (if None, does not print the formula)",
                            action='store')
        parser.add_argument('-p', '--past-days', metavar='N',
                            help="Add a filter to show only structures created in the past N days",
                            type=int, action='store')
        parser.add_argument('-g', '--group-name', metavar='N', nargs="+", default=None,
                            help="add a filter to show only objects belonging to groups",
                            type=str, action='store')
        parser.add_argument('-G', '--group-pk', metavar='N', nargs="+", default=None,
                            help="add a filter to show only objects belonging to groups",
                            type=int, action='store')
        parser.add_argument('-A', '--all-users', action='store_true', default=False,
                            help="show groups for all users, rather than only for the"
                                 "current user")

    def get_column_names(self):
        return ["ID", "formula", "label"]

    def _show_xcrysden(self, exec_name, structure_list):
        """
        Plugin for xcrysden
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

    def _show_ase(self,exec_name,structure_list):
        """
        Plugin to show the structure with the ASE visualizer
        """
        try:
            from ase.visualize import view
            for structure in structure_list:
                view(structure.get_ase())
        except ImportError:
            raise

    def _show_vmd(self, exec_name, structure_list):
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

    def _show_jmol(self, exec_name, structure_list):
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
                    print ("No executable '{}' found. Add to the path, "
                           "or try with an absolute path.".format(
                        exec_name))
                    sys.exit(1)
                else:
                    raise

    def _export_tcod(self, node, output_fname, overwrite, parameter_data=None, **kwargs):
        """
        Plugin for TCOD
        """

        parameters = None
        if parameter_data is not None:
            from aiida.orm import DataFactory
            ParameterData = DataFactory('parameter')
            parameters = load_node(parameter_data, parent_class=ParameterData)
        self.print_or_store(node, output_fname, fileformat='tcod', overwrite=overwrite,
                            other_args=kwargs)

    def _export_tcod_parameters(self, parser, **kwargs):
        """
        Command line parameters for TCOD
        """
        from aiida.tools.dbexporters.tcod import extend_with_cmdline_parameters
        extend_with_cmdline_parameters(parser,self.dataclass.__name__)

    def _export_xsf(self, node, output_fname, overwrite, **kwargs):
        """
        Exporter to XSF.
        """
        self.print_or_store(node, output_fname, fileformat='xsf', overwrite=overwrite,
                            other_args=kwargs)

    def _export_cif(self, node, output_fname, overwrite, **kwargs):
        """
        Exporter to CIF.
        """
        self.print_or_store(node, output_fname, fileformat='cif', overwrite=overwrite,
                            other_args=kwargs)

    def _export_xyz(self, node, output_fname, overwrite, **kwargs):
        """
        Exporter to XYZ.
        """
        self.print_or_store(node, output_fname, fileformat='xyz', overwrite=overwrite,
                            other_args=kwargs)

    def _import_xyz_parameters(self, parser):
        """
        Adding some functionality to the parser to deal with importing files
        """
        # In order to deal with structures that do not have a cell defined:
        # We can increase the size of the cell from the minimal cell
        # The minimal cell is the cell the just accomodates the structure given,
        # defined by the minimum and maximum of position in each dimension
        parser.add_argument('--vacuum-factor', type=float, default=1.0,
                help = 'The factor by which the cell accomodating the structure should be increased, default: 1.0')
        #To that increased cell, we can also add a "safety margin"
        parser.add_argument('--vacuum-addition', type=float, default=10.0,
                help = 'The distance to add to the unit cell after vacuum-factor was applied to expand in each dimension, default: 10.0')
        parser.add_argument('--pbc', type=int, nargs = 3, default= [0,0,0],
                help = """
                Set periodic boundary conditions for each lattice direction,
                0 for no periodicity, any other integer for periodicity""")
        parser.add_argument('--view', action='store_true', default = False, help= 'View resulting structure using ASE')
        parser.add_argument('--dont-store', action='store_true', default = False, help= 'Do not store the structure')

    def _import_xyz(self, filename, **kwargs):
        """
        Imports an XYZ-file.
        """
        from os.path import abspath
        vacuum_addition = kwargs.pop('vacuum_addition')
        vacuum_factor = kwargs.pop('vacuum_factor')
        pbc = [bool(i) for i in kwargs.pop('pbc')]
        dont_store = kwargs.pop('dont_store')
        view_in_ase = kwargs.pop('view')

        print 'importing XYZ-structure from: \n  {}'.format(abspath(filename))
        filepath =  abspath(filename)
        with open(filepath) as f:
            xyz_txt = f.read()
        new_structure = self.dataclass()
        try:
            new_structure._parse_xyz(xyz_txt)
            new_structure._adjust_default_cell( vacuum_addition = vacuum_addition,
                                                vacuum_factor = vacuum_factor,
                                                pbc = pbc)

            if not dont_store:
                new_structure.store()
            if view_in_ase:
                from ase.visualize import view
                view(new_structure.get_ase())
            print  (
                    '  Succesfully imported structure {}, '
                    '(PK = {})'.format(new_structure.get_formula(), new_structure.pk)
                )

        except ValueError as e:
            print e

    def _import_pwi(self, filename, **kwargs):
        """
        Imports a structure from a quantumespresso input file.
        """
        from os.path import abspath
        from aiida.tools.codespecific.quantumespresso.qeinputparser import get_structuredata_from_qeinput
        dont_store = kwargs.pop('dont_store')
        view_in_ase = kwargs.pop('view')

        print 'importing structure from: \n  {}'.format(abspath(filename))
        filepath =  abspath(filename)

        try:
            new_structure = get_structuredata_from_qeinput(filepath=filepath)

            if not dont_store:
                new_structure.store()
            if view_in_ase:
                from ase.visualize import view
                view(new_structure.get_ase())
            print  (
                    '  Succesfully imported structure {}, '
                    '(PK = {})'.format(new_structure.get_formula(), new_structure.pk)
                )

        except ValueError as e:
            print e

    def _deposit_tcod(self, node, parameter_data=None, **kwargs):
        """
        Deposition plugin for TCOD.
        """
        from aiida.tools.dbexporters.tcod import deposit

        parameters = None
        if parameter_data is not None:
            from aiida.orm import DataFactory
            ParameterData = DataFactory('parameter')
            parameters = load_node(parameter_data, parent_class=ParameterData)
        return deposit(node,parameters=parameters,**kwargs)

    def _deposit_tcod_parameters(self,parser,**kwargs):
        """
        Command line parameters deposition plugin for TCOD.
        """
        from aiida.tools.dbexporters.tcod import (deposition_cmdline_parameters,
                                                  extend_with_cmdline_parameters)
        deposition_cmdline_parameters(parser,self.dataclass.__name__)
        extend_with_cmdline_parameters(parser,self.dataclass.__name__)


class _Cif(VerdiCommandWithSubcommands,
           Listable, Visualizable, Exportable, Importable, Depositable):
    """
    Visualize CIF structures
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        if not is_dbenv_loaded():
            load_dbenv()
        from aiida.orm.data.cif import CifData

        self.dataclass = CifData
        self.valid_subcommands = {
            'show': (self.show, self.complete_none),
            'list': (self.list, self.complete_none),
            'export': (self.export, self.complete_none),
            'import': (self.importfile, self.complete_none),
            'deposit': (self.deposit, self.complete_none),
        }

    def _show_jmol(self, exec_name, structure_list):
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
                    print ("No executable '{}' found. Add to the path, "
                           "or try with an absolute path.".format(
                        exec_name))
                    sys.exit(1)
                else:
                    raise

    def query(self, args):
        """
        Perform the query and return information for the list.

        :param args: a namespace with parsed command line parameters.
        :return: table (list of lists) with information, describing nodes.
            Each row describes a single hit.
        """
        if not is_dbenv_loaded():
            load_dbenv()
        from django.db.models import Q
        from aiida.backends.utils import get_automatic_user

        q_object = None
        if args.all_users is False:
            q_object = Q(user=get_automatic_user())
        else:
            q_object = Q()

        self.query_past_days(q_object, args)
        self.query_group(q_object, args)

        object_list = self.dataclass.query(q_object).distinct().order_by('ctime')

        entry_list = []
        for obj in object_list:
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

    def get_column_names(self):
        """
        Return the list with column names.

        :note: neither the number nor correspondence of column names and
            actual columns in the output from the query() are checked.
        """
        return ["ID", "formulae", "source_uri"]

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
            parameters = load_node(parameter_data, parent_class=ParameterData)
        self.print_or_store(node, output_fname, fileformat='tcod', overwrite=overwrite,
                            other_args=kwargs)

    def _export_tcod_parameters(self,parser,**kwargs):
        """
        Command line parameters for TCOD
        """
        from aiida.tools.dbexporters.tcod import extend_with_cmdline_parameters
        extend_with_cmdline_parameters(parser,self.dataclass.__name__)

    def _import_cif(self, filename, **kwargs):
        """
        Importer from CIF.
        """
        import os.path

        try:
            node, _ = self.dataclass.get_or_create(os.path.abspath(filename))
            print node
        except ValueError as e:
            print e

    def _deposit_tcod(self, node, parameter_data=None, **kwargs):
        """
        Deposition plugin for TCOD.
        """
        from aiida.tools.dbexporters.tcod import deposit

        parameters = None
        if parameter_data is not None:
            from aiida.orm import DataFactory
            ParameterData = DataFactory('parameter')
            parameters = load_node(parameter_data, parent_class=ParameterData)
        return deposit(node,parameters=parameters,**kwargs)

    def _deposit_tcod_parameters(self, parser, **kwargs):
        """
        Command line parameters deposition plugin for TCOD.
        """
        from aiida.tools.dbexporters.tcod import (deposition_cmdline_parameters,
                                                  extend_with_cmdline_parameters)
        deposition_cmdline_parameters(parser,self.dataclass.__name__)
        extend_with_cmdline_parameters(parser,self.dataclass.__name__)


class _Trajectory(VerdiCommandWithSubcommands,
                  Listable, Visualizable, Exportable, Depositable):
    """
    View and manipulate TrajectoryData instances.
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        if not is_dbenv_loaded():
            load_dbenv()
        from aiida.orm.data.array.trajectory import TrajectoryData

        self.dataclass = TrajectoryData
        self.valid_subcommands = {
            'show': (self.show, self.complete_none),
            'list': (self.list, self.complete_none),
            'export': (self.export, self.complete_none),
            'deposit': (self.deposit, self.complete_none),
        }

    def _show_jmol(self, exec_name, trajectory_list, **kwargs):
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
                    print ("No executable '{}' found. Add to the path, "
                           "or try with an absolute path.".format(
                        exec_name))
                    sys.exit(1)
                else:
                    raise

    def _show_jmol_parameters(self, parser):
        """
        Describe command line parameters.
        """
        parser.add_argument('--step',
                            help="ID of the trajectory step. If none is "
                                 "supplied, all steps are exported.",
                            type=int, action='store')

    def _show_xcrysden(self, exec_name, trajectory_list, **kwargs):
        """
        Plugin for xcrysden
        """
        import tempfile, subprocess

        if len(trajectory_list) > 1:
            raise MultipleObjectsError("Visualization of multiple trajectories "
                                       "is not implemented")
        trajectory = trajectory_list[0]

        with tempfile.NamedTemporaryFile(suffix='.xsf') as f:
            f.write(trajectory._exportstring('xsf', **kwargs)[0])
            f.flush()

            try:
                subprocess.check_output([exec_name, '--xsf',f.name])
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

    def _show_mpl_pos_parameters(self, parser):
        """
        Describe command line parameters for _show_pos
        """
        parser.add_argument('-s', '--stepsize',
                type=int,
                help=''
                    'The stepsize for the trajectory, set it higher to reduce '
                    'number of points',
                default=1
            )
        parser.add_argument('--mintime',
                type=int, default=None,
                help='The time to plot from'
            )
        parser.add_argument('--maxtime',
                type=int, default=None,
                help='The time to plot to'
            )
        parser.add_argument('-e', '--elements',
                type=str, nargs='+',
                help='Show only atoms of that species'
            )
        parser.add_argument('-i', '--indices',
                type=int, nargs='+',
                help='Show only these indices'
            )
        parser.add_argument('--dont-block',
                action='store_true',
                help="Don't block interpreter when showing plot"
            )

    def _show_mpl_heatmap_parameters(self, parser):
        """
        Describe command line parameters for _show_mpl_heatmap
        """
        parser.add_argument('-c', '--contours',
                type=float, nargs='+',
                help='Isovalues to plot'
            )
        parser.add_argument( '--sampling-stepsize',
                type=int,
                help='Sample positions in plot every sampling_stepsize timestep'
            )
    def _show_mpl_pos(self, exec_name, trajectory_list, **kwargs):
        """
        Produces a matplotlib plot of the trajectory
        """
        for t in trajectory_list:
            t.show_mpl_pos(**kwargs)

    def _show_mpl_heatmap(self, exec_name, trajectory_list, **kwargs):
        """
        Produces a matplotlib plot of the trajectory
        """
        for t in trajectory_list:
            t.show_mpl_heatmap(**kwargs)


    def _export_xsf(self, node, output_fname, overwrite, **kwargs):
        """
        Exporter to XSF.
        """
        self.print_or_store(node, output_fname, fileformat='xsf', overwrite=overwrite,
                            other_args=kwargs)

    def _export_tcod(self, node, output_fname, overwrite, parameter_data=None, **kwargs):
        """
        Plugin for TCOD
        """

        parameters = None
        if parameter_data is not None:
            from aiida.orm import DataFactory
            ParameterData = DataFactory('parameter')
            parameters = load_node(parameter_data, parent_class=ParameterData)
        self.print_or_store(node, output_fname, fileformat='tcod', overwrite=overwrite,
                            other_args=kwargs)

    def _export_tcod_parameters(self, parser, **kwargs):
        """
        Command line parameters for TCOD
        """
        from aiida.tools.dbexporters.tcod import extend_with_cmdline_parameters
        extend_with_cmdline_parameters(parser,self.dataclass.__name__)

    def _export_cif(self, node, output_fname, overwrite, **kwargs):
        """
        Exporter to CIF.
        """
        self.print_or_store(node, output_fname, fileformat='cif', overwrite=overwrite,
                            other_args=kwargs)


    def _export_cif_parameters(self, parser, **kwargs):
        """
        Describe command line parameters.
        """
        parser.add_argument('--step', dest='trajectory_index',
                            help="ID of the trajectory step. If none is "
                                 "supplied, all steps are exported.",
                            type=int, action='store')

    def _deposit_tcod(self, node, parameter_data=None, **kwargs):
        """
        Deposition plugin for TCOD.
        """
        from aiida.tools.dbexporters.tcod import deposit

        parameters = None
        if parameter_data is not None:
            from aiida.orm import DataFactory
            ParameterData = DataFactory('parameter')
            parameters = load_node(parameter_data, parent_class=ParameterData)
        return deposit(node,parameters=parameters,**kwargs)

    def _deposit_tcod_parameters(self, parser, **kwargs):
        """
        Command line parameters deposition plugin for TCOD.
        """
        from aiida.tools.dbexporters.tcod import (deposition_cmdline_parameters,
                                                  extend_with_cmdline_parameters)
        deposition_cmdline_parameters(parser,self.dataclass.__name__)
        extend_with_cmdline_parameters(parser,self.dataclass.__name__)
        self._export_cif_parameters(parser)


class _Parameter(VerdiCommandWithSubcommands, Visualizable):
    """
    View and manipulate Parameter data classes.
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        if not is_dbenv_loaded():
            load_dbenv()
        from aiida.orm.data.parameter import ParameterData

        self.dataclass = ParameterData
        self._default_show_format = 'json_date'
        self.valid_subcommands = {
            'show': (self.show, self.complete_none),
        }

    def _show_json_date(self, exec_name, node_list):
        """
        Show contents of ParameterData nodes.
        """
        from aiida.cmdline import print_dictionary

        for node in node_list:
            the_dict = node.get_dict()
            print_dictionary(the_dict, 'json+date')


class _Array(VerdiCommandWithSubcommands, Visualizable):
    """
    View and manipulate Array data classes.
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        if not is_dbenv_loaded():
            load_dbenv()

        from aiida.orm.data.array import ArrayData

        self.dataclass = ArrayData
        self._default_show_format = 'json_date'
        self.valid_subcommands = {
            'show': (self.show, self.complete_none),
        }

    def _show_json_date(self, exec_name, node_list):
        """
        Show contents of ArrayData nodes.
        """
        from aiida.cmdline import print_dictionary

        for node in node_list:
            the_dict = {}
            for arrayname in node.arraynames():
                the_dict[arrayname] = node.get_array(arrayname).tolist()
            print_dictionary(the_dict, 'json+date')
