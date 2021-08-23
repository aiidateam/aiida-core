# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
The QueryBuilder: A class that allows you to query the AiiDA database, independent from backend.
Note that the backend implementation is enforced and handled with a composition model!
:func:`QueryBuilder` is the frontend class that the user can use. It inherits from *object* and contains
backend-specific functionality. Backend specific functionality is provided by the implementation classes.

These inherit from :func:`aiida.orm.implementation.BackendQueryBuilder`,
an interface classes which enforces the implementation of its defined methods.
An instance of one of the implementation classes becomes a member of the :func:`QueryBuilder` instance
when instantiated by the user.
"""
import copy
from datetime import date, datetime, timedelta
from enum import Enum
from functools import partial
from inspect import isclass as inspect_isclass
import logging
from typing import (
    Any, Dict, Iterable, Iterator, List, NamedTuple, Optional, Sequence, Set, Tuple, Type, Union, TYPE_CHECKING
)
import warnings

from sqlalchemy import func as sa_func
from sqlalchemy.orm.util import AliasedClass

from aiida.manage.manager import get_manager

from . import authinfos
from . import comments
from . import computers
from . import groups
from . import logs
from . import nodes
from . import users
from . import entities
from . import convert

try:
    from typing import TypedDict  # pylint: disable=ungrouped-imports
except ImportError:
    # Python <3.8 backport
    from typing_extensions import TypedDict

if TYPE_CHECKING:
    # pylint: disable=ungrouped-imports
    from sqlalchemy.orm import Query
    from sqlalchemy.sql.compiler import SQLCompiler
    from aiida.orm.implementation import Backend
    from aiida.orm.implementation.querybuilder import BackendQueryBuilder

__all__ = ('QueryBuilder',)

_LOGGER = logging.getLogger(__name__)

# This global variable is necessary to enable the subclassing functionality for the `Group` entity. The current
# implementation of the `QueryBuilder` was written with the assumption that only `Node` was subclassable. Support for
# subclassing was added later for `Group` and is based on its `type_string`, but the current implementation does not
# allow to extend this support to the `QueryBuilder` in an elegant way. The prefix `group.` needs to be used in various
# places to make it work, but really the internals of the `QueryBuilder` should be rewritten to in principle support
# subclassing for any entity type. This workaround should then be able to be removed.
GROUP_ENTITY_TYPE_PREFIX = 'group.'

# re-usable type annotations
NodeClsType = Type[Any]  # pylint: disable=invalid-name
ProjectType = Union[str, dict, Sequence[Union[str, dict]]]  # pylint: disable=invalid-name
FilterType = Dict[str, Any]  # pylint: disable=invalid-name
RowType = Any  # pylint: disable=invalid-name


class PathItemType(TypedDict):
    """An item on the query path"""

    entity_type: Any
    tag: str
    joining_keyword: str
    joining_value: str
    outerjoin: bool
    edge_tag: str


class QueryDict(TypedDict, total=False):
    """A JSON serialisable representation of a ``QueryBuilder`` instance"""

    path: List[PathItemType]
    filters: Dict[str, FilterType]
    project: Dict[str, ProjectType]
    order_by: List[dict]
    offset: Optional[int]
    limit: Optional[int]


class EntityTypes(Enum):
    """The entity types and their allowed relationships."""
    AUTHINFO = 'authinfo'
    COMMENT = 'comment'
    COMPUTER = 'computer'
    GROUP = 'group'
    LOG = 'log'
    NODE = 'node'
    USER = 'user'


EntityRelationships: Dict[EntityTypes, Set[str]] = {
    EntityTypes.AUTHINFO: set(),
    EntityTypes.COMMENT: {'with_node', 'with_user'},
    EntityTypes.COMPUTER: {'with_node'},
    EntityTypes.GROUP: {'with_node', 'with_user'},
    EntityTypes.LOG: {'with_node'},
    EntityTypes.NODE: {
        'with_comment', 'with_log', 'with_incoming', 'with_outgoing', 'with_descendants', 'with_ancestors',
        'with_computer', 'with_user', 'with_group'
    },
    EntityTypes.USER: {'with_comment', 'with_group', 'with_node'}
}


class Classifier(NamedTuple):
    """A classifier for an entity."""
    ormclass_type_string: str
    process_type_string: Optional[str] = None


class QueryBuilder:
    """
    The class to query the AiiDA database.

    Usage::

        from aiida.orm.querybuilder import QueryBuilder
        qb = QueryBuilder()
        # Querying nodes:
        qb.append(Node)
        # retrieving the results:
        results = qb.all()

    """

    # pylint: disable=too-many-instance-attributes,too-many-public-methods

    # This tag defines how edges are tagged (labeled) by the QueryBuilder default
    # namely tag of first entity + _EDGE_TAG_DELIM + tag of second entity
    _EDGE_TAG_DELIM = '--'
    _VALID_PROJECTION_KEYS = ('func', 'cast')

    def __init__(
        self,
        backend: Optional['Backend'] = None,
        *,
        debug: bool = False,
        path: Optional[Sequence[Union[str, Dict[str, Any], NodeClsType]]] = (),
        filters: Optional[Dict[str, FilterType]] = None,
        project: Optional[Dict[str, ProjectType]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[Any] = None,
        distinct: bool = False,
    ) -> None:
        """
        Instantiates a QueryBuilder instance.

        Which backend is used decided here based on backend-settings (taken from the user profile).
        This cannot be overridden so far by the user.

        :param debug:
            Turn on debug mode. This feature prints information on the screen about the stages
            of the QueryBuilder. Does not affect results.
        :param path:
            A list of the vertices to traverse. Leave empty if you plan on using the method
            :func:`QueryBuilder.append`.
        :param filters:
            The filters to apply. You can specify the filters here, when appending to the query
            using :func:`QueryBuilder.append` or even later using :func:`QueryBuilder.add_filter`.
            Check latter gives API-details.
        :param project:
            The projections to apply. You can specify the projections here, when appending to the query
            using :func:`QueryBuilder.append` or even later using :func:`QueryBuilder.add_projection`.
            Latter gives you API-details.
        :param limit:
            Limit the number of rows to this number. Check :func:`QueryBuilder.limit`
            for more information.
        :param offset:
            Set an offset for the results returned. Details in :func:`QueryBuilder.offset`.
        :param order_by:
            How to order the results. As the 2 above, can be set also at later stage,
            check :func:`QueryBuilder.order_by` for more information.
        :param distinct: Whether to return de-duplicated rows

        """
        backend = backend or get_manager().get_backend()
        self._impl = backend.query()
        self._query: 'Query' = None
        # Hashing the internal query representation avoids rebuilding a query
        self._hash: Optional[str] = None

        # SERIALISABLE ATTRIBUTES
        # A list storing the path being traversed by the query
        self._path: List[PathItemType] = []
        # A dictionary tag: filter specification for this alias
        self._filters: Dict[str, FilterType] = {}
        # A dictionary tag: projections for this alias
        self._projections: Dict[str, List[dict]] = {}
        self._order_by: List[dict] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._distinct: bool = distinct

        # cache of tag mappings
        # populated during appends
        self._tags = _QueryTagMap()
        # mapping of tag -> field -> projection_index
        # populated on query build
        self._tag_to_projected_fields: Dict[str, Dict[str, int]] = {}
        # mapping that helps the projection postprocessing: projection_index -> field
        # populated on query build
        self._projection_index_to_field: Optional[Dict[int, str]] = None

        # Set the debug level
        self.set_debug(debug)

        # Validate & add the query path
        if not isinstance(path, (list, tuple)):
            raise TypeError('Path needs to be a tuple or a list')
        for path_spec in path:
            if isinstance(path_spec, dict):
                self.append(**path_spec)
            elif isinstance(path_spec, str):
                # Assume user means the entity_type
                self.append(entity_type=path_spec)
            else:
                self.append(cls=path_spec)
        # Validate & add projections
        projection_dict = project or {}
        if not isinstance(projection_dict, dict):
            raise TypeError('You need to provide the projections as dictionary')
        for key, val in projection_dict.items():
            self.add_projection(key, val)
        # Validate & add filters
        filter_dict = filters or {}
        if not isinstance(filter_dict, dict):
            raise TypeError('You need to provide the filters as dictionary')
        for key, val in filter_dict.items():
            self.add_filter(key, val)
        # Validate & add limit
        self.limit(limit)
        # Validate & add offset
        self.offset(offset)
        # Validate & add order_by
        if order_by:
            self.order_by(order_by)

    def as_dict(self) -> QueryDict:
        """Convert to a JSON serialisable dictionary representation of the query."""
        return copy.deepcopy({  # type: ignore[return-value]
            'path': self._path,
            'filters': self._filters,
            'project': self._projections,
            'order_by': self._order_by,
            'limit': self._limit,
            'offset': self._offset,
            'distinct': self._distinct,
        })

    @property
    def queryhelp(self) -> QueryDict:
        """"Legacy name for ``as_dict`` method."""
        return self.as_dict()

    @classmethod
    def from_dict(cls, dct: QueryDict) -> 'QueryBuilder':
        """Create an instance from a dictionary representation of the query."""
        return cls(**dct)  # type: ignore[arg-type]

    def __repr__(self) -> str:
        """Return an unambiguous string representation of the instance."""
        params = ', '.join(f'{key}={value!r}' for key, value in self.as_dict().items())
        return f'QueryBuilder({params})'

    def __str__(self) -> str:
        """Return a readable string representation of the instance."""
        return repr(self)

    def __deepcopy__(self, memo) -> 'QueryBuilder':
        """Create deep copy of the instance."""
        return type(self)(**self.as_dict())  # type: ignore[arg-type]

    def get_used_tags(self, vertices: bool = True, edges: bool = True) -> List[str]:
        """Returns a list of all the vertices that are being used.

        :param vertices: If True, adds the tags of vertices to the returned list
        :param edges: If True, adds the tags of edges to the returnend list.

        :returns: A list of tags
        """
        given_tags = []
        for idx, path in enumerate(self._path):
            if vertices:
                given_tags.append(path['tag'])
            if edges and idx > 0:
                given_tags.append(path['edge_tag'])
        return given_tags

    def _get_unique_tag(self, classifiers: List[Classifier]) -> str:
        """
        Using the function get_tag_from_type, I get a tag.
        I increment an index that is appended to that tag until I have an unused tag.
        This function is called in :func:`QueryBuilder.append` when no tag is given.

        :param dict classifiers:
            Classifiers, containing the string that defines the type of the AiiDA ORM class.
            For subclasses of Node, this is the Node._plugin_type_string, for other they are
            as defined as returned by :func:`QueryBuilder._get_ormclass`.

            Can also be a list of dictionaries, when multiple classes are passed to QueryBuilder.append

        :returns: A tag as a string (it is a single string also when passing multiple classes).
        """
        basetag = '-'.join([t.ormclass_type_string.rstrip('.').split('.')[-1] or 'node' for t in classifiers])
        for i in range(1, 100):
            tag = f'{basetag}_{i}'
            if tag not in self._tags:
                return tag

        raise RuntimeError('Cannot find a tag after 100 tries')

    def append(
        self,
        cls: Optional[Union[NodeClsType, Sequence[NodeClsType]]] = None,
        entity_type: Optional[Union[str, Sequence[str]]] = None,
        tag: Optional[str] = None,
        filters: Optional[FilterType] = None,
        project: Optional[ProjectType] = None,
        subclassing: bool = True,
        edge_tag: Optional[str] = None,
        edge_filters: Optional[FilterType] = None,
        edge_project: Optional[ProjectType] = None,
        outerjoin: bool = False,
        joining_keyword: Optional[str] = None,
        joining_value: Optional[Any] = None,
        **kwargs: Any
    ) -> 'QueryBuilder':
        """
        Any iterative procedure to build the path for a graph query
        needs to invoke this method to append to the path.

        :param cls:
            The Aiida-class (or backend-class) defining the appended vertice.
            Also supports a tuple/list of classes. This results in an all instances of
            this class being accepted in a query. However the classes have to have the same orm-class
            for the joining to work. I.e. both have to subclasses of Node. Valid is::

                cls=(StructureData, Dict)

            This is invalid:

                cls=(Group, Node)

        :param entity_type: The node type of the class, if cls is not given. Also here, a tuple or list is accepted.
        :param tag:
            A unique tag. If none is given, I will create a unique tag myself.
        :param filters:
            Filters to apply for this vertex.
            See :meth:`.add_filter`, the method invoked in the background, or usage examples for details.
        :param project:
            Projections to apply. See usage examples for details.
            More information also in :meth:`.add_projection`.
        :param subclassing:
            Whether to include subclasses of the given class (default **True**).
            E.g. Specifying a ProcessNode as cls will include CalcJobNode, WorkChainNode, CalcFunctionNode, etc..
        :param edge_tag:
            The tag that the edge will get. If nothing is specified
            (and there is a meaningful edge) the default is tag1--tag2 with tag1 being the entity joining
            from and tag2 being the entity joining to (this entity).
        :param edge_filters:
            The filters to apply on the edge. Also here, details in :meth:`.add_filter`.
        :param edge_project:
            The project from the edges. API-details in :meth:`.add_projection`.
        :param outerjoin:
            If True, (default is False), will do a left outerjoin
            instead of an inner join

        Joining can be specified in two ways:

            - Specifying the 'joining_keyword' and 'joining_value' arguments
            - Specify a single keyword argument

        The joining keyword wil be ``with_*`` or ``direction``, depending on the joining entity type.
        The joining value is the tag name or class of the entity to join to.

        A small usage example how this can be invoked::

            qb = QueryBuilder()             # Instantiating empty querybuilder instance
            qb.append(cls=StructureData)    # First item is StructureData node
            # The
            # next node in the path is a PwCalculation, with
            # the structure joined as an input
            qb.append(
                cls=PwCalculation,
                with_incoming=StructureData
            )

        :return: self
        """
        # pylint: disable=too-many-arguments,too-many-locals,too-many-branches,too-many-statements
        # INPUT CHECKS ##########################
        # This function can be called by users, so I am checking the input now.
        # First of all, let's make sure the specified the class or the type (not both)

        if cls is not None and entity_type is not None:
            raise ValueError(f'You cannot specify both a class ({cls}) and a entity_type ({entity_type})')

        if cls is None and entity_type is None:
            raise ValueError('You need to specify at least a class or a entity_type')

        # Let's check if it is a valid class or type
        if cls:
            if isinstance(cls, (list, tuple)):
                for sub_cls in cls:
                    if not inspect_isclass(sub_cls):
                        raise TypeError(f"{sub_cls} was passed with kw 'cls', but is not a class")
            elif not inspect_isclass(cls):
                raise TypeError(f"{cls} was passed with kw 'cls', but is not a class")
        elif entity_type is not None:
            if isinstance(entity_type, (list, tuple)):
                for sub_type in entity_type:
                    if not isinstance(sub_type, str):
                        raise TypeError(f'{sub_type} was passed as entity_type, but is not a string')
            elif not isinstance(entity_type, str):
                raise TypeError(f'{entity_type} was passed as entity_type, but is not a string')

        ormclass, classifiers = _get_ormclass(cls, entity_type)

        # TAG #################################
        # Let's get a tag
        if tag:
            if self._EDGE_TAG_DELIM in tag:
                raise ValueError(
                    f'tag cannot contain {self._EDGE_TAG_DELIM}\nsince this is used as a delimiter for links'
                )
            if tag in self._tags:
                raise ValueError(f'This tag ({tag}) is already in use')
        else:
            tag = self._get_unique_tag(classifiers)

        # Checks complete
        # This is where I start doing changes to self!
        # Now, several things can go wrong along the way, so I need to split into
        # atomic blocks that I can reverse if something goes wrong.

        # TAG ALIASING ##############################
        try:
            self._tags.add(tag, ormclass, cls)
        except Exception as exception:
            self.debug('Exception caught in append, cleaning up: %s', exception)
            self._tags.remove(tag)
            raise

        # FILTERS ######################################
        try:
            self._filters[tag] = {}
            # Subclassing is currently only implemented for the `Node` and `Group` classes.
            # So for those cases we need to construct the correct filters,
            # corresponding to the provided classes and value of `subclassing`.
            if ormclass == EntityTypes.NODE:
                self._add_node_type_filter(tag, classifiers, subclassing)
                self._add_process_type_filter(tag, classifiers, subclassing)

            elif ormclass == EntityTypes.GROUP:
                self._add_group_type_filter(tag, classifiers, subclassing)

            # The order has to be first _add_node_type_filter and then add_filter.
            # If the user adds a query on the type column, it overwrites what I did
            # if the user specified a filter, add it:
            if filters is not None:
                self.add_filter(tag, filters)
        except Exception as exception:
            self.debug('Exception caught in append, cleaning up: %s', exception)
            self._tags.remove(tag)
            self._filters.pop(tag)
            raise

        # PROJECTIONS ##############################
        try:
            self._projections[tag] = []
            if project is not None:
                self.add_projection(tag, project)
        except Exception as exception:
            self.debug('Exception caught in append, cleaning up: %s', exception)
            self._tags.remove(tag)
            self._filters.pop(tag)
            self._projections.pop(tag)
            raise exception

        # JOINING #####################################
        # pylint: disable=too-many-nested-blocks
        try:
            # Get the functions that are implemented:
            spec_to_function_map = set(EntityRelationships[ormclass])
            if ormclass == EntityTypes.NODE:
                # 'direction 'was an old implementation, which is now converted below to with_outgoing or with_incoming
                spec_to_function_map.add('direction')
            for key, val in kwargs.items():
                if key not in spec_to_function_map:
                    raise ValueError(
                        f"'{key}' is not a valid keyword for joining specification\n"
                        f'Valid keywords are: {spec_to_function_map or []!r}'
                    )
                if joining_keyword:
                    raise ValueError(
                        'You already specified joining specification {}\n'
                        'But you now also want to specify {}'
                        ''.format(joining_keyword, key)
                    )

                joining_keyword = key
                if joining_keyword == 'direction':
                    if not isinstance(val, int):
                        raise TypeError('direction=n expects n to be an integer')
                    try:
                        if val < 0:
                            joining_keyword = 'with_outgoing'
                        elif val > 0:
                            joining_keyword = 'with_incoming'
                        else:
                            raise ValueError('direction=0 is not valid')
                        joining_value = self._path[-abs(val)]['tag']
                    except IndexError as exc:
                        raise ValueError(
                            f'You have specified a non-existent entity with\ndirection={joining_value}\n{exc}\n'
                        )
                else:
                    joining_value = self._tags.get(val)

            if joining_keyword is None and len(self._path) > 0:
                # the default is that this vertice is 'with_incoming' as the previous one
                if ormclass == EntityTypes.NODE:
                    joining_keyword = 'with_incoming'
                else:
                    joining_keyword = 'with_node'
                joining_value = self._path[-1]['tag']

        except Exception as exception:
            self.debug('Exception caught in append (part filters), cleaning up: %s', exception)
            self._tags.remove(tag)
            self._filters.pop(tag)
            self._projections.pop(tag)
            # There's not more to clean up here!
            raise exception

        # EDGES #################################
        if len(self._path) > 0:
            try:
                if edge_tag is None:
                    edge_destination_tag = self._tags.get(joining_value)
                    edge_tag = edge_destination_tag + self._EDGE_TAG_DELIM + tag
                else:
                    if edge_tag in self._tags:
                        raise ValueError(f'The tag {edge_tag} is already in use')
                self.debug('edge_tag chosen: %s', edge_tag)

                # My edge is None for now, since this is created on the FLY,
                # the _tag_to_alias_map will be updated later (in _build)
                self._tags.add(edge_tag)

                # Filters on links:
                # Beware, I alway add this entry now, but filtering here might be
                # non-sensical, since this ONLY works for m2m relationship where
                # I go through a different table
                self._filters[edge_tag] = {}
                if edge_filters is not None:
                    self.add_filter(edge_tag, edge_filters)
                # Projections on links
                self._projections[edge_tag] = []
                if edge_project is not None:
                    self.add_projection(edge_tag, edge_project)
            except Exception as exception:
                self.debug('Exception caught in append (part joining), cleaning up %s', exception)
                self._tags.remove(tag)
                self._filters.pop(tag)
                self._projections.pop(tag)
                if edge_tag is not None:
                    self._tags.remove(edge_tag)
                    self._filters.pop(edge_tag, None)
                    self._projections.pop(edge_tag, None)
                # There's not more to clean up here!
                raise exception

        # EXTENDING THE PATH #################################
        # Note: 'type' being a list is a relict of an earlier implementation
        # Could simply pass all classifiers here.
        path_type: Union[List[str], str]
        if len(classifiers) > 1:
            path_type = [c.ormclass_type_string for c in classifiers]
        else:
            path_type = classifiers[0].ormclass_type_string

        self._path.append(
            dict(
                entity_type=path_type,
                tag=tag,
                # for the first item joining_keyword/joining_value can be None,
                # but after they always default to 'with_incoming' of the previous item
                joining_keyword=joining_keyword,  # type: ignore
                joining_value=joining_value,  # type: ignore
                # same for edge_tag for which a default is applied
                edge_tag=edge_tag,  # type: ignore
                outerjoin=outerjoin,
            )
        )

        return self

    def order_by(self, order_by: Union[dict, List[dict], Tuple[dict, ...]]) -> 'QueryBuilder':
        """
        Set the entity to order by

        :param order_by:
            This is a list of items, where each item is a dictionary specifies
            what to sort for an entity

        In each dictionary in that list, keys represent valid tags of
        entities (tables), and values are list of columns.

        Usage::

            #Sorting by id (ascending):
            qb = QueryBuilder()
            qb.append(Node, tag='node')
            qb.order_by({'node':['id']})

            # or
            #Sorting by id (ascending):
            qb = QueryBuilder()
            qb.append(Node, tag='node')
            qb.order_by({'node':[{'id':{'order':'asc'}}]})

            # for descending order:
            qb = QueryBuilder()
            qb.append(Node, tag='node')
            qb.order_by({'node':[{'id':{'order':'desc'}}]})

            # or (shorter)
            qb = QueryBuilder()
            qb.append(Node, tag='node')
            qb.order_by({'node':[{'id':'desc'}]})
        """
        # pylint: disable=too-many-nested-blocks,too-many-branches
        self._order_by = []
        allowed_keys = ('cast', 'order')
        possible_orders = ('asc', 'desc')

        if not isinstance(order_by, (list, tuple)):
            order_by = [order_by]

        for order_spec in order_by:
            if not isinstance(order_spec, dict):
                raise TypeError(
                    f'Invalid input for order_by statement: {order_spec!r}\n'
                    'Expecting a dictionary like: {tag: field} or {tag: [field1, field2, ...]}'
                )
            _order_spec: dict = {}
            for tagspec, items_to_order_by in order_spec.items():
                if not isinstance(items_to_order_by, (tuple, list)):
                    items_to_order_by = [items_to_order_by]
                tag = self._tags.get(tagspec)
                _order_spec[tag] = []
                for item_to_order_by in items_to_order_by:
                    if isinstance(item_to_order_by, str):
                        item_to_order_by = {item_to_order_by: {}}
                    elif isinstance(item_to_order_by, dict):
                        pass
                    else:
                        raise ValueError(
                            f'Cannot deal with input to order_by {item_to_order_by}\nof type{type(item_to_order_by)}\n'
                        )
                    for entityname, orderspec in item_to_order_by.items():
                        # if somebody specifies eg {'node':{'id':'asc'}}
                        # tranform to {'node':{'id':{'order':'asc'}}}

                        if isinstance(orderspec, str):
                            this_order_spec = {'order': orderspec}
                        elif isinstance(orderspec, dict):
                            this_order_spec = orderspec
                        else:
                            raise TypeError(
                                'I was expecting a string or a dictionary\n'
                                'You provided {} {}\n'
                                ''.format(type(orderspec), orderspec)
                            )
                        for key in this_order_spec:
                            if key not in allowed_keys:
                                raise ValueError(
                                    'The allowed keys for an order specification\n'
                                    'are {}\n'
                                    '{} is not valid\n'
                                    ''.format(', '.join(allowed_keys), key)
                                )
                        this_order_spec['order'] = this_order_spec.get('order', 'asc')
                        if this_order_spec['order'] not in possible_orders:
                            raise ValueError(
                                'You gave {} as an order parameters,\n'
                                'but it is not a valid order parameter\n'
                                'Valid orders are: {}\n'
                                ''.format(this_order_spec['order'], possible_orders)
                            )
                        item_to_order_by[entityname] = this_order_spec

                    _order_spec[tag].append(item_to_order_by)

            self._order_by.append(_order_spec)
        return self

    def add_filter(self, tagspec: Union[str, Type[Any]], filter_spec: FilterType) -> None:
        """
        Adding a filter to my filters.

        :param tagspec: A tag string or an ORM class which maps to an existing tag
        :param filter_spec: The specifications for the filter, has to be a dictionary

        Usage::

            qb = QueryBuilder()         # Instantiating the QueryBuilder instance
            qb.append(Node, tag='node') # Appending a Node
            #let's put some filters:
            qb.add_filter('node',{'id':{'>':12}})
            # 2 filters together:
            qb.add_filter('node',{'label':'foo', 'uuid':{'like':'ab%'}})
            # Now I am overriding the first filter I set:
            qb.add_filter('node',{'id':13})
        """
        filters = self._process_filters(filter_spec)
        tag = self._tags.get(tagspec)
        self._filters[tag].update(filters)

    @staticmethod
    def _process_filters(filters: FilterType) -> dict:
        """Process filters."""
        if not isinstance(filters, dict):
            raise TypeError('Filters have to be passed as dictionaries')

        processed_filters = {}

        for key, value in filters.items():
            if isinstance(value, entities.Entity):
                # Convert to be the id of the joined entity because we can't query
                # for the object instance directly
                processed_filters[f'{key}_id'] = value.id
            else:
                processed_filters[key] = value

        return processed_filters

    def _add_node_type_filter(self, tagspec: str, classifiers: List[Classifier], subclassing: bool):
        """
        Add a filter based on node type.

        :param tagspec: The tag, which has to exist already as a key in self._filters
        :param classifiers: a dictionary with classifiers
        :param subclassing: if True, allow for subclasses of the ormclass
        """
        if len(classifiers) > 1:
            # If a list was passed to QueryBuilder.append, this propagates to a list in the classifiers
            entity_type_filter: dict = {'or': []}
            for classifier in classifiers:
                entity_type_filter['or'].append(_get_node_type_filter(classifier, subclassing))
        else:
            entity_type_filter = _get_node_type_filter(classifiers[0], subclassing)

        self.add_filter(tagspec, {'node_type': entity_type_filter})

    def _add_process_type_filter(self, tagspec: str, classifiers: List[Classifier], subclassing: bool) -> None:
        """
        Add a filter based on process type.

        :param tagspec: The tag, which has to exist already as a key in self._filters
        :param classifiers: a dictionary with classifiers
        :param subclassing: if True, allow for subclasses of the process type

        Note: This function handles the case when process_type_string is None.
        """
        if len(classifiers) > 1:
            # If a list was passed to QueryBuilder.append, this propagates to a list in the classifiers
            process_type_filter: dict = {'or': []}
            for classifier in classifiers:
                if classifier.process_type_string is not None:
                    process_type_filter['or'].append(_get_process_type_filter(classifier, subclassing))

            if len(process_type_filter['or']) > 0:
                self.add_filter(tagspec, {'process_type': process_type_filter})

        else:
            if classifiers[0].process_type_string is not None:
                process_type_filter = _get_process_type_filter(classifiers[0], subclassing)
                self.add_filter(tagspec, {'process_type': process_type_filter})

    def _add_group_type_filter(self, tagspec: str, classifiers: List[Classifier], subclassing: bool) -> None:
        """
        Add a filter based on group type.

        :param tagspec: The tag, which has to exist already as a key in self._filters
        :param classifiers: a dictionary with classifiers
        :param subclassing: if True, allow for subclasses of the ormclass
        """
        if len(classifiers) > 1:
            # If a list was passed to QueryBuilder.append, this propagates to a list in the classifiers
            type_string_filter: dict = {'or': []}
            for classifier in classifiers:
                type_string_filter['or'].append(_get_group_type_filter(classifier, subclassing))
        else:
            type_string_filter = _get_group_type_filter(classifiers[0], subclassing)

        self.add_filter(tagspec, {'type_string': type_string_filter})

    def add_projection(self, tag_spec: Union[str, Type[Any]], projection_spec: ProjectType) -> None:
        r"""Adds a projection

        :param tag_spec: A tag string or an ORM class which maps to an existing tag
        :param projection_spec:
            The specification for the projection.
            A projection is a list of dictionaries, with each dictionary
            containing key-value pairs where the key is database entity
            (e.g. a column / an attribute) and the value is (optional)
            additional information on how to process this database entity.

        If the given *projection_spec* is not a list, it will be expanded to
        a list.
        If the listitems are not dictionaries, but strings (No additional
        processing of the projected results desired), they will be expanded to
        dictionaries.

        Usage::

            qb = QueryBuilder()
            qb.append(StructureData, tag='struc')

            # Will project the uuid and the kinds
            qb.add_projection('struc', ['uuid', 'attributes.kinds'])

        The above example will project the uuid and the kinds-attribute of all matching structures.
        There are 2 (so far) special keys.

        The single star *\** will project the *ORM-instance*::

            qb = QueryBuilder()
            qb.append(StructureData, tag='struc')
            # Will project the ORM instance
            qb.add_projection('struc', '*')
            print type(qb.first()[0])
            # >>> aiida.orm.nodes.data.structure.StructureData

        The double star ``**`` projects all possible projections of this entity:

            QueryBuilder().append(StructureData,tag='s', project='**').limit(1).dict()[0]['s'].keys()

            # >>> 'user_id, description, ctime, label, extras, mtime, id, attributes, dbcomputer_id, type, uuid'

        Be aware that the result of ``**`` depends on the backend implementation.

        """
        tag = self._tags.get(tag_spec)
        _projections = []
        self.debug('Adding projection of %s: %s', tag_spec, projection_spec)
        if not isinstance(projection_spec, (list, tuple)):
            projection_spec = [projection_spec]  # type: ignore
        for projection in projection_spec:
            if isinstance(projection, dict):
                _thisprojection = projection
            elif isinstance(projection, str):
                _thisprojection = {projection: {}}
            else:
                raise ValueError(f'Cannot deal with projection specification {projection}\n')
            for spec in _thisprojection.values():
                if not isinstance(spec, dict):
                    raise TypeError(
                        f'\nThe value of a key-value pair in a projection\nhas to be a dictionary\nYou gave: {spec}\n'
                    )

                for key, val in spec.items():
                    if key not in self._VALID_PROJECTION_KEYS:
                        raise ValueError(f'{key} is not a valid key {self._VALID_PROJECTION_KEYS}')
                    if not isinstance(val, str):
                        raise TypeError(f'{val} has to be a string')
            _projections.append(_thisprojection)
        self.debug('projections have become: %s', _projections)
        self._projections[tag] = _projections

    def set_debug(self, debug: bool) -> 'QueryBuilder':
        """
        Run in debug mode. This does not affect functionality, but prints intermediate stages
        when creating a query on screen.

        :param debug: Turn debug on or off
        """
        if not isinstance(debug, bool):
            return TypeError('I expect a boolean')
        self._debug = debug

        return self

    def debug(self, msg: str, *objects: Any) -> None:
        """Log debug message.

        objects will passed to the format string, e.g. ``msg % objects``
        """
        if self._debug:
            print(f'DEBUG: {msg}' % objects)

    def limit(self, limit: Optional[int]) -> 'QueryBuilder':
        """
        Set the limit (nr of rows to return)

        :param limit: integers of number of rows of rows to return
        """
        if (limit is not None) and (not isinstance(limit, int)):
            raise TypeError('The limit has to be an integer, or None')
        self._limit = limit
        return self

    def offset(self, offset: Optional[int]) -> 'QueryBuilder':
        """
        Set the offset. If offset is set, that many rows are skipped before returning.
        *offset* = 0 is the same as omitting setting the offset.
        If both offset and limit appear,
        then *offset* rows are skipped before starting to count the *limit* rows
        that are returned.

        :param offset: integers of nr of rows to skip
        """
        if (offset is not None) and (not isinstance(offset, int)):
            raise TypeError('offset has to be an integer, or None')
        self._offset = offset
        return self

    def distinct(self, value: bool = True) -> 'QueryBuilder':
        """
        Asks for distinct rows, which is the same as asking the backend to remove
        duplicates.
        Does not execute the query!

        If you want a distinct query::

            qb = QueryBuilder()
            # append stuff!
            qb.append(...)
            qb.append(...)
            ...
            qb.distinct().all() #or
            qb.distinct().dict()

        :returns: self
        """
        if not isinstance(value, bool):
            raise TypeError(f'distinct() takes a boolean as parameter, not {value!r}')
        self._distinct = value
        return self

    def inputs(self, **kwargs: Any) -> 'QueryBuilder':
        """
        Join to inputs of previous vertice in path.

        :returns: self
        """
        from aiida.orm import Node
        join_to = self._path[-1]['tag']
        cls = kwargs.pop('cls', Node)
        self.append(cls=cls, with_outgoing=join_to, **kwargs)
        return self

    def outputs(self, **kwargs: Any) -> 'QueryBuilder':
        """
        Join to outputs of previous vertice in path.

        :returns: self
        """
        from aiida.orm import Node
        join_to = self._path[-1]['tag']
        cls = kwargs.pop('cls', Node)
        self.append(cls=cls, with_incoming=join_to, **kwargs)
        return self

    def children(self, **kwargs: Any) -> 'QueryBuilder':
        """
        Join to children/descendants of previous vertice in path.

        :returns: self
        """
        from aiida.orm import Node
        join_to = self._path[-1]['tag']
        cls = kwargs.pop('cls', Node)
        self.append(cls=cls, with_ancestors=join_to, **kwargs)
        return self

    def parents(self, **kwargs: Any) -> 'QueryBuilder':
        """
        Join to parents/ancestors of previous vertice in path.

        :returns: self
        """
        from aiida.orm import Node
        join_to = self._path[-1]['tag']
        cls = kwargs.pop('cls', Node)
        self.append(cls=cls, with_descendants=join_to, **kwargs)
        return self

    # above here it is not necessary to build the query

    # Run query methods

    @staticmethod
    def _compile_query(query: 'Query', literal_binds: bool = False) -> 'SQLCompiler':
        """Compile the query to the SQL executable.

        :params literal_binds: Inline bound parameters (this is normally handled by the Python DBAPI).
        """
        dialect = query.session.bind.dialect

        class _Compiler(dialect.statement_compiler):  # type: ignore[name-defined]
            """Override the compiler with additional literal value renderers."""

            def render_literal_value(self, value, type_):
                """Render the value of a bind parameter as a quoted literal.

                See https://www.postgresql.org/docs/current/functions-json.html for serialisation specs
                """
                try:
                    return super().render_literal_value(value, type_)
                except NotImplementedError:
                    if isinstance(value, list):
                        values = ','.join(self.render_literal_value(item, type_) for item in value)
                        return f"'[{values}]'"
                    if isinstance(value, int):
                        return str(value)
                    if isinstance(value, (str, date, datetime, timedelta)):
                        escaped = str(value).replace('"', '\\"')
                        return f'"{escaped}"'
                    raise

        return _Compiler(dialect, query.statement, compile_kwargs=dict(literal_binds=literal_binds))

    def as_sql(self, inline: bool = False) -> str:
        """Convert the query to an SQL string representation.

        .. warning::

            This method should be used for debugging purposes only,
            since normally sqlalchemy will handle this process internally.

        :params inline: Inline bound parameters (this is normally handled by the Python DBAPI).
        """
        compiled = self._compile_query(self.get_query(), literal_binds=inline)
        if inline:
            return compiled.string + '\n'
        return f'{compiled.string!r} % {compiled.params!r}\n'

    def analyze_query(self, execute: bool = True, verbose: bool = False) -> str:
        """Return the query plan, i.e. a list of SQL statements that will be executed.

        See: https://www.postgresql.org/docs/11/sql-explain.html

        :params execute: Carry out the command and show actual run times and other statistics.
        :params verbose: Display additional information regarding the plan.
        """
        query = self.get_query()
        if query.session.bind.dialect.name != 'postgresql':
            raise NotImplementedError('Only PostgreSQL is supported for this method')
        compiled = self._compile_query(query, literal_binds=True)
        options = ', '.join((['ANALYZE'] if execute else []) + (['VERBOSE'] if verbose else []))
        options = f' ({options})' if options else ''
        rows = self._impl.get_session().execute(f'EXPLAIN{options} {compiled.string}').fetchall()
        return '\n'.join(row.values()[0] for row in rows)

    @staticmethod
    def _get_aiida_entity_res(value) -> RowType:
        """Convert a projected query result to front end class if it is an instance of a `BackendEntity`.

        Values that are not an `BackendEntity` instance will be returned unaltered

        :param value: a projected query result to convert
        :return: the converted value
        """
        try:
            return convert.get_orm_entity(value)
        except TypeError:
            return value

    def first(self) -> Optional[List[RowType]]:
        """Executes the query, asking for the first row of results.

        Note, this may change if several rows are valid for the query,
        as persistent ordering is not guaranteed unless explicitly specified.

        :returns: One row of results as a list, or None if no result returned.
        """
        query = self.get_query()
        result = self._impl.first(query)

        if result is None:
            return None

        if not isinstance(result, (list, tuple)):
            result = [result]

        if not self._projection_index_to_field or len(result) != len(self._projection_index_to_field):
            raise Exception('length of query result does not match the number of specified projections')

        return [
            self._get_aiida_entity_res(self._impl.get_aiida_res(rowitem)) for colindex, rowitem in enumerate(result)
        ]

    def one(self) -> RowType:
        """
        Executes the query asking for exactly one results. Will raise an exception if this is not the case
        :raises: MultipleObjectsError if more then one row can be returned
        :raises: NotExistent if no result was found
        """
        from aiida.common.exceptions import MultipleObjectsError, NotExistent
        self.limit(2)
        res = self.all()
        if len(res) > 1:
            raise MultipleObjectsError('More than one result was found')
        elif len(res) == 0:
            raise NotExistent('No result was found')
        return res[0]

    def count(self) -> int:
        """
        Counts the number of rows returned by the backend.

        :returns: the number of rows as an integer
        """
        query = self.get_query()
        return self._impl.count(query)

    def iterall(self, batch_size: Optional[int] = 100) -> Iterator[List[RowType]]:
        """
        Same as :meth:`.all`, but returns a generator.
        Be aware that this is only safe if no commit will take place during this
        transaction. You might also want to read the SQLAlchemy documentation on
        https://docs.sqlalchemy.org/en/14/orm/query.html#sqlalchemy.orm.Query.yield_per

        :param batch_size:
            The size of the batches to ask the backend to batch results in subcollections.
            You can optimize the speed of the query by tuning this parameter.

        :returns: a generator of lists
        """
        query = self.get_query()

        for item in self._impl.iterall(query, batch_size, self._projection_index_to_field):
            # Convert to AiiDA frontend entities (if they are such)
            for i, item_entry in enumerate(item):
                item[i] = self._get_aiida_entity_res(item_entry)

            yield item

    def iterdict(self, batch_size: Optional[int] = 100) -> Iterable[Dict[str, RowType]]:
        """
        Same as :meth:`.dict`, but returns a generator.
        Be aware that this is only safe if no commit will take place during this
        transaction. You might also want to read the SQLAlchemy documentation on
        https://docs.sqlalchemy.org/en/14/orm/query.html#sqlalchemy.orm.Query.yield_per


        :param batch_size:
            The size of the batches to ask the backend to batch results in subcollections.
            You can optimize the speed of the query by tuning this parameter.

        :returns: a generator of dictionaries
        """
        query = self.get_query()

        for item in self._impl.iterdict(query, batch_size, self._tag_to_projected_fields, self._tags):
            for key, value in item.items():
                item[key] = self._get_aiida_entity_res(value)

            yield item

    def all(self, batch_size: Optional[int] = None, flat: bool = False) -> Union[List[List[RowType]], List[RowType]]:
        """Executes the full query with the order of the rows as returned by the backend.

        The order inside each row is given by the order of the vertices in the path and the order of the projections for
        each vertex in the path.

        :param batch_size: the size of the batches to ask the backend to batch results in subcollections. You can
            optimize the speed of the query by tuning this parameter. Leave the default `None` if speed is not critical
            or if you don't know what you're doing.
        :param flat: return the result as a flat list of projected entities without sub lists.
        :returns: a list of lists of all projected entities.
        """
        matches = list(self.iterall(batch_size=batch_size))

        if not flat:
            return matches

        return [projection for entry in matches for projection in entry]

    def dict(self, batch_size: Optional[int] = None) -> List[Dict[str, RowType]]:
        """
        Executes the full query with the order of the rows as returned by the backend.
        the order inside each row is given by the order of the vertices in the path
        and the order of the projections for each vertice in the path.

        :param batch_size:
            The size of the batches to ask the backend to batch results in subcollections.
            You can optimize the speed of the query by tuning this parameter.
            Leave the default (*None*) if speed is not critical or if you don't know
            what you're doing!

        :returns:
            a list of dictionaries of all projected entities.
            Each dictionary consists of key value pairs, where the key is the tag
            of the vertice and the value a dictionary of key-value pairs where key
            is the entity description (a column name or attribute path)
            and the value the value in the DB.

        Usage::

            qb = QueryBuilder()
            qb.append(
                StructureData,
                tag='structure',
                filters={'uuid':{'==':myuuid}},
            )
            qb.append(
                Node,
                with_ancestors='structure',
                project=['entity_type', 'id'],  # returns entity_type (string) and id (string)
                tag='descendant'
            )

            # Return the dictionaries:
            print "qb.iterdict()"
            for d in qb.iterdict():
                print '>>>', d

        results in the following output::

            qb.iterdict()
            >>> {'descendant': {
                    'entity_type': 'calculation.job.quantumespresso.pw.PwCalculation.',
                    'id': 7716}
                }
            >>> {'descendant': {
                    'entity_type': 'data.remote.RemoteData.',
                    'id': 8510}
                }

        """
        return list(self.iterdict(batch_size=batch_size))

    # Backend query build methods

    def get_query(self) -> 'Query':
        """Return the sqlalchemy.orm.Query instance for the current query specification.

        To avoid unnecessary re-builds of the query, the hashed dictionary representation of this instance
        is compared to the last query returned, which is cached by its hash.
        """
        from aiida.common.hashing import make_hash

        need_to_build = True
        query_hash = make_hash(self.as_dict())
        if self._hash is None:
            # this is the first time the query has been built
            need_to_build = True
        elif self._hash == query_hash:
            need_to_build = False

        if need_to_build:
            query = self._build()
            self._hash = query_hash
        else:
            try:
                query = self._query
            except AttributeError:
                _LOGGER.warning('AttributeError thrown even though I should have _query as an attribute')
                query = self._build()
                self._hash = query_hash
        return query

    def _build(self):
        """
        build the query and return a sqlalchemy.Query instance
        """
        # pylint: disable=too-many-branches

        # Starting the query by receiving a session
        # Every subclass needs to have _get_session and give me the right session
        firstalias = self._tags._get_alias(self._impl, self._path[0]['tag'])
        self._query = self._impl.get_session().query(firstalias)

        # JOINS ################################
        # Start on second path item, since there is nothing to join if that is the first table
        for index, verticespec in enumerate(self._path[1:], start=1):
            join_to = self._tags._get_alias(self._impl, verticespec['tag'])
            join_func = self._build_join_func(
                self._query, index, verticespec['joining_keyword'], verticespec['joining_value']
            )
            edge_tag = verticespec['edge_tag']

            # if verticespec['joining_keyword'] in ('with_ancestors', 'with_descendants'):
            # These require a filter_dict, to help the recursive function find a good starting point.
            filter_dict = self._filters.get(verticespec['joining_value'], {})
            # Also find out whether the path is used in a filter or a project and, if so,
            # instruct the recursive function to build the path on the fly.
            # The default is False, because it's super expensive
            expand_path = ((self._filters[edge_tag].get('path', None) is not None) or
                           any('path' in d.keys() for d in self._projections[edge_tag]))

            result = join_func(
                join_to, isouterjoin=verticespec.get('outerjoin'), filter_dict=filter_dict, expand_path=expand_path
            )
            self._query = result.query
            if result.aliased_edge is not None:
                self._tags._set_alias(edge_tag, result.aliased_edge)

        ######################### FILTERS ##############################

        for tag, filter_specs in self._filters.items():
            if not filter_specs:
                continue
            try:
                alias = self._tags._get_alias(self._impl, tag)
            except KeyError:
                raise ValueError(
                    f'You looked for tag {tag} among the alias list\nThe tags I know are:\n{list(self._tags)}'
                )
            self._query = self._query.filter(self._impl.build_filters(alias, filter_specs))

        ######################### PROJECTIONS ##########################
        # first clear the entities in the case the first item in the
        # path was not meant to be projected
        # attribute of Query instance storing entities to project:

        # Mapping between entities and the tag used/ given by user:
        self._tag_to_projected_fields = {}

        projection_count = 0
        self.debug('self._projections: %s', self._projections)

        if not any(self._projections.values()):
            # If user has not set projection,
            # I will simply project the last item specified!
            # Don't change, path traversal querying
            # relies on this behavior!
            projection_count = self._build_projections(
                self._path[-1]['tag'], projection_count, items_to_project=[{
                    '*': {}
                }]
            )
        else:
            for vertex in self._path:
                projection_count = self._build_projections(vertex['tag'], projection_count)

            # LINK-PROJECTIONS #########################

            for vertex in self._path[1:]:
                edge_tag = vertex.get('edge_tag', None)  # type: ignore

                self.debug(
                    'Checking projections for edges: This is edge %s from %s, %s of %s', edge_tag, vertex.get('tag'),
                    vertex.get('joining_keyword'), vertex.get('joining_value')
                )
                if edge_tag is not None:
                    projection_count = self._build_projections(edge_tag, projection_count)

        # ORDER ################################
        for order_spec in self._order_by:
            for tag, entity_list in order_spec.items():
                alias = self._tags._get_alias(self._impl, tag)
                for entitydict in entity_list:
                    for entitytag, entityspec in entitydict.items():
                        self._build_order(alias, entitytag, entityspec)

        # LIMIT ################################
        if self._limit is not None:
            self._query = self._query.limit(self._limit)

        ######################## OFFSET ################################
        if self._offset is not None:
            self._query = self._query.offset(self._offset)

        ################ LAST BUT NOT LEAST ############################
        # pop the entity that I added to start the query
        self._query._entities.pop(0)  # pylint: disable=protected-access

        # Dirty solution coming up:
        # Sqlalchemy is by default de-duplicating results if possible.
        # This can lead to strange results, as shown in:
        # https://github.com/aiidateam/aiida-core/issues/1600
        # essentially qb.count() != len(qb.all()) in some cases.
        # We also addressed this with sqlachemy:
        # https://github.com/sqlalchemy/sqlalchemy/issues/4395#event-2002418814
        # where the following solution was sanctioned:
        self._query._has_mapper_entities = False  # pylint: disable=protected-access
        # We should monitor SQLAlchemy, for when a solution is officially supported by the API!

        # Make a list that helps the projection postprocessing
        self._projection_index_to_field = {
            index_in_sql_result: attrkey for tag, projected_entities_dict in self._tag_to_projected_fields.items()
            for attrkey, index_in_sql_result in projected_entities_dict.items()
        }

        if projection_count > len(self._projection_index_to_field):
            raise ValueError('You are projecting the same key multiple times within the same node')
        ######################### DONE #################################

        if self._distinct:
            self._query = self._query.distinct()

        return self._query

    def _build_join_func(self, query, index: int, joining_keyword: str, joining_value: str):
        """
        :param index: Index of this node within the path specification
        :param joining_keyword: the relation on which to join
        :param joining_value: the tag of the nodes to be joined
        """
        # pylint: disable=unused-argument
        # Set the calling entity - to allow for the correct join relation to be set
        entity_type = self._path[index]['entity_type']

        if isinstance(entity_type, str) and entity_type.startswith(GROUP_ENTITY_TYPE_PREFIX):
            calling_entity = 'group'
        elif entity_type not in ['computer', 'user', 'comment', 'log']:
            # entity types such as 'data.Data.' are all assumed to be nodes
            calling_entity = 'node'
        else:
            calling_entity = entity_type

        try:
            func = self._impl.get_join_func(calling_entity, joining_keyword)
        except KeyError:
            raise ValueError(f"'{joining_keyword}' is not a valid joining keyword for a '{calling_entity}' type entity")

        if isinstance(joining_value, str):
            try:
                return partial(func, query, self._tags._get_alias(self._impl, self._tags.get(joining_value)))
            except KeyError:
                raise ValueError(
                    f'Key {self._tags.get(joining_value)} is unknown to the types I know about:\n{list(self._tags)}'
                )
        raise ValueError(f"'joining_value' value is not a string: {joining_value}")

    def _build_order(self, alias, entitytag, entityspec):
        """
        Build the order parameter of the query
        """
        column_name = entitytag.split('.')[0]
        attrpath = entitytag.split('.')[1:]
        if attrpath and 'cast' not in entityspec.keys():
            raise ValueError(
                f'To order_by ({entitytag!r}), I have to cast the the values,\n'
                'but you have not specified the datatype to cast to\n'
                "You can do this with keyword 'cast'"
            )

        entity = self._get_projectable_entity(alias, column_name, attrpath, **entityspec)
        order = entityspec.get('order', 'asc')
        if order == 'desc':
            entity = entity.desc()
        self._query = self._query.order_by(entity)

    def _build_projections(self, tag, projection_count: int, items_to_project=None) -> int:
        """Build the projections for a given tag."""
        if items_to_project is None:
            items_to_project = self._projections.get(tag, [])

        # Return here if there is nothing to project, reduces number of key in return dictionary
        self.debug('projection for %s: %s', tag, items_to_project)
        if not items_to_project:
            return projection_count

        alias = self._tags._get_alias(self._impl, tag)

        self._tag_to_projected_fields[tag] = {}

        for projectable_spec in items_to_project:
            for projectable_entity_name, extraspec in projectable_spec.items():
                property_names = list()
                if projectable_entity_name == '**':
                    # Need to expand
                    property_names.extend(self._impl.modify_expansions(alias, self._impl.get_column_names(alias)))
                else:
                    property_names.extend(self._impl.modify_expansions(alias, [projectable_entity_name]))

                for property_name in property_names:
                    self._add_to_projections(alias, property_name, **extraspec)
                    self._tag_to_projected_fields[tag][property_name] = projection_count
                    projection_count += 1

        return projection_count

    def _add_to_projections(self, alias, projectable_entity_name, cast=None, func: str = None):
        """
        :param alias: A instance of *sqlalchemy.orm.util.AliasedClass*, alias for an ormclass
        :type alias: :class:`sqlalchemy.orm.util.AliasedClass`
        :param projectable_entity_name:
            User specification of what to project.
            Appends to query's entities what the user wants to project
            (have returned by the query)

        """
        column_name = projectable_entity_name.split('.')[0]
        attr_key = projectable_entity_name.split('.')[1:]

        if column_name == '*':
            if func is not None:
                raise ValueError(
                    'Very sorry, but functions on the aliased class\n'
                    "(You specified '*')\n"
                    'will not work!\n'
                    "I suggest you apply functions on a column, e.g. ('id')\n"
                )
            self._query = self._query.add_entity(alias)
        else:
            entity_to_project = self._get_projectable_entity(alias, column_name, attr_key, cast=cast)
            if func is None:
                pass
            elif func == 'max':
                entity_to_project = sa_func.max(entity_to_project)
            elif func == 'min':
                entity_to_project = sa_func.max(entity_to_project)
            elif func == 'count':
                entity_to_project = sa_func.count(entity_to_project)
            else:
                raise ValueError(f'\nInvalid function specification {func}')
            self._query = self._query.add_columns(entity_to_project)

    def _get_projectable_entity(self, alias, column_name, attrpath, **entityspec):
        """Return projectable entity for a given alias and column name."""
        if attrpath or column_name in ('attributes', 'extras'):
            entity = self._impl.get_projectable_attribute(alias, column_name, attrpath, **entityspec)
        else:
            entity = self._impl.get_column(column_name, alias)
        return entity


