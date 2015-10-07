# -*- coding: utf-8 -*-
import sys

from aiida.cmdline.baseclass import VerdiCommand
from aiida.common.utils import (export_shard_uuid,
                                get_class_string, get_object_from_string)
from aiida import load_dbenv

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Andrius Merkys, Giovanni Pizzi, Nicolas Mounet"


def serialize_field(data, track_conversion=False):
    """
    Serialize a single field.
    
    :todo: Generalize such that it the proper function is selected also during
        import
    """
    import datetime
    import pytz

    if isinstance(data, dict):
        if track_conversion:
            ret_data = {}
            ret_conversion = {}
            for k, v in data.iteritems():
                ret_data[k], ret_conversion[k] = serialize_field(
                    data=v, track_conversion=track_conversion)
        else:
            ret_data = {k: serialize_field(data=v,
                                           track_conversion=track_conversion)
                        for k, v in data.iteritems()}
    elif isinstance(data, (list, tuple)):
        if track_conversion:
            ret_data = []
            ret_conversion = []
            for value in data:
                this_data, this_conversion = serialize_field(
                    data=value, track_conversion=track_conversion)
                ret_data.append(this_data)
                ret_conversion.append(this_conversion)
        else:
            ret_data = [serialize_field(
                data=value, track_conversion=track_conversion)
                        for value in data]
    elif isinstance(data, datetime.datetime):
        # Note: requires timezone-aware objects!
        ret_data = data.astimezone(pytz.utc).strftime(
            '%Y-%m-%dT%H:%M:%S.%f')
        ret_conversion = 'date'
    else:
        ret_data = data
        ret_conversion = None

    if track_conversion:
        return (ret_data, ret_conversion)
    else:
        return ret_data


def serialize_dict(datadict, remove_fields=[], rename_fields={},
                   track_conversion=False):
    """
    Serialize the dict using the serialize_field function to serialize
    each field.
    
    :param remove_fields: a list of strings. 
      If a field with key inside the remove_fields list is found, 
      it is removed from the dict.
      
      This is only used at level-0, no removal
      is possible at deeper levels.
    
    :param rename_fields: a dictionary in the format
      ``{"oldname": "newname"}``. 

      If the "oldname" key is found, it is replaced with the
      "newname" string in the output dictionary.
      
      This is only used at level-0, no renaming
      is possible at deeper levels.
    :param track_conversion: if True, a tuple is returned, where the first
      element is the serialized dictionary, and the second element is a
      dictionary with the information on the serialized fields.
    """
    ret_dict = {}

    conversions = {}

    for k, v in datadict.iteritems():
        if k not in remove_fields:
            # rename_fields.get(k,k): use the replacement if found in rename_fields,
            # otherwise use 'k' as the default value.
            if track_conversion:
                (ret_dict[rename_fields.get(k, k)],
                 conversions[rename_fields.get(k, k)]) = serialize_field(
                    data=v, track_conversion=track_conversion)
            else:
                ret_dict[rename_fields.get(k, k)] = serialize_field(
                    data=v, track_conversion=track_conversion)

    if track_conversion:
        return (ret_dict, conversions)
    else:
        return ret_dict


