# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=protected-access,fixme,too-many-arguments,too-many-locals,too-many-statements,too-many-branches,too-many-nested-blocks
""" Django-specific import of AiiDA entities """

from distutils.version import StrictVersion
import logging
import os
import tarfile
import zipfile
from itertools import chain

from aiida.common import timezone, json
from aiida.common.folders import SandboxFolder, RepositoryFolder
from aiida.common.links import LinkType, validate_link_label
from aiida.common.log import override_log_formatter
from aiida.common.utils import grouper, get_object_from_string
from aiida.manage.configuration import get_config_option
from aiida.orm.utils._repository import Repository
from aiida.orm import QueryBuilder, Node, Group, ImportGroup

from aiida.tools.importexport.common import exceptions, get_progress_bar, close_progress_bar
from aiida.tools.importexport.common.archive import extract_tree, extract_tar, extract_zip
from aiida.tools.importexport.common.config import DUPL_SUFFIX, EXPORT_VERSION, NODES_EXPORT_SUBFOLDER, BAR_FORMAT
from aiida.tools.importexport.common.config import (
    NODE_ENTITY_NAME, GROUP_ENTITY_NAME, COMPUTER_ENTITY_NAME, USER_ENTITY_NAME, LOG_ENTITY_NAME, COMMENT_ENTITY_NAME
)
from aiida.tools.importexport.common.config import entity_names_to_signatures
from aiida.tools.importexport.common.utils import export_shard_uuid
from aiida.tools.importexport.dbimport.utils import (
    deserialize_field, merge_comment, merge_extras, start_summary, result_summary, IMPORT_LOGGER
)


