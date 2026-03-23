###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# ruff: noqa: N802
"""A module containing the logic for creating joined queries."""

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Protocol, Type

from sqlalchemy import and_, join, select
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.orm import Query, aliased
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.expression import cast as type_cast
from sqlalchemy.sql.schema import Table
from sqlalchemy.types import Integer

from aiida.common.links import LinkType
from aiida.storage.psql_dos.models.base import Model


class _EntityMapper(Protocol):
    """Mapping of implemented entity types."""

    @property
    def AuthInfo(self) -> Type[Model]: ...

    @property
    def Node(self) -> Type[Model]: ...

    @property
    def Group(self) -> Type[Model]: ...

    @property
    def Link(self) -> Type[Model]: ...

    @property
    def User(self) -> Type[Model]: ...

    @property
    def Computer(self) -> Type[Model]: ...

    @property
    def Comment(self) -> Type[Model]: ...

    @property
    def Log(self) -> Type[Model]: ...

    @property
    def table_groups_nodes(self) -> Type[Table]: ...


@dataclass
class JoinReturn:
    join: Callable[[Query], Query]
    aliased_edge: Optional[AliasedClass] = None
    edge_tag: str = ''


FilterType = Dict[str, Any]
JoinFuncType = Callable[[Any, Any, bool, FilterType, bool], JoinReturn]


