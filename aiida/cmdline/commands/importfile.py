# -*- coding: utf-8 -*-
import sys

from aiida.backends.utils import load_dbenv
from aiida.cmdline.baseclass import VerdiCommand

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0.1"
__authors__ = "The AiiDA team."

IMPORTGROUP_TYPE = 'aiida.import'


def deserialize_attributes(attributes_data, conversion_data):
    import datetime
    import pytz

    if isinstance(attributes_data, dict):
        ret_data = {}
        for k, v in attributes_data.iteritems():
            ret_data[k] = deserialize_attributes(v, conversion_data[k])
    elif isinstance(attributes_data, (list, tuple)):
        ret_data = []
        for value, conversion in zip(attributes_data, conversion_data):
            ret_data.append(deserialize_attributes(value, conversion))
    else:
        if conversion_data is None:
            ret_data = attributes_data
        else:
            if conversion_data == 'date':
                ret_data = datetime.datetime.strptime(
                    attributes_data, '%Y-%m-%dT%H:%M:%S.%f').replace(
                    tzinfo=pytz.utc)
            else:
                raise ValueError("Unknown convert_type '{}'".format(
                    conversion_data))

    return ret_data


def deserialize_field(k, v, fields_info, import_unique_ids_mappings,
                      foreign_ids_reverse_mappings):
    try:
        field_info = fields_info[k]
    except KeyError:
        raise ValueError("Unknown field '{}'".format(k))

    if k == 'id' or k == 'pk':
        raise ValueError("ID or PK explicitly passed!")

    requires = field_info.get('requires', None)
    if requires is None:
        # Actual data, no foreign key
        converter = field_info.get('convert_type', None)
        return (k, deserialize_attributes(v, converter))
    else:
        # Foreign field
        # Correctly manage nullable fields
        if v is not None:
            unique_id = import_unique_ids_mappings[requires][v]
            # map to the PK/ID associated to the given entry, in the arrival DB,
            # rather than in the export DB

            # I store it in the FIELDNAME_id variable, that directly stores the
            # PK in the remote table, rather than requiring to create Model
            # instances for the foreing relations
            return ("{}_id".format(k),
                    foreign_ids_reverse_mappings[requires][unique_id])
        else:
            return ("{}_id".format(k), None)

def extract_zip(infile,folder,nodes_export_subfolder="nodes",silent=False):
    """
    Extract the nodes to be imported from a zip file.

    :param infile: file path
    :param folder: a SandboxFolder, used to extract the file tree
    :param nodes_export_subfolder: name of the subfolder for AiiDA nodes
    :param silent: suppress debug print
    """
    import os
    import zipfile

    if not silent:
        print "READING DATA AND METADATA..."

    try:
        with zipfile.ZipFile(infile, "r") as zip:

            zip.extract(path=folder.abspath,
                   member='metadata.json')
            zip.extract(path=folder.abspath,
                   member='data.json')

            if not silent:
                print "EXTRACTING NODE DATA..."

            for membername in zip.namelist():
                # Check that we are only exporting nodes within
                # the subfolder!
                # TODO: better check such that there are no .. in the
                # path; use probably the folder limit checks
                if not membername.startswith(nodes_export_subfolder+os.sep):
                    continue
                zip.extract(path=folder.abspath,
                            member=membername)
    except zipfile.BadZipfile:
        raise ValueError("The input file format for import is not valid (not"
                         " a zip file)")


def extract_tar(infile,folder,nodes_export_subfolder="nodes",silent=False):
    """
    Extract the nodes to be imported from a (possibly zipped) tar file.

    :param infile: file path
    :param folder: a SandboxFolder, used to extract the file tree
    :param nodes_export_subfolder: name of the subfolder for AiiDA nodes
    :param silent: suppress debug print
    """
    import os
    import tarfile

    if not silent:
        print "READING DATA AND METADATA..."

    try:
        with tarfile.open(infile, "r:*", format=tarfile.PAX_FORMAT) as tar:

            tar.extract(path=folder.abspath,
                   member=tar.getmember('metadata.json'))
            tar.extract(path=folder.abspath,
                   member=tar.getmember('data.json'))

            if not silent:
                print "EXTRACTING NODE DATA..."

            for member in tar.getmembers():
                if member.isdev():
                    # safety: skip if character device, block device or FIFO
                    print >> sys.stderr, ("WARNING, device found inside the "
                        "import file: {}".format(member.name))
                    continue
                if member.issym() or member.islnk():
                    # safety: in export, I set dereference=True therefore
                    # there should be no symbolic or hard links.
                    print >> sys.stderr, ("WARNING, link found inside the "
                        "import file: {}".format(member.name))
                    continue
                # Check that we are only exporting nodes within
                # the subfolder!
                # TODO: better check such that there are no .. in the
                # path; use probably the folder limit checks
                if not member.name.startswith(nodes_export_subfolder+os.sep):
                    continue
                tar.extract(path=folder.abspath,
                            member=member)
    except tarfile.ReadError:
        raise ValueError("The input file format for import is not valid (1)")

