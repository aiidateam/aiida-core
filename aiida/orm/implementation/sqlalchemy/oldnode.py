# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
SQL Alchemy Node concrete implementation
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from sqlalchemy.exc import SQLAlchemyError

from aiida.backends.sqlalchemy.models.node import DbNode, DbLink
from aiida.backends.sqlalchemy.utils import flag_modified
from aiida.common.utils import get_new_uuid
from aiida.common.folders import RepositoryFolder
from aiida.common.exceptions import (ModificationNotAllowed, NotExistent, UniquenessError)
from aiida.common.links import LinkType
from aiida.common.lang import type_check
from aiida.orm.implementation.general.node import AbstractNode, _HASH_EXTRA_KEY
from .utils import get_attr

from . import computer as computers


class Node(AbstractNode):
    """
    Concrete SQLAlchemy Node implementation
    """
    _plugin_type_string = None

    def __init__(self, **kwargs):
        from aiida import orm

        super(Node, self).__init__()

        self._temp_folder = None

        dbnode = kwargs.pop('dbnode', None)

        # Set the internal parameters
        # Can be redefined in the subclasses
        self._init_internal_params()

        if dbnode is not None:
            type_check(dbnode, DbNode)
            if dbnode.id is None:
                raise ValueError("I cannot load an aiida.orm.Node instance from an unsaved DbNode object.")
            if kwargs:
                raise ValueError("If you pass a dbnode, you cannot pass any further parameter")

            # If I am loading, I cannot modify it
            self._to_be_stored = False

            self._dbnode = dbnode

            # If this is changed, fix also the importer
            self._repo_folder = RepositoryFolder(section=self._section_name, uuid=self.uuid)

        else:
            user = orm.User.objects(backend=self._backend).get_default().backend_entity

            if user is None:
                raise RuntimeError("Could not find a default user")

            self._dbnode = DbNode(user=user.dbmodel, uuid=get_new_uuid(), type=self._plugin_type_string)

            self._to_be_stored = True

            # As creating the temp folder may require some time on slow
            # filesystems, we defer its creation
            self._temp_folder = None
            # Used only before the first save
            self._attrs_cache = {}
            # If this is changed, fix also the importer
            self._repo_folder = RepositoryFolder(section=self._section_name, uuid=self.uuid)

            # Automatically set all *other* attributes, if possible, otherwise
            # stop
            self._set_with_defaults(**kwargs)

    # @classmethod
    # def get_subclass_from_uuid(cls, uuid):
    #     from aiida.orm.querybuilder import QueryBuilder
    #     from sqlalchemy.exc import DatabaseError
    #     try:
    #         query = QueryBuilder()
    #         query.append(cls, filters={'uuid': {'==': str(uuid)}})

    #         if query.count() == 0:
    #             raise NotExistent("No entry with UUID={} found".format(uuid))

    #         node = query.first()[0]

    #         if not isinstance(node, cls):
    #             raise NotExistent("UUID={} is not an instance of {}".format(uuid, cls.__name__))
    #         return node
    #     except DatabaseError as exc:
    #         raise ValueError(str(exc))

    # @classmethod
    # def get_subclass_from_pk(cls, pk):
    #     from aiida.orm.querybuilder import QueryBuilder
    #     from sqlalchemy.exc import DatabaseError
    #     # If it is not an int make a final attempt
    #     # to convert to an integer. If you fail,
    #     # raise an exception.
    #     try:
    #         pk = int(pk)
    #     except:
    #         raise ValueError("Incorrect type for int")

    #     try:
    #         query = QueryBuilder()
    #         query.append(cls, filters={'id': {'==': pk}})

    #         if query.count() == 0:
    #             raise NotExistent("No entry with pk= {} found".format(pk))

    #         node = query.first()[0]

    #         if not isinstance(node, cls):
    #             raise NotExistent("pk= {} is not an instance of {}".format(pk, cls.__name__))
    #         return node
    #     except DatabaseError as exc:
    #         raise ValueError(str(exc))

    # def __int__(self):
    #     if self._to_be_stored:
    #         return None

    #     return self._dbnode.id