class _QueryTagMap:
    """Cache of tag mappings for a query."""

    def __init__(self):
        self._tag_to_alias: Dict[str, Union[None, EntityTypes, AliasedClass]] = {}
        # A dictionary for classes passed to the tag given to them
        # Everything is specified with unique tags, which are strings.
        # But somebody might not care about giving tags, so to do
        # everything with classes one needs a map, that also defines classes
        # as tags, to allow the following example:

        # qb = QueryBuilder()
        # qb.append(PwCalculation, tag='pwcalc')
        # qb.append(StructureData, tag='structure', with_outgoing=PwCalculation)

        # The cls_to_tag_map in this case would be:
        # {PwCalculation: {'pwcalc'}, StructureData: {'structure'}}
        self._cls_to_tag_map: Dict[Any, Set[str]] = {}

    def __repr__(self) -> str:
        return repr(list(self._tag_to_alias))

    def __contains__(self, tag: str) -> bool:
        return tag in self._tag_to_alias

    def __iter__(self):
        return iter(self._tag_to_alias)

    def add(self, tag: str, ormclass: Union[None, EntityTypes, AliasedClass] = None, klasses=None) -> None:
        """Add a tag."""
        self._tag_to_alias[tag] = ormclass

        # if a class was specified allow to get the tag given a class
        if klasses:
            tag_key = tuple(klasses) if isinstance(klasses, (list, set)) else klasses
            self._cls_to_tag_map.setdefault(tag_key, set()).add(tag)

    def _set_alias(self, tag: str, alias: AliasedClass) -> None:
        self._tag_to_alias[tag] = alias

    def remove(self, tag: str) -> None:
        """Remove a tag."""
        self._tag_to_alias.pop(tag, None)
        for tags in self._cls_to_tag_map.values():
            tags.discard(tag)

    def get(self, tag_or_cls: Any) -> str:
        """Return the tag or, given a class(es), map to a tag.

        :raises ValueError: if the tag is not found, or the class(es) does not map to a single tag
        """
        if isinstance(tag_or_cls, str):
            if tag_or_cls in self:
                return tag_or_cls
            raise ValueError(f'Tag {tag_or_cls} is not among my known tags: {list(self)}')
        if self._cls_to_tag_map.get(tag_or_cls, None):
            if len(self._cls_to_tag_map[tag_or_cls]) != 1:
                raise ValueError(
                    f'The object used as a tag ({tag_or_cls}) has multiple values associated with it: '
                    f'{self._cls_to_tag_map[tag_or_cls]}'
                )
            return list(self._cls_to_tag_map[tag_or_cls])[0]
        raise ValueError(f'The given object ({tag_or_cls}) has no tags associated with it.')

    def _get_alias(self, impl: 'BackendQueryBuilder', tag: str) -> AliasedClass:
        # move to implementation
        # issue here is that build joiners directly add aliased edge instances
        from sqlalchemy.orm import aliased
        alias = self._tag_to_alias[tag]
        if alias is None:
            raise AssertionError('alias is not set')
        if isinstance(alias, EntityTypes):
            cls = {
                EntityTypes.AUTHINFO: impl.AuthInfo,
                EntityTypes.COMMENT: impl.Comment,
                EntityTypes.COMPUTER: impl.Computer,
                EntityTypes.GROUP: impl.Group,
                EntityTypes.NODE: impl.Node,
                EntityTypes.LOG: impl.Log,
                EntityTypes.USER: impl.User,
            }[alias]
            alias = aliased(cls)
            # needs to return same instance
            self._tag_to_alias[tag] = alias
        return alias


