###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Entities for the AiiDA Graph Explorer utility"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections import namedtuple
from typing import Any, Literal, TypedDict, overload

from aiida import orm
from aiida.common.typing import Self, TypeAlias
from aiida.orm.utils.links import LinkQuadruple

VALID_ENTITY_CLASSES = (orm.Node, orm.Group)

GroupNodeEdge = namedtuple('GroupNodeEdge', ['node_id', 'group_id'])

_NodeOrGroupCls: TypeAlias = 'type[orm.Node] | type[orm.Group]'
_ContainerTypes: TypeAlias = 'list[Any] | tuple[Any, ...] | set[Any]'
_EdgeType: TypeAlias = 'type[LinkQuadruple] | type[GroupNodeEdge]'
_EdgeIdentifiers: TypeAlias = tuple[tuple[str, str], ...]


class AbstractSetContainer(metaclass=ABCMeta):
    """Abstract Class

    This class defines a set that can be speciaized to contain either
    nodes (either AiiDA nodes or Aiida groups) or edges (AiiDA links,
    or records of the connections between groups and nodes).
    Instances of this class reference a subset of entities in a database
    via a unique identifier.
    There are also a few operators defined, for simplicity, to do
    set-additions (unions) and deletions.
    The underlying Python-class is **set**, which means that adding
    an instance to an AiidaEntitySet that is already contained by it
    will not create a duplicate.
    """

    def __init__(self) -> None:
        """Initialization method"""
        super().__init__()
        self._keyset: set[Any] = set()

    @abstractmethod
    def _check_self_and_other(self, other: Self) -> None:
        """Utility function

        When called, will check whether self and other instance are compatible.
        (i.e. if they contain the same AiiDA class, same identifiers, length of
        tuples, etc)

        :type other: :py:class:`aiida.tools.graph.age_entities.AbstractSetContainer`
        :param other: the other entity to check for compatibility.
        """

    @abstractmethod
    def _check_input_for_set(self, input_for_set: Any) -> Any:
        """Utility function

        When provinding input keys for the internal set, this utility function will
        check and process the input accordingly.

        :param input_for_set: input argument for the keyset (must be either an
            AiiDA instance of node or group, or an identifier of the type used
            by the container).
        """

    @abstractmethod
    def get_template(self) -> Self:
        """Create new instance with the same defining attributes."""

    @property
    def keyset(self) -> set[Any]:
        """Set containing the keys of the entities"""
        return self._keyset

    @keyset.setter
    def keyset(self, inpset: set[Any] | None) -> None:
        """Setter for the keyset

        Use with care! There is no way to check if the keys are consistent ids here.
        Checks should be performed upstream in the code, previous to calling this setter.

        :type inpset: set or None
        :param inpset: input set of identifiers that will become the new set contained
        """
        if inpset is None:
            self._keyset = set()
        elif isinstance(inpset, set):
            self._keyset = inpset
        else:
            raise ValueError('keyset must be assigned a set or None')

    def __add__(self, other: Self) -> Self:
        """Addition (return = self + other): defined as the set union"""
        self._check_self_and_other(other)
        new = self.get_template()
        new.keyset = self.keyset.union(other.keyset)
        return new

    def __iadd__(self, other: Self) -> Self:
        """Addition inplace (self += other)"""
        self._check_self_and_other(other)
        self.keyset = self.keyset.union(other.keyset)
        return self

    def __sub__(self, other: Self) -> Self:
        """Subtraction (return = self - other): defined as the set-difference"""
        self._check_self_and_other(other)
        new = self.get_template()
        new.keyset = self.keyset.difference(other.keyset)
        return new

    def __isub__(self, other: Self) -> Self:
        """Subtraction inplace (self -= other)"""
        self._check_self_and_other(other)
        self.keyset = self.keyset.difference(other.keyset)
        return self

    def __len__(self) -> int:
        return len(self.keyset)

    def __repr__(self) -> str:
        return f"{{{','.join(map(str, self.keyset))}}}"

    def __eq__(self, other: Any) -> Any:
        return self.keyset == other.keyset

    def __ne__(self, other: Any) -> bool:
        return not self == other

    def set_entities(self, new_entitites: _ContainerTypes) -> None:
        """Replaces contained set with the new entities.

        :param new_entities: entities which will replace the ones contained
            by the EntitySet. Must be an AiiDA instance (Node or Group) or
            an appropriate identifier (ID).
        """
        self.keyset = set(map(self._check_input_for_set, new_entitites))

    def add_entities(self, new_entitites: _ContainerTypes) -> None:
        """Add new entitities to the existing set of self.

        :param new_entities: an iterable of new entities to add.
        """
        self.keyset = self.keyset.union(list(map(self._check_input_for_set, new_entitites)))

    def copy(self) -> Self:
        """Create new instance with the same defining attributes and the same keyset."""
        new = self.get_template()
        new.keyset = self.keyset.copy()
        return new

    def empty(self) -> None:
        """Resets the contained set to be an empty set"""
        self.keyset = set()


