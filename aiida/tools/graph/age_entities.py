# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=unnecessary-pass
"""AGE entities"""

from abc import ABCMeta, abstractmethod
from aiida.orm import Node, Group
from aiida.orm.querybuilder import QueryBuilder

VALID_ENTITY_CLASSES = (Node, Group)


class AbstractSetContainer(metaclass=ABCMeta):
    """Abstract Set Container"""

    @abstractmethod
    def _check_self_and_other(self, other):
        """
        Utility function. When called, will check whether self and other instance
        are compatible. Same aiida classes, same identifiers, length of tuples...
        """
        pass

    @abstractmethod
    def _check_input_for_set(self, input_for_set):
        """
        When giving me something to the set, this utility function can be used
        to do the right thing.
        """
        pass

    @abstractmethod
    def copy(self, with_data=False):
        """
        Copy
        """
        pass

    def __init__(self):
        super().__init__()
        self._set = None
        self._additional_identifiers = ()

    def __len__(self):
        return len(self._set)

    def __add__(self, other):
        """
        Addition of self and another AiidaEntitySet, given by the union of their sets::

            a = Enitity(...)
            b = Entity(...)
            c = a+b # new set that contains everything in a and b
        """
        self._check_self_and_other(other)
        new = self.copy(with_data=False)  # , identifier=self.identifier)
        new.set_key_set_nocheck(self._set.union(other.get_keys()))
        return new

    def __iadd__(self, other):
        """
        Adding inplace::

            a = Entity(...)
            b = Entity(...)
            a += b # now a contains also everything that was in b
        """
        self._check_self_and_other(other)
        self.set_key_set_nocheck(self._set.union(other.get_keys()))
        return self

    def __sub__(self, other):
        """
        Subtraction, defined as the set-difference between two entities
        """
        self._check_self_and_other(other)
        new = self.copy(with_data=False)  #, identifier=self.identifier)
        new.set_key_set_nocheck(self._set.difference(other.get_keys()))
        return new

    def __isub__(self, other):
        """
        subtracting inplace!
        """
        self._check_self_and_other(other)
        self._set = self._set.difference(other.get_keys())
        return self

    def __repr__(self):
        return '{{{}}}'.format(','.join(map(str, self._set)))

    def __eq__(self, other):
        return self._set == other.get_keys()

    def __ne__(self, other):
        return not self == other

    def set_entities(self, new_entitites):
        """
        Replacing my set with the new entities, given by their identifier.
        """
        self._set = set(map(self._check_input_for_set, new_entitites))

    def add_entities(self, new_entitites):
        """
        Add new entitities to the existing set of self
        :param new_entities: An iterable of new entities to add.
        """
        self._set = self._set.union(list(map(self._check_input_for_set, new_entitites)))

    def get_keys(self):
        return self._set

    def get_additional_identifiers(self):
        return self._additional_identifiers

    def set_key_set_nocheck(self, _set):
        """
        Use with care! If you know that the new set is valid, call this function.
        Has the advantage of not checking every entry.
        """
        self._set = _set

    def empty(self):
        """
        Nulls the set
        """
        self._set = set()


class AiidaEntitySet(AbstractSetContainer):
    """
    Instances of this class reference a subset of entities in a databases
    via a unique identifier.
    There are also a few operators defined, for simplicity,
    to do set-additions (unions) and deletions.
    The underlying Python-class is **set**, which means that adding an instance
    again to an AiidaEntitySet will not create a duplicate.
    """

    def __init__(self, aiida_cls):
        """
        :param aiida_cls: A valid AiiDA ORM class, i.e. Node, Group, Computer
        """
        super().__init__()
        if not aiida_cls in VALID_ENTITY_CLASSES:
            raise TypeError('aiida_cls has to be among:{}'.format(VALID_ENTITY_CLASSES))
        # Done with checks, saving to attributes:
        self._aiida_cls = aiida_cls
        # The _set is the set where keys are set:
        self._set = set()
        # The identifier for the key, when I get instance classes it has a type
        # that I check as well
        self._identifier = 'id'
        self._identifier_type = int
        # For the future: Customize both _identifier and _identifier_type.
        # (uuid or name (for groups) could also work)

    def _check_self_and_other(self, other):
        """
        Utility function. When called, will check whether self and other instance
        are compatible. Same aiida classes, same identifiers, etc...
        """
        if not isinstance(other, AiidaEntitySet):
            raise TypeError('Other class is not an instance of AiidaEntitySet')
        if self.aiida_cls != other.aiida_cls:
            raise TypeError('The two instances do not have the same aiida type!')
        if self.identifier != other.identifier:
            raise ValueError('The two instances do not have the same identifier!')
        if self._identifier_type != other.identifier_type:
            raise TypeError('The two instances do not have the same identifier type!')
        return True

    @property
    def identifier(self):
        return self._identifier

    @property
    def identifier_type(self):
        return self._identifier_type

    @property
    def aiida_cls(self):
        return self._aiida_cls

    def _check_input_for_set(self, input_for_set):
        """
        When giving me something to the set, this utility function can be used
        to do the right thing.
        """
        if isinstance(input_for_set, self._aiida_cls):
            return getattr(input_for_set, self._identifier)

        if isinstance(input_for_set, self._identifier_type):
            return input_for_set

        raise ValueError(
            '{} is not a valid input\n'
            'You can either pass an AiiDA instance or a key to an instance that'
            'matches the identifier you defined ({})'.format(input_for_set, self._identifier_type)
        )

    def copy(self, with_data=True):
        """
        Create a new instance, with the attributes defining being the same.
        :param bool with_data: Whether to copy also the data.
        """
        new = AiidaEntitySet(aiida_cls=self.aiida_cls)  #
        #  , identifier=self.identifier, identifier_type=self._identifier_type)
        if with_data:
            new.set_key_set_nocheck(self._set.copy())
        return new

    def get_entities(self):
        """
        Return the AiiDA entities
        """
        for entity, in QueryBuilder().append(
            self._aiida_cls, project='*', filters={
                self._identifier: {
                    'in': self._set
                }
            }
        ).iterall():
            yield entity