@override_log_formatter('%(message)s')
def import_data_dj(
    in_path,
    group=None,
    ignore_unknown_nodes=False,
    extras_mode_existing='kcl',
    extras_mode_new='import',
    comment_mode='newest',
    silent=False,
    **kwargs
):
    """Import exported AiiDA archive to the AiiDA database and repository.

    Specific for the Django backend.
    If ``in_path`` is a folder, calls extract_tree; otherwise, tries to detect the compression format
    (zip, tar.gz, tar.bz2, ...) and calls the correct function.

    :param in_path: the path to a file or folder that can be imported in AiiDA.
    :type in_path: str

    :param group: Group wherein all imported Nodes will be placed.
    :type group: :py:class:`~aiida.orm.groups.Group`

    :param extras_mode_existing: 3 letter code that will identify what to do with the extras import.
        The first letter acts on extras that are present in the original node and not present in the imported node.
        Can be either:
        'k' (keep it) or
        'n' (do not keep it).
        The second letter acts on the imported extras that are not present in the original node.
        Can be either:
        'c' (create it) or
        'n' (do not create it).
        The third letter defines what to do in case of a name collision.
        Can be either:
        'l' (leave the old value),
        'u' (update with a new value),
        'd' (delete the extra), or
        'a' (ask what to do if the content is different).
    :type extras_mode_existing: str

    :param extras_mode_new: 'import' to import extras of new nodes or 'none' to ignore them.
    :type extras_mode_new: str

    :param comment_mode: Comment import modes (when same UUIDs are found).
        Can be either:
        'newest' (will keep the Comment with the most recent modification time (mtime)) or
        'overwrite' (will overwrite existing Comments with the ones from the import file).
    :type comment_mode: str

    :param silent: suppress progress bar and summary.
    :type silent: bool

    :return: New and existing Nodes and Links.
    :rtype: dict

    :raises `~aiida.tools.importexport.common.exceptions.ImportValidationError`: if parameters or the contents of
        `metadata.json` or `data.json` can not be validated.
    :raises `~aiida.tools.importexport.common.exceptions.CorruptArchive`: if the provided archive at ``in_path`` is
        corrupted.
    :raises `~aiida.tools.importexport.common.exceptions.IncompatibleArchiveVersionError`: if the provided archive's
        export version is not equal to the export version of AiiDA at the moment of import.
    :raises `~aiida.tools.importexport.common.exceptions.ArchiveImportError`: if there are any internal errors when
        importing.
    :raises `~aiida.tools.importexport.common.exceptions.ImportUniquenessError`: if a new unique entity can not be
        created.
    """
    from django.db import transaction  # pylint: disable=import-error,no-name-in-module
    from aiida.backends.djsite.db import models

    # This is the export version expected by this function
    expected_export_version = StrictVersion(EXPORT_VERSION)

    # The returned dictionary with new and existing nodes and links
    ret_dict = {}

    # Initial check(s)
    if group:
        if not isinstance(group, Group):
            raise exceptions.ImportValidationError('group must be a Group entity')
        elif not group.is_stored:
            group.store()

    if silent:
        logging.disable(level=logging.CRITICAL)

    ################
    # EXTRACT DATA #
    ################
    # The sandbox has to remain open until the end
    with SandboxFolder() as folder:
        if os.path.isdir(in_path):
            extract_tree(in_path, folder)
        else:
            if tarfile.is_tarfile(in_path):
                extract_tar(in_path, folder, silent=silent, nodes_export_subfolder=NODES_EXPORT_SUBFOLDER, **kwargs)
            elif zipfile.is_zipfile(in_path):
                extract_zip(in_path, folder, silent=silent, nodes_export_subfolder=NODES_EXPORT_SUBFOLDER, **kwargs)
            else:
                raise exceptions.ImportValidationError(
                    'Unable to detect the input file format, it is neither a '
                    'tar file, nor a (possibly compressed) zip file.'
                )

        if not folder.get_content_list():
            raise exceptions.CorruptArchive('The provided file/folder ({}) is empty'.format(in_path))
        try:
            with open(folder.get_abs_path('metadata.json'), 'r', encoding='utf8') as fhandle:
                metadata = json.load(fhandle)

            with open(folder.get_abs_path('data.json'), 'r', encoding='utf8') as fhandle:
                data = json.load(fhandle)
        except IOError as error:
            raise exceptions.CorruptArchive(
                'Unable to find the file {} in the import file or folder'.format(error.filename)
            )

        ######################
        # PRELIMINARY CHECKS #
        ######################
        export_version = StrictVersion(str(metadata['export_version']))
        if export_version != expected_export_version:
            msg = 'Export file version is {}, can import only version {}'\
                    .format(metadata['export_version'], expected_export_version)
            if export_version < expected_export_version:
                msg += "\nUse 'verdi export migrate' to update this export file."
            else:
                msg += '\nUpdate your AiiDA version in order to import this file.'

            raise exceptions.IncompatibleArchiveVersionError(msg)

        start_summary(in_path, comment_mode, extras_mode_new, extras_mode_existing)

        ##########################################################################
        # CREATE UUID REVERSE TABLES AND CHECK IF I HAVE ALL NODES FOR THE LINKS #
        ##########################################################################
        linked_nodes = set(chain.from_iterable((l['input'], l['output']) for l in data['links_uuid']))
        group_nodes = set(chain.from_iterable(data['groups_uuid'].values()))

        if NODE_ENTITY_NAME in data['export_data']:
            import_nodes_uuid = set(v['uuid'] for v in data['export_data'][NODE_ENTITY_NAME].values())
        else:
            import_nodes_uuid = set()

        # the combined set of linked_nodes and group_nodes was obtained from looking at all the links
        # the set of import_nodes_uuid was received from the stuff actually referred to in export_data
        unknown_nodes = linked_nodes.union(group_nodes) - import_nodes_uuid

        if unknown_nodes and not ignore_unknown_nodes:
            raise exceptions.DanglingLinkError(
                'The import file refers to {} nodes with unknown UUID, therefore it cannot be imported. Either first '
                'import the unknown nodes, or export also the parents when exporting. The unknown UUIDs are:\n'
                ''.format(len(unknown_nodes)) + '\n'.join('* {}'.format(uuid) for uuid in unknown_nodes)
            )

        ###################################
        # DOUBLE-CHECK MODEL DEPENDENCIES #
        ###################################
        # The entity import order. It is defined by the database model relationships.
        model_order = (
            USER_ENTITY_NAME, COMPUTER_ENTITY_NAME, NODE_ENTITY_NAME, GROUP_ENTITY_NAME, LOG_ENTITY_NAME,
            COMMENT_ENTITY_NAME
        )

        for import_field_name in metadata['all_fields_info']:
            if import_field_name not in model_order:
                raise exceptions.ImportValidationError(
                    "You are trying to import an unknown model '{}'!".format(import_field_name)
                )

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
                    raise exceptions.ArchiveImportError(
                        'Model {} requires {} but would be loaded first; stopping...'.format(model_name, dependency)
                    )

        ###################################################
        # CREATE IMPORT DATA DIRECT UNIQUE_FIELD MAPPINGS #
        ###################################################
        import_unique_ids_mappings = {}
        for model_name, import_data in data['export_data'].items():
            if model_name in metadata['unique_identifiers']:
                # I have to reconvert the pk to integer
                import_unique_ids_mappings[model_name] = {
                    int(k): v[metadata['unique_identifiers'][model_name]] for k, v in import_data.items()
                }

        ###############
        # IMPORT DATA #
        ###############
        # DO ALL WITH A TRANSACTION
        # !!! EXCEPT: Creating final import Group containing all Nodes in archive

        # batch size for bulk create operations
        batch_size = get_config_option('db.batch_size')

        with transaction.atomic():
            foreign_ids_reverse_mappings = {}
            new_entries = {}
            existing_entries = {}

            IMPORT_LOGGER.debug('GENERATING LIST OF DATA...')

            # Instantiate progress bar
            progress_bar = get_progress_bar(total=1, leave=False, disable=silent)
            pbar_base_str = 'Generating list of data - '

            # Get total entities from data.json
            # To be used with progress bar
            number_of_entities = 0

            # I first generate the list of data
            for model_name in model_order:
                cls_signature = entity_names_to_signatures[model_name]
                model = get_object_from_string(cls_signature)
                fields_info = metadata['all_fields_info'].get(model_name, {})
                unique_identifier = metadata['unique_identifiers'].get(model_name, None)

                new_entries[model_name] = {}
                existing_entries[model_name] = {}

                foreign_ids_reverse_mappings[model_name] = {}

                # Not necessarily all models are exported
                if model_name in data['export_data']:

                    IMPORT_LOGGER.debug('  %s...', model_name)

                    progress_bar.set_description_str(pbar_base_str + model_name, refresh=False)
                    number_of_entities += len(data['export_data'][model_name])

                    # skip nodes that are already present in the DB
                    if unique_identifier is not None:
                        import_unique_ids = set(v[unique_identifier] for v in data['export_data'][model_name].values())

                        relevant_db_entries = {}
                        if import_unique_ids:
                            relevant_db_entries_result = model.objects.filter(
                                **{'{}__in'.format(unique_identifier): import_unique_ids}
                            )

                            # Note: UUIDs need to be converted to strings
                            if relevant_db_entries_result.count():
                                progress_bar = get_progress_bar(
                                    total=relevant_db_entries_result.count(), disable=silent
                                )
                                # Imitating QueryBuilder.iterall() with default settings
                                for object_ in relevant_db_entries_result.iterator(chunk_size=100):
                                    progress_bar.update()
                                    relevant_db_entries.update({str(getattr(object_, unique_identifier)): object_})

                        foreign_ids_reverse_mappings[model_name] = {k: v.pk for k, v in relevant_db_entries.items()}

                        IMPORT_LOGGER.debug('    GOING THROUGH ARCHIVE...')

                        imported_comp_names = set()
                        for key, value in data['export_data'][model_name].items():
                            if model_name == GROUP_ENTITY_NAME:
                                # Check if there is already a group with the same name
                                dupl_counter = 0
                                orig_label = value['label']
                                while model.objects.filter(label=value['label']):
                                    value['label'] = orig_label + DUPL_SUFFIX.format(dupl_counter)
                                    dupl_counter += 1
                                    if dupl_counter == 100:
                                        raise exceptions.ImportUniquenessError(
                                            'A group of that label ( {} ) already exists and I could not create a new '
                                            'one'.format(orig_label)
                                        )

                            elif model_name == COMPUTER_ENTITY_NAME:
                                # Check if there is already a computer with the same name in the database
                                dupl = (
                                    model.objects.filter(name=value['name']) or value['name'] in imported_comp_names
                                )
                                orig_name = value['name']
                                dupl_counter = 0
                                while dupl:
                                    # Rename the new computer
                                    value['name'] = orig_name + DUPL_SUFFIX.format(dupl_counter)
                                    dupl = (
                                        model.objects.filter(name=value['name']) or value['name'] in imported_comp_names
                                    )
                                    dupl_counter += 1
                                    if dupl_counter == 100:
                                        raise exceptions.ImportUniquenessError(
                                            'A computer of that name ( {} ) already exists and I could not create a '
                                            'new one'.format(orig_name)
                                        )

                                imported_comp_names.add(value['name'])

                            if value[unique_identifier] in relevant_db_entries:
                                # Already in DB
                                existing_entries[model_name][key] = value
                            else:
                                # To be added
                                new_entries[model_name][key] = value
                    else:
                        new_entries[model_name] = data['export_data'][model_name]

            # Reset for import
            progress_bar = get_progress_bar(total=number_of_entities, disable=silent)

            # I import data from the given model
            for model_name in model_order:
                # Progress bar initialization - Model
                pbar_base_str = '{}s - '.format(model_name)
                progress_bar.set_description_str(pbar_base_str + 'Initializing', refresh=True)

                cls_signature = entity_names_to_signatures[model_name]
                model = get_object_from_string(cls_signature)
                fields_info = metadata['all_fields_info'].get(model_name, {})
                unique_identifier = metadata['unique_identifiers'].get(model_name, None)

                # EXISTING ENTRIES
                if existing_entries[model_name]:
                    # Progress bar update - Model
                    progress_bar.set_description_str(
                        pbar_base_str + '{} existing entries'.format(len(existing_entries[model_name])), refresh=True
                    )

                for import_entry_pk, entry_data in existing_entries[model_name].items():
                    unique_id = entry_data[unique_identifier]
                    existing_entry_id = foreign_ids_reverse_mappings[model_name][unique_id]
                    import_data = dict(
                        deserialize_field(
                            k,
                            v,
                            fields_info=fields_info,
                            import_unique_ids_mappings=import_unique_ids_mappings,
                            foreign_ids_reverse_mappings=foreign_ids_reverse_mappings
                        ) for k, v in entry_data.items()
                    )
                    # TODO COMPARE, AND COMPARE ATTRIBUTES

                    if model is models.DbComment:
                        new_entry_uuid = merge_comment(import_data, comment_mode)
                        if new_entry_uuid is not None:
                            entry_data[unique_identifier] = new_entry_uuid
                            new_entries[model_name][import_entry_pk] = entry_data

                    if model_name not in ret_dict:
                        ret_dict[model_name] = {'new': [], 'existing': []}
                    ret_dict[model_name]['existing'].append((import_entry_pk, existing_entry_id))
                    IMPORT_LOGGER.debug(
                        'Existing %s: %s (%s->%s)', model_name, unique_id, import_entry_pk, existing_entry_id
                    )
                    # print('  `-> WARNING: NO DUPLICITY CHECK DONE!')
                    # CHECK ALSO FILES!

                # Store all objects for this model in a list, and store them all in once at the end.
                objects_to_create = []
                # This is needed later to associate the import entry with the new pk
                import_new_entry_pks = {}

                # NEW ENTRIES
                if new_entries[model_name]:
                    # Progress bar update - Model
                    progress_bar.set_description_str(
                        pbar_base_str + '{} new entries'.format(len(new_entries[model_name])), refresh=True
                    )

                for import_entry_pk, entry_data in new_entries[model_name].items():
                    unique_id = entry_data[unique_identifier]
                    import_data = dict(
                        deserialize_field(
                            k,
                            v,
                            fields_info=fields_info,
                            import_unique_ids_mappings=import_unique_ids_mappings,
                            foreign_ids_reverse_mappings=foreign_ids_reverse_mappings
                        ) for k, v in entry_data.items()
                    )

                    objects_to_create.append(model(**import_data))
                    import_new_entry_pks[unique_id] = import_entry_pk

                if model_name == NODE_ENTITY_NAME:
                    IMPORT_LOGGER.debug('STORING NEW NODE REPOSITORY FILES...')

                    # NEW NODES
                    for object_ in objects_to_create:
                        import_entry_uuid = object_.uuid
                        import_entry_pk = import_new_entry_pks[import_entry_uuid]

                        # Progress bar initialization - Node
                        progress_bar.update()
                        pbar_node_base_str = pbar_base_str + 'UUID={} - '.format(import_entry_uuid.split('-')[0])

                        # Before storing entries in the DB, I store the files (if these are nodes).
                        # Note: only for new entries!
                        subfolder = folder.get_subfolder(
                            os.path.join(NODES_EXPORT_SUBFOLDER, export_shard_uuid(import_entry_uuid))
                        )
                        if not subfolder.exists():
                            raise exceptions.CorruptArchive(
                                'Unable to find the repository folder for Node with UUID={} in the exported '
                                'file'.format(import_entry_uuid)
                            )
                        destdir = RepositoryFolder(section=Repository._section_name, uuid=import_entry_uuid)
                        # Replace the folder, possibly destroying existing previous folders, and move the files
                        # (faster if we are on the same filesystem, and in any case the source is a SandboxFolder)
                        progress_bar.set_description_str(pbar_node_base_str + 'Repository', refresh=True)
                        destdir.replace_with_folder(subfolder.abspath, move=True, overwrite=True)

                        # For DbNodes, we also have to store its attributes
                        IMPORT_LOGGER.debug('STORING NEW NODE ATTRIBUTES...')
                        progress_bar.set_description_str(pbar_node_base_str + 'Attributes', refresh=True)

                        # Get attributes from import file
                        try:
                            object_.attributes = data['node_attributes'][str(import_entry_pk)]
                        except KeyError:
                            raise exceptions.CorruptArchive(
                                'Unable to find attribute info for Node with UUID={}'.format(import_entry_uuid)
                            )

                        # For DbNodes, we also have to store its extras
                        if extras_mode_new == 'import':
                            IMPORT_LOGGER.debug('STORING NEW NODE EXTRAS...')
                            progress_bar.set_description_str(pbar_node_base_str + 'Extras', refresh=True)

                            # Get extras from import file
                            try:
                                extras = data['node_extras'][str(import_entry_pk)]
                            except KeyError:
                                raise exceptions.CorruptArchive(
                                    'Unable to find extra info for Node with UUID={}'.format(import_entry_uuid)
                                )
                            # TODO: remove when aiida extras will be moved somewhere else
                            # from here
                            extras = {key: value for key, value in extras.items() if not key.startswith('_aiida_')}
                            if object_.node_type.endswith('code.Code.'):
                                extras = {key: value for key, value in extras.items() if not key == 'hidden'}
                            # till here
                            object_.extras = extras
                        elif extras_mode_new == 'none':
                            IMPORT_LOGGER.debug('SKIPPING NEW NODE EXTRAS...')
                        else:
                            raise exceptions.ImportValidationError(
                                "Unknown extras_mode_new value: {}, should be either 'import' or 'none'"
                                ''.format(extras_mode_new)
                            )

                    # EXISTING NODES (Extras)
                    # For the existing nodes that are also in the imported list we also update their extras if necessary
                    IMPORT_LOGGER.debug('UPDATING EXISTING NODE EXTRAS...')

                    import_existing_entry_pks = {
                        entry_data[unique_identifier]: import_entry_pk
                        for import_entry_pk, entry_data in existing_entries[model_name].items()
                    }
                    for node in models.DbNode.objects.filter(uuid__in=import_existing_entry_pks).all():  # pylint: disable=no-member
                        import_entry_uuid = str(node.uuid)
                        import_entry_pk = import_existing_entry_pks[import_entry_uuid]

                        # Progress bar initialization - Node
                        pbar_node_base_str = pbar_base_str + 'UUID={} - '.format(import_entry_uuid.split('-')[0])
                        progress_bar.set_description_str(pbar_node_base_str + 'Extras', refresh=False)
                        progress_bar.update()

                        # Get extras from import file
                        try:
                            extras = data['node_extras'][str(import_entry_pk)]
                        except KeyError:
                            raise exceptions.CorruptArchive(
                                'Unable to find extra info for Node with UUID={}'.format(import_entry_uuid)
                            )

                        old_extras = node.extras.copy()
                        # TODO: remove when aiida extras will be moved somewhere else
                        # from here
                        extras = {key: value for key, value in extras.items() if not key.startswith('_aiida_')}
                        if node.node_type.endswith('code.Code.'):
                            extras = {key: value for key, value in extras.items() if not key == 'hidden'}
                        # till here
                        new_extras = merge_extras(node.extras, extras, extras_mode_existing)

                        if new_extras != old_extras:
                            # Already saving existing node here to update its extras
                            node.extras = new_extras
                            node.save()

                else:
                    # Update progress bar with new non-Node entries
                    progress_bar.update(n=len(existing_entries[model_name]) + len(new_entries[model_name]))

                progress_bar.set_description_str(pbar_base_str + 'Storing', refresh=True)

                # If there is an mtime in the field, disable the automatic update
                # to keep the mtime that we have set here
                if 'mtime' in [field.name for field in model._meta.local_fields]:
                    with models.suppress_auto_now([(model, ['mtime'])]):
                        # Store them all in once; however, the PK are not set in this way...
                        model.objects.bulk_create(objects_to_create, batch_size=batch_size)
                else:
                    model.objects.bulk_create(objects_to_create, batch_size=batch_size)

                # Get back the just-saved entries
                just_saved_queryset = model.objects.filter(
                    **{
                        '{}__in'.format(unique_identifier): import_new_entry_pks.keys()
                    }
                ).values_list(unique_identifier, 'pk')
                # note: convert uuids from type UUID to strings
                just_saved = {str(key): value for key, value in just_saved_queryset}

                # Now I have the PKs, print the info
                # Moreover, add newly created Nodes to foreign_ids_reverse_mappings
                for unique_id, new_pk in just_saved.items():
                    import_entry_pk = import_new_entry_pks[unique_id]
                    foreign_ids_reverse_mappings[model_name][unique_id] = new_pk
                    if model_name not in ret_dict:
                        ret_dict[model_name] = {'new': [], 'existing': []}
                    ret_dict[model_name]['new'].append((import_entry_pk, new_pk))

                    IMPORT_LOGGER.debug('New %s: %s (%s->%s)' % (model_name, unique_id, import_entry_pk, new_pk))

            IMPORT_LOGGER.debug('STORING NODE LINKS...')
            import_links = data['links_uuid']
            links_to_store = []

            # Needed, since QueryBuilder does not yet work for recently saved Nodes
            existing_links_raw = models.DbLink.objects.all().values_list('input', 'output', 'label', 'type')
            existing_links = {(l[0], l[1], l[2], l[3]) for l in existing_links_raw}
            existing_outgoing_unique = {(l[0], l[3]) for l in existing_links_raw}
            existing_outgoing_unique_pair = {(l[0], l[2], l[3]) for l in existing_links_raw}
            existing_incoming_unique = {(l[1], l[3]) for l in existing_links_raw}
            existing_incoming_unique_pair = {(l[1], l[2], l[3]) for l in existing_links_raw}

            calculation_node_types = 'process.calculation.'
            workflow_node_types = 'process.workflow.'
            data_node_types = 'data.'

            link_mapping = {
                LinkType.CALL_CALC: (workflow_node_types, calculation_node_types, 'unique_triple', 'unique'),
                LinkType.CALL_WORK: (workflow_node_types, workflow_node_types, 'unique_triple', 'unique'),
                LinkType.CREATE: (calculation_node_types, data_node_types, 'unique_pair', 'unique'),
                LinkType.INPUT_CALC: (data_node_types, calculation_node_types, 'unique_triple', 'unique_pair'),
                LinkType.INPUT_WORK: (data_node_types, workflow_node_types, 'unique_triple', 'unique_pair'),
                LinkType.RETURN: (workflow_node_types, data_node_types, 'unique_pair', 'unique_triple'),
            }

            if import_links:
                progress_bar = get_progress_bar(total=len(import_links), disable=silent)
                pbar_base_str = 'Links - '

            for link in import_links:
                # Check for dangling Links within the, supposed, self-consistent archive
                progress_bar.set_description_str(pbar_base_str + 'label={}'.format(link['label']), refresh=False)
                progress_bar.update()

                try:
                    in_id = foreign_ids_reverse_mappings[NODE_ENTITY_NAME][link['input']]
                    out_id = foreign_ids_reverse_mappings[NODE_ENTITY_NAME][link['output']]
                except KeyError:
                    if ignore_unknown_nodes:
                        continue
                    raise exceptions.ImportValidationError(
                        'Trying to create a link with one or both unknown nodes, stopping (in_uuid={}, out_uuid={}, '
                        'label={}, type={})'.format(link['input'], link['output'], link['label'], link['type'])
                    )

                # Check if link already exists, skip if it does
                # This is equivalent to an existing triple link (i.e. unique_triple from below)
                if (in_id, out_id, link['label'], link['type']) in existing_links:
                    continue

                # Since backend specific Links (DbLink) are not validated upon creation, we will now validate them.
                try:
                    validate_link_label(link['label'])
                except ValueError as why:
                    raise exceptions.ImportValidationError('Error during Link label validation: {}'.format(why))

                source = models.DbNode.objects.get(id=in_id)
                target = models.DbNode.objects.get(id=out_id)

                if source.uuid == target.uuid:
                    raise exceptions.ImportValidationError('Cannot add a link to oneself')

                link_type = LinkType(link['type'])
                type_source, type_target, outdegree, indegree = link_mapping[link_type]

                # Check if source Node is a valid type
                if not source.node_type.startswith(type_source):
                    raise exceptions.ImportValidationError(
                        'Cannot add a {} link from {} to {}'.format(link_type, source.node_type, target.node_type)
                    )

                # Check if target Node is a valid type
                if not target.node_type.startswith(type_target):
                    raise exceptions.ImportValidationError(
                        'Cannot add a {} link from {} to {}'.format(link_type, source.node_type, target.node_type)
                    )

                # If the outdegree is `unique` there cannot already be any other outgoing link of that type,
                # i.e., the source Node may not have a LinkType of current LinkType, going out, existing already.
                if outdegree == 'unique' and (in_id, link['type']) in existing_outgoing_unique:
                    raise exceptions.ImportValidationError(
                        'Node<{}> already has an outgoing {} link'.format(source.uuid, link_type)
                    )

                # If the outdegree is `unique_pair`,
                # then the link labels for outgoing links of this type should be unique,
                # i.e., the source Node may not have a LinkType of current LinkType, going out,
                # that also has the current Link label, existing already.
                elif outdegree == 'unique_pair' and \
                (in_id, link['label'], link['type']) in existing_outgoing_unique_pair:
                    raise exceptions.ImportValidationError(
                        'Node<{}> already has an outgoing {} link with label "{}"'.format(
                            source.uuid, link_type, link['label']
                        )
                    )

                # If the indegree is `unique` there cannot already be any other incoming links of that type,
                # i.e., the target Node may not have a LinkType of current LinkType, coming in, existing already.
                if indegree == 'unique' and (out_id, link['type']) in existing_incoming_unique:
                    raise exceptions.ImportValidationError(
                        'Node<{}> already has an incoming {} link'.format(target.uuid, link_type)
                    )

                # If the indegree is `unique_pair`,
                # then the link labels for incoming links of this type should be unique,
                # i.e., the target Node may not have a LinkType of current LinkType, coming in
                # that also has the current Link label, existing already.
                elif indegree == 'unique_pair' and \
                (out_id, link['label'], link['type']) in existing_incoming_unique_pair:
                    raise exceptions.ImportValidationError(
                        'Node<{}> already has an incoming {} link with label "{}"'.format(
                            target.uuid, link_type, link['label']
                        )
                    )

                # New link
                links_to_store.append(
                    models.DbLink(input_id=in_id, output_id=out_id, label=link['label'], type=link['type'])
                )
                if 'Link' not in ret_dict:
                    ret_dict['Link'] = {'new': []}
                ret_dict['Link']['new'].append((in_id, out_id))

                # Add new Link to sets of existing Links 'input PK', 'output PK', 'label', 'type'
                existing_links.add((in_id, out_id, link['label'], link['type']))
                existing_outgoing_unique.add((in_id, link['type']))
                existing_outgoing_unique_pair.add((in_id, link['label'], link['type']))
                existing_incoming_unique.add((out_id, link['type']))
                existing_incoming_unique_pair.add((out_id, link['label'], link['type']))

            # Store new links
            if links_to_store:
                IMPORT_LOGGER.debug('   (%d new links...)', len(links_to_store))

                models.DbLink.objects.bulk_create(links_to_store, batch_size=batch_size)
            else:
                IMPORT_LOGGER.debug('   (0 new links...)')

            IMPORT_LOGGER.debug('STORING GROUP ELEMENTS...')

            import_groups = data['groups_uuid']

            if import_groups:
                progress_bar = get_progress_bar(total=len(import_groups), disable=silent)
                pbar_base_str = 'Groups - '

            for groupuuid, groupnodes in import_groups.items():
                # TODO: cache these to avoid too many queries
                group_ = models.DbGroup.objects.get(uuid=groupuuid)

                progress_bar.set_description_str(pbar_base_str + 'label={}'.format(group_.label), refresh=False)
                progress_bar.update()

                nodes_to_store = [foreign_ids_reverse_mappings[NODE_ENTITY_NAME][node_uuid] for node_uuid in groupnodes]
                if nodes_to_store:
                    group_.dbnodes.add(*nodes_to_store)

        ######################################################
        # Put everything in a specific group
        ######################################################
        existing = existing_entries.get(NODE_ENTITY_NAME, {})
        existing_pk = [foreign_ids_reverse_mappings[NODE_ENTITY_NAME][v['uuid']] for v in existing.values()]
        new = new_entries.get(NODE_ENTITY_NAME, {})
        new_pk = [foreign_ids_reverse_mappings[NODE_ENTITY_NAME][v['uuid']] for v in new.values()]

        pks_for_group = existing_pk + new_pk

        # So that we do not create empty groups
        if pks_for_group:
            # If user specified a group, import all things into it
            if not group:
                # Get an unique name for the import group, based on the current (local) time
                basename = timezone.localtime(timezone.now()).strftime('%Y%m%d-%H%M%S')
                counter = 0
                group_label = basename

                while Group.objects.find(filters={'label': group_label}):
                    counter += 1
                    group_label = '{}_{}'.format(basename, counter)

                    if counter == 100:
                        raise exceptions.ImportUniquenessError(
                            "Overflow of import groups (more than 100 import groups exists with basename '{}')"
                            ''.format(basename)
                        )
                group = ImportGroup(label=group_label).store()

            # Add all the nodes to the new group
            builder = QueryBuilder().append(Node, filters={'id': {'in': pks_for_group}})

            progress_bar = get_progress_bar(total=len(pks_for_group), disable=silent)
            progress_bar.set_description_str('Creating import Group - Preprocessing', refresh=True)
            first = True

            nodes = []
            for entry in builder.iterall():
                if first:
                    progress_bar.set_description_str('Creating import Group', refresh=False)
                    first = False
                progress_bar.update()
                nodes.append(entry[0])
            group.add_nodes(nodes)
            progress_bar.set_description_str('Done (cleaning up)', refresh=True)
        else:
            IMPORT_LOGGER.debug('No Nodes to import, so no Group created, if it did not already exist')

    # Finalize Progress bar
    close_progress_bar(leave=False)

    # Summarize import
    result_summary(ret_dict, getattr(group, 'label', None))

    # Reset logging level
    if silent:
        logging.disable(level=logging.NOTSET)

    return ret_dict