def get_all_fields_info():
    """
    Retrieve automatically the information on the fields and store them in a
    dictionary, that will be also stored in the export data, in the metadata
    file.
    
    :return: a tuple with two elements, the all_fiekds_info dictionary, and the
      unique_identifiers dictionary.
    """
    import importlib

    import django.db.models.fields as djf
    import django_extensions

    from aiida.djsite.db import models

    all_fields_info = {}

    user_model_string = get_class_string(models.DbUser)

    # TODO: These will probably need to have a default value in the IMPORT!
    # TODO: maybe define this inside the Model!
    all_exclude_fields = {
        user_model_string: ['password', 'is_staff',
                            'is_superuser', 'is_active',
                            'last_login', 'date_joined'],
    }

    # I start only with DbNode
    export_models = set([get_class_string(Model) for Model in
                         [models.DbNode, models.DbAttribute,
                          models.DbLink, models.DbGroup]])

    while True:
        missing_models = export_models - set(all_fields_info.keys())
        if not missing_models:
            break

        for model_name in missing_models:
            Model = get_object_from_string(model_name)

            thisinfo = {}
            exclude_fields = all_exclude_fields.get(model_name, [])
            for field in Model._meta.fields:
                if field.name in exclude_fields:
                    continue
                if isinstance(field, djf.AutoField):
                    # Do not explicitly store the ID field
                    pass
                elif isinstance(field, (djf.CharField, djf.TextField,
                                        djf.IntegerField, djf.FloatField,
                                        djf.BooleanField, djf.NullBooleanField,
                                        django_extensions.db.fields.UUIDField)):
                    thisinfo[field.name] = {}
                elif isinstance(field, djf.DateTimeField):
                    # This information is needed on importing
                    thisinfo[field.name] = {'convert_type': 'date'}
                elif isinstance(field, django_extensions.db.fields.UUIDField):
                    thisinfo[field.name] = {}
                elif isinstance(field, djf.related.ForeignKey):
                    rel_model_name = get_class_string(field.rel.to)
                    related_name = field.rel.related_name
                    thisinfo[field.name] = {
                        # The 'values' method will return the id (an integer),
                        # so no custom serializer is required
                        'requires': rel_model_name,
                        'related_name': related_name,
                    }
                    export_models.add(rel_model_name)
                else:
                    raise NotImplementedError(
                        "Export not implemented for field of type {}.{}".format(
                            get_class_string(field)))
                all_fields_info[model_name] = thisinfo

    unique_identifiers = {}
    for k in all_fields_info:
        if k == user_model_string:
            unique_identifiers[k] = 'email'
            continue

        # No unique identifier in this case
        if k in [get_class_string(models.DbAttribute),
                 get_class_string(models.DbLink),
                 get_class_string(models.DbExtra)]:
            unique_identifiers[k] = None
            continue

        m = get_object_from_string(k)
        field_names = [f.name for f in m._meta.fields]
        if 'uuid' in field_names:
            unique_identifiers[k] = 'uuid'
        else:
            raise ValueError("Unable to identify the unique identifier "
                             "for model {}".format(k))

    return all_fields_info, unique_identifiers