class AiidaEntitySet(AbstractSetContainer):
    """Extension of AbstractSetContainer

    This class is used to store `graph nodes` (aidda nodes or aiida groups).
    """

    def __init__(self, aiida_cls: _NodeOrGroupCls):
        """Initialization method

        :param aiida_cls: a valid AiiDA ORM class (Node or Group supported).
        """
        super().__init__()
        if aiida_cls not in VALID_ENTITY_CLASSES:
            raise TypeError(f'aiida_cls has to be among:{VALID_ENTITY_CLASSES}')
        self._aiida_cls = aiida_cls
        self.keyset = set()
        # Currently only 'id' is supported
        self._identifier: Literal['id'] = 'id'
        self._identifier_type = int

    def _check_self_and_other(self, other: Self) -> None:
        if not isinstance(other, AiidaEntitySet):
            raise TypeError('Other class is not an instance of AiidaEntitySet')
        if self.aiida_cls != other.aiida_cls:
            raise TypeError('The two instances do not have the same aiida type!')
        if self.identifier != other.identifier:
            raise ValueError('The two instances do not have the same identifier!')
        if self._identifier_type != other.identifier_type:
            raise TypeError('The two instances do not have the same identifier type!')

    def _check_input_for_set(self, input_for_set: _NodeOrGroupCls | int) -> Any:
        if isinstance(input_for_set, self._aiida_cls):
            return getattr(input_for_set, self._identifier)

        if isinstance(input_for_set, self._identifier_type):
            return input_for_set

        raise ValueError(
            '{} is not a valid input\n'
            'You can either pass an AiiDA instance or a key to an instance that'
            'matches the identifier you defined ({})'.format(input_for_set, self._identifier_type)
        )

    def get_template(self) -> AiidaEntitySet:
        return AiidaEntitySet(aiida_cls=self.aiida_cls)

    @property
    def identifier(self) -> Literal['id']:
        """Identifier used for the nodes or groups (currently always id)"""
        return self._identifier

    @property
    def identifier_type(self) -> type[int]:
        """Type of identifier for the node or group (for id is int)"""
        return self._identifier_type

    @property
    def aiida_cls(self) -> _NodeOrGroupCls:
        """Class of nodes contained in the entity set (node or group)"""
        return self._aiida_cls