def _get_ormclass(cls: Union[None, Type[Any], Sequence[Type[Any]]],
                  entity_type: Union[None, str, Sequence[str]]) -> Tuple[EntityTypes, List[Classifier]]:
    """Get ORM classifiers from either class(es) or ormclass_type_string(s).

    :param cls: a class or tuple/set/list of classes that are either AiiDA ORM classes or backend ORM classes.
    :param ormclass_type_string: type string for ORM class

    :returns: the ORM class as well as a dictionary with additional classifier strings

    Handles the case of lists as well.
    """
    if cls is not None:
        func = _get_ormclass_from_cls
        input_info = cls
    elif entity_type is not None:
        func = _get_ormclass_from_str  # type: ignore
        input_info = entity_type  # type: ignore
    else:
        raise ValueError('Neither cls nor entity_type specified')

    if isinstance(input_info, str) or not isinstance(input_info, Sequence):
        input_info = (input_info,)

    ormclass = EntityTypes.NODE
    classifiers = []

    for index, classifier in enumerate(input_info):
        new_ormclass, new_classifiers = func(classifier)
        if index:
            # check consistency with previous item
            if new_ormclass != ormclass:
                raise ValueError('Non-matching types have been passed as list/tuple/set.')
        else:
            ormclass = new_ormclass

        classifiers.append(new_classifiers)

    return ormclass, classifiers


