import sys

from aiida.cmdline.baseclass import VerdiCommand
from aiida.common.utils import load_django, export_shard_uuid, grouper

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
                    attributes_data,'%Y-%m-%dT%H:%M:%S.%f').replace(
                        tzinfo=pytz.utc)
            else:
                raise ValueError("Unknown convert_type '{}'".format(
                    conversion_data))

    return ret_data

def deserialize_field(k, v, fields_info, import_unique_ids_mappings,
                        foreign_ids_reverse_mappings):
    import datetime
    import pytz
    
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
            

def import_file(infile):     
    import json
    import os
    import tarfile
    from itertools import chain

    from django.db import transaction

    from aiida.orm import Node
    from aiida.common.folders import SandboxFolder, RepositoryFolder
    from aiida.djsite.db import models
    from aiida.common.utils import get_class_string, get_object_from_string
    

    # This is the export version expected by this function
    expected_export_version = '0.1'

    # The name of the subfolder in which the node files are stored
    nodes_export_subfolder = 'nodes'

    ################
    # EXTRACT DATA #
    ################
    # The sandbox has to remain open until the end
    with SandboxFolder() as folder:
        try:
            with tarfile.open(infile, "r:gz", format=tarfile.PAX_FORMAT) as tar:        
                print "READING DATA AND METADATA..."                
                tar.extract(path=folder.abspath,
                       member=tar.getmember('metadata.json'))
                tar.extract(path=folder.abspath,
                       member=tar.getmember('data.json'))
                
                try:
                    with open(folder.get_abs_path('metadata.json')) as f:
                        metadata = json.load(f)

                    with open(folder.get_abs_path('data.json')) as f:
                        data = json.load(f)
                except IOError as e:
                    raise ValueError(
                        "Unable to find the file {} in the import file".format(
                            e.filename))

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

                #print os.listdir(folder.abspath)
                #print os.listdir(folder.abspath + "/nodes")
        except tarfile.ReadError:
            raise ValueError("The input file format for import is not valid (1)")
    
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
        
        unknown_nodes = linked_nodes - db_nodes_uuid.union(
            import_nodes_uuid)
        
        if unknown_nodes:
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
                        )
                        ]
        
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
                    int(k): v[metadata['unique_identifiers'][model_name]] for k,v in 
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
                                        
                        relevant_db_entries = {getattr(n,unique_identifier): n
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
                    print "existing %s: %s (%s->%s)" % (model_name, unique_id,
                                                        import_entry_id,
                                                        existing_entry_id)
                    #print "  `-> WARNING: NO DUPLICITY CHECK DONE!"
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
                    print "STORING NEW NODE FILES..."
                    for o in objects_to_create:
                        
                        subfolder = folder.get_subfolder(os.path.join(
                            nodes_export_subfolder,export_shard_uuid(o.uuid)))
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
                #Now I have the PKs, print the info
                for unique_id, new_pk in just_saved.iteritems():
                    import_entry_id = import_entry_ids[unique_id]
                    foreign_ids_reverse_mappings[model_name][unique_id] = new_pk
            
                    print "NEW %s: %s (%s->%s)" % (model_name, unique_id, 
                                                   import_entry_id,
                                                   new_pk)

                # For DbNodes, we also have to store Attributes!
                if model_name == get_class_string(models.DbNode):
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

                        for k, v in deserialized_attributes.iteritems():
                            models.DbAttribute.set_value_for_node(
                                dbnode=new_pk, key=k, value=v,
                                with_transaction=False)
                        
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
                in_id = dbnode_reverse_mappings[link['input']]
                out_id = dbnode_reverse_mappings[link['output']]
                
                
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
    
            # Store new links
            if links_to_store:                
                print "   ({} new links...)".format(len(links_to_store))
                                
                models.DbLink.objects.bulk_create(links_to_store)
            else:
                print "   (0 new links...)"

    
    
    print "*** WARNING: MISSING EXISTING UUID CHECKS!!"
    print "*** WARNING: TODO: UPDATE IMPORT_DATA WITH DEFAULT VALUES! (e.g. calc status, user pwd, ...)"
    print "*** WARNING: TODO: PUT ALL NEW NODES IN A NEW GROUP!"


    print "DONE."


class Import(VerdiCommand):
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
            print "Pass a file name to import"
            sys.exit(1)
        

        ## TODO: parse cmdline parameters and pass them
        ## in particular: also_parents; what; outputfile
        import_file(args[0])

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
