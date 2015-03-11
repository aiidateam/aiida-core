# -*- coding: utf-8 -*-
import sys

from aiida.cmdline.baseclass import VerdiCommand
from aiida.common.utils import (export_shard_uuid,
                                get_class_string, get_object_from_string)
from aiida import load_dbenv

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.0"
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
                (ret_dict[rename_fields.get(k,k)],
                 conversions[rename_fields.get(k,k)]) = serialize_field(
                    data=v, track_conversion=track_conversion)
            else:
                ret_dict[rename_fields.get(k,k)] = serialize_field(
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
                                        djf.BooleanField,djf.NullBooleanField,
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

def export_tree(what, folder = None, also_parents = True,
                also_calc_outputs = True, silent = False):
    """
    Export the DB entries passed in the 'what' list to a file tree.
    
    :todo: limit the export to finished or failed calculations.
    
    :param what: a list of Django database entries; they can belong to different
      models.
    :param folder: a :py:class:`Folder <aiida.common.folders.Folder>` object
    :param also_parents: if True, also all the parents are stored (from th
      DbPath transitive closure table)
    :param also_calc_outputs: if True, any output of a calculation is also exported
    :param silent: suppress debug prints
    """
    import json
    import os
    import operator
    from collections import defaultdict
    
    from django.db.models import Q

    import aiida
    from aiida.djsite.db import models
    from aiida.orm import Node, Calculation
    from aiida.common.folders import SandboxFolder

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
    

    ############################################################
    ##### Start automatic recursive export data generation #####
    ############################################################
    if not silent:
        print "STORING DATABASE ENTRIES..."
    export_data = {}   
    while entries_to_add:
        new_entries_to_add = {}
        for model_name, querysets in entries_to_add.iteritems():
            Model = get_object_from_string(model_name)

            # I do a filter with an 'OR' (|) operator between all the possible
            # queries. querysets, if present, should always have at least one
            # element, so for the time being I do not check if it is an empty
            # list (TODO: check, otherwise I add the whole DB I believe).
            dbentries = Model.objects.filter(
                reduce(operator.or_, querysets)).distinct()
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
    all_nodes_pk = export_data.get(get_class_string(models.DbNode),{}).keys()
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
    #all_nodes_query = models.DbNode.objects.filter(pk__in=all_nodes_pk)
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
        serialize_dict(l, rename_fields= {
            'input__uuid': 'input',
            'output__uuid': 'output'})
         for l in linksquery.values(
              'input__uuid', 'output__uuid', 'label')]

    if not silent:
        print "STORING GROUP ELEMENTS..."
    groups_uuid = {g.uuid: list(g.dbnodes.values_list('uuid', flat=True))
                   for g in groups_entries}

    if not silent:
        print groups_uuid
    
    ######################################
    # Now I store
    ######################################    
    # subfolder inside the export package
    nodesubfolder = folder.get_subfolder('nodes',create=True,
                                         reset_limit=True)

    if not silent:
        print "STORING DATA..."
    
    with open(folder.get_abs_path('data.json'), 'w') as f:
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

    with open(folder.get_abs_path('metadata.json'), 'w') as f:
        json.dump(metadata, f)

    if silent is not True:
        print "STORING FILES..."

    for pk in all_nodes_pk:
        # Maybe we do not need to get the subclass, if it is too slow?
        node = Node.get_subclass_from_pk(pk)

        sharded_uuid = export_shard_uuid(node.uuid)

        # Important to set create=False, otherwise creates
        # twice a subfolder. Maybe this is a bug of insert_path??

        thisnodefolder = nodesubfolder.get_subfolder(
            sharded_uuid, create=False,
            reset_limit=True)
        # In this way, I copy the content of the folder, and not the folder
        # itself
        thisnodefolder.insert_path(src=node._repository_folder.abspath,
                                   dest_name='.')

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
    from aiida.common.folders import SandboxFolder

    if not overwrite and os.path.exists(outfile):
        raise IOError("The output file '{}' already "
                      "exists".format(outfile))

    folder = SandboxFolder()
    export_tree(what, folder=folder, silent=silent, **kwargs)

    if not silent:
        print "COMPRESSING..."

    # PAX_FORMAT: virtually no limitations, better support for unicode
    #   characters
    # dereference=True: at the moment, we should not have any symlink or
    #   hardlink in the AiiDA repository; therefore, do not store symlinks
    #   or hardlinks, but store the actual destinations.
    #   This also simplifies the checks on import.
    with tarfile.open(outfile, "w:gz", format=tarfile.PAX_FORMAT,
                      dereference=True) as tar:
        tar.add(folder.abspath, arcname="")