def _get_ormclass_from_cls(cls: Type[Any]) -> Tuple[EntityTypes, Classifier]:
    """
    Return the correct classifiers for the QueryBuilder from an ORM class.

    :param cls: an AiiDA ORM class or backend ORM class.
    :param query: an instance of the appropriate QueryBuilder backend.
    :returns: the ORM class as well as a dictionary with additional classifier strings

    Note: the ormclass_type_string is currently hardcoded for group, computer etc. One could instead use something like
        aiida.orm.utils.node.get_type_string_from_class(cls.__module__, cls.__name__)
    """
    # pylint: disable=protected-access,too-many-branches,too-many-statements
    # Note: Unable to move this import to the top of the module for some reason
    from aiida.engine import Process
    from aiida.orm.utils.node import is_valid_node_type_string

    classifiers: Classifier

    if issubclass(cls, nodes.Node):
        classifiers = Classifier(cls._plugin_type_string)
        ormclass = EntityTypes.NODE
    elif issubclass(cls, groups.Group):
        classifiers = Classifier(GROUP_ENTITY_TYPE_PREFIX + cls._type_string)
        ormclass = EntityTypes.GROUP
    elif issubclass(cls, computers.Computer):
        classifiers = Classifier('computer')
        ormclass = EntityTypes.COMPUTER
    elif issubclass(cls, users.User):
        classifiers = Classifier('user')
        ormclass = EntityTypes.USER
    elif issubclass(cls, authinfos.AuthInfo):
        classifiers = Classifier('authinfo')
        ormclass = EntityTypes.AUTHINFO
    elif issubclass(cls, comments.Comment):
        classifiers = Classifier('comment')
        ormclass = EntityTypes.COMMENT
    elif issubclass(cls, logs.Log):
        classifiers = Classifier('log')
        ormclass = EntityTypes.LOG

    # Process
    # This is a special case, since Process is not an ORM class.
    # We need to deduce the ORM class used by the Process.
    elif issubclass(cls, Process):
        classifiers = Classifier(cls._node_class._plugin_type_string, cls.build_process_type())
        ormclass = EntityTypes.NODE

    else:
        raise ValueError(f'I do not know what to do with {cls}')

    if ormclass == EntityTypes.NODE:
        is_valid_node_type_string(classifiers.ormclass_type_string, raise_on_false=True)

    return ormclass, classifiers


