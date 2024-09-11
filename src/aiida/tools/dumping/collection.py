###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Functionality for dumping of a Collections of AiiDA ORMs."""

from aiida import orm
import logging
from collections import Counter

LOGGER = logging.getLogger(__name__)
# TODO: Could also get the entities, or UUIDs directly, rather than just counting them here

class CollectionDumper:

    @staticmethod
    def create_entity_counter(orm_collection: orm.Group | orm.Collection | None = None):
        if orm_collection is None:
            return CollectionDumper._create_entity_counter_profile()
        if isinstance(orm_collection, orm.Group):
            return CollectionDumper._create_entity_counter_group(group=orm_collection)

    @staticmethod
    def _create_entity_counter_profile():

        nodes = orm.QueryBuilder().append(orm.Node).all(flat=True)
        type_counter = Counter()

        # Iterate over all the entities in the group
        for entity in nodes:
            # Count the type string of each entity
            type_counter[entity.__class__] += 1

        # Convert the Counter to a dictionary (optional)
        # type_dict = dict(type_counter)

        return type_counter

    @staticmethod
    def _create_entity_counter_group(group: orm.Group | str):
        # ? If the group only has one WorkChain assigned to it, this will only return a count of 1 for the
        # ? WorkChainNode, nothing more, that is, not recursively.
        if isinstance(group, str):
            group = orm.Group.get(group)
        type_counter = Counter()

        # Iterate over all the entities in the group
        for entity in group.nodes:
            # Count the type string of each entity
            type_counter[entity.__class__] += 1

        # Convert the Counter to a dictionary (optional)
        # type_dict = dict(type_counter)

        return type_counter



    # @staticmethod
    # def _create_entity_counter_storage():
    #     # ? If the group only has one WorkChain assigned to it, this will only return a count of 1 for the
    #     # ? WorkChainNode, nothing more, that is, not recursively.

    #     from aiida.manage.manager import get_manager

    #     manager = get_manager()
    #     storage = manager.get_profile_storage()

    #     LOGGER.report(storage)

    #     # if isinstance(group, str):
    #     #     group = orm.Group.get(group)
    #     # type_counter = Counter()

    #     # # Iterate over all the entities in the group
    #     # for entity in group.nodes:
    #     #     # Count the type string of each entity
    #     #     type_counter[entity.__class__.__name__] += 1

    #     # # Convert the Counter to a dictionary (optional)
    #     # # type_dict = dict(type_counter)

    #     # return type_counter