#        import shutil
#        shutil.make_archive(outfile, 'zip', folder.abspath)#, base_dir='aiida')

    if not silent:
        print "DONE."

class Export(VerdiCommand):
    """
    Export nodes and group of nodes

    This command allows to export to file nodes and group of nodes, for backup
    purposes or to share data with collaborators.
    Call this command with the '-h' option for some documentation of its usage.
    """
    def run(self,*args):                    
        load_dbenv()

        import argparse

        from aiida.orm import Group
        from aiida.common.exceptions import NotExistent
        from aiida.djsite.db import models
        from aiida.cmdline.commands.group import get_group_type_mapping
        
        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Export data from the DB.')
        parser.add_argument('-c', '--computers', nargs='+', type=int, metavar="PK",
                            help="Export the given computers")
        parser.add_argument('-n', '--nodes', nargs='+', type=int, metavar="PK",
                            help="Export the given nodes")
        parser.add_argument('-g', '--groups', nargs='+', metavar="GROUPNAME",
                            help="Export all nodes in the given user-defined groups",
                            type=str)
        parser.add_argument('-P', '--no-parents',
                            dest='no_parents',action='store_true',
                            help="Store only the nodes that are explicitly given, without exporting the parents")        
        parser.set_defaults(no_parents=False)
        parser.add_argument('-O', '--no-calc-outputs',
                            dest='no_calc_outputs',action='store_true',
                            help="If a calculation is included in the list of nodes to export, do not export its outputs")
        parser.set_defaults(no_calc_outputs=False)
        parser.add_argument('-y', '--overwrite',
                            dest='overwrite',action='store_true',
                            help="Overwrite the output file, if it exists")       
        parser.set_defaults(overwrite=False)
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
                name, sep, typestr = group_name.rpartition(':')
                if not sep:
                    name = typestr
                    typestr = ""
                if typestr:
                    try:
                        internal_type_string = get_group_type_mapping()[typestr]
                    except KeyError:
                        print >> sys.stderr, "Invalid group type '{}'. Valid group types are:".format(typestr)
                        print >> sys.stderr, ",".join(sorted(
                                get_group_type_mapping().keys()))
                        sys.exit(1)
                else:
                    internal_type_string=""
                
                try:
                    group = Group.get(name=name,
                                      type_string=internal_type_string)
                except NotExistent:
                    if typestr:
                        print >> sys.stderr, (
                            "No group of type '{}' with name '{}' "
                            "found. Stopping.".format(typestr, name))
                    else:
                        print >> sys.stderr, (
                            "No user-defined group with name '{}' "
                            "found. Stopping.".format(name))
                    sys.exit(1)
                node_pk_list += group.dbgroup.dbnodes.values_list('pk',flat=True)
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

        # TODO: Export of groups not implemented yet!
        what_list = node_list + computer_list + groups_list

        try:
            export(what = what_list, 
                   also_parents = not parsed_args.no_parents,
                   also_calc_outputs = not parsed_args.no_calc_outputs,
                   outfile=parsed_args.output_file,
                   overwrite=parsed_args.overwrite)
        except IOError as e:
            print >> sys.stderr, e.message
            sys.exit(1)

    def complete(self,subargs_idx, subargs):
        return ""

# Following code: to serialize the date directly when dumping into JSON.
# In our case, it is better to have a finer control on how to parse fields.

#def default_jsondump(data):
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