def _get_ormclass_from_str(type_string: str) -> Tuple[EntityTypes, Classifier]:
    """Return the correct classifiers for the QueryBuilder from an ORM type string.

    :param type_string: type string for ORM class
    :param query: an instance of the appropriate QueryBuilder backend.
    :returns: the ORM class as well as a dictionary with additional classifier strings
    """
    from aiida.orm.utils.node import is_valid_node_type_string

    classifiers: Classifier
    type_string_lower = type_string.lower()

    if type_string_lower.startswith(GROUP_ENTITY_TYPE_PREFIX):
        classifiers = Classifier('group.core')
        ormclass = EntityTypes.GROUP
    elif type_string_lower == 'computer':
        classifiers = Classifier('computer')
        ormclass = EntityTypes.COMPUTER
    elif type_string_lower == 'user':
        classifiers = Classifier('user')
        ormclass = EntityTypes.USER
    else:
        # At this point, we assume it is a node. The only valid type string then is a string
        # that matches exactly the _plugin_type_string of a node class
        is_valid_node_type_string(type_string, raise_on_false=True)
        classifiers = Classifier(type_string)
        ormclass = EntityTypes.NODE

    return ormclass, classifiers


def _get_node_type_filter(classifiers: Classifier, subclassing: bool) -> dict:
    """
    Return filter dictionaries given a set of classifiers.

    :param classifiers: a dictionary with classifiers (note: does *not* support lists)
    :param subclassing: if True, allow for subclasses of the ormclass

    :returns: dictionary in QueryBuilder filter language to pass into {"type": ... }
    """
    from aiida.orm.utils.node import get_query_type_from_type_string
    from aiida.common.escaping import escape_for_sql_like
    value = classifiers.ormclass_type_string

    if not subclassing:
        filters = {'==': value}
    else:
        # Note: the query_type_string always ends with a dot. This ensures that "like {str}%" matches *only*
        # the query type string
        filters = {'like': f'{escape_for_sql_like(get_query_type_from_type_string(value))}%'}

    return filters