def export_tree(what, folder, also_parents = True,
                also_calc_outputs = True, allowed_licenses = None,
                exclude_forbidden_licenses = False, silent = False):
    """
    Export the DB entries passed in the 'what' list to a file tree.
    
    :todo: limit the export to finished or failed calculations.
    
    :param what: a list of Django database entries; they can belong to different
      models.
    :param folder: a :py:class:`Folder <aiida.common.folders.Folder>` object
    :param also_parents: if True, also all the parents are stored (from th
      DbPath transitive closure table)
    :param also_calc_outputs: if True, any output of a calculation is also exported
    :param allowed_licenses: a list or a function. If a list, then checks
      whether all licenses of Data nodes are in the list. If a function,
      then calls function for licenses of Data nodes expecting True if
      license is allowed, False otherwise.
    :param exclude_forbidden_licenses: if True, skips exporting of Data
      nodes with forbidden licenses. If False, raises LicensingException
      if any Data node with forbidden license exists.
    :param silent: suppress debug prints
    :raises LicensingException: if any node is licensed under forbidden
      license and exclude_forbidden_licenses = False
    """
    import json
    import os
    import operator
    from collections import defaultdict

    from django.db.models import Q

    import aiida
    from aiida.djsite.db import models
    from aiida.orm import Node, Calculation, load_node
    from aiida.orm.data import Data
    from aiida.common.exceptions import LicensingException
    from aiida.common.folders import RepositoryFolder

    if not silent:
        print "STARTING EXPORT..."

    EXPORT_VERSION = '0.1'
    
    all_fields_info, unique_identifiers = get_all_fields_info()

    entries_ids_to_add = defaultdict(list)
    # I store a list of the actual dbnodes
    groups_entries = []
    group_class_string = get_class_string(models.DbGroup)
    for entry in what:
        class_string = get_class_string(entry)
        entries_ids_to_add[class_string].append(entry.pk)
        if class_string == group_class_string:
            groups_entries.append(entry)

    if also_parents:
        # It is a defaultdict, it will provide an empty list
        given_nodes = entries_ids_to_add[get_class_string(models.DbNode)]

        if given_nodes:
            # Alsof add the parents (to any level) to the query
            given_nodes = list(set(given_nodes +
                                   list(models.DbNode.objects.filter(
                                       children__in=given_nodes).values_list('pk', flat=True))))
            entries_ids_to_add[get_class_string(models.DbNode)] = given_nodes

    if also_calc_outputs:
        given_nodes = entries_ids_to_add[get_class_string(models.DbNode)]

        if given_nodes:
            # Add all (direct) outputs of a calculation object that was already
            # selected
            given_nodes = list(set(given_nodes +
                                   list(models.DbNode.objects.filter(
                                       inputs__pk__in=given_nodes,
                                       inputs__type__startswith=Calculation._query_type_string
                                   ).values_list('pk', flat=True)
                                   )))
            entries_ids_to_add[get_class_string(models.DbNode)] = given_nodes

    # Initial query to fire the generation of the export data
    entries_to_add = {k: [Q(id__in=v)] for k, v
                      in entries_ids_to_add.iteritems()}

    # Check the licenses of exported data.
    # TODO: use standard django constructions or QueryTool, since current
    # implementation is far from optimal.
    if allowed_licenses is not None:
        from inspect import isfunction
        for k, v in entries_ids_to_add.iteritems():
            for pk in v:
                node = load_node(int(pk))
                try:
                    if isinstance(node, Data) and node.source and \
                      node.source.get('license', None):
                        if isfunction(allowed_licenses):
                            try:
                                if not allowed_licenses(node.source['license']):
                                    raise LicensingException
                            except Exception as e:
                                raise LicensingException
                        else:
                            if node.source['license'] not in allowed_licenses:
                                raise LicensingException
                except LicensingException:
                    if exclude_forbidden_licenses:
                        entries_ids_to_add[k].remove(pk)
                    else:
                        raise LicensingException("Node {} is licensed "
                                                 "under {} license, which "
                                                 "is not in the list of "
                                                 "allowed licenses".format(
                                                  node, node.source['license']))

    ############################################################
    ##### Start automatic recursive export data generation #####
    ############################################################
    if not silent:
        print "STORING DATABASE ENTRIES..."
    export_data = {}
    while entries_to_add:
        new_entries_to_add = {}
        for model_name, querysets in entries_to_add.iteritems():
            if not silent:
                print "  - Model: {}".format(model_name)
            Model = get_object_from_string(model_name)

            ## Before I was doing this. But it is VERY slow! E.g. 
            ## To get the user owning 44 nodes or 1 group was taking
            ## 26 seconds, while it was taking only 0.1 seconds if the two
            ## queries were run independently!
            ## I think this was doing the wrong type of UNION
            #dbentries = Model.objects.filter(
            #    reduce(operator.or_, querysets)).distinct()
            ## Now I instead create the list of UUIDs and do a set() instead
            ## of .distinct(); then I get the final results with a further
            ## query.
            db_ids = set()
            for queryset in querysets:
                db_ids.update(Model.objects.filter(queryset).values_list(
                    'id', flat=True))
            dbentries = Model.objects.filter(id__in=db_ids)
            entryvalues = dbentries.values(
                'id', *all_fields_info[model_name].keys()
            )

            # Only serialize new nodes (also to avoid infinite loops)
            if model_name in export_data:
                serialized = {
                    str(v['id']): serialize_dict(v, remove_fields=['id'])
                    for v in entryvalues
                    if v['id'] not in export_data[model_name]
                }
            else:
                serialized = {
                    str(v['id']): serialize_dict(v, remove_fields=['id'])
                    for v in entryvalues
                }

            try:
                export_data[model_name].update(serialized)
            except KeyError:
                export_data[model_name] = serialized

            if serialized:
                foreign_fields = {k: v for k, v in
                                  all_fields_info[model_name].iteritems()
                                  if 'requires' in v}

                for k, v in foreign_fields.iteritems():
                    related_queryobj = Q(**{'{}__in'.format(v['related_name']):
                                                serialized.keys()})
                    try:
                        new_entries_to_add[v['requires']].append(related_queryobj)
                    except KeyError:
                        new_entries_to_add[v['requires']] = [related_queryobj]

        entries_to_add = new_entries_to_add

    ######################################
    # Manually manage links and attributes
    ######################################
    # I use .get because there may be no nodes to export
    all_nodes_pk = export_data.get(get_class_string(models.DbNode), {}).keys()
    if sum(len(model_data) for model_data in export_data.values()) == 0:
        if not silent:
            print "No nodes to store, exiting..."
        return

    if not silent:
        print "Exporting a total of {} db entries, of which {} nodes.".format(
            sum(len(model_data) for model_data in export_data.values()),
            len(all_nodes_pk))
    all_nodes_query = models.DbNode.objects.filter(pk__in=all_nodes_pk)

    ## ATTRIBUTES
    if not silent:
        print "STORING NODE ATTRIBUTES..."
    node_attributes = {}
    node_attributes_conversion = {}
    for n in all_nodes_query:
        (node_attributes[str(n.pk)],
         node_attributes_conversion[str(n.pk)]) = serialize_dict(
            n.attributes, track_conversion=True)
    ## If I want to store them 'raw'; it is faster, but more error prone and
    ## less version-independent, I think. Better to optimize the n.attributes 
    ## call.
    # all_nodes_query = models.DbNode.objects.filter(pk__in=all_nodes_pk)
    #node_attributes_raw = list(models.DbAttribute.objects.filter(
    #    dbnode__in=all_nodes_pk).distinct().values(
    #    'bval', 'tval', 'ival', 'fval', 'dval',
    #    'datatype', 'time', 'dbnode', 'key')

    if not silent:
        print "STORING NODE LINKS..."
    ## All 'parent' links (in this way, I can automatically export a node 
    ## that will get automatically attached to a parent node in the end DB,
    ## if the parent node is already present in the DB)
    linksquery = models.DbLink.objects.filter(
        output__in=all_nodes_query).distinct()

    links_uuid = [
        serialize_dict(l, rename_fields={
            'input__uuid': 'input',
            'output__uuid': 'output'})
        for l in linksquery.values(
            'input__uuid', 'output__uuid', 'label')]

    if not silent:
        print "STORING GROUP ELEMENTS..."
    groups_uuid = {g.uuid: list(g.dbnodes.values_list('uuid', flat=True))
                   for g in groups_entries}

    ######################################
    # Now I store
    ######################################    
    # subfolder inside the export package
    nodesubfolder = folder.get_subfolder('nodes',create=True,
                                         reset_limit=True)

    if not silent:
        print "STORING DATA..."
    
    with folder.open('data.json', 'w') as f:
        json.dump({
                'node_attributes': node_attributes,
                'node_attributes_conversion': node_attributes_conversion,
                'export_data': export_data,
                'links_uuid': links_uuid,
                'groups_uuid': groups_uuid,
                }, f)

    metadata = {
        'aiida_version': aiida.get_version(),
        'export_version': EXPORT_VERSION,
        'all_fields_info': all_fields_info,
        'unique_identifiers': unique_identifiers,
        }

    with folder.open('metadata.json', 'w') as f:
        json.dump(metadata, f)

    if silent is not True:
        print "STORING FILES..."

    # Large speed increase by not getting the node itself and looping in memory
    # in python, but just getting the uuid
    for uuid in models.DbNode.objects.filter(pk__in=all_nodes_pk).values_list(
        'uuid', flat=True):
        sharded_uuid = export_shard_uuid(uuid)

        # Important to set create=False, otherwise creates
        # twice a subfolder. Maybe this is a bug of insert_path??

        thisnodefolder = nodesubfolder.get_subfolder(
            sharded_uuid, create=False,
            reset_limit=True)
        # In this way, I copy the content of the folder, and not the folder
        # itself
        thisnodefolder.insert_path(src=RepositoryFolder(
            section=Node._section_name, uuid=uuid).abspath,
                                   dest_name='.')