def extract_tree(infile,folder,silent=False):
    """
    Prepare to import nodes from plain file system tree.

    :param infile: path
    :param folder: a SandboxFolder, used to extract the file tree
    :param silent: suppress debug print
    """
    import os

    def add_files(args,path,files):
        folder = args['folder']
        root = args['root']
        for f in files:
            fullpath = os.path.join(path,f)
            if os.path.isfile(fullpath) == False:
                continue
            relpath = os.path.relpath(fullpath,root)
            if os.path.dirname(relpath) != '':
                folder.get_subfolder(os.path.dirname(relpath)+os.sep,create=True)
            folder.insert_path(os.path.abspath(fullpath),relpath)

    os.path.walk(infile,add_files,{'folder': folder,'root': infile})

def import_data(in_path,ignore_unknown_nodes=False,
                silent=False):
    """
    Import exported AiiDA environment to the AiiDA database.
    If the 'in_path' is a folder, calls export_tree; otherwise, tries to
    detect the compression format (zip, tar.gz, tar.bz2, ...) and calls the
    correct function.

    :param in_path: the path to a file or folder that can be imported in AiiDA
    """
    import json
    import os
    import tarfile
    import zipfile
    from itertools import chain

    from django.db import transaction
    from aiida.utils import timezone

    from aiida.orm.node import Node
    from aiida.orm.group import Group
    from aiida.common.exceptions import UniquenessError
    from aiida.common.folders import SandboxFolder, RepositoryFolder
    from aiida.backends.djsite.db import models
    from aiida.common.utils import get_class_string, get_object_from_string
    from aiida.common.datastructures import calc_states


    # This is the export version expected by this function
    expected_export_version = '0.1'

    # The name of the subfolder in which the node files are stored
    nodes_export_subfolder = 'nodes'

    # The returned dictionary with new and existing nodes and links
    ret_dict = {}

    ################
    # EXTRACT DATA #
    ################
    # The sandbox has to remain open until the end
    with SandboxFolder() as folder:
        if os.path.isdir(in_path):
            extract_tree(in_path,folder,silent=silent)
        else:
            if tarfile.is_tarfile(in_path):
                extract_tar(in_path,folder,silent=silent,
                            nodes_export_subfolder=nodes_export_subfolder)
            elif zipfile.is_zipfile(in_path):
                extract_zip(in_path,folder,silent=silent,
                            nodes_export_subfolder=nodes_export_subfolder)
            else:
                raise ValueError("Unable to detect the input file format, it "
                                 "is neither a (possibly compressed) tar file, "
                                 "nor a zip file.")

        try:
            with open(folder.get_abs_path('metadata.json')) as f:
                metadata = json.load(f)

            with open(folder.get_abs_path('data.json')) as f:
                data = json.load(f)
        except IOError as e:
            raise ValueError("Unable to find the file {} in the import "
                             "file or folder".format(e.filename))

        ######################
        # PRELIMINARY CHECKS #
        ######################
        if metadata['export_version'] != expected_export_version:
            raise ValueError("File export version is {}, but I can import only "
                             "version {}".format(metadata['export_version'],
                                                 expected_export_version))

        ##########################################################################
        # CREATE UUID REVERSE TABLES AND CHECK IF I HAVE ALL NODES FOR THE LINKS #
        ##########################################################################
        linked_nodes = set(chain.from_iterable((l['input'], l['output'])
                                               for l in data['links_uuid']))
        group_nodes = set(chain.from_iterable(data['groups_uuid'].itervalues()))

        # I preload the nodes, I need to check each of them later, and I also
        # store them in a reverse table
        # I break up the query due to SQLite limitations..
        relevant_db_nodes = {}
        for group in grouper(999, linked_nodes):
            relevant_db_nodes.update({n.uuid: n for n in
                                      models.DbNode.objects.filter(uuid__in=group)})

        db_nodes_uuid = set(relevant_db_nodes.keys())
        dbnode_model = get_class_string(models.DbNode)
        import_nodes_uuid = set(v['uuid'] for v in
                                data['export_data'][dbnode_model].values())

        unknown_nodes = linked_nodes.union(group_nodes) - db_nodes_uuid.union(
            import_nodes_uuid)

        if unknown_nodes and not ignore_unknown_nodes:
            raise ValueError(
                "The import file refers to {} nodes with unknown UUID, therefore "
                "it cannot be imported. Either first import the unknown nodes, "
                "or export also the parents when exporting. The unknown UUIDs "
                "are:\n".format(len(unknown_nodes)) +
                "\n".join('* {}'.format(uuid) for uuid in unknown_nodes))

        ###################################
        # DOUBLE-CHECK MODEL DEPENDENCIES #
        ###################################
        # I hardcode here the model order, for simplicity; in any case, this is
        # fixed by the export version
        model_order = [get_class_string(m) for m in
                       (models.DbUser,
                        models.DbComputer,
                        models.DbNode,
                        models.DbGroup,
                       )
        ]

        # Models that do appear in the import file, but whose import is
        # managed manually
        model_manual = [get_class_string(m) for m in
                        (models.DbLink,
                         models.DbAttribute,)
        ]

        all_known_models = model_order + model_manual

        for import_field_name in metadata['all_fields_info']:
            if import_field_name not in all_known_models:
                raise NotImplementedError("Apparently, you are importing a "
                                          "file with a model '{}', but this does not appear in "
                                          "all_known_models!".format(import_field_name))

        for idx, model_name in enumerate(model_order):
            dependencies = []
            for field in metadata['all_fields_info'][model_name].values():
                try:
                    dependencies.append(field['requires'])
                except KeyError:
                    # (No ForeignKey)
                    pass
            for dependency in dependencies:
                if dependency not in model_order[:idx]:
                    raise ValueError("Model {} requires {} but would be loaded "
                                     "first; stopping...".format(model_name,
                                                                 dependency))

        ###################################################
        # CREATE IMPORT DATA DIRECT UNIQUE_FIELD MAPPINGS #
        ###################################################
        import_unique_ids_mappings = {}
        for model_name, import_data in data['export_data'].iteritems():
            if model_name in metadata['unique_identifiers']:
                # I have to reconvert the pk to integer
                import_unique_ids_mappings[model_name] = {
                    int(k): v[metadata['unique_identifiers'][model_name]] for k, v in
                    import_data.iteritems()}

        ###############
        # IMPORT DATA #
        ###############
        # DO ALL WITH A TRANSACTION
        with transaction.commit_on_success():
            foreign_ids_reverse_mappings = {}
            new_entries = {}
            existing_entries = {}

            # I first generate the list of data
            for model_name in model_order:
                Model = get_object_from_string(model_name)
                fields_info = metadata['all_fields_info'].get(model_name, {})
                unique_identifier = metadata['unique_identifiers'].get(
                    model_name, None)

                new_entries[model_name] = {}
                existing_entries[model_name] = {}

                foreign_ids_reverse_mappings[model_name] = {}

                # Not necessarily all models are exported
                if model_name in data['export_data']:

                    if unique_identifier is not None:
                        import_unique_ids = set(v[unique_identifier] for v in
                                                data['export_data'][model_name].values())

                        relevant_db_entries = {getattr(n, unique_identifier): n
                                               for n in Model.objects.filter(
                            **{'{}__in'.format(unique_identifier):
                                   import_unique_ids})}

                        foreign_ids_reverse_mappings[model_name] = {
                            k: v.pk for k, v in relevant_db_entries.iteritems()}
                        for k, v in data['export_data'][model_name].iteritems():
                            if v[unique_identifier] in relevant_db_entries.keys():
                                # Already in DB
                                existing_entries[model_name][k] = v
                            else:
                                # To be added
                                new_entries[model_name][k] = v
                    else:
                        new_entries[model_name] = data['export_data'][model_name].copy()

            # I import data from the given model
            for model_name in model_order:
                Model = get_object_from_string(model_name)
                fields_info = metadata['all_fields_info'].get(model_name, {})
                unique_identifier = metadata['unique_identifiers'].get(
                    model_name, None)

                for import_entry_id, entry_data in existing_entries[model_name].iteritems():
                    unique_id = entry_data[unique_identifier]
                    existing_entry_id = foreign_ids_reverse_mappings[model_name][unique_id]
                    # TODO COMPARE, AND COMPARE ATTRIBUTES
                    if model_name not in ret_dict:
                        ret_dict[model_name] = { 'new': [], 'existing': [] }
                    ret_dict[model_name]['existing'].append((import_entry_id,
                                                             existing_entry_id))
                    if not silent:
                        print "existing %s: %s (%s->%s)" % (model_name, unique_id,
                                                            import_entry_id,
                                                            existing_entry_id)
                        # print "  `-> WARNING: NO DUPLICITY CHECK DONE!"
                        # CHECK ALSO FILES!

                # Store all objects for this model in a list, and store them
                # all in once at the end.
                objects_to_create = []
                # This is needed later to associate the import entry with the new pk
                import_entry_ids = {}
                for import_entry_id, entry_data in new_entries[model_name].iteritems():
                    unique_id = entry_data[unique_identifier]
                    import_data = dict(deserialize_field(
                        k, v, fields_info=fields_info,
                        import_unique_ids_mappings=import_unique_ids_mappings,
                        foreign_ids_reverse_mappings=foreign_ids_reverse_mappings)
                                       for k, v in entry_data.iteritems())

                    objects_to_create.append(Model(**import_data))
                    import_entry_ids[unique_id] = import_entry_id

                # Before storing entries in the DB, I store the files (if these
                # are nodes). Note: only for new entries!
                if model_name == get_class_string(models.DbNode):
                    if not silent:
                        print "STORING NEW NODE FILES..."
                    for o in objects_to_create:

                        subfolder = folder.get_subfolder(os.path.join(
                            nodes_export_subfolder, export_shard_uuid(o.uuid)))
                        if not subfolder.exists():
                            raise ValueError("Unable to find the repository "
                                             "folder for node with UUID={} in the exported "
                                             "file".format(o.uuid))
                        destdir = RepositoryFolder(
                            section=Node._section_name,
                            uuid=o.uuid)
                        # Replace the folder, possibly destroying existing
                        # previous folders, and move the files (faster if we
                        # are on the same filesystem, and
                        # in any case the source is a SandboxFolder)
                        destdir.replace_with_folder(subfolder.abspath,
                                                    move=True, overwrite=True)

                # Store them all in once; however, the PK are not set in this way...
                Model.objects.bulk_create(objects_to_create)

                # Get back the just-saved entries
                just_saved = dict(Model.objects.filter(
                    **{"{}__in".format(unique_identifier):
                           import_entry_ids.keys()}).values_list(unique_identifier, 'pk'))

                imported_states = []
                if model_name == get_class_string(models.DbNode):
                    if not silent:
                        print "SETTING THE IMPORTED STATES FOR NEW NODES..."
                    # I set for all nodes, even if I should set it only
                    # for calculations
                    for unique_id, new_pk in just_saved.iteritems():
                        imported_states.append(
                            models.DbCalcState(dbnode_id=new_pk,
                                               state=calc_states.IMPORTED))
                    models.DbCalcState.objects.bulk_create(imported_states)

                # Now I have the PKs, print the info
                # Moreover, set the foreing_ids_reverse_mappings
                for unique_id, new_pk in just_saved.iteritems():
                    import_entry_id = import_entry_ids[unique_id]
                    foreign_ids_reverse_mappings[model_name][unique_id] = new_pk
                    if model_name not in ret_dict:
                        ret_dict[model_name] = { 'new': [], 'existing': [] }
                    ret_dict[model_name]['new'].append((import_entry_id,
                                                        new_pk))

                    if not silent:
                        print "NEW %s: %s (%s->%s)" % (model_name, unique_id,
                                                       import_entry_id,
                                                       new_pk)

                # For DbNodes, we also have to store Attributes!
                if model_name == get_class_string(models.DbNode):
                    if not silent:
                        print "STORING NEW NODE ATTRIBUTES..."
                    for unique_id, new_pk in just_saved.iteritems():
                        import_entry_id = import_entry_ids[unique_id]
                        # Get attributes from import file
                        try:
                            attributes = data['node_attributes'][
                                str(import_entry_id)]
                            attributes_conversion = data[
                                'node_attributes_conversion'][
                                str(import_entry_id)]
                        except KeyError:
                            raise ValueError("Unable to find attribute info "
                                             "for DbNode with UUID = {}".format(
                                unique_id))

                        # Here I have to deserialize the attributes
                        deserialized_attributes = deserialize_attributes(
                            attributes, attributes_conversion)
                        models.DbAttribute.reset_values_for_node(
                            dbnode=new_pk,
                            attributes=deserialized_attributes,
                            with_transaction=False)

            if not silent:
                print "STORING NODE LINKS..."
            ## TODO: check that we are not creating input links of an already
            ##       existing node...
            import_links = data['links_uuid']
            links_to_store = []

            # Needed for fast checks of existing links
            existing_links_raw = models.DbLink.objects.all().values_list(
                'input', 'output', 'label')
            existing_links_labels = {(l[0], l[1]): l[2] for l in existing_links_raw}
            existing_input_links = {(l[1], l[2]): l[0] for l in existing_links_raw}

            dbnode_reverse_mappings = foreign_ids_reverse_mappings[
                get_class_string(models.DbNode)]
            for link in import_links:
                try:
                    in_id = dbnode_reverse_mappings[link['input']]
                    out_id = dbnode_reverse_mappings[link['output']]
                except KeyError:
                    if ignore_unknown_nodes:
                        continue
                    else:
                        raise ValueError("Trying to create a link with one "
                                         "or both unknown nodes, stopping "
                                         "(in_uuid={}, out_uuid={}, "
                                         "label={})".format(link['input'],
                                                            link['output'], link['label']))

                try:
                    existing_label = existing_links_labels[in_id, out_id]
                    if existing_label != link['label']:
                        raise ValueError("Trying to rename an existing link name, "
                                         "stopping (in={}, out={}, old_label={}, "
                                         "new_label={})".format(in_id, out_id,
                                                                existing_label, link['label']))
                        # Do nothing, the link is already in place and has the correct
                        # name
                except KeyError:
                    try:
                        existing_input = existing_input_links[out_id, link['label']]
                        # If existing_input were the correct one, I would have found
                        # it already in the previous step!
                        raise ValueError("There exists already an input link to "
                                         "node {} with label {} but it does not "
                                         "come the expected input {}".format(
                            out_id, link['label'], in_id))
                    except KeyError:
                        # New link
                        links_to_store.append(models.DbLink(
                            input_id=in_id, output_id=out_id, label=link['label']))
                        if 'aiida.backends.djsite.db.models.DbLink' not in ret_dict:
                            ret_dict['aiida.backends.djsite.db.models.DbLink'] = { 'new': [] }
                        ret_dict['aiida.backends.djsite.db.models.DbLink']['new'].append((in_id,out_id))

            # Store new links
            if links_to_store:
                if not silent:
                    print "   ({} new links...)".format(len(links_to_store))

                models.DbLink.objects.bulk_create(links_to_store)
            else:
                if not silent:
                    print "   (0 new links...)"

            if not silent:
                print "STORING GROUP ELEMENTS..."
            import_groups = data['groups_uuid']
            for groupuuid, groupnodes in import_groups.iteritems():
                # TODO: cache these to avoid too many queries
                group = models.DbGroup.objects.get(uuid=groupuuid)
                nodes_to_store = [dbnode_reverse_mappings[node_uuid]
                                  for node_uuid in groupnodes]
                if nodes_to_store:
                    group.dbnodes.add(*nodes_to_store)

            ######################################################
            # Put everything in a specific group
            dbnode_model_name = get_class_string(models.DbNode)
            existing = existing_entries.get(dbnode_model_name, {})
            existing_pk = [foreign_ids_reverse_mappings[
                               dbnode_model_name][v['uuid']]
                           for v in existing.itervalues()]
            new = new_entries.get(dbnode_model_name, {})
            new_pk = [foreign_ids_reverse_mappings[
                          dbnode_model_name][v['uuid']]
                      for v in new.itervalues()]

            pks_for_group = existing_pk + new_pk

            # So that we do not create empty groups
            if pks_for_group:
                # Get an unique name for the import group, based on the
                # current (local) time
                basename = timezone.localtime(timezone.now()).strftime(
                    "%Y%m%d-%H%M%S")
                counter = 0
                created = False
                while not created:
                    if counter == 0:
                        group_name = basename
                    else:
                        group_name = "{}_{}".format(basename, counter)
                    try:
                        group = Group(name=group_name,
                                      type_string=IMPORTGROUP_TYPE).store()
                        created = True
                    except UniquenessError:
                        counter += 1

                # Add all the nodes to the new group
                # TODO: decide if we want to return the group name
                group.add_nodes(models.DbNode.objects.filter(
                    pk__in=pks_for_group))

                if not silent:
                    print "IMPORTED NODES GROUPED IN IMPORT GROUP NAMED '{}'".format(group.name)
            else:
                if not silent:
                    print "NO DBNODES TO IMPORT, SO NO GROUP CREATED"

    if not silent:
        print "*** WARNING: MISSING EXISTING UUID CHECKS!!"
        print "*** WARNING: TODO: UPDATE IMPORT_DATA WITH DEFAULT VALUES! (e.g. calc status, user pwd, ...)"
        print "DONE."

    return ret_dict

