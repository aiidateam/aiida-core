# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities related to the ORM."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

__all__ = ('load_code', 'load_computer', 'load_group', 'load_node')


def load_entity(entity_loader=None,
                identifier=None,
                pk=None,
                uuid=None,
                label=None,
                sub_classes=None,
                query_with_dashes=True):
    # pylint: disable=too-many-arguments
    """
    Load an entity instance by one of its identifiers: pk, uuid or label

    If the type of the identifier is unknown simply pass it without a keyword and the loader will attempt to
    automatically infer the type.

    :param identifier: pk (integer), uuid (string) or label (string) of a Code
    :param pk: pk of a Code
    :param uuid: uuid of a Code, or the beginning of the uuid
    :param label: label of a Code
    :param sub_classes: an optional tuple of orm classes to narrow the queryset. Each class should be a strict sub class
        of the ORM class of the given entity loader.
    :param bool query_with_dashes: allow to query for a uuid with dashes
    :returns: the Code instance
    :raise ValueError: if none or more than one of the identifiers are supplied
    :raise TypeError: if the provided identifier has the wrong type
    :raise aiida.common.NotExistent: if no matching Code is found
    :raise aiida.common.MultipleObjectsError: if more than one Code was found
    """
    from aiida.orm.utils.loaders import OrmEntityLoader, IdentifierType

    if entity_loader is None or not issubclass(entity_loader, OrmEntityLoader):
        raise TypeError('entity_loader should be a sub class of {}'.format(type(OrmEntityLoader)))

    inputs_provided = [value is not None for value in (identifier, pk, uuid, label)].count(True)

    if inputs_provided == 0:
        raise ValueError("one of the parameters 'identifier', pk', 'uuid' or 'label' has to be specified")
    elif inputs_provided > 1:
        raise ValueError("only one of parameters 'identifier', pk', 'uuid' or 'label' has to be specified")

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

    return entity_loader.load_entity(
        identifier, identifier_type, sub_classes=sub_classes, query_with_dashes=query_with_dashes)


def load_code(identifier=None, pk=None, uuid=None, label=None, sub_classes=None, query_with_dashes=True):
    """
    Load a Code instance by one of its identifiers: pk, uuid or label

    If the type of the identifier is unknown simply pass it without a keyword and the loader will attempt to
    automatically infer the type.

    :param identifier: pk (integer), uuid (string) or label (string) of a Code
    :param pk: pk of a Code
    :param uuid: uuid of a Code, or the beginning of the uuid
    :param label: label of a Code
    :param sub_classes: an optional tuple of orm classes to narrow the queryset. Each class should be a strict sub class
        of the ORM class of the given entity loader.
    :param bool query_with_dashes: allow to query for a uuid with dashes
    :return: the Code instance
    :raise ValueError: if none or more than one of the identifiers are supplied
    :raise TypeError: if the provided identifier has the wrong type
    :raise aiida.common.NotExistent: if no matching Code is found
    :raise aiida.common.MultipleObjectsError: if more than one Code was found
    """
    from aiida.orm.utils.loaders import CodeEntityLoader
    return load_entity(
        CodeEntityLoader,
        identifier=identifier,
        pk=pk,
        uuid=uuid,
        label=label,
        sub_classes=sub_classes,
        query_with_dashes=query_with_dashes)


def load_computer(identifier=None, pk=None, uuid=None, label=None, sub_classes=None, query_with_dashes=True):
    """
    Load a Computer instance by one of its identifiers: pk, uuid or label

    If the type of the identifier is unknown simply pass it without a keyword and the loader will attempt to
    automatically infer the type.

    :param identifier: pk (integer), uuid (string) or label (string) of a Computer
    :param pk: pk of a Computer
    :param uuid: uuid of a Computer, or the beginning of the uuid
    :param label: label of a Computer
    :param sub_classes: an optional tuple of orm classes to narrow the queryset. Each class should be a strict sub class
        of the ORM class of the given entity loader.
    :param bool query_with_dashes: allow to query for a uuid with dashes
    :return: the Computer instance
    :raise ValueError: if none or more than one of the identifiers are supplied
    :raise TypeError: if the provided identifier has the wrong type
    :raise aiida.common.NotExistent: if no matching Computer is found
    :raise aiida.common.MultipleObjectsError: if more than one Computer was found
    """
    from aiida.orm.utils.loaders import ComputerEntityLoader
    return load_entity(
        ComputerEntityLoader,
        identifier=identifier,
        pk=pk,
        uuid=uuid,
        label=label,
        sub_classes=sub_classes,
        query_with_dashes=query_with_dashes)


def load_group(identifier=None, pk=None, uuid=None, label=None, sub_classes=None, query_with_dashes=True):
    """
    Load a Group instance by one of its identifiers: pk, uuid or label

    If the type of the identifier is unknown simply pass it without a keyword and the loader will attempt to
    automatically infer the type.

    :param identifier: pk (integer), uuid (string) or label (string) of a Group
    :param pk: pk of a Group
    :param uuid: uuid of a Group, or the beginning of the uuid
    :param label: label of a Group
    :param sub_classes: an optional tuple of orm classes to narrow the queryset. Each class should be a strict sub class
        of the ORM class of the given entity loader.
    :param bool query_with_dashes: allow to query for a uuid with dashes
    :return: the Group instance
    :raise ValueError: if none or more than one of the identifiers are supplied
    :raise TypeError: if the provided identifier has the wrong type
    :raise aiida.common.NotExistent: if no matching Group is found
    :raise aiida.common.MultipleObjectsError: if more than one Group was found
    """
    from aiida.orm.utils.loaders import GroupEntityLoader
    return load_entity(
        GroupEntityLoader,
        identifier=identifier,
        pk=pk,
        uuid=uuid,
        label=label,
        sub_classes=sub_classes,
        query_with_dashes=query_with_dashes)


def load_node(identifier=None, pk=None, uuid=None, label=None, sub_classes=None, query_with_dashes=True):
    """
    Load a node by one of its identifiers: pk or uuid. If the type of the identifier is unknown
    simply pass it without a keyword and the loader will attempt to infer the type

    :param identifier: pk (integer) or uuid (string)
    :param pk: pk of a node
    :param uuid: uuid of a node, or the beginning of the uuid
    :param label: label of a Node
    :param sub_classes: an optional tuple of orm classes to narrow the queryset. Each class should be a strict sub class
        of the ORM class of the given entity loader.
    :param bool query_with_dashes: allow to query for a uuid with dashes
    :returns: the node instance
    :raise ValueError: if none or more than one of the identifiers are supplied
    :raise TypeError: if the provided identifier has the wrong type
    :raise aiida.common.NotExistent: if no matching Node is found
    :raise aiida.common.MultipleObjectsError: if more than one Node was found
    """
    from aiida.orm.utils.loaders import NodeEntityLoader
    return load_entity(
        NodeEntityLoader,
        identifier=identifier,
        pk=pk,
        uuid=uuid,
        label=label,
        sub_classes=sub_classes,
        query_with_dashes=query_with_dashes)
