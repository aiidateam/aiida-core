# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""" Utility functions for export of AiiDA entities """
# pylint: disable=too-many-locals,too-many-branches,too-many-nested-blocks
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

from aiida.orm import QueryBuilder, ProcessNode
from aiida.tools.importexport.common import exceptions
from aiida.tools.importexport.common.config import (
    file_fields_to_model_fields, entity_names_to_entities, get_all_fields_info
)


def fill_in_query(partial_query, originating_entity_str, current_entity_str, tag_suffixes=None, entity_separator='_'):
    """
    This function recursively constructs QueryBuilder queries that are needed
    for the SQLA export function. To manage to construct such queries, the
    relationship dictionary is consulted (which shows how to reference
    different AiiDA entities in QueryBuilder.
    To find the dependencies of the relationships of the exported data, the
    get_all_fields_info (which described the exported schema and its
    dependencies) is consulted.
    """
    if not tag_suffixes:
        tag_suffixes = []

    relationship_dic = {
        'Node': {
            'Computer': 'with_computer',
            'Group': 'with_group',
            'User': 'with_user',
            'Log': 'with_log',
            'Comment': 'with_comment'
        },
        'Group': {
            'Node': 'with_node'
        },
        'Computer': {
            'Node': 'with_node'
        },
        'User': {
            'Node': 'with_node',
            'Group': 'with_group',
            'Comment': 'with_comment',
        },
        'Log': {
            'Node': 'with_node'
        },
        'Comment': {
            'Node': 'with_node',
            'User': 'with_user'
        }
    }

    all_fields_info, _ = get_all_fields_info()

    entity_prop = all_fields_info[current_entity_str].keys()

    project_cols = ['id']
    for prop in entity_prop:
        nprop = prop
        if current_entity_str in file_fields_to_model_fields:
            if prop in file_fields_to_model_fields[current_entity_str]:
                nprop = file_fields_to_model_fields[current_entity_str][prop]

        project_cols.append(nprop)

    # Here we should reference the entity of the main query
    current_entity_mod = entity_names_to_entities[current_entity_str]

    rel_string = relationship_dic[current_entity_str][originating_entity_str]
    mydict = {rel_string: entity_separator.join(tag_suffixes)}

    partial_query.append(
        current_entity_mod,
        tag=entity_separator.join(tag_suffixes) + entity_separator + current_entity_str,
        project=project_cols,
        outerjoin=True,
        **mydict
    )

    # prepare the recursion for the referenced entities
    foreign_fields = {
        k: v
        for k, v in all_fields_info[current_entity_str].items()
        # all_fields_info[model_name].items()
        if 'requires' in v
    }

    new_tag_suffixes = tag_suffixes + [current_entity_str]
    for value in foreign_fields.values():
        ref_model_name = value['requires']
        fill_in_query(partial_query, current_entity_str, ref_model_name, new_tag_suffixes)


def check_licences(node_licenses, allowed_licenses, forbidden_licenses):
    """Check licenses"""
    from aiida.common.exceptions import LicensingException
    from inspect import isfunction

    for pk, license_ in node_licenses:
        if allowed_licenses is not None:
            try:
                if isfunction(allowed_licenses):
                    try:
                        if not allowed_licenses(license_):
                            raise LicensingException
                    except Exception:
                        raise LicensingException
                else:
                    if license_ not in allowed_licenses:
                        raise LicensingException
            except LicensingException:
                raise LicensingException(
                    'Node {} is licensed '
                    'under {} license, which '
                    'is not in the list of '
                    'allowed licenses'.format(pk, license_)
                )
        if forbidden_licenses is not None:
            try:
                if isfunction(forbidden_licenses):
                    try:
                        if forbidden_licenses(license_):
                            raise LicensingException
                    except Exception:
                        raise LicensingException
                else:
                    if license_ in forbidden_licenses:
                        raise LicensingException
            except LicensingException:
                raise LicensingException(
                    'Node {} is licensed '
                    'under {} license, which '
                    'is in the list of '
                    'forbidden licenses'.format(pk, license_)
                )