class MyWritingZipFile(object):
    def __init__(self, zipfile, fname):
        
        self._zipfile = zipfile
        self._fname = fname
        self._buffer = None
        
    def open(self):
        import StringIO
        
        if self._buffer is not None:
            raise IOError("Cannot open again!")
        self._buffer = StringIO.StringIO()

    def write(self, data):
        self._buffer.write(data)

    def close(self):
        self._buffer.seek(0)
        self._zipfile.writestr(self._fname, self._buffer.read())
        self._buffer = None
        
    def __enter__(self):
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        self.close()
        
class ZipFolder(object):
    """
    To improve: if zipfile is closed, do something
    (e.g. add explicit open method, rename open to openfile,
    set _zipfile to None, ...)
    """
    def __init__(self, zipfolder_or_fname, mode=None, subfolder='.', 
                  use_compression=True):
        """
        :param zipfolder_or_fname: either another ZipFolder instance,
          of which you want to get a subfolder, or a filename to create.
        :param mode: the file mode; see the zipfile.ZipFile docs for valid
          strings. Note: can be specified only if zipfolder_or_fname is a
          string (the filename to generate)
        :param subfolder: the subfolder that specified the "current working
          directory" in the zip file. If zipfolder_or_fname is a ZipFolder,
          subfolder is a relative path from zipfolder_or_fname.subfolder
        :param use_compression: either True, to compress files in the Zip, or
          False if you just want to pack them together without compressing.
          It is ignored if zipfolder_or_fname is a ZipFolder isntance.  
        """
        import zipfile
        import os
        
        if isinstance(zipfolder_or_fname, basestring):
            the_mode = mode
            if the_mode is None:
                the_mode = "r"
            if use_compression:
                compression = zipfile.ZIP_DEFLATED
            else:
                compression = zipfile.ZIP_STORED
            self._zipfile = zipfile.ZipFile(zipfolder_or_fname, mode=the_mode,
                                            compression=compression)
            self._pwd = subfolder
        else:
            if mode is not None:
                raise ValueError("Cannot specify 'mode' when passing a ZipFolder")
            self._zipfile = zipfolder_or_fname._zipfile
            self._pwd = os.path.join(zipfolder_or_fname.pwd, subfolder)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()    
            
    def close(self):
        self._zipfile.close()
            
    @property
    def pwd(self):
        return self._pwd

    def open(self, fname, mode='r'):
        if mode == 'w':
            return MyWritingZipFile(
                zipfile=self._zipfile, fname=self._get_internal_path(fname))
        else:
            return self._zipfile.open(self._get_internal_path(fname), mode)

    def _get_internal_path(self, filename):
        import os
        return os.path.normpath(os.path.join(self.pwd, filename))
        
    def get_subfolder(self, subfolder, create=False, reset_limit=False):
        # reset_limit: ignored
        # create: ignored, for the time being
        subfolder = ZipFolder(self, subfolder=subfolder)
        return subfolder

    def insert_path(self, src, dest_name=None, overwrite=True):
        import os

        if dest_name is None:
            base_filename = unicode(os.path.basename(src))
        else:
            base_filename = unicode(dest_name)

        base_filename = self._get_internal_path(base_filename)
        
        if not isinstance(src, unicode):
            src = unicode(src)

        if not os.path.isabs(src):
            raise ValueError("src must be an absolute path in insert_file")

        if not overwrite:
            try:
                self._zipfile.getinfo(filename)
                exists = True
            except KeyError:
                exists = False
            if exists:
                raise IOError("destination already exists: {}".format(
                        filename))

        #print src, filename
        if os.path.isdir(src):
            for dirpath, dirnames, filenames in os.walk(src):
                relpath = os.path.relpath(dirpath, src)
                for fn in dirnames + filenames:
                    real_src = os.path.join(dirpath,fn)
                    real_dest = os.path.join(base_filename,relpath,fn)
                    self._zipfile.write(real_src,
                                        real_dest)
        else:
            self._zipfile.write(src, base_filename)
        
        
        
