import sys

from aiida.cmdline.baseclass import VerdiCommand
from aiida.common.utils import (export_shard_uuid,
                                get_class_string, get_object_from_string,
                                load_django)

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
                         [models.DbNode, models.DbAttribute, models.DbLink]])
    
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

def export(what, also_parents = True, also_calc_outputs = True,
           outfile = 'export_data.aiida.tar.gz', overwrite=False):     
    import json
    import os
    import tarfile
    import operator
    from collections import defaultdict
    
    from django.db.models import Q

    import aiida
    from aiida.djsite.db import models
    from aiida.orm import Node, Calculation
    from aiida.common.folders import SandboxFolder
    from aiida.common.exceptions import ModificationNotAllowed

    EXPORT_VERSION = '0.1'
    
    if not overwrite and os.path.exists(outfile):
        raise ModificationNotAllowed("The output file '{}' already "
                                     "exists".format(outfile))
    
    all_fields_info, unique_identifiers = get_all_fields_info()
    
    entries_ids_to_add = defaultdict(list)
    for entry in what:
        entries_ids_to_add[get_class_string(entry)].append(entry.pk)
    
    if also_parents:
        # It is a defaultdict, it will provide an empty list
        given_nodes = entries_ids_to_add[get_class_string(models.DbNode)]
        
        if given_nodes:
            # Also add the parents (to any level) to the query
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
    print "Exporting a total of {} db entries, of which {} nodes.".format(
        sum(len(model_data) for model_data in export_data.values()),
        len(all_nodes_pk))
    all_nodes_query = models.DbNode.objects.filter(pk__in=all_nodes_pk)

    ## ATTRIBUTES
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
    
    ######################################
    # Now I store
    ######################################    
    with SandboxFolder() as folder:
        # subfolder inside the export package
        nodesubfolder = folder.get_subfolder('nodes',create=True,
                                             reset_limit=True)
    
        print "STORING DATA..."
        
        with open(folder.get_abs_path('data.json'), 'w') as f:
            json.dump({
                    'node_attributes': node_attributes,
                    'node_attributes_conversion': node_attributes_conversion,
                    'export_data': export_data,
                    'links_uuid': links_uuid,
                    }, f)
    
        metadata = {
            'aiida_version': aiida.get_version(),
            'export_version': EXPORT_VERSION,
            'all_fields_info': all_fields_info,
            'unique_identifiers': unique_identifiers,
            }

        with open(folder.get_abs_path('metadata.json'), 'w') as f:
            json.dump(metadata, f)
    
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
            thisnodefolder.insert_path(src=node.repo_folder.abspath,
                                       dest_name='.')
    
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

    print "DONE."


class Export(VerdiCommand):
    """
    Export nodes and group of nodes

    This command allows to export to file nodes and group of nodes, for backup
    purposes or to share data with collaborators.
    """
    def run(self,*args):                    
        load_django()

        from aiida.djsite.db import models
        from aiida.orm import Group
        
        print "FEATURE UNDER DEVELOPMENT!"

        if len(args) != 1:
            print "Pass a group name to export all entries in that group"
            sys.exit(1)
        
        ## TODO: parse cmdline parameters and pass them
        ## in particular: also_parents; what; outputfile
        export(what = [_.dbnode for _ in set(Group.get(name=args[0]).nodes)])

        print "Default output file written."

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
