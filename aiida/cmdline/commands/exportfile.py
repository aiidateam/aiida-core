import sys

from aiida.cmdline.baseclass import VerdiCommand
from aiida.common.utils import load_django

def get_class_string(obj):
    """
    Return the string identifying the class of the object (module + object name,
    joined by dots).

    It works both for classes and for class instances.
    """
    import inspect
    if inspect.isclass(obj):
        return "{}.{}".format(
            obj.__module__,
            obj.__name__)     
    else:
        return "{}.{}".format(
            obj.__module__,
            obj.__class__.__name__)


def get_object_from_string(string):
    """
    Given a string identifying an object (as returned by the get_class_string
    method) load and return the actual object.
    """
    import importlib

    the_module, _, the_name = string.rpartition('.')
    
    return getattr(importlib.import_module(the_module), the_name)

def serialize_field(data):
    """
    Serialize a single field.
    
    :todo: Generalize such that it the proper function is selected also during
        import
    """
    import datetime

    if isinstance(data, datetime.datetime):
        return data.strftime('%Y-%m-%dT%H:%M:%S.%f%z')
    else:
        return data

def serialize_dict(datadict, remove_fields=[], rename_fields={}):
    """
    Serialize the dict using the serialize_field function to serialize
    each field.
    
    :param remove_fields: a list of strings. 
      If a field with key inside the remove_fields list is found, 
      it is removed from the dict.
    
    :param rename_fields: a dictionary in the format
      ``{"oldname": "newname"}``.

      If the "oldname" key is found, it is replaced with the
      "newname" string in the output dictionary.
    """
    # rename_fields.get(k,k): use the replacement if found in rename_fields,
    # otherwise use 'k' as the default value.
    return {rename_fields.get(k,k): serialize_field(v)
            for k, v in datadict.iteritems() if k not in remove_fields}

def get_all_fields_info():
    """
    Retrieve automatically the information on the fields and store them in a
    dictionary, that will be also stored in the export data, in the metadata
    file.
    """
    import importlib

    import django.db.models.fields as djf
    import django_extensions
    
    from aiida.djsite.db import models
    
    all_fields_info = {}
    
    # TODO: These will probably need to have a default value in the IMPORT!
    # TODO: maybe define this inside the Model!
    all_exclude_fields = {
        'django.contrib.auth.models.User': ['password', 'is_staff', 
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

    return all_fields_info

def export(what, also_parents = True, outfile = 'export_data.aiida.tar.gz'):     
    import json
    import tarfile
    import operator
    from collections import defaultdict
    
    from django.db.models import Q

    import aiida
    from aiida.djsite.db import models
    from aiida.orm import Node
    from aiida.common.folders import SandboxFolder

    EXPORT_VERSION = '0.1'
    
    all_fields_info = get_all_fields_info()
    
    entries_ids_to_add = defaultdict(list)
    for entry in what:
        entries_ids_to_add[get_class_string(entry)].append(entry.pk)
    
    # Initial query to fire the generation of the export data
    entries_to_add = {k: [Q(id__in=v)] for k, v
                      in entries_ids_to_add.iteritems()}

    if also_parents:
        # It is a defaultdict, it will provide an empty list
        given_nodes = entries_ids_to_add[get_class_string(models.DbNode)]
        
        if given_nodes:
            # Also add the parents (to any level) to the query
            entries_to_add[get_class_string(models.DbNode)].append(
                Q(children__in=given_nodes))

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
                    v['id']: serialize_dict(v, remove_fields=['id'])
                    for v in entryvalues
                    if v['id'] not in export_data[model_name]
                    }
            else:
                serialized = {
                    v['id']: serialize_dict(v, remove_fields=['id'])
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
    node_attributes = {n.pk: serialize_dict(n.attributes)
                   for n in all_nodes_query}
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
                    'export_data': export_data,
                    'links_uuid': links_uuid,
                    }, f)
    
        metadata = {
            'aiida_version': aiida.get_version(),
            'export_version': EXPORT_VERSION,
            'all_fields_info': all_fields_info,
            }

        with open(folder.get_abs_path('metadata.json'), 'w') as f:
            json.dump(metadata, f)
    
        print "STORING FILES..."
    
        for pk in all_nodes_pk:
            # Maybe we do not need to get the subclass, if it is too slow?
            node = Node.get_subclass_from_pk(pk)
            # ToDo: use the same function for sharding?
            
            sharded_uuid = '{}/{}/{}'.format(node.uuid[:2], node.uuid[2:4], 
                                             node.uuid[4:])
    
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
    
        with tarfile.open(outfile, "w:gz") as tar:
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
        
        print "FEATURE UNDER DEVELOPMENT!"

        if len(args) != 1:
            print "Pass a group name to export all entries in that group"
            sys.exit(1)
        
        

        ## TODO: parse cmdline parameters and pass them
        ## in particular: also_parents; what; outputfile
        export(what = models.DbNode.objects.filter(
            dbgroups__name=args[0]).distinct())

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