class DirectedEdgeSet(AbstractSetContainer):
    """
    Instances of this class reference a subset of edges in a databases
    via the unique identifiers.
    The underlying Python-class is **set**, which means that adding an instance
    again to an AiidaEntitySet will not create a duplicate.
    """

    @property
    def aiida_cls_to(self):
        return self._aiida_cls_to

    @property
    def aiida_cls_from(self):
        return self._aiida_cls_from

    def __init__(self, aiida_cls_to, aiida_cls_from, additional_identifiers=None):
        """
        :param aiida_cls: A valid AiiDA ORM class, i.e. Node, Group, Computer
        """
        super().__init__()
        for aiida_cls in (aiida_cls_to, aiida_cls_from):
            if not aiida_cls in VALID_ENTITY_CLASSES:
                raise TypeError('aiida_cls has to be among:{}'.format(VALID_ENTITY_CLASSES))
        # Done with checks, saving to attributes:
        self._aiida_cls_to = aiida_cls_to
        self._aiida_cls_from = aiida_cls_from
        # The _set is the set where keys are set:
        self._set = set()

        # the additional identifiers for the key
        if additional_identifiers is None:
            self._additional_identifiers = tuple()
        elif not isinstance(additional_identifiers, (tuple, list)):
            raise TypeError('Identifiers need to be a list or tuple')
        else:
            self._additional_identifiers = tuple(additional_identifiers)

        # The following attribute defines the edge specification that are enforced and stored,
        # In addition to the primary keys that are stored anyway.
        # I.e. for node to node this could be (type, label).
        self._len_additional_identifiers = len(self._additional_identifiers)
        self._len_all_identifiers = 2 + self._len_additional_identifiers

    def _check_self_and_other(self, other):
        """
        Utility function. When called, will check whether self and other instance
        are compatible. Same aiida classes, same identifiers, etc...
        """
        if not isinstance(other, DirectedEdgeSet):
            raise TypeError('Other class is not an instance of AiidaEntitySet')
        if self.aiida_cls_to != other.aiida_cls_to:
            raise TypeError('The two instances do not have the same aiida type!')
        if self.aiida_cls_from != other.aiida_cls_from:
            raise TypeError('The two instances do not have the same aiida type!')
        if self._additional_identifiers != other.get_additional_identifiers():
            raise ValueError('The two instances do not have the same identifiers!')
        return True

    def _check_input_for_set(self, input_for_set):
        """
        When giving me something to the set, this utility function can be used
        to do the right thing.
        """
        if isinstance(input_for_set, tuple):
            if len(input_for_set) != self._len_all_identifiers:
                raise ValueError(
                    'The tuple you passed has not the right length {} != {}'.format(
                        len(tuple), self._len_all_identifiers
                    )
                )
            return input_for_set

        raise TypeError('{} is not a valid input\n' 'It has to be a tuple'.format(input_for_set))

    def copy(self, with_data=True):
        """
        Create a new instance, with the attributes defining being the same.
        :param bool with_data: Whether to copy also the data.
        """
        new = DirectedEdgeSet(
            aiida_cls_to=self.aiida_cls_to,
            aiida_cls_from=self.aiida_cls_from,
            additional_identifiers=self._additional_identifiers
        )  #
        #  , identifier=self.identifier, identifier_type=self._identifier_type)
        if with_data:
            new.set_key_set_nocheck(self._set.copy())
        return new


