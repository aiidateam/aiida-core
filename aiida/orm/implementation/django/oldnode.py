# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.db.models import F

from aiida.common.exceptions import (InternalError, ModificationNotAllowed, NotExistent, UniquenessError)
from aiida.common.folders import RepositoryFolder
from aiida.common.links import LinkType
from aiida.common.utils import get_new_uuid
from aiida.common.lang import type_check
from aiida.orm.implementation.general.node import AbstractNode, _HASH_EXTRA_KEY


class Node(AbstractNode):

    # @classmethod
    # def get_subclass_from_uuid(cls, uuid):
    #     from .convert import get_backend_entity
    #     from aiida.backends.djsite.db.models import DbNode
    #     try:
    #         node = get_backend_entity(DbNode.objects.get(uuid=uuid), None)
    #     except ObjectDoesNotExist:
    #         raise NotExistent("No entry with UUID={} found".format(uuid))
    #     if not isinstance(node, cls):
    #         raise NotExistent("UUID={} is not an instance of {}".format(uuid, cls.__name__))
    #     return node

    # @classmethod
    # def get_subclass_from_pk(cls, pk):
    #     from .convert import get_backend_entity
    #     from aiida.backends.djsite.db.models import DbNode
    #     try:
    #         node = get_backend_entity(DbNode.objects.get(pk=pk), None)
    #     except ObjectDoesNotExist:
    #         raise NotExistent("No entry with pk= {} found".format(pk))
    #     if not isinstance(node, cls):
    #         raise NotExistent("pk= {} is not an instance of {}".format(pk, cls.__name__))
    #     return node

    def __init__(self, **kwargs):
        from aiida.backends.djsite.db.models import DbNode
        from aiida import orm

        super(Node, self).__init__()

        self._temp_folder = None

        dbnode = kwargs.pop('dbnode', None)

        # Set the internal parameters
        # Can be redefined in the subclasses
        self._init_internal_params()

        if dbnode is not None:
            if not isinstance(dbnode, DbNode):
                raise TypeError("dbnode is not a DbNode instance")
            if dbnode.pk is None:
                raise ValueError("If cannot load an aiida.orm.Node instance " "from an unsaved Django DbNode object.")
            if kwargs:
                raise ValueError("If you pass a dbnode, you cannot pass any " "further parameter")

            # If I am loading, I cannot modify it
            self._to_be_stored = False

            self._dbnode = dbnode

            # If this is changed, fix also the importer
            self._repo_folder = RepositoryFolder(section=self._section_name, uuid=self.uuid)

        # NO VALIDATION ON __init__ BY DEFAULT, IT IS TOO SLOW SINCE IT OFTEN
        # REQUIRES MULTIPLE DB HITS
        # try:
        #                # Note: the validation often requires to load at least one
        #                # attribute, and therefore it will take a lot of time
        #                # because it has to cache every attribute.
        #                self._validate()
        #            except ValidationError as e:
        #                raise DbContentError("The data in the DB with UUID={} is not "
        #                                     "valid for class {}: {}".format(
        #                    uuid, self.__class__.__name__, e.message))
        else:
            # TODO: allow to get the user from the parameters
            user = orm.User.objects.get_default().backend_entity
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