def _get_process_type_filter(classifiers: Classifier, subclassing: bool) -> dict:
    """
    Return filter dictionaries given a set of classifiers.

    :param classifiers: a dictionary with classifiers (note: does *not* support lists)
    :param subclassing: if True, allow for subclasses of the process type
            This is activated only, if an entry point can be found for the process type
            (as well as for a selection of built-in process types)


    :returns: dictionary in QueryBuilder filter language to pass into {"process_type": ... }
    """
    from aiida.common.escaping import escape_for_sql_like
    from aiida.common.warnings import AiidaEntryPointWarning
    from aiida.engine.processes.process import get_query_string_from_process_type_string

    value = classifiers.process_type_string
    assert value is not None
    filters: Dict[str, Any]

    if not subclassing:
        filters = {'==': value}
    else:
        if ':' in value:
            # if value is an entry point, do usual subclassing

            # Note: the process_type_string stored in the database does *not* end in a dot.
            # In order to avoid that querying for class 'Begin' will also find class 'BeginEnd',
            # we need to search separately for equality and 'like'.
            filters = {
                'or': [
                    {
                        '==': value
                    },
                    {
                        'like': escape_for_sql_like(get_query_string_from_process_type_string(value))
                    },
                ]
            }
        elif value.startswith('aiida.engine'):
            # For core process types, a filter is not is needed since each process type has a corresponding
            # ormclass type that already specifies everything.
            # Note: This solution is fragile and will break as soon as there is not an exact one-to-one correspondence
            # between process classes and node classes

            # Note: Improve this when issue https://github.com/aiidateam/aiida-core/issues/2475 is addressed
            filters = {'like': '%'}
        else:
            warnings.warn(
                "Process type '{value}' does not correspond to a registered entry. "
                'This risks queries to fail once the location of the process class changes. '
                "Add an entry point for '{value}' to remove this warning.".format(value=value), AiidaEntryPointWarning
            )
            filters = {
                'or': [
                    {
                        '==': value
                    },
                    {
                        'like': escape_for_sql_like(get_query_string_from_process_type_string(value))
                    },
                ]
            }

    return filters


def _get_group_type_filter(classifiers: Classifier, subclassing: bool) -> dict:
    """Return filter dictionaries for `Group.type_string` given a set of classifiers.

    :param classifiers: a dictionary with classifiers (note: does *not* support lists)
    :param subclassing: if True, allow for subclasses of the ormclass

    :returns: dictionary in QueryBuilder filter language to pass into {'type_string': ... }
    """
    from aiida.common.escaping import escape_for_sql_like

    value = classifiers.ormclass_type_string[len(GROUP_ENTITY_TYPE_PREFIX):]

    if not subclassing:
        filters = {'==': value}
    else:
        # This is a hardcoded solution to the problem that the base class `Group` should match all subclasses, however
        # its entry point string is `core` and so will only match those subclasses whose entry point also starts with
        # 'core', however, this is only the case for group subclasses shipped with `aiida-core`. Any plugins from
        # external packages will never be matched. Making the entry point name of `Group` an empty string is also not
        # possible so we perform the switch here in code.
        if value == 'core':
            value = ''
        filters = {'like': f'{escape_for_sql_like(value)}%'}

    return filters