import HTMLParser


class HTMLGetLinksParser(HTMLParser.HTMLParser):
    def __init__(self, filter_extension=None):
        """
        If a filter_extension is passed, only links with extension matching
        the given one will be returned.
        """
        self.filter_extension = filter_extension
        self.links = []
        HTMLParser.HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        """
        Store the urls encountered, if they match the request.
        """
        if tag == 'a':
            for k, v in attrs:
                if k == 'href':
                    if (self.filter_extension is None or
                            v.endswith('.{}'.format(self.filter_extension))):
                        self.links.append(v)

    def get_links(self):
        """
        Return the links that were found during the parsing phase.
        """
        return self.links


def get_valid_import_links(url):
    """
    Open the given URL, parse the HTML and return a list of valid links where
    the link file has a .aiida extension.
    """
    import urllib2
    import urlparse

    request = urllib2.urlopen(url)
    parser = HTMLGetLinksParser(filter_extension='aiida')
    parser.feed(request.read())

    return_urls = []

    for link in parser.get_links():
        return_urls.append(urlparse.urljoin(request.geturl(), link))

    return return_urls

class Import(VerdiCommand):
    """
    Import nodes and group of nodes

    This command allows to import nodes from file, for backup purposes or
    to share data with collaborators.
    """

    def run(self, *args):
        load_dbenv()

        import argparse
        import traceback
        import urllib2

        from aiida.common.folders import SandboxFolder
        from aiida.orm.importexport import get_valid_import_links, import_data

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Import data in the DB.')
        parser.add_argument('-w', '--webpage', nargs='+', type=str,
                            dest='webpages', metavar='URL',
                            help="Download all URLs in the given HTTP web "
                                 "page with extension .aiida")
        parser.add_argument(nargs='*', type=str,
                            dest='files', metavar='URL_OR_PATH',
                            help="Import the given files or URLs")

        parsed_args = parser.parse_args(args)

        all_args = [] if parsed_args.files is None else parsed_args.files
        urls = []
        files = []
        for path in all_args:
            if path.startswith('http://') or path.startswith('https://'):
                urls.append(path)
            else:
                files.append(path)

        webpages = [] if parsed_args.webpages is None else parsed_args.webpages

        for webpage in webpages:
            try:
                print "**** Getting links from {}".format(webpage)
                found_urls = get_valid_import_links(webpage)
                print " `-> {} links found.".format(len(found_urls))
                urls += found_urls
            except Exception:
                traceback.print_exc()
                print ""
                print "> There has been an exception during the import of webpage"
                print "> {}".format(webpage)
                answer = raw_input("> Do you want to continue (c) or stop "
                                   "(S, default)? ")
                if answer.lower() == 'c':
                    continue
                else:
                    return

        if not (urls + files):
            print >> sys.stderr, ("Pass at least one file or URL from which "
                                  "you want to import data.")
            sys.exit(1)

        for filename in files:
            try:
                print "**** Importing file {}".format(filename)
                import_data(filename)
            except Exception:
                traceback.print_exc()

                print ""
                print "> There has been an exception during the import of file"
                print "> {}".format(filename)
                answer = raw_input("> Do you want to continue (c) or stop "
                                   "(S, default)? ")
                if answer.lower() == 'c':
                    continue
                else:
                    return

        download_file_name = 'importfile.tar.gz'
        for url in urls:
            try:
                print "**** Downloading url {}".format(url)
                response = urllib2.urlopen(url)
                with SandboxFolder() as temp_download_folder:
                    temp_download_folder.create_file_from_filelike(
                        response, download_file_name)

                    print " `-> File downloaded. Importing it..."
                    import_data(temp_download_folder.get_abs_path(
                        download_file_name))
            except Exception:
                traceback.print_exc()

                print ""
                print "> There has been an exception during the import of url"
                print "> {}".format(url)
                answer = raw_input("> Do you want to continue (c) or stop "
                                   "(S, default)? ")
                if answer.lower() == 'c':
                    continue
                else:
                    return


    def complete(self, subargs_idx, subargs):
        return ""