def serialize_field(data, track_conversion=False):
    """
    Serialize a single field.

    :todo: Generalize such that it the proper function is selected also during
        import
    """
    import datetime
    import pytz
    from uuid import UUID

    if isinstance(data, dict):
        ret_data = {}
        if track_conversion:
            ret_conversion = {}
            for key, value in data.items():
                ret_data[key], ret_conversion[key] = serialize_field(data=value, track_conversion=track_conversion)
        else:
            for key, value in data.items():
                ret_data[key] = serialize_field(data=value, track_conversion=track_conversion)
    elif isinstance(data, (list, tuple)):
        ret_data = []
        if track_conversion:
            ret_conversion = []
            for value in data:
                this_data, this_conversion = serialize_field(data=value, track_conversion=track_conversion)
                ret_data.append(this_data)
                ret_conversion.append(this_conversion)
        else:
            for value in data:
                ret_data.append(serialize_field(data=value, track_conversion=track_conversion))
    elif isinstance(data, datetime.datetime):
        # Note: requires timezone-aware objects!
        ret_data = data.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')
        ret_conversion = 'date'
    elif isinstance(data, UUID):
        ret_data = str(data)
        ret_conversion = None
    else:
        ret_data = data
        ret_conversion = None

    if track_conversion:
        return (ret_data, ret_conversion)
    # else
    return ret_data


def serialize_dict(datadict, remove_fields=None, rename_fields=None, track_conversion=False):
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

    if not remove_fields:
        remove_fields = []

    if not rename_fields:
        rename_fields = {}

    for key, value in datadict.items():
        if key not in remove_fields:
            # rename_fields.get(key,key): use the replacement if found in rename_fields,
            # otherwise use 'key' as the default value.
            if track_conversion:
                (ret_dict[rename_fields.get(key, key)],
                 conversions[rename_fields.get(key,
                                               key)]) = serialize_field(data=value, track_conversion=track_conversion)
            else:
                ret_dict[rename_fields.get(key, key)] = serialize_field(data=value, track_conversion=track_conversion)

    if track_conversion:
        return (ret_dict, conversions)
    # else
    return ret_dict


def check_process_nodes_sealed(nodes):
    """Check ``ProcessNode`` s are sealed
    Only sealed ``ProcessNode`` s may be exported.

    :param nodes: :py:class:`~aiida.orm.nodes.process.process.ProcessNode` s to be checked. Should be their PK(s).
    :type nodes: list, int

    :raises `~aiida.tools.importexport.common.exceptions.ExportValidationError`:
        if a ``ProcessNode`` is not sealed or `nodes` is not a `list`, `set`, or `int`.
    """
    if not nodes:
        return

    # Check `nodes` type, and if necessary change to set
    if isinstance(nodes, set):
        pass
    elif isinstance(nodes, list):
        nodes = set(nodes)
    elif isinstance(nodes, int):
        nodes = set([nodes])
    else:
        raise exceptions.ExportValidationError('nodes must be either an int or set/list of ints')

    filters = {'id': {'in': nodes}, 'attributes.sealed': True}
    sealed_nodes = QueryBuilder().append(ProcessNode, filters=filters, project=['id']).all()
    sealed_nodes = {_[0] for _ in sealed_nodes}

    if sealed_nodes != nodes:
        raise exceptions.ExportValidationError(
            'All ProcessNodes must be sealed before they can be exported. '
            'Node(s) with PK(s): {} is/are not sealed.'.format(', '.join(str(pk) for pk in nodes - sealed_nodes))
        )


def _retrieve_linked_nodes_query(current_node, input_type, output_type, direction, link_types):
    """Helper function for :py:func:`~aiida.tools.importexport.dbexport.utils.retrieve_linked_nodes`

    A general :py:class:`~aiida.orm.querybuilder.QueryBuilder` query, retrieving linked Nodes and returning link
    information and the found Nodes.

    :param current_node: The current Node's PK.
    :type current_node: int

    :param input_type: ORM Node class
    :type input_type: :py:class:`~aiida.orm.nodes.data.data.Data`,
        :py:class:`~aiida.orm.nodes.process.process.ProcessNode`.

    :param output_type: ORM Node class
    :type output_type: :py:class:`~aiida.orm.nodes.data.data.Data`,
        :py:class:`~aiida.orm.nodes.process.process.ProcessNode`.

    :param direction: Link direction, must be either ``'forward'`` or ``'reverse'``.
    :type direction: str

    :param link_types: List of :py:class:`~aiida.common.links.LinkType` values, e.g. ``LinkType.RETURN.value``.
    :type link_types: list

    :return: Dictionary of link information to be used for the export archive and set of found Nodes.
    :rtype: dict
    """
    found_nodes = set()
    links_uuid_dict = {}

    get_current_node = {'id': current_node}
    filters_input = get_current_node if direction == 'forward' else {}
    filters_output = get_current_node if direction == 'reverse' else {}
    if filters_input == filters_output:
        raise exceptions.ExportValidationError("direction must be either 'forward' or 'reverse'")

    builder = QueryBuilder()
    builder.append(input_type, project=['uuid', 'id'], tag='input', filters=filters_input)
    builder.append(
        output_type,
        project=['uuid', 'id'],
        with_incoming='input',
        filters=filters_output,
        edge_filters={'type': {
            'in': link_types
        }},
        edge_project=['label', 'type']
    )

    for input_uuid, input_pk, output_uuid, output_pk, link_label, link_type in builder.iterall():
        links_uuid_entry = {
            'input': str(input_uuid),
            'output': str(output_uuid),
            'label': str(link_label),
            'type': str(link_type)
        }
        links_uuid_dict[frozenset(links_uuid_entry.items())] = links_uuid_entry

        node_pk = output_pk if direction == 'forward' else input_pk
        found_nodes.add(node_pk)

    return links_uuid_dict, found_nodes