class SqlaJoiner:
    """A class containing the logic for SQLAlchemy entities joining entities."""

    def __init__(
        self,
        entity_mapper: _EntityMapper,
        filter_builder: Callable[[AliasedClass, FilterType], Optional[ColumnElement[bool]]],
    ):
        """Initialise the class"""
        self._entities = entity_mapper
        self._build_filters = filter_builder

    def get_join_func(self, entity_key: str, relationship: str) -> JoinFuncType:
        """Return the function to join two entities"""
        return self._entity_join_map()[entity_key][relationship]

    def _entity_join_map(self) -> Dict[str, Dict[str, JoinFuncType]]:
        """Map relationship type keywords to functions
        The first level defines the entity which has been passed to the qb.append function,
        and the second defines the relationship with respect to a given tag.
        """
        mapping = {
            'authinfo': {
                'with_computer': self._join_computer_authinfo,
                'with_user': self._join_user_authinfo,
            },
            'comment': {
                'with_node': self._join_node_comment,
                'with_user': self._join_user_comment,
            },
            'computer': {
                'with_node': self._join_node_computer,
            },
            'group': {
                'with_node': self._join_node_group,
                'with_user': self._join_user_group,
            },
            'link': {},
            'log': {
                'with_node': self._join_node_log,
            },
            'node': {
                'with_log': self._join_log_node,
                'with_comment': self._join_comment_node,
                'with_incoming': self._join_node_outputs,
                'with_outgoing': self._join_node_inputs,
                'with_descendants': self._join_node_ancestors_recursive,
                'with_ancestors': self._join_node_descendants_recursive,
                'with_computer': self._join_computer_node,
                'with_user': self._join_user_node,
                'with_group': self._join_group_node,
            },
            'user': {
                'with_authinfo': self._join_authinfo_user,
                'with_comment': self._join_comment_user,
                'with_node': self._join_node_user,
                'with_group': self._join_group_user,
            },
        }

        return mapping  # type: ignore[return-value]

    def _join_computer_authinfo(self, joined_entity, entity_to_join, isouterjoin: bool, **_kw):
        """:param joined_entity: the aliased user you want to join to
        :param entity_to_join: the (aliased) node or group in the DB to join with
        """
        _check_dbentities(
            (joined_entity, self._entities.Computer), (entity_to_join, self._entities.AuthInfo), 'with_computer'
        )

        def new_query(q):
            return q.join(entity_to_join, entity_to_join.dbcomputer_id == joined_entity.id, isouter=isouterjoin)

        return JoinReturn(new_query)

    def _join_user_authinfo(self, joined_entity, entity_to_join, isouterjoin: bool, **_kw):
        """:param joined_entity: the aliased user you want to join to
        :param entity_to_join: the (aliased) node or group in the DB to join with
        """
        _check_dbentities((joined_entity, self._entities.User), (entity_to_join, self._entities.AuthInfo), 'with_user')

        def new_query(q):
            return q.join(entity_to_join, entity_to_join.aiidauser_id == joined_entity.id, isouter=isouterjoin)

        return JoinReturn(new_query)

    def _join_group_node(self, joined_entity, entity_to_join, isouterjoin: bool, **_kw):
        """:param joined_entity:
            The (aliased) ORMclass that is
            a group in the database
        :param entity_to_join:
            The (aliased) ORMClass that is a node and member of the group

        **joined_entity** and **entity_to_join**
        are joined via the table_groups_nodes table.
        from **joined_entity** as group to **enitity_to_join** as node.
        (**enitity_to_join** is *with_group* **joined_entity**)
        """
        _check_dbentities((joined_entity, self._entities.Group), (entity_to_join, self._entities.Node), 'with_group')
        aliased_group_nodes = aliased(self._entities.table_groups_nodes)

        def new_query(q):
            return q.join(aliased_group_nodes, aliased_group_nodes.c.dbgroup_id == joined_entity.id).join(
                entity_to_join, entity_to_join.id == aliased_group_nodes.c.dbnode_id, isouter=isouterjoin
            )

        return JoinReturn(new_query, aliased_group_nodes)

    def _join_node_group(self, joined_entity, entity_to_join, isouterjoin: bool, **_kw):
        """:param joined_entity: The (aliased) node in the database
        :param entity_to_join: The (aliased) Group

        **joined_entity** and **entity_to_join** are
        joined via the table_groups_nodes table.
        from **joined_entity** as node to **enitity_to_join** as group.
        (**enitity_to_join** is a group *with_node* **joined_entity**)
        """
        _check_dbentities((joined_entity, self._entities.Node), (entity_to_join, self._entities.Group), 'with_node')
        aliased_group_nodes = aliased(self._entities.table_groups_nodes)

        def new_query(q):
            return q.join(aliased_group_nodes, aliased_group_nodes.c.dbnode_id == joined_entity.id).join(
                entity_to_join, entity_to_join.id == aliased_group_nodes.c.dbgroup_id, isouter=isouterjoin
            )

        return JoinReturn(new_query, aliased_group_nodes)

    def _join_node_user(self, joined_entity, entity_to_join, isouterjoin: bool, **_kw):
        """:param joined_entity: the aliased node
        :param entity_to_join: the aliased user to join to that node
        """
        _check_dbentities((joined_entity, self._entities.Node), (entity_to_join, self._entities.User), 'with_node')

        def new_query(q):
            return q.join(entity_to_join, entity_to_join.id == joined_entity.user_id, isouter=isouterjoin)

        return JoinReturn(new_query)

    def _join_user_node(self, joined_entity, entity_to_join, isouterjoin: bool, **_kw):
        """:param joined_entity: the aliased user you want to join to
        :param entity_to_join: the (aliased) node or group in the DB to join with
        """
        _check_dbentities((joined_entity, self._entities.User), (entity_to_join, self._entities.Node), 'with_user')

        def new_query(q):
            return q.join(entity_to_join, entity_to_join.user_id == joined_entity.id, isouter=isouterjoin)

        return JoinReturn(new_query)

    def _join_computer_node(self, joined_entity, entity_to_join, isouterjoin: bool, **_kw):
        """:param joined_entity: the (aliased) computer entity
        :param entity_to_join: the (aliased) node entity

        """
        _check_dbentities(
            (joined_entity, self._entities.Computer), (entity_to_join, self._entities.Node), 'with_computer'
        )

        def new_query(q):
            return q.join(entity_to_join, entity_to_join.dbcomputer_id == joined_entity.id, isouter=isouterjoin)

        return JoinReturn(new_query)

    def _join_node_computer(self, joined_entity, entity_to_join, isouterjoin: bool, **_kw):
        """:param joined_entity: An entity that can use a computer (eg a node)
        :param entity_to_join: aliased dbcomputer entity
        """
        _check_dbentities((joined_entity, self._entities.Node), (entity_to_join, self._entities.Computer), 'with_node')

        def new_query(q):
            return q.join(entity_to_join, joined_entity.dbcomputer_id == entity_to_join.id, isouter=isouterjoin)

        return JoinReturn(new_query)

    def _join_group_user(self, joined_entity, entity_to_join, isouterjoin: bool, **_kw):
        """:param joined_entity: An aliased dbgroup
        :param entity_to_join: aliased dbuser
        """
        _check_dbentities((joined_entity, self._entities.Group), (entity_to_join, self._entities.User), 'with_group')

        def new_query(q):
            return q.join(entity_to_join, joined_entity.user_id == entity_to_join.id, isouter=isouterjoin)

        return JoinReturn(new_query)

    def _join_user_group(self, joined_entity, entity_to_join, isouterjoin: bool, **_kw):
        """:param joined_entity: An aliased user
        :param entity_to_join: aliased group
        """
        _check_dbentities((joined_entity, self._entities.User), (entity_to_join, self._entities.Group), 'with_user')

        def new_query(q):
            return q.join(entity_to_join, joined_entity.id == entity_to_join.user_id, isouter=isouterjoin)

        return JoinReturn(new_query)

    def _join_node_comment(self, joined_entity, entity_to_join, isouterjoin: bool, **_kw):
        """:param joined_entity: An aliased node
        :param entity_to_join: aliased comment
        """
        _check_dbentities((joined_entity, self._entities.Node), (entity_to_join, self._entities.Comment), 'with_node')

        def new_query(q):
            return q.join(entity_to_join, joined_entity.id == entity_to_join.dbnode_id, isouter=isouterjoin)

        return JoinReturn(new_query)

    def _join_comment_node(self, joined_entity, entity_to_join, isouterjoin: bool, **_kw):
        """:param joined_entity: An aliased comment
        :param entity_to_join: aliased node
        """
        _check_dbentities(
            (joined_entity, self._entities.Comment), (entity_to_join, self._entities.Node), 'with_comment'
        )

        def new_query(q):
            return q.join(entity_to_join, joined_entity.dbnode_id == entity_to_join.id, isouter=isouterjoin)

        return JoinReturn(new_query)

    def _join_node_log(self, joined_entity, entity_to_join, isouterjoin: bool, **_kw):
        """:param joined_entity: An aliased node
        :param entity_to_join: aliased log
        """
        _check_dbentities((joined_entity, self._entities.Node), (entity_to_join, self._entities.Log), 'with_node')

        def new_query(q):
            return q.join(entity_to_join, joined_entity.id == entity_to_join.dbnode_id, isouter=isouterjoin)

        return JoinReturn(new_query)

    def _join_log_node(self, joined_entity, entity_to_join, isouterjoin: bool, **_kw):
        """:param joined_entity: An aliased log
        :param entity_to_join: aliased node
        """
        _check_dbentities((joined_entity, self._entities.Log), (entity_to_join, self._entities.Node), 'with_log')

        def new_query(q):
            return q.join(entity_to_join, joined_entity.dbnode_id == entity_to_join.id, isouter=isouterjoin)

        return JoinReturn(new_query)

    def _join_user_comment(self, joined_entity, entity_to_join, isouterjoin: bool, **_kw):
        """:param joined_entity: An aliased user
        :param entity_to_join: aliased comment
        """
        _check_dbentities((joined_entity, self._entities.User), (entity_to_join, self._entities.Comment), 'with_user')

        def new_query(q):
            return q.join(entity_to_join, joined_entity.id == entity_to_join.user_id, isouter=isouterjoin)

        return JoinReturn(new_query)

    def _join_authinfo_user(self, joined_entity, entity_to_join, isouterjoin: bool, **_kw):
        """:param joined_entity: An aliased comment
        :param entity_to_join: aliased user
        """
        _check_dbentities(
            (joined_entity, self._entities.AuthInfo), (entity_to_join, self._entities.User), 'with_authinfo'
        )

        def new_query(q):
            return q.join(entity_to_join, joined_entity.aiidauser_id == entity_to_join.id, isouter=isouterjoin)

        return JoinReturn(new_query)

    def _join_comment_user(self, joined_entity, entity_to_join, isouterjoin: bool, **_kw):
        """:param joined_entity: An aliased comment
        :param entity_to_join: aliased user
        """
        _check_dbentities(
            (joined_entity, self._entities.Comment), (entity_to_join, self._entities.User), 'with_comment'
        )

        def new_query(q):
            return q.join(entity_to_join, joined_entity.user_id == entity_to_join.id, isouter=isouterjoin)

        return JoinReturn(new_query)

    def _join_node_outputs(self, joined_entity, entity_to_join, isouterjoin: bool, **_kw):
        """:param joined_entity: The (aliased) ORMclass that is an input
        :param entity_to_join: The (aliased) ORMClass that is an output.

        **joined_entity** and **entity_to_join** are joined with a link
        from **joined_entity** as input to **enitity_to_join** as output
        (**enitity_to_join** is *with_incoming* **joined_entity**)
        """
        _check_dbentities((joined_entity, self._entities.Node), (entity_to_join, self._entities.Node), 'with_incoming')

        aliased_edge = aliased(self._entities.Link)

        def new_query(q):
            return q.join(aliased_edge, aliased_edge.input_id == joined_entity.id, isouter=isouterjoin).join(
                entity_to_join, aliased_edge.output_id == entity_to_join.id, isouter=isouterjoin
            )

        return JoinReturn(new_query, aliased_edge)

    def _join_node_inputs(self, joined_entity, entity_to_join, isouterjoin: bool, **_kw):
        """:param joined_entity: The (aliased) ORMclass that is an output
        :param entity_to_join: The (aliased) ORMClass that is an input.

        **joined_entity** and **entity_to_join** are joined with a link
        from **joined_entity** as output to **enitity_to_join** as input
        (**enitity_to_join** is *with_outgoing* **joined_entity**)

        """
        _check_dbentities((joined_entity, self._entities.Node), (entity_to_join, self._entities.Node), 'with_outgoing')
        aliased_edge = aliased(self._entities.Link)

        def new_query(q):
            return q.join(aliased_edge, aliased_edge.output_id == joined_entity.id).join(
                entity_to_join, aliased_edge.input_id == entity_to_join.id, isouter=isouterjoin
            )

        return JoinReturn(new_query, aliased_edge)

    def _join_node_descendants_recursive(
        self, joined_entity, entity_to_join, isouterjoin: bool, filter_dict: FilterType, expand_path=False
    ):
        """Joining descendants using the recursive functionality
        :TODO: Move the filters to be done inside the recursive query (for example on depth)
        :TODO: Pass an option to also show the path, if this is wanted.
        """
        _check_dbentities((joined_entity, self._entities.Node), (entity_to_join, self._entities.Node), 'with_ancestors')

        link1 = aliased(self._entities.Link)
        link2 = aliased(self._entities.Link)
        node1 = aliased(self._entities.Node)

        link_filters = link1.type.in_((LinkType.CREATE.value, LinkType.INPUT_CALC.value))  # follow input / create links
        in_recursive_filters = self._build_filters(node1, filter_dict)
        if in_recursive_filters is None:
            filters = link_filters
        else:
            filters = and_(in_recursive_filters, link_filters)

        selection_walk_list = [
            link1.input_id.label('ancestor_id'),
            link1.output_id.label('descendant_id'),
            type_cast(0, Integer).label('depth'),
        ]
        if expand_path:
            selection_walk_list.append(array((link1.input_id, link1.output_id)).label('path'))

        walk = (
            select(*selection_walk_list)
            .select_from(join(node1, link1, link1.input_id == node1.id))
            .where(filters)
            .cte(recursive=True)
        )

        aliased_walk = aliased(walk)

        selection_union_list = [
            aliased_walk.c.ancestor_id.label('ancestor_id'),
            link2.output_id.label('descendant_id'),
            (aliased_walk.c.depth + type_cast(1, Integer)).label('current_depth'),
        ]
        if expand_path:
            selection_union_list.append((aliased_walk.c.path + array((link2.output_id,))).label('path'))

        descendants_recursive = aliased(
            aliased_walk.union_all(
                select(*selection_union_list)
                .select_from(
                    join(
                        aliased_walk,
                        link2,
                        link2.input_id == aliased_walk.c.descendant_id,
                    )
                )
                .where(link2.type.in_((LinkType.CREATE.value, LinkType.INPUT_CALC.value)))
            )
        )  # .alias()

        def new_query(q):
            return q.join(descendants_recursive, descendants_recursive.c.ancestor_id == joined_entity.id).join(
                entity_to_join, descendants_recursive.c.descendant_id == entity_to_join.id, isouter=isouterjoin
            )

        return JoinReturn(new_query, descendants_recursive.c)

    def _join_node_ancestors_recursive(
        self, joined_entity, entity_to_join, isouterjoin: bool, filter_dict: FilterType, expand_path=False
    ):
        """Joining ancestors using the recursive functionality
        :TODO: Move the filters to be done inside the recursive query (for example on depth)
        :TODO: Pass an option to also show the path, if this is wanted.

        """
        _check_dbentities((joined_entity, self._entities.Node), (entity_to_join, self._entities.Node), 'with_ancestors')

        link1 = aliased(self._entities.Link)
        link2 = aliased(self._entities.Link)
        node1 = aliased(self._entities.Node)

        link_filters = link1.type.in_((LinkType.CREATE.value, LinkType.INPUT_CALC.value))  # follow input / create links
        in_recursive_filters = self._build_filters(node1, filter_dict)
        if in_recursive_filters is None:
            filters = link_filters
        else:
            filters = and_(in_recursive_filters, link_filters)

        selection_walk_list = [
            link1.input_id.label('ancestor_id'),
            link1.output_id.label('descendant_id'),
            type_cast(0, Integer).label('depth'),
        ]
        if expand_path:
            selection_walk_list.append(array((link1.output_id, link1.input_id)).label('path'))

        walk = (
            select(*selection_walk_list)
            .select_from(join(node1, link1, link1.output_id == node1.id))
            .where(filters)
            .cte(recursive=True)
        )

        aliased_walk = aliased(walk)

        selection_union_list = [
            link2.input_id.label('ancestor_id'),
            aliased_walk.c.descendant_id.label('descendant_id'),
            (aliased_walk.c.depth + type_cast(1, Integer)).label('current_depth'),
        ]
        if expand_path:
            selection_union_list.append((aliased_walk.c.path + array((link2.input_id,))).label('path'))

        ancestors_recursive = aliased(
            aliased_walk.union_all(
                select(*selection_union_list)
                .select_from(
                    join(
                        aliased_walk,
                        link2,
                        link2.output_id == aliased_walk.c.ancestor_id,
                    )
                )
                .where(link2.type.in_((LinkType.CREATE.value, LinkType.INPUT_CALC.value)))
                # I can't follow RETURN or CALL links
            )
        )

        def new_query(q):
            return q.join(ancestors_recursive, ancestors_recursive.c.descendant_id == joined_entity.id).join(
                entity_to_join, ancestors_recursive.c.ancestor_id == entity_to_join.id, isouter=isouterjoin
            )

        return JoinReturn(new_query, ancestors_recursive.c)


def _check_dbentities(entities_cls_joined, entities_cls_to_join, relationship: str):
    """Type check for entities

    :param entities_cls_joined:
        A tuple of the aliased class passed as joined_entity and the ormclass that was expected
    :type entities_cls_to_join: tuple
    :param entities_cls_joined:
        A tuple of the aliased class passed as entity_to_join and the ormclass that was expected
    :type entities_cls_to_join: tuple
    :param str relationship:
        The relationship between the two entities to make the Exception comprehensible
    """
    for entity, cls in (entities_cls_joined, entities_cls_to_join):
        if not issubclass(entity._sa_class_manager.class_, cls):
            raise TypeError(
                "You are attempting to join {} as '{}' of {}\n"
                'This failed because you passed:\n'
                ' - {} as entity joined (expected {})\n'
                ' - {} as entity to join (expected {})\n'
                '\n'.format(
                    entities_cls_joined[0].__name__,
                    relationship,
                    entities_cls_to_join[0].__name__,
                    entities_cls_joined[0]._sa_class_manager.class_.__name__,
                    entities_cls_joined[1].__name__,
                    entities_cls_to_join[0]._sa_class_manager.class_.__name__,
                    entities_cls_to_join[1].__name__,
                )
            )