class DirectedEdgeSet(AbstractSetContainer):
    """Extension of AbstractSetContainer

    This class is used to store `graph edges` (aidda nodes or aiida groups).
    """

    def __init__(self, aiida_cls_to: _NodeOrGroupCls, aiida_cls_from: _NodeOrGroupCls):
        """Initialization method

        The classes that the link connects must be provided.

        :param aiida_cls_to: a valid AiiDA ORM class (Node or Group supported).
        :param aiida_cls_from: a valid AiiDA ORM class (Node supported).
        """
        super().__init__()
        for aiida_cls in (aiida_cls_to, aiida_cls_from):
            if aiida_cls not in VALID_ENTITY_CLASSES:
                raise TypeError(f'aiida_cls has to be among:{VALID_ENTITY_CLASSES}')
        self._aiida_cls_to = aiida_cls_to
        self._aiida_cls_from = aiida_cls_from
        self.keyset = set()

        # I need to get the identifiers for the edge. For now, these should be hardcoded
        if aiida_cls_from is orm.Node:
            if aiida_cls_to is orm.Node:
                # This is a Node-Node connection, therefore I will get information on the links
                self._edge_identifiers: _EdgeIdentifiers = (
                    ('edge', 'input_id'),
                    ('edge', 'output_id'),
                    ('edge', 'type'),
                    ('edge', 'label'),
                )
                self._edge_namedtuple: _EdgeType = LinkQuadruple
            elif aiida_cls_to is orm.Group:
                self._edge_identifiers = (('nodes', 'id'), ('groups', 'id'))
                self._edge_namedtuple = GroupNodeEdge
            else:
                raise TypeError(f'Unexpted types aiida_cls_from={aiida_cls_from} and aiida_cls_to={aiida_cls_to}')
        else:
            raise TypeError(f'Unexpted types aiida_cls_from={aiida_cls_from} and aiida_cls_to={aiida_cls_to}')

    def _check_self_and_other(self, other: Self) -> None:
        if not isinstance(other, DirectedEdgeSet):
            raise TypeError('Other class is not an instance of AiidaEntitySet')
        if self.aiida_cls_to != other.aiida_cls_to:
            raise TypeError('The two instances do not have the same aiida type!')
        if self.aiida_cls_from != other.aiida_cls_from:
            raise TypeError('The two instances do not have the same aiida type!')
        if self.edge_namedtuple != other.edge_namedtuple:
            raise ValueError('The two instances do not have the same identifiers!')

    def _check_input_for_set(self, input_for_set: tuple[Any, ...]) -> tuple[Any, ...]:
        if not isinstance(input_for_set, tuple):
            raise TypeError(f'value for `input_for_set` {input_for_set} is not a tuple')
        if len(input_for_set) != len(self._edge_identifiers):
            inputs_len = len(input_for_set)
            inside_len = len(self._edge_identifiers)
            raise ValueError(f'tuple passed has len = {inputs_len}, but there are {inside_len} identifiers')
        return input_for_set

    def get_template(self) -> DirectedEdgeSet:
        return DirectedEdgeSet(aiida_cls_to=self.aiida_cls_to, aiida_cls_from=self.aiida_cls_from)

    @property
    def aiida_cls_to(self) -> _NodeOrGroupCls:
        """The class of nodes which the edge points to"""
        return self._aiida_cls_to

    @property
    def aiida_cls_from(self) -> _NodeOrGroupCls:
        """The class of nodes which the edge points from"""
        return self._aiida_cls_from

    @property
    def edge_namedtuple(self) -> _EdgeType:
        """The namedtuple type used for the edges` identifiers"""
        return self._edge_namedtuple

    @property
    def edge_identifiers(self) -> _EdgeIdentifiers:
        """The identifiers for the edges"""
        return self._edge_identifiers


# NOTE: Lot of the remaining type-ignores in the Basket class are due to
# https://github.com/python/mypy/issues/7981
class _BasketDict(TypedDict):
    nodes: AiidaEntitySet
    groups: AiidaEntitySet
    nodes_nodes: DirectedEdgeSet
    groups_nodes: DirectedEdgeSet


_BasketKeys: TypeAlias = Literal['nodes', 'groups', 'nodes_nodes', 'groups_nodes']
_BasketValues: TypeAlias = 'AiidaEntitySet | DirectedEdgeSet'