def retrieve_linked_nodes(process_nodes, data_nodes, **kwargs):
    """Recursively retrieve linked Nodes and the links

    The rules for recursively following links/edges in the provenance graph are as follows,
    where the Node types in bold symbolize the Node that is currently being exported, i.e.,
    it is this Node onto which the Link in question has been found.

    +------------+---------------------+---------------------+----------------+----------------------------+
    |**LinkType**| **From**            | **To**              |Follow (default)| Togglable                  |
    +============+=====================+=====================+================+============================+
    | INPUT_CALC | **Data**            | CalculationNode     | False          | True (``input_forward``)   |
    +------------+---------------------+---------------------+----------------+----------------------------+
    | INPUT_CALC | Data                | **CalculationNode** | True           | False                      |
    +------------+---------------------+---------------------+----------------+----------------------------+
    | CREATE     | **CalculationNode** | Data                | True           | False                      |
    +------------+---------------------+---------------------+----------------+----------------------------+
    | CREATE     | CalculationNode     | **Data**            | True           | True (``create_reversed``) |
    +------------+---------------------+---------------------+----------------+----------------------------+
    | RETURN     | **WorkflowNode**    | Data                | True           | False                      |
    +------------+---------------------+---------------------+----------------+----------------------------+
    | RETURN     | WorkflowNode        | **Data**            | False          | True (``return_reversed``) |
    +------------+---------------------+---------------------+----------------+----------------------------+
    | INPUT_WORK | **Data**            | WorkflowNode        | False          | True (``input_forward``)   |
    +------------+---------------------+---------------------+----------------+----------------------------+
    | INPUT_WORK | Data                | **WorkflowNode**    | True           | False                      |
    +------------+---------------------+---------------------+----------------+----------------------------+
    | CALL_CALC  | **WorkflowNode**    | CalculationNode     | True           | False                      |
    +------------+---------------------+---------------------+----------------+----------------------------+
    | CALL_CALC  | WorkflowNode        | **CalculationNode** | False          | True (``call_reversed``)   |
    +------------+---------------------+---------------------+----------------+----------------------------+
    | CALL_WORK  | **WorkflowNode**    | WorkflowNode        | True           | False                      |
    +------------+---------------------+---------------------+----------------+----------------------------+
    | CALL_WORK  | WorkflowNode        | **WorkflowNode**    | False          | True (``call_reversed``)   |
    +------------+---------------------+---------------------+----------------+----------------------------+

    :param process_nodes: Set of :py:class:`~aiida.orm.nodes.process.process.ProcessNode` nodes.
    :param data_nodes: Set of :py:class:`~aiida.orm.nodes.data.data.Data` nodes.

    :param input_forward: Follow forward INPUT links (recursively) when calculating the node set to export.
    :type input_forward: bool

    :param create_reversed: Follow reversed CREATE links (recursively) when calculating the node set to export.
    :type create_reversed: bool

    :param return_reversed: Follow reversed RETURN links (recursively) when calculating the node set to export.
    :type return_reversed: bool

    :param call_reversed: Follow reversed CALL links (recursively) when calculating the node set to export.
    :type call_reversed: bool

    :return: Set of retrieved Nodes and list of links information.

    :raises `~aiida.tools.importexport.common.exceptions.ExportValidationError`: if wrong or too many kwargs are given.
    """
    from aiida.common.links import LinkType
    from aiida.orm import Data

    # Initialization and set flags according to rules
    retrieved_nodes = set()
    links_uuid_dict = {}
    input_forward = kwargs.pop('input_forward', False)
    create_reversed = kwargs.pop('create_reversed', True)
    return_reversed = kwargs.pop('return_reversed', False)
    call_reversed = kwargs.pop('call_reversed', False)

    if kwargs:
        raise exceptions.ExportValidationError(
            'retrieve_linked_nodes received too many keyword arguments: {}. '.format(kwargs) +
            "Only 'input_forward', 'create_reversed', 'return_reversed', 'call_reversed' are accepted."
        )

    # We repeat until there are no further nodes to be visited
    while process_nodes or data_nodes:

        # If is is a ProcessNode
        if process_nodes:
            current_node_pk = process_nodes.pop()
            # If it is already visited continue to the next node
            if current_node_pk in retrieved_nodes:
                continue
            # Otherwise say that it is a node to be exported
            else:
                retrieved_nodes.add(current_node_pk)

            # INPUT(Data, ProcessNode) - Reversed
            links_uuids, found_nodes = _retrieve_linked_nodes_query(
                current_node_pk,
                input_type=Data,
                output_type=ProcessNode,
                direction='reverse',
                link_types=[LinkType.INPUT_CALC.value, LinkType.INPUT_WORK.value]
            )
            data_nodes.update(found_nodes - retrieved_nodes)
            links_uuid_dict.update(links_uuids)

            # CREATE/RETURN(ProcessNode, Data) - Forward
            links_uuids, found_nodes = _retrieve_linked_nodes_query(
                current_node_pk,
                input_type=ProcessNode,
                output_type=Data,
                direction='forward',
                link_types=[LinkType.CREATE.value, LinkType.RETURN.value]
            )
            data_nodes.update(found_nodes - retrieved_nodes)
            links_uuid_dict.update(links_uuids)

            # CALL(WorkflowNode, ProcessNode) - Forward
            links_uuids, found_nodes = _retrieve_linked_nodes_query(
                current_node_pk,
                input_type=ProcessNode,
                output_type=ProcessNode,
                direction='forward',
                link_types=[LinkType.CALL_CALC.value, LinkType.CALL_WORK.value]
            )
            process_nodes.update(found_nodes - retrieved_nodes)
            links_uuid_dict.update(links_uuids)

            # CALL(WorkflowNode, ProcessNode) - Reversed
            if call_reversed:
                links_uuids, found_nodes = _retrieve_linked_nodes_query(
                    current_node_pk,
                    input_type=ProcessNode,
                    output_type=ProcessNode,
                    direction='reverse',
                    link_types=[LinkType.CALL_CALC.value, LinkType.CALL_WORK.value]
                )
                process_nodes.update(found_nodes - retrieved_nodes)
                links_uuid_dict.update(links_uuids)

        # If it is a Data
        else:
            current_node_pk = data_nodes.pop()
            # If it is already visited continue to the next node
            if current_node_pk in retrieved_nodes:
                continue
            # Otherwise say that it is a node to be exported
            else:
                retrieved_nodes.add(current_node_pk)

            # INPUT(Data, ProcessNode) - Forward
            if input_forward:
                links_uuids, found_nodes = _retrieve_linked_nodes_query(
                    current_node_pk,
                    input_type=Data,
                    output_type=ProcessNode,
                    direction='forward',
                    link_types=[LinkType.INPUT_CALC.value, LinkType.INPUT_WORK.value]
                )
                process_nodes.update(found_nodes - retrieved_nodes)
                links_uuid_dict.update(links_uuids)

            # CREATE(CalculationNode, Data) - Reversed
            if create_reversed:
                links_uuids, found_nodes = _retrieve_linked_nodes_query(
                    current_node_pk,
                    input_type=ProcessNode,
                    output_type=Data,
                    direction='reverse',
                    link_types=[LinkType.CREATE.value]
                )
                process_nodes.update(found_nodes - retrieved_nodes)
                links_uuid_dict.update(links_uuids)

            # RETURN(WorkflowNode, Data) - Reversed
            if return_reversed:
                links_uuids, found_nodes = _retrieve_linked_nodes_query(
                    current_node_pk,
                    input_type=ProcessNode,
                    output_type=Data,
                    direction='reverse',
                    link_types=[LinkType.RETURN.value]
                )
                process_nodes.update(found_nodes - retrieved_nodes)
                links_uuid_dict.update(links_uuids)

    return retrieved_nodes, list(links_uuid_dict.values())