class Basket():
    """
    Basket are a container for several AiidaEntitySet.
    In the current implementation, they contain a Node "set" and a Group "set".
    :TODO: Computers and Users!
    """

    def __init__(self, nodes=None, groups=None, nodes_nodes=None):
        """
        :param nodes: An AiidaEntitySet of Node
        :param groups: An AiidaEntitySet of Group
        """

        def get_check_set_entity_set(var, keyword, cls):
            if var is None:
                return AiidaEntitySet(cls)

            if isinstance(var, AiidaEntitySet):
                if var.aiida_cls is cls:
                    return var
                raise TypeError('{}  has to  have {} as aiida_cls'.format(keyword, cls))

            else:
                raise TypeError('{} has to be an instance of AiidaEntitySet'.format(keyword))

        def get_check_set_directed_edge_set(var, keyword, cls_from, cls_to, additional_identifiers):
            if var is None:
                return DirectedEdgeSet(
                    aiida_cls_to=cls_to, aiida_cls_from=cls_from, additional_identifiers=additional_identifiers
                )
            if isinstance(var, DirectedEdgeSet):
                if var.aiida_cls_from is not cls_from:
                    raise TypeError('{} has to  have {} as aiida_cls_from'.format(keyword, cls_from))
                elif var.aiida_cls_to is not cls_to:
                    raise TypeError('{} has to  have {} as aiida_cls_to'.format(keyword, cls_to))
                else:
                    return var
            else:
                raise TypeError('{} has to be an instance of DirectedEdgeSet'.format(keyword))

        nodes = get_check_set_entity_set(nodes, 'nodes', Node)
        groups = get_check_set_entity_set(groups, 'groups', Group)
        nodes_nodes = get_check_set_directed_edge_set(
            nodes_nodes, 'nodes-nodes', Node, Node, additional_identifiers=('label', 'type')
        )

        # ~ if nodes is None:
        # ~ nodes = AiidaEntitySet(Node) #, identifier='id', identifier_type=int)
        # ~ elif isinstance(nodes, AiidaEntitySet):
        # ~ pass
        # ~ else:

        # ~ if groups is None:
        # ~ groups = AiidaEntitySet(Group) #, identifier='id', identifier_type=int)
        # ~ elif isinstance(groups, AiidaEntitySet):
        # ~ pass
        # ~ else:
        # ~ raise TypeError("groups has to be an instance of AiidaEntitySet")
        # the Edges:
        # ~ nodes_nodes = AiidaEdgeSet(Node, Node, additional_identifiers=('type', 'label'))
        # ~ nodes_groups = AiidaEdgeSet(Node, Group, additional_identifiers=())
        self._dict = dict(
            nodes=nodes,
            groups=groups,
            nodes_nodes=nodes_nodes,  #nodes_groups=nodes_groups
        )

    @property
    def sets(self):
        return list(zip(*sorted(self.dict.items())))[1]

    @property
    def dict(self):
        return self._dict

    @property
    def nodes(self):
        return self._dict['nodes']

    @property
    def groups(self):
        return self._dict['groups']

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, val):
        self._dict[key] = val

    def __add__(self, other):
        new_dict = {}
        for key in self._dict:
            new_dict[key] = self._dict[key] + other.dict[key]
        return Basket(**new_dict)

    def __iadd__(self, other):
        for key in self._dict:
            self[key] += other[key]
        return self

    def __sub__(self, other):
        new_dict = {}
        for key in self._dict:
            new_dict[key] = self[key] - other[key]
        return Basket(**new_dict)

    def __isub__(self, other):
        for key in other.dict:
            self[key] -= other[key]
        return self

    def __len__(self):
        return sum([len(s) for s in self.sets])

    def __eq__(self, other):
        for key in self._dict:
            if self[key] != other[key]:
                return False
        return True

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        ret_str = ''
        for key, val in self._dict.items():
            ret_str += '  ' + key + ': '
            ret_str += str(val) + '\n'
        return ret_str

    def empty(self):
        """
        Empty every subset from its content
        """
        for set_ in self._dict.values():
            set_.empty()

    def copy(self, with_data=True):
        new_dict = dict()
        for key, val in self._dict.items():
            new_dict[key] = val.copy(with_data=with_data)
        return Basket(**new_dict)


def get_basket(node_ids=None, group_ids=None):
    """
    Utility function to get an instance of Basket.
    :param node_ids: An iterable of node-ids (pks) that are wanted
    :param group_ids: An iterable group-ids (pks) that are wanted in the set

    Examples::
        # Will return the collection
        aiida_entitiy_sets = get_entit_sets(node_ids=(1,2), group_ids=8)
    """

    node_set = AiidaEntitySet(Node)  #, identifier='id', identifier_type=int)
    if node_ids:
        node_set.set_entities(node_ids)
    group_set = AiidaEntitySet(Group)  #, identifier='id', identifier_type=int)
    if group_ids:
        group_set.set_entities(group_ids)

    return Basket(nodes=node_set, groups=group_set)
