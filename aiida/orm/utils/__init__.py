# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
from abc import ABCMeta

import six

from aiida.common.exceptions import InputValidationError
from aiida.common.utils import abstractclassmethod
from aiida.plugins.factory import BaseFactory

__all__ = ['CalculationFactory', 'DataFactory', 'WorkflowFactory', 'load_group', 
           'load_node', 'load_workflow', 'BackendDelegateWithDefault']


def CalculationFactory(entry_point):
    """
    Return the Calculation plugin class for a given entry point

    :param entry_point: the entry point name of the Calculation plugin
    """
    return BaseFactory('aiida.calculations', entry_point)


def DataFactory(entry_point):
    """
    Return the Data plugin class for a given entry point

    :param entry_point: the entry point name of the Data plugin
    """
    return BaseFactory('aiida.data', entry_point)


def WorkflowFactory(entry_point):
    """
    Return the Workflow plugin class for a given entry point

    :param entry_point: the entry point name of the Workflow plugin
    """
    return BaseFactory('aiida.workflows', entry_point)


def load_group(identifier=None, pk=None, uuid=None, label=None, query_with_dashes=True):
    """
    Load a group by one of its identifiers: pk, uuid or label. If the type of the identifier is unknown
    simply pass it without a keyword and the loader will attempt to infer the type

    :param identifier: pk (integer), uuid (string) or label (string) of a group
    :param pk: pk of a group
    :param uuid: uuid of a group, or the beginning of the uuid
    :param label: label of a group
    :param bool query_with_dashes: allow to query for a uuid with dashes
    :returns: the group instance
    :raise InputValidationError: if none or more than one of the identifiers are supplied
    :raise TypeError: if the provided identifier has the wrong type
    :raise NotExistent: if no matching Group is found
    :raise MultipleObjectsError: if more than one Group was found
    """
    from aiida.orm.utils.loaders import IdentifierType, GroupEntityLoader

    # Verify that at least and at most one identifier is specified
    inputs_provided = [value is not None for value in (identifier, pk, uuid, label)].count(True)
    if inputs_provided == 0:
        raise InputValidationError("one of the parameters 'identifier', pk', 'uuid' or 'label' has to be specified")
    elif inputs_provided > 1:
        raise InputValidationError("only one of parameters 'identifier', pk', 'uuid' or 'label' has to be specified")

    if pk is not None:

        if not isinstance(pk, int):
            raise TypeError('a pk has to be an integer')

        identifier = pk
        identifier_type = IdentifierType.ID

    elif uuid is not None:

        if not isinstance(uuid, six.string_types):
            raise TypeError('uuid has to be a string type')

        identifier = uuid
        identifier_type = IdentifierType.UUID

    elif label is not None:

        if not isinstance(label, six.string_types):
            raise TypeError('label has to be a string type')

        identifier = label
        identifier_type = IdentifierType.LABEL
    else:
        identifier = str(identifier)
        identifier_type = None

    return GroupEntityLoader.load_entity(identifier, identifier_type, query_with_dashes=query_with_dashes)


def load_node(identifier=None, pk=None, uuid=None, sub_class=None, query_with_dashes=True):
    """
    Load a node by one of its identifiers: pk or uuid. If the type of the identifier is unknown
    simply pass it without a keyword and the loader will attempt to infer the type

    :param identifier: pk (integer) or uuid (string)
    :param pk: pk of a node
    :param uuid: uuid of a node, or the beginning of the uuid
    :param sub_class: an optional tuple of orm classes, that should each be strict sub class of Node,
        to narrow the queryset
    :param bool query_with_dashes: allow to query for a uuid with dashes
    :returns: the node instance
    :raise InputValidationError: if none or more than one of the identifiers are supplied
    :raise TypeError: if the provided identifier has the wrong type
    :raise NotExistent: if no matching Node is found
    :raise MultipleObjectsError: if more than one Node was found
    """
    from aiida.orm.utils.loaders import IdentifierType, NodeEntityLoader

    # Verify that at least and at most one identifier is specified
    inputs_provided = [value is not None for value in (identifier, pk, uuid)].count(True)
    if inputs_provided == 0:
        raise InputValidationError("one of the parameters 'identifier', 'pk' or 'uuid' has to be specified")
    elif inputs_provided > 1:
        raise InputValidationError("only one of parameters 'identifier', 'pk' or 'uuid' has to be specified")

    if pk is not None:

        if not isinstance(pk, int):
            raise TypeError('a pk has to be an integer')

        identifier = pk
        identifier_type = IdentifierType.ID

    elif uuid is not None:

        if not isinstance(uuid, six.string_types):
            raise TypeError('uuid has to be a string type')

        identifier = uuid
        identifier_type = IdentifierType.UUID
    else:
        identifier = str(identifier)
        identifier_type = None

    if sub_class is not None and not isinstance(sub_class, tuple):
        sub_class = (sub_class,)

    return NodeEntityLoader.load_entity(identifier, identifier_type, sub_class, query_with_dashes)


def load_workflow(wf_id=None, pk=None, uuid=None):
    """
    Return an AiiDA workflow given PK or UUID.

    :param wf_id: PK (integer) or UUID (string) or UUID instance or a workflow
    :param pk: PK of a workflow
    :param uuid: UUID of a workflow
    :return: an AiiDA workflow
    :raises: ValueError if none or more than one of parameters is supplied
        or type of wf_id is neither string nor integer
    """
    # This must be done inside here, because at import time the profile
    # must have been already loaded. If you put it at the module level,
    # the implementation is frozen to the default one at import time.
    from aiida.orm.implementation import Workflow
    from uuid import UUID as uuid_type

    if int(wf_id is None) + int(pk is None) + int(uuid is None) == 3:
        raise ValueError("one of the parameters 'wf_id', 'pk' and 'uuid' "
                         "has to be supplied")
    if int(wf_id is None) + int(pk is None) + int(uuid is None) < 2:
        raise ValueError("only one of parameters 'wf_id', 'pk' and 'uuid' "
                         "has to be supplied")

    if wf_id is not None:
        if wf_id and isinstance(wf_id, uuid_type):
            wf_id = str(wf_id)

        if isinstance(wf_id, six.string_types):
            return Workflow.get_subclass_from_uuid(wf_id)
        elif isinstance(wf_id, int):
            return Workflow.get_subclass_from_pk(wf_id)
        else:
            raise ValueError("'wf_id' has to be either string, unicode, "
                             "integer or UUID instance, {} given".format(type(wf_id)))
    if pk is not None:
        if isinstance(pk, int):
            return Workflow.get_subclass_from_pk(pk)
        else:
            raise ValueError("'pk' has to be an integer")
    else:
        if uuid and isinstance(uuid, uuid_type):
            uuid = str(uuid)
        if isinstance(uuid, six.string_types):
            return Workflow.get_subclass_from_uuid(uuid)
        else:
            raise ValueError("'uuid' has to be a string, unicode or a UUID instance")


@six.add_metaclass(ABCMeta)
class BackendDelegateWithDefault(object):
    """
    This class is a helper to implement the delegation pattern [1] by
    delegating functionality (i.e. calling through) to the backend class
    which will do the actual work.

    [1] https://en.wikipedia.org/wiki/Delegation_pattern
    """

    _DEFAULT = None

    @abstractclassmethod
    def create_default(cls):
        raise NotImplementedError("The subclass should implement this")

    @classmethod
    def get_default(cls):
        if cls._DEFAULT is None:
            cls._DEFAULT = cls.create_default()
        return cls._DEFAULT

    def __init__(self, backend):
        self._backend = backend