def export_zip(what, outfile = 'testzip', overwrite = False,
              silent = False, use_compression = True, **kwargs):
    import os

    if not overwrite and os.path.exists(outfile):
        raise IOError("The output file '{}' already "
                      "exists".format(outfile))

    import time
    t = time.time()
    with ZipFolder(outfile, mode='w', use_compression = use_compression) as folder:
        export_tree(what, folder=folder, silent=silent, **kwargs)
    if not silent:
        print "File written in {:10.3g} s.".format(time.time() - t)
        
def export(what, outfile = 'export_data.aiida.tar.gz', overwrite = False,
           silent = False, **kwargs):
    """
    Export the DB entries passed in the 'what' list on a file.
    
    :todo: limit the export to finished or failed calculations.
    
    :param what: a list of Django database entries; they can belong to different
      models.
    :param also_parents: if True, also all the parents are stored (from th
      DbPath transitive closure table)
    :param also_calc_outputs: if True, any output of a calculation is also exported
    :param outfile: the filename of the file on which to export
    :param overwrite: if True, overwrite the output file without asking.
        if False, raise an IOError in this case.
    :param silent: suppress debug print
    
    :raise IOError: if overwrite==False and the filename already exists.
    """
    import os
    import tarfile
    import time
    
    from aiida.common.folders import SandboxFolder

    if not overwrite and os.path.exists(outfile):
        raise IOError("The output file '{}' already "
                      "exists".format(outfile))

    folder = SandboxFolder()
    t1 = time.time()
    export_tree(what, folder=folder, silent=silent, **kwargs)
    t2 = time.time()
    
    if not silent:
        print "COMPRESSING..."

    # PAX_FORMAT: virtually no limitations, better support for unicode
    #   characters
    # dereference=True: at the moment, we should not have any symlink or
    #   hardlink in the AiiDA repository; therefore, do not store symlinks
    #   or hardlinks, but store the actual destinations.
    #   This also simplifies the checks on import.
    t3 = time.time()
    with tarfile.open(outfile, "w:gz", format=tarfile.PAX_FORMAT,
                      dereference=True) as tar:
        tar.add(folder.abspath, arcname="")

        #        import shutil
        #        shutil.make_archive(outfile, 'zip', folder.abspath)#, base_dir='aiida')
    t4 = time.time()

    if not silent:
        filecr_time = t2-t1
        filecomp_time = t4-t3
        print "Exported in {:6.2g}s, compressed in {:6.2g}s, total: {:6.2g}s.".format(filecr_time, filecomp_time, filecr_time + filecomp_time)
        
    if not silent:
        print "DONE."