class Basket:
    """Container for several instances of
    :py:class:`aiida.tools.graph.age_entities.AiidaEntitySet` .

    In the current implementation, it contains one EntitySet for Nodes and one for Groups,
    and one EdgeSet for Node-Node edges (links) and one for Group-Node connections.
    """

    def __init__(
        self,
        nodes: AiidaEntitySet | _ContainerTypes | None = None,
        groups: AiidaEntitySet | _ContainerTypes | None = None,
        nodes_nodes: DirectedEdgeSet | None = None,
        groups_nodes: DirectedEdgeSet | None = None,
    ):
        """Initialization method

        During initialization of the basket, both the sets of nodes and the set of
        groups can be provided as one of the following: an AiidaEntitySet with the
        respective type (node or group) or a list/set/tuple with the ids of the
        respective node or group.

        :param nodes: AiiDA nodes provided in an acceptable way.
        :param groups: AiiDA groups provided in an acceptable way.
        """

        def get_check_set_entity_set(
            input_object: AiidaEntitySet | _ContainerTypes | None, keyword: str, aiida_class: _NodeOrGroupCls
        ) -> AiidaEntitySet:
            if input_object is None:
                output_set = AiidaEntitySet(aiida_class)
                return output_set

            if isinstance(input_object, (list, tuple, set)):
                output_set = AiidaEntitySet(aiida_class)
                output_set.set_entities(input_object)
                return output_set

            if isinstance(input_object, AiidaEntitySet):
                if input_object.aiida_cls is not aiida_class:
                    raise TypeError(f'{keyword}  has to  have {aiida_class} as aiida_cls')
                return input_object

            else:
                raise ValueError(
                    'Input object is of type {}.\n'
                    'Instead, it should be either None or one of:\n'
                    ' - {}\n - {}\n - {}\n - {}\n'.format(input_object, AiidaEntitySet, list, tuple, set)
                )

        def get_check_set_directed_edge_set(
            var: DirectedEdgeSet | None, keyword: str, cls_from: _NodeOrGroupCls, cls_to: _NodeOrGroupCls
        ) -> DirectedEdgeSet:
            if var is None:
                return DirectedEdgeSet(aiida_cls_to=cls_to, aiida_cls_from=cls_from)

            if not isinstance(var, DirectedEdgeSet):
                raise TypeError(f'{keyword} has to be an instance of DirectedEdgeSet or None')

            if var.aiida_cls_from is not cls_from:
                raise TypeError(f'{keyword} has to have {cls_from} as aiida_cls_from')
            elif var.aiida_cls_to is not cls_to:
                raise TypeError(f'{keyword} has to have {cls_to} as aiida_cls_to')
            else:
                return var

        nodes = get_check_set_entity_set(nodes, 'nodes', orm.Node)
        groups = get_check_set_entity_set(groups, 'groups', orm.Group)
        nodes_nodes = get_check_set_directed_edge_set(nodes_nodes, 'nodes-nodes', orm.Node, orm.Node)
        groups_nodes = get_check_set_directed_edge_set(groups_nodes, 'groups-nodes', orm.Node, orm.Group)
        self._dict: _BasketDict = dict(nodes=nodes, groups=groups, nodes_nodes=nodes_nodes, groups_nodes=groups_nodes)

    @property
    def sets(self) -> tuple[Any, ...]:
        """All sets in the basket returned as an ordered list.
        The order is: 'groups', 'groups_nodes', 'nodes', 'nodes_nodes'.
        """
        return list(zip(*sorted(self.dict.items())))[1]

    @property
    def dict(self) -> _BasketDict:
        """All sets in the basket returned as a dictionary.
        This includes the keys 'nodes', 'groups', 'nodes_nodes' and 'nodes_groups'.
        """
        return self._dict

    @property
    def nodes(self) -> AiidaEntitySet:
        """Set of nodes stored in the basket"""
        return self._dict['nodes']

    @property
    def groups(self) -> AiidaEntitySet:
        """Set of groups stored in the basket"""
        return self._dict['groups']

    @overload
    def __getitem__(self, key: Literal['nodes', 'groups']) -> AiidaEntitySet: ...

    @overload
    def __getitem__(self, key: Literal['nodes_nodes', 'groups_nodes']) -> DirectedEdgeSet: ...

    def __getitem__(self, key: _BasketKeys) -> _BasketValues:
        return self._dict[key]

    def __setitem__(self, key: _BasketKeys, val: _BasketValues) -> None:
        self._dict[key] = val

    def __add__(self, other: Self) -> 'Basket':
        new_dict = {}
        for key, value in self._dict.items():
            new_dict[key] = value + other.dict[key]  # type: ignore[literal-required]
        return Basket(**new_dict)

    def __iadd__(self, other: Self) -> Self:
        for key in self._dict:
            self[key] += other[key]  # type: ignore[index,call-overload]
        return self

    def __sub__(self, other: Self) -> 'Basket':
        new_dict = {}
        for key in self._dict:
            new_dict[key] = self[key] - other[key]  # type: ignore[call-overload]
        return Basket(**new_dict)

    def __isub__(self, other: Self) -> Self:
        for key in other.dict:
            self[key] -= other[key]  # type: ignore[call-overload,index]
        return self

    def __len__(self) -> int:
        return sum(len(s) for s in self.sets)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Basket):
            return False
        for key in self._dict:
            if self[key] != other[key]:  # type: ignore[call-overload]
                return False
        return True

    def __ne__(self, other: Any) -> bool:
        return not self == other

    def __repr__(self) -> str:
        """Return string representation."""
        ret_str = ''
        for key, val in self._dict.items():
            ret_str += f'  {key}: '
            ret_str += f'{val!s}\n'
        return ret_str

    def empty(self) -> None:
        """Empty every subset from its content"""
        for set_ in self._dict.values():
            set_.empty()  # type: ignore[attr-defined]

    def get_template(self) -> 'Basket':
        """Create new nasket with the same defining attributes for its internal containers."""
        new_dict = {}
        for key, val in self._dict.items():
            new_dict[key] = val.get_template()  # type: ignore[attr-defined]
        return Basket(**new_dict)

    def copy(self) -> 'Basket':
        """Create new instance with the same defining attributes and content."""
        new_dict = {}
        for key, val in self._dict.items():
            new_dict[key] = val.copy()  # type: ignore[attr-defined]
        return Basket(**new_dict)