class Export(VerdiCommand):
    """
    Export nodes and group of nodes

    This command allows to export to file nodes and group of nodes, for backup
    purposes or to share data with collaborators.
    Call this command with the '-h' option for some documentation of its usage.
    """

    def run(self, *args):
        load_dbenv()

        import argparse

        from aiida.orm import Group
        from aiida.common.exceptions import NotExistent
        from aiida.djsite.db import models

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Export data from the DB.')
        parser.add_argument('-c', '--computers', nargs='+', type=int, metavar="PK",
                            help="Export the given computers")
        parser.add_argument('-n', '--nodes', nargs='+', type=int, metavar="PK",
                            help="Export the given nodes")
        parser.add_argument('-g', '--groups', nargs='+', metavar="GROUPNAME",
                            help="Export all nodes in the given group(s).",
                            type=str)
        parser.add_argument('-P', '--no-parents',
                            dest='no_parents', action='store_true',
                            help="Store only the nodes that are explicitly given, without exporting the parents")
        parser.set_defaults(no_parents=False)
        parser.add_argument('-O', '--no-calc-outputs',
                            dest='no_calc_outputs', action='store_true',
                            help="If a calculation is included in the list of nodes to export, do not export its outputs")
        parser.set_defaults(no_calc_outputs=False)
        parser.add_argument('-y', '--overwrite',
                            dest='overwrite', action='store_true',
                            help="Overwrite the output file, if it exists")
        parser.set_defaults(overwrite=False)

        zipsubgroup = parser.add_mutually_exclusive_group()
        zipsubgroup.add_argument('-z', '--zipfile-compressed',
                            dest='zipfilec', action='store_true',
                            help="Store as zip file (experimental, should be faster")
        zipsubgroup.add_argument('-Z', '--zipfile-uncompressed',
                            dest='zipfileu', action='store_true',
                            help="Store as uncompressed zip file (experimental, should be faster")
        parser.set_defaults(zipfilec=False)
        parser.set_defaults(zipfileu=False)

        parser.add_argument('output_file', type=str,
                            help='The output file name for the export file')

        parsed_args = parser.parse_args(args)

        if parsed_args.nodes is None:
            node_pk_list = []
        else:
            node_pk_list = parsed_args.nodes

        groups_list = []

        if parsed_args.groups is not None:
            for group_name in parsed_args.groups:
                try:
                    group = Group.get_from_string(group_name)
                except (ValueError, NotExistent) as e:
                    print >> sys.stderr, e.message
                    sys.exit(1)
                node_pk_list += group.dbgroup.dbnodes.values_list('pk', flat=True)
                groups_list.append(group.dbgroup)
        node_pk_list = set(node_pk_list)
        
        node_list = list(
            models.DbNode.objects.filter(pk__in=node_pk_list))
        missing_nodes = node_pk_list.difference(_.pk for _ in node_list)
        for pk in missing_nodes:
            print >> sys.stderr, ("WARNING! Node with pk= {} "
                                  "not found, skipping.".format(pk))
        if parsed_args.computers is not None:
            computer_list = list(models.DbComputer.objects.filter(
                pk__in=parsed_args.computers))
            missing_computers = set(parsed_args.computers).difference(
                _.pk for _ in computer_list)
            for pk in missing_computers:
                print >> sys.stderr, ("WARNING! Computer with pk= {} "
                                      "not found, skipping.".format(pk))
        else:
            computer_list = []

        what_list = node_list + computer_list + groups_list

        export_function = export
        additional_kwargs = {}
        if parsed_args.zipfileu:
            export_function = export_zip
            additional_kwargs.update({"use_compression": False})
        elif parsed_args.zipfilec:
            export_function = export_zip
            additional_kwargs.update({"use_compression": True})
        try:
            export_function(what=what_list,
                   also_parents=not parsed_args.no_parents,
                   also_calc_outputs=not parsed_args.no_calc_outputs,
                   outfile=parsed_args.output_file,
                   overwrite=parsed_args.overwrite,**additional_kwargs)
        except IOError as e:
            print >> sys.stderr, "IOError: {}".format(e.message)
            sys.exit(1)

    def complete(self, subargs_idx, subargs):
        return ""

# Following code: to serialize the date directly when dumping into JSON.
# In our case, it is better to have a finer control on how to parse fields.

# def default_jsondump(data):
#    import datetime 
#
#    if isinstance(data, datetime.datetime):
#        return data.strftime('%Y-%m-%dT%H:%M:%S.%f%z')
#    
#    raise TypeError(repr(data) + " is not JSON serializable")
#with open('testout.json', 'w') as f:
#    json.dump({
#            'entries': serialized_entries,             
#        },
#        f,
#        default=default_jsondump)
