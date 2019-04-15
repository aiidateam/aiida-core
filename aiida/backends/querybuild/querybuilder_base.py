# -*- coding: utf-8 -*-


"""
The general functionalities that all querybuilders need to have
are found in this module.
:func:`AbstractQueryBuilder` is the abstract class for QueryBuilder classes.
Subclasses need to be written for *every* schema/backend implemented
in backends.

"""

import copy
import datetime
import warnings
from abc import abstractmethod, ABCMeta
from inspect import isclass as inspect_isclass
from sa_init import (
        aliased, and_, or_, not_, func as sa_func,
        InstrumentedAttribute, Cast
    )
from aiida.common.exceptions import (
        InputValidationError, DbContentError, MissingPluginError
    )
from aiida.common.utils import flatten_list
from aiida.common.hashing import make_hash



__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0.1"

class AbstractQueryBuilder(object):
    """
    QueryBuilderBase is the base class for QueryBuilder classes,
    which are than adapted to the individual schema and ORM used.
    In here, general graph traversal functionalities are implemented,
    the specific type of node and link is dealt in subclasses.
    In order to load the correct subclass::

        from aiida.orm.querybuilder import QueryBuilder
    """

    __metaclass__ = ABCMeta


    _EDGE_TAG_DELIM = '--'
    _VALID_PROJECTION_KEYS = ('func', 'cast')


    def __init__(self, *args, **kwargs):

        # A list storing the path being traversed by the query
        self._path = []

        # The list of unique tags
        # self.tag_list = []# not needed any more

        # A list of unique aliases in same order as path
        self._aliased_path = []

        # A dictionary tag:alias of ormclass
        # redundant but makes life easier
        self._tag_to_alias_map = {}

        # A dictionary tag: filter specification for this alias
        self._filters = {}

        # A dictionary tag: projections for this alias
        self._projections = {}

        # A dictionary for classes passed to the tag given to them
        # Everything is specified with unique tags, which are strings.
        # But somebody might not care about giving tags, so to do
        # everything with classes one needs a map
        # qb = QueryBuilder(path = [PwCalculation])
        # qb.append(StructureData, input_of=PwCalculation

        # The cls_to_tag_map in this case would be:
        # {PwCalculation:'PwCalculation', StructureData:'StructureData'}

        self._cls_to_tag_map = {}

        self._hash = None

        self._injected = False
        if args:
            raise InputValidationError(
                    "Arguments are not accepted\n"
                    "when instantiating a QueryBuilder instance"
                )

        path = kwargs.pop('path', [])
        if not isinstance(path, (tuple, list)):
            raise InputValidationError(
                    "Path needs to be a tuple or a list"
                )
        for path_spec in path:
            try:
                self.append(**path_spec)
            except TypeError as e:
                if isinstance(path_spec, basestring):
                    # Maybe it is just a string,
                    # I assume user means the type
                    self.append(type=path_spec)
                else:
                    # Or a class, let's try
                    self.append(cls=path_spec)

        for key, val in kwargs.pop('project', {}).items():
            self.add_projection(key, val)

        for key, val in kwargs.pop('filters', {}).items():
            self.add_filter(key, val)

        self.limit(kwargs.pop('limit', None))

        self.offset(kwargs.pop('offset', None))

        self._order_by = {}
        order_spec = kwargs.pop('order_by', None)
        if order_spec:
            self.order_by(order_spec)

        if kwargs:
            valid_keys = [
                    'path', 'filters', 'project', 'limit', 'order_by'
            ]
            raise InputValidationError(
                    "Received additional keywords: {}"
                    "\nwhich I cannot process"
                    "\nValid keywords are: {}"
                    "".format(kwargs.keys(), valid_keys)
            )


    def __str__(self):
        from aiida.common.setup import get_profile_config
        from aiida.backends import settings
        from aiida.common.exceptions import ConfigurationError

        engine = get_profile_config(settings.AIIDADB_PROFILE)["AIIDADB_ENGINE"]

        if engine == "sqlite3":
            from sqlalchemy.dialects import sqlite as mydialect
        elif engine.startswith("mysql"):
            from sqlalchemy.dialects import mysql as mydialect
        elif engine.startswith("postgre"):
            from sqlalchemy.dialects import postgresql as mydialect
        else:
            raise ConfigurationError("Unknown DB engine: {}".format(
                    engine))

        que = self.get_query()
        return str(que.statement.compile(
                compile_kwargs={"literal_binds": True},
                dialect=mydialect.dialect()
            )
        )



    def _get_ormclass(self, cls, ormclasstype):
        """
        Return the valid ormclass for the connections
        """
        # Checks whether valid cls and ormclasstype are done before

        # If it is a class:
        if cls:
            # Nodes:
            if issubclass(cls, self.Node):
                # If something pass an ormclass node
                # Users wouldn't do that, by why not...
                ormclasstype = self.AiidaNode._plugin_type_string
                query_type_string = self.AiidaNode._query_type_string
                ormclass = cls
            elif issubclass(cls, self.AiidaNode):
                ormclasstype = cls._plugin_type_string
                query_type_string = cls._query_type_string
                ormclass = self.Node
            # Groups:
            elif issubclass(cls, self.Group):
                ormclasstype = 'group'
                query_type_string = None
                ormclass = cls
            elif issubclass(cls, self.AiidaGroup):
                ormclasstype = 'group'
                query_type_string = None
                ormclass = self.Group
            # Computers:
            elif issubclass(cls, self.Computer):
                ormclasstype = 'computer'
                query_type_string = None
                ormclass = cls
            elif issubclass(cls, self.AiidaComputer):
                ormclasstype = 'computer'
                query_type_string = None
                ormclass = self.Computer

            # Users
            elif issubclass(cls, self.User):
                ormclasstype = 'user'
                query_type_string = None
                ormclass = cls
            elif issubclass(cls, self.AiidaUser):
                ormclasstype = 'user'
                query_type_string = None
                ormclass = self.User
            else:
                raise InputValidationError(
                        "\n\n\n"
                        "I do not know what to do with {}"
                        "\n\n\n".format(cls)
                    )
        # If it is not a class
        else:
            if ormclasstype.lower() == 'group':
                ormclasstype = ormclasstype.lower()
                query_type_string = None
                ormclass = self.Group
            elif ormclasstype.lower() == 'computer':
                ormclasstype = ormclasstype.lower()
                query_type_string = None
                ormclass = self.Computer
            elif ormclasstype.lower() == 'user':
                ormclasstype = ormclasstype.lower()
                query_type_string = None
                ormclass = self.User
            else:
                # At this point, it has to be a node.
                # The only valid string at this point is a string
                # that matches exactly the _plugin_type_string
                # of a node class
                from aiida.common.pluginloader import (
                        from_type_to_pluginclassname,
                        load_plugin
                    )
                ormclass = self.Node
                try:
                    pluginclassname = from_type_to_pluginclassname(ormclasstype)

                    # I want to check at this point if that is a valid class,
                    # so I use the load_plugin to load the plugin class
                    # and use the classes _plugin_type_string attribute
                    # In the future, assuming the user knows what he or she is doing
                    # we could remove that check
                    # The query_type_string we can get from
                    # the aiida.common.pluginloader function get_query_type_string
                    PluginClass = load_plugin(self.AiidaNode, 'aiida.orm', pluginclassname)
                except (DbContentError, MissingPluginError) as e:
                    raise InputValidationError(
                        "\nYou provide a vertice of the path with\n"
                        "type={}\n"
                        "But that string is not a valid type string\n"
                        "Exception raise during check\n"
                        "{}".format(ormclasstype, e)
                    )


                ormclasstype = PluginClass._plugin_type_string
                query_type_string = PluginClass._query_type_string

        return ormclass, ormclasstype, query_type_string

    def _get_autotag(self, ormclasstype):
        basetag = self._get_tag_from_type(ormclasstype)
        tags_used = self._tag_to_alias_map.keys()
        for i in range(1, 100):
            tag = '{}_{}'.format(basetag, i)
            if tag not in tags_used:
                return tag


    def _get_tag_from_type(self, ormclasstype):
        """
        Assign a tag to the given
        vertice of a path, based mainly on the type
        *   data.structure.StructureData -> StructureData
        *   data.structure.StructureData. -> StructureData
        *   calculation.job.quantumespresso.pw.PwCalculation. -. PwCalculation
        *   node.Node. -> Node
        *   Node -> Node
        *   computer -> computer
        """
        return ormclasstype.rstrip('.').split('.')[-1]


    def append(self, cls=None, type=None, tag=None,
                autotag=False, filters=None, project=None, subclassing=True,
                edge_tag=None, edge_filters=None, edge_project=None, **kwargs
        ):
        """
        Any iterative procedure to build the path for a graph query
        needs to invoke this method to append to the path.

        :param cls: The Aiida-class (or backend-class) defining the appended vertice
        :param type: The type of the class, if cls is not given
        :param tag:
            A unique tag. If none is given, will take the classname.
            See keyword autotag to achieve unique tag.
        :param filters:
            Filters to apply for this vertice.
            See usage examples for details.
        :param autotag:
            Whether to search for a unique tag,
            (default **False**). If **True**, will find a unique tag.
            Cannot be set to **True** if tag is specified.
        :param subclassing:
            Whether to include subclasses of the given class
            (default **True**).
            E.g. Specifying JobCalculation will include PwCalculation

        A small usage example how this can be invoked::

            qb = QueryBuilder()             # Instantiating empty querybuilder instance
            qb.append(cls=StructureData)    # First item is StructureData node
            # The
            # next node in the path is a PwCalculation, with
            # the structure joined as an input
            qb.append(
                cls=PwCalculation,
                output_of=StructureData
            )

        :returns: self
        """
        ######################## INPUT CHECKS ##########################
        # This function can be called by users, so I am checking the
        # input now.
        # First of all, let's make sure the specified
        # the class or the type (not both)
        if cls and type:
            raise InputValidationError(
                    "\n\n\n"
                    "You cannot specify both a \n"
                    "class ({})\n"
                    "and a type ({})\n\n"
                    "".format(cls, type)
                )

        if not (cls or type):
            raise InputValidationError(
                    "\n\n"
                    "You need to specify either a class or a type"
                    "\n\n"
                )

        # Let's check if it is a valid class or type
        if cls:
            if not inspect_isclass(cls):
                raise InputValidationError(
                    "\n\n"
                    "{} was passed with kw 'cls', but is not a class"
                    "\n\n".format(cls)
                )
        elif type:
            if not isinstance(type, basestring):
                raise InputValidationError(
                    "\n\n\n"
                    "{} was passed as type, but is not a string"
                    "\n\n\n".format(type)
                )

        if 'link_tag' in kwargs:
            raise DeprecationWarning("link_tag is deprecated, use edge_tag instead")
        ormclass, ormclasstype, query_type_string = self._get_ormclass(cls, type)
        ############################### TAG #################################
        # Let's get a tag
        user_defined_tag = False
        label = kwargs.pop('label', None)
        if label is not None:
            if tag is None:
                warnings.warn(
                    "\nUse of the keyword 'label' will be deprecated soon\n"
                    "Please use 'tag' instead\n",
                    DeprecationWarning,
                )
                tag = label
            else:
                raise InputValidationError("Both label and tag specified")

        if tag:
            if self._EDGE_TAG_DELIM in tag:
                raise InputValidationError(
                    "tag cannot contain {}\n"
                    "since this is used as a delimiter for links"
                    "".format(self._EDGE_TAG_DELIM)
                )
            tag = tag
            user_defined_tag = True
        elif autotag:
            tag = self._get_autotag(ormclasstype)
        else:
            tag = self._get_tag_from_type(ormclasstype)
        # Check if the tag is not yet used:
        if tag in self._tag_to_alias_map.keys():
            if user_defined_tag:
                raise InputValidationError(
                    "\n"
                    "This tag ({}) is already in use\n"
                    "\n".format(tag)
                )
            else:
                raise InputValidationError(
                    "\n"
                    "You did not specify a tag, so I am making one myself\n"
                    "based on the class/type you gave me\n"
                    "The tag that I made ({}) is already in use\n"
                    "please specify a tag or set autotag to true"
                    "".format(tag)
                )

        ################ TAG MAPPING #################################
        # Let's fill the cls_to_tag_map so that one can specify
        # this vertice in a joining specification later
        # First this only makes sense if a class was specified:
        if cls:
            if cls in self._cls_to_tag_map.keys():
                # In this case, this class already stands for another
                # tag that was used before.
                # This means that the first tag will be the correct
                # one. This is dangerous and maybe should be avoided in
                # the future
                pass

            else:
                self._cls_to_tag_map[cls] = tag
            # TODO check with duplicate classes


        ######################## ALIASING ##############################
        alias = aliased(ormclass)
        self._aliased_path.append(alias)
        self._tag_to_alias_map[tag] = alias



        ################# FILTERS ######################################

        self._filters[tag] = {}

        # I have to add a filter on column type.
        # This so far only is necessary for AiidaNodes
        # GROUPS?
        if query_type_string is not None:
            self._add_type_filter(tag, query_type_string, subclassing)
        # The order has to be first _add_type_filter and then add_filter.
        # If the user adds a query on the type column, it overwrites what I did

        #if the user specified a filter, add it:
        if filters is not None:
            self.add_filter(tag, filters)


        ##################### PROJECTIONS ##############################
        self._projections[tag] = []

        if project is not None:
            self.add_projection(tag, project)




        ################## JOINING #####################################

        # Get the functions that are implemented:
        spec_to_function_map = self._get_function_map().keys()


        joining_keyword = kwargs.pop('joining_keyword', None)
        joining_value = kwargs.pop('joining_value', None)
        #~ reverse_linklabel = kwargs.pop('reverse_linklabel', None)


        for key, val in kwargs.items():
            if key not in spec_to_function_map:
                raise InputValidationError(
                        "\n\n\n"
                        "{} is not a valid keyword "
                        "for joining specification\n"
                        "Valid keywords are:\n"
                        "{}\n\n\n".format(
                                key,
                                spec_to_function_map+[
                                    'cls', 'type', 'tag',
                                    'autotag', 'filters', 'project'
                                ]
                            )
                    )
            elif joining_keyword:
                raise InputValidationError(
                        "\n\n\n"
                        "You already specified joining specification {}\n"
                        "But you now also want to specify {}"
                        "\n\n\n".format(joining_keyword, key)
                    )
            else:
                joining_keyword = key
                joining_value = self._get_tag_from_specification(val)
        # the default is that this vertice is 'output_of' the previous one
        if joining_keyword is None and len(self._path)>0:
            joining_keyword = 'output_of'
            joining_value = self._path[-1]['tag']

        if joining_keyword == 'direction':
            if not isinstance(joining_value, int):
                raise InputValidationError("direction=n expects n to be an integer")
            try:
                if joining_value < 0:
                    joining_keyword = 'input_of'
                elif joining_value > 0:
                    joining_keyword = 'output_of'
                else:
                    raise InputValidationError("direction=0 is not valid")
                joining_value = self._path[-abs(joining_value)]['tag']
            except IndexError as e:
                raise InputValidationError(
                    "You have specified a non-existent entity with\n"
                    "direction={}\n"
                    "{}\n".format(joining_value, e.message)
                )

        ############################# EDGES #################################
        # See if this requires a link:
        aliased_edge = None
        if len(self._path) > 0:
            if joining_keyword in ('input_of', 'output_of'):
                aliased_edge = aliased(self.Link)
            elif joining_keyword in ('ancestor_of', 'descendant_of'):
                aliased_edge = aliased(self.Path)

            if aliased_edge is not None:

                # Ok, so here we are joining through a m2m relationship,
                # e.g. input or output.
                # This means that the user might want to query by that edge!

                if edge_tag is None:
                    edge_destination_tag = self._get_tag_from_specification(joining_value)
                    edge_tag = edge_destination_tag + self._EDGE_TAG_DELIM + tag
                else:
                    if edge_tag in self._tag_to_alias_map.keys():
                        raise InputValidationError(
                            "The tag {} is already in use".format(edge_tag)
                        )

                self._tag_to_alias_map[edge_tag] = aliased_edge

                # Filters on links:
                self._filters[edge_tag] = {}
                if edge_filters is not None:
                    self.add_filter(edge_tag, edge_filters)

                # Projections on links
                self._projections[edge_tag] = {}
                if edge_project is not None:
                    self.add_projection(edge_tag, edge_project)


        ################### EXTENDING THE PATH #################################


        path_extension = dict(
                type=ormclasstype, tag=tag, joining_keyword=joining_keyword,
                joining_value=joining_value
            )
        if aliased_edge is not None:
            path_extension.update(dict(edge_tag=edge_tag))
            #~ if reverse_linktag is not None:
                #~ path_extension.update(dict(reverse_linktag=reverse_linktag))

        self._path.append(path_extension)
        return self

    def order_by(self, order_by):
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

        self._order_by = []
        allowed_keys = ('cast', 'order')
        possible_orders = ('asc', 'desc')

        if not isinstance(order_by, (list, tuple)):
            order_by = [order_by]

        for order_spec in order_by:
            if not isinstance(order_spec, dict):
                    raise InputValidationError(
                        "Invalid input for order_by statement: {}\n"
                        "I am expecting a dictionary ORMClass,"
                        "[columns to sort]"
                        "".format(order_spec)
                    )
            _order_spec = {}
            for tagspec,items_to_order_by in order_spec.items():
                if not isinstance(items_to_order_by, (tuple, list)):
                    items_to_order_by = [items_to_order_by]
                tag = self._get_tag_from_specification(tagspec)
                _order_spec[tag] = []
                for item_to_order_by in items_to_order_by:
                    if isinstance(item_to_order_by, basestring):
                        item_to_order_by = {item_to_order_by:{}}
                    elif isinstance(item_to_order_by, dict):
                        pass
                    else:
                        raise InputValidationError(
                            "Cannot deal with input to order_by {}\n"
                            "of type{}"
                            "\n".format(item_to_order_by, type(item_to_order_by))
                        )
                    for entityname, orderspec in item_to_order_by.items():
                        # if somebody specifies eg {'node':{'id':'asc'}}
                        # tranform to {'node':{'id':{'order':'asc'}}}

                        if isinstance(orderspec, basestring):
                            this_order_spec = {'order':orderspec}
                        elif isinstance(orderspec, dict):
                            this_order_spec = orderspec
                        else:
                            raise InputValidationError(
                                "I was expecting a string or a dictionary\n"
                                "You provided {} {}\n"
                                "".format(type(orderspec), orderspec)
                            )
                        for key in this_order_spec.keys():
                            if key not in allowed_keys:
                                raise InputValidationError(
                                    "The allowed key for an order specification\n"
                                    "are {}\n"
                                    "{} is not valid\n"
                                    "".format(', '.join(allowed_keys), k)
                                )
                        this_order_spec['order'] = this_order_spec.get('order', 'asc')
                        if this_order_spec['order'] not in possible_orders:
                            raise InputValidationError(
                                "You gave {} as an order parameters,\n"
                                "but it is not a valid order parameter\n"
                                "Valid orders are: {}\n"
                                "".format(this_order_spec['order'], possible_orders)
                            )
                        item_to_order_by[entityname] = this_order_spec

                    _order_spec[tag].append(item_to_order_by)

            self._order_by.append(_order_spec)
        return self

    def add_filter(self, tagspec, filter_spec):
        """
        Adding a filter to my filters.

        :param tagspec:
            The tag, which has to exist already as a key
            in self._filters
        :param filter_spec:
            The specifications for the filter, has to be a dictionary
        """


        if not isinstance(filter_spec, dict):
            raise InputValidationError(
                    "Filters have to be passed as dictionaries"
                )

        tag = self._get_tag_from_specification(tagspec)
        self._filters[tag].update(filter_spec)

    def _add_type_filter(
        self, tagspec, query_type_string,
        ormclasstype, subclassing=True):
        """
        Add a filter on the type based on the query_type_string
        """
        tag = self._get_tag_from_specification(tagspec)

        if subclassing:
            node_type_flt = {'like':'{}%'.format(query_type_string)}
        else:
            node_type_flt = {'==':ormclasstype}

        self.add_filter(tagspec, {'type':node_type_flt})

    def add_projection(self, tag_spec, projection_spec):
        """
        Adds a projection

        :param tag_spec: A valid specification for a tag
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
        """
        tag = self._get_tag_from_specification(tag_spec)
        _projections = []
        if not isinstance(projection_spec, (list, tuple)):
            projection_spec = [projection_spec]
        for projection in projection_spec:
            if isinstance(projection, dict):
                _thisprojection = projection
            elif isinstance(projection, basestring):
                _thisprojection = {projection:{}}
            else:
                raise InputValidationError(
                    "Cannot deal with projection specification {}\n"
                    "".format(projection)
                )
            for p,spec in _thisprojection.items():
                if not isinstance(spec, dict):
                    raise InputValidationError(
                        "\nThe value of a key-value pair in a projection\n"
                        "has to be a dictionary\n"
                        "You gave: {}\n"
                        "".format(spec)
                    )

                for key, val in spec.items():
                    if key not in self._VALID_PROJECTION_KEYS:
                        raise InputValidationError(
                            "{} is not a valid key {}".format(
                                key, self._VALID_PROJECTION_KEYS)
                        )
                        if not isinstance(val, basestring):
                            raise InputValidationError(
                                "{} has to be a string".format(val)
                            )
            _projections.append(_thisprojection)
        self._projections[tag] = _projections


    def _get_projectable_entity(self, alias, column_name, attrpath, **entityspec):

        if len(attrpath) or column_name in ('attributes', 'extras'):

            entity = self._get_projectable_attribute(
                        alias, column_name, attrpath, **entityspec
                    )
        else:
            entity = self._get_column(column_name, alias)
        return entity

    def _add_to_projections(self, alias, projectable_entity_name, cast=None, func=None):
        """
        :param alias:
            A instance of *sqlalchemy.orm.util.AliasedClass*, alias for an ormclass
        :param projectable_entity_name:
            User specification of what to project.
            Appends to query's entities what the user wants to project
            (have returned by the query)

        """
        column_name = projectable_entity_name.split('.')[0]
        attr_key = projectable_entity_name.split('.')[1:]


        if column_name == '*':
            if func is not None:
                raise InputValidationError(
                        "Very sorry, but functions on the aliased class\n"
                        "(You specified '*')\n"
                        "will not work!\n"
                        "I suggest you apply functions on a column, e.g. ('id')\n"
                    )
            self._query = self._query.add_entity(alias)
        else:
            entity_to_project = self._get_projectable_entity(
                    alias, column_name, attr_key,
                    cast=cast
                )
            if func is None:
                pass
            elif func == 'max':
                entity_to_project = sa_func.max(entity_to_project)
            elif func == 'min':
                entity_to_project = sa_func.max(entity_to_project)
            elif func == 'count':
                entity_to_project = sa_func.count(entity_to_project)
            else:
                raise InputValidationError(
                        "\nInvalid function specification {}".format(func)
                    )
            self._query =  self._query.add_columns(entity_to_project)




    def _build_projections(self, tag, items_to_project=None):

        if items_to_project is None:
            items_to_project = self._projections.get(tag, [])

        # Return here if there is nothing to project,
        # reduces number of key in return dictionary
        if not items_to_project:
            return

        alias = self._tag_to_alias_map[tag]

        self.tag_to_projected_entity_dict[tag] = {}

        for projectable_spec in items_to_project:
            for projectable_entity_name, extraspec in projectable_spec.items():
                if projectable_entity_name == '**':
                    # Need to expand
                    entity_names = [str(c).replace(alias.__table__.name+'.','') for c in alias.__table__.columns]
                    #~ for s in ('attributes', 'extras'):
                        #~ try:
                            #~ entity_names.remove(s)
                        #~ except ValueError:
                            #~ pass
                else:
                    entity_names = [projectable_entity_name]
                for entity_name in entity_names:
                    self._add_to_projections(
                            alias, entity_name, **extraspec
                        )

                    self.tag_to_projected_entity_dict[tag][
                            entity_name
                        ] = self.nr_of_projections
                    self.nr_of_projections += 1


    def _get_tag_from_specification(self, specification):
        if isinstance(specification, basestring):
            if specification in self._tag_to_alias_map.keys():
                tag = specification
            else:
                raise InputValidationError(
                        "tag {} is not among my known tags\n"
                        "   My tags are: {}"
                        "\n\n".format(
                                specification, self._tag_to_alias_map.keys()
                            )
                    )
        else:
            if specification in self._cls_to_tag_map.keys():
                tag = self._cls_to_tag_map[specification]
            else:
                raise InputValidationError(
                    "\nYou specified as a class for which I have to find a tag\n"
                    "The classes that I can do this for are:{}\n"
                    "The tags I have are: {}\n"
                    "\n".format(
                        specification, self._cls_to_tag_map.keys(),
                        self._tag_to_alias_map.keys()
                    )
                )
        return tag

    def limit(self, limit):
        """
        Set the limit (nr of rows to return)

        :param int limit: integers of nr of rows to return
        """

        if limit is not None:
            if not isinstance(limit, int):
                raise InputValidationError("limit has to be an integer")
        self._limit = limit
        return self

    def offset(self, offset):
        """
        Set the offset. If offset is set, that many rows are skipped before returning.
        *offset* = 0 is the same as omitting setting the offset.
        If both offset and limit appear,
        then *offset* rows are skipped before starting to count the *limit* rows
        that are returned.

        :param int offset: integers of nr of rows to skip
        """
        if offset is not None:
            if not isinstance(offset, int):
                raise InputValidationError(
                    "offset has to be an integer"
                )
        self._offset = offset
        return self


    @staticmethod
    @abstractmethod
    def _get_session():
        pass

    @staticmethod
    def _get_filter_expr_from_column(operator, value, column):

        if not isinstance(column, (Cast, InstrumentedAttribute)):
            raise TypeError(
                'column ({}) {} is not a valid column'.format(
                    type(column), column
                )
            )
        database_entity = column
        if operator == '==':
            expr = database_entity == value
        elif operator == '>':
            expr = database_entity > value
        elif operator == '<':
            expr = database_entity < value
        elif operator == '>=':
            expr = database_entity >= value
        elif operator == '<=':
            expr = database_entity <= value
        elif operator == 'like':
            expr = database_entity.like(value)
        elif operator == 'ilike':
            expr = database_entity.ilike(value)
        elif operator == 'in':
            expr = database_entity.in_(value)
        else:
            raise InputValidationError(
                'Unknown operator {} for filters on columns'.format(operator)
            )
        return expr


    @classmethod
    def _get_filter_expr(
            cls, operator, value, attr_key, is_attribute,
            alias=None, column=None, column_name=None
        ):
        """
        Applies a filter on the alias given.
        Expects the alias of the ORM-class on which to filter, and filter_spec.
        Filter_spec contains the specification on the filter.
        Expects:

        :param operator: The operator to apply, see below for further details
        :param value:
            The value for the right side of the expression,
            the value you want to compare with.

        :param path: The path leading to the value

        :param attr_key: Boolean, whether the value is in a json-column,
            or in an attribute like table.


        Implemented and valid operators:

        *   for any type:
            *   ==  (compare single value, eg: '==':5.0)
            *   in    (compare whether in list, eg: 'in':[5, 6, 34]
        *  for floats and integers:
            *   >
            *   <
            *   <=
            *   >=
        *  for strings:
            *   like  (case - sensitive), for example
                'like':'node.calc.%'  will match node.calc.relax and
                node.calc.RELAX and node.calc. but
                not node.CALC.relax
            *   ilike (case - unsensitive)
                will also match node.CaLc.relax in the above example

            .. note::
                The character % is a reserved special character in SQL,
                and acts as a wildcard. If you specifically
                want to capture a ``%`` in the string, use: ``_%``

        *   for arrays and dictionaries (only for the
            SQLAlchemy implementation):

            *   contains: pass a list with all the items that
                the array should contain, or that should be among
                the keys, eg: 'contains': ['N', 'H'])
            *   has_key: pass an element that the list has to contain
                or that has to be a key, eg: 'has_key':'N')

        *  for arrays only (SQLAlchemy version):
            *   of_length
            *   longer
            *   shorter

        All the above filters invoke a negation of the
        expression if preceded by **~**::

            # first example:
            filter_spec = {
                'name' : {
                    '~in':[
                        'halle',
                        'lujah'
                    ]
                } # Name not 'halle' or 'lujah'
            }

            # second example:
            filter_spec =  {
                'id' : {
                    '~==': 2
                }
            } # id is not 2
        """


        expr = None
        if operator.startswith('~'):
            negation = True
            operator = operator.lstrip('~')
        elif operator.startswith('!'):
            negation = True
            operator = operator.lstrip('!')
        else:
            negation = False
        if operator in ('longer', 'shorter', 'of_length'):
            if not isinstance(value, int):
                raise InputValidationError(
                    "You have to give an integer when comparing to a length"
                )
        elif operator in ('like', 'ilike'):
            if not isinstance(value, basestring):
                raise InputValidationError(
                    "Value for operator {} has to be a string (you gave {})"
                    "".format(operator, value)
                )

        elif operator == 'in':
            value_type_set = set([type(i) for i in value])
            if len(value_type_set) > 1:
                raise InputValidationError(
                        '{}  contains more than one type'.format(value)
                    )
            elif len(value_type_set) == 0:
                raise InputValidationError(
                        '{}  contains is an empty list'.format(value)
                    )
        elif operator in ('and', 'or'):
            expressions_for_this_path = []
            for filter_operation_dict in value:
                for newoperator, newvalue in filter_operation_dict.items():
                    expressions_for_this_path.append(
                            cls._get_filter_expr(
                                    newoperator, newvalue,
                                    attr_key=attr_key, is_attribute=is_attribute,
                                    alias=alias, column=column,
                                    column_name=column_name
                                )
                        )
            if operator == 'and':
                expr = and_(*expressions_for_this_path)
            elif operator == 'or':
                 expr = or_(*expressions_for_this_path)

        if expr is None:
            if is_attribute:
                expr = cls._get_filter_expr_from_attributes(
                        operator, value, attr_key,
                        column=column, column_name=column_name, alias=alias
                    )
            else:
                if column is None:
                    if (alias is None) and (column_name is None):
                        raise Exception(
                            "I need to get the column but do not know \n"
                            "the alias and the column name"
                        )
                    column = cls._get_column(column_name, alias)
                expr = cls._get_filter_expr_from_column(operator, value, column)
        if negation:
            return not_(expr)
        return expr



    def _build_filters(self, alias, filter_spec):
        """
        Recurse through the filter specification and apply filter operations.

        :param alias: The alias of the ORM class the filter will be applied on
        :param filter_spec: the specification as given by the queryhelp

        :returns: an instance of *sqlalchemy.sql.elements.BinaryExpression*.
        """
        expressions = []
        for path_spec, filter_operation_dict in filter_spec.items():
            if path_spec in  ('and', 'or', '~or', '~and', '!and', '!or'):
                subexpressions = [
                    self._build_filters(alias, sub_filter_spec)
                    for sub_filter_spec in filter_operation_dict
                ]
                if path_spec == 'and':
                    expressions.append(and_(*subexpressions))
                elif path_spec == 'or':
                    expressions.append(or_(*subexpressions))
                elif path_spec in ('~and', '!and'):
                    expressions.append(not_(and_(*subexpressions)))
                elif path_spec in ('~or', '!or'):
                    expressions.append(not_(or_(*subexpressions)))
            else:
                column_name = path_spec.split('.')[0]

                attr_key = path_spec.split('.')[1:]
                is_attribute = (
                    attr_key or
                    column_name in ('attributes', 'extras')
                )
                try:
                    column = self._get_column(column_name, alias)
                except InputValidationError as e:
                    if is_attribute:
                        column = None
                    else:
                        raise e
                #~ is_attribute = bool(attr_key)
                if not isinstance(filter_operation_dict, dict):
                    filter_operation_dict = {'==':filter_operation_dict}
                [
                    expressions.append(
                        self._get_filter_expr(
                            operator, value, attr_key,
                            is_attribute=is_attribute,
                            column=column, column_name=column_name,
                            alias=alias
                        )
                    )
                    for operator, value
                    in filter_operation_dict.items()
                ]
        return and_(*expressions)

    #~ @abstractmethod
    #~ def _build_filters(self, alias, filter_spec):
        #~ pass
    @staticmethod
    def _check_dbentities(entities_cls_joined, entities_cls_to_join, relationship):
        """
        :param list entities_cls_joined:
            A list (tuple) of the aliased class passed as joined_entity and
            the ormclass that was expected
        :param list entities_cls_joined:
            A list (tuple) of the aliased class passed as entity_to_join and
            the ormclass that was expected
        :param str relationship:
            The relationship between the two entities to make the Exception
            comprehensible
        """
        for entity, cls in (entities_cls_joined, entities_cls_to_join):

            if not issubclass(entity._sa_class_manager.class_, cls):
                raise InputValidationError(
                    "\nYou are attempting to join {} as '{}' of {}\n"
                    "This failed because you passed:\n"
                    " - {} as entity joined (expected {})\n"
                    " - {} as entity to join (expected {})\n"
                    "\n".format(
                        entities_cls_joined[0],
                        relationship,
                        entities_cls_to_join[0],
                        entities_cls_joined[0]._sa_class_manager.class_,
                        entities_cls_joined[1],
                        entities_cls_to_join[0]._sa_class_manager.class_,
                        entities_cls_to_join[1],
                    )
                )


    def _join_slaves(self, joined_entity, entity_to_join):
        raise NotImplementedError(
                "Master - slave relationships are not implemented"
            )
        #~ call = aliased(Call)
        #~ self._query = self._query.join(call,  call.caller_id == joined_entity.id)
        #~ self._query = self._query.join(
                #~ entity_to_join,
                #~ call.called_id == entity_to_join.id
            #~ )

    def _join_masters(self, joined_entity, entity_to_join):
        raise NotImplementedError(
                "Master - slave relationships are not implemented"
            )
        #~ call = aliased(Call)
        #~ self._query = self._query.join(call,  call.called_id == joined_entity.id)
        #~ self._query = self._query.join(
                #~ entity_to_join,
                #~ call.caller_id == entity_to_join.id
            #~ )

    def _join_outputs(self, joined_entity, entity_to_join, aliased_edge):
        """
        :param joined_entity: The (aliased) ORMclass that is an input
        :param entity_to_join: The (aliased) ORMClass that is an output.

        **joined_entity** and **entity_to_join** are joined with a link
        from **joined_entity** as input to **enitity_to_join** as output
        (**enitity_to_join** is an *output_of* **joined_entity**)
        """
        self._check_dbentities(
                (joined_entity, self.Node),
                (entity_to_join, self.Node),
                'output_of'
            )
        self._query = self._query.join(
                aliased_edge,
                aliased_edge.input_id == joined_entity.id
        ).join(
                entity_to_join,
                aliased_edge.output_id == entity_to_join.id
        )

    def _join_inputs(self, joined_entity, entity_to_join, aliased_edge):
        """
        :param joined_entity: The (aliased) ORMclass that is an output
        :param entity_to_join: The (aliased) ORMClass that is an input.

        **joined_entity** and **entity_to_join** are joined with a link
        from **joined_entity** as output to **enitity_to_join** as input
        (**enitity_to_join** is an *input_of* **joined_entity**)
        """
        self._check_dbentities(
                (joined_entity, self.Node),
                (entity_to_join, self.Node),
                'input_of'
            )
        self._query = self._query.join(
                aliased_edge,
                aliased_edge.output_id == joined_entity.id
        ).join(
                entity_to_join,
                aliased_edge.input_id == entity_to_join.id
        )

    def _join_descendants(self, joined_entity, entity_to_join, aliased_path):
        """
        :param joined_entity: The (aliased) ORMclass that is an ancestor
        :param entity_to_join: The (aliased) ORMClass that is a descendant.
        :param aliased_path: An aliased instance of DbPath

        **joined_entity** and **entity_to_join** are
        joined via the DbPath table.
        from **joined_entity** as parent to **enitity_to_join** as child
        (**enitity_to_join** is a *descendant_of* **joined_entity**)
        """
        self._check_dbentities(
                (joined_entity, self.Node),
                (entity_to_join, self.Node),
                'descendant_of'
            )
        
        self._query = self._query.join(
                aliased_path,
                aliased_path.parent_id == joined_entity.id
        ).join(
                entity_to_join,
                aliased_path.child_id == entity_to_join.id
        )

    def _join_ancestors(self, joined_entity, entity_to_join, aliased_path):
        """
        :param joined_entity: The (aliased) ORMclass that is a descendant
        :param entity_to_join: The (aliased) ORMClass that is an ancestor.
        :param aliased_path: An aliased instance of DbPath

        **joined_entity** and **entity_to_join**
        are joined via the DbPath table.
        from **joined_entity** as child to **enitity_to_join** as parent
        (**enitity_to_join** is an *ancestor_of* **joined_entity**)
        """
        self._check_dbentities(
                (joined_entity, self.Node),
                (entity_to_join, self.Node),
                'ancestor_of'
            )
        #~ aliased_path = aliased(self.Path)
        self._query = self._query.join(
                aliased_path,
                aliased_path.child_id == joined_entity.id
        ).join(
                entity_to_join,
                aliased_path.parent_id == entity_to_join.id
        )
    def _join_group_members(self, joined_entity, entity_to_join):
        """
        :param joined_entity:
            The (aliased) ORMclass that is
            a group in the database
        :param entity_to_join:
            The (aliased) ORMClass that is a node and member of the group

        **joined_entity** and **entity_to_join**
        are joined via the table_groups_nodes table.
        from **joined_entity** as group to **enitity_to_join** as node.
        (**enitity_to_join** is an *member_of* **joined_entity**)
        """
        self._check_dbentities(
                (joined_entity, self.Group),
                (entity_to_join, self.Node),
                'member_of'
            )
        aliased_group_nodes = aliased(self.table_groups_nodes)
        self._query = self._query.join(
                aliased_group_nodes,
                aliased_group_nodes.c.dbgroup_id == joined_entity.id
        ).join(
                entity_to_join,
                entity_to_join.id == aliased_group_nodes.c.dbnode_id
        )
    def _join_groups(self, joined_entity, entity_to_join):
        """
        :param joined_entity: The (aliased) node in the database
        :param entity_to_join: The (aliased) Group

        **joined_entity** and **entity_to_join** are
        joined via the table_groups_nodes table.
        from **joined_entity** as node to **enitity_to_join** as group.
        (**enitity_to_join** is an *group_of* **joined_entity**)
        """
        self._check_dbentities(
                (joined_entity, self.Node),
                (entity_to_join, self.Group),
                'group_of'
            )
        aliased_group_nodes = aliased(self.table_groups_nodes)
        self._query = self._query.join(
                aliased_group_nodes,
                aliased_group_nodes.c.dbnode_id == joined_entity.id
        ).join(
                entity_to_join,
                entity_to_join.id == aliased_group_nodes.c.dbgroup_id
        )
    def _join_creator_of(self, joined_entity, entity_to_join):
        """
        :param joined_entity: the aliased node
        :param entity_to_join: the aliased user to join to that node
        """
        self._check_dbentities(
                (joined_entity, self.Node),
                (entity_to_join, self.User),
                'creator_of'
            )
        self._query = self._query.join(
                entity_to_join,
                entity_to_join.id == joined_entity.user_id
            )
    def _join_created_by(self, joined_entity, entity_to_join):
        """
        :param joined_entity: the aliased user you want to join to
        :param entity_to_join: the (aliased) node or group in the DB to join with
        """
        self._check_dbentities(
                (joined_entity, self.User),
                (entity_to_join, self.Node),
                'created_by'
            )
        self._query = self._query.join(
                entity_to_join,
                entity_to_join.user_id == joined_entity.id
            )

    def _join_to_computer_used(self, joined_entity, entity_to_join):
        """
        :param joined_entity: the (aliased) computer entity
        :param entity_to_join: the (aliased) node entity

        """
        self._check_dbentities(
                (joined_entity, self.Computer),
                (entity_to_join, self.Node),
                'has_computer'
            )
        self._query = self._query.join(
                entity_to_join,
                entity_to_join.dbcomputer_id == joined_entity.id
        )

    def _join_computer(self, joined_entity, entity_to_join):
        """
        :param joined_entity: An entity that can use a computer (eg a node)
        :param entity_to_join: aliased dbcomputer entity


        """
        self._check_dbentities(
                (joined_entity, self.Node),
                (entity_to_join, self.Computer),
                'computer_of'
            )
        self._query = self._query.join(
                entity_to_join,
                joined_entity.dbcomputer_id == entity_to_join.id
        )

    def _get_function_map(self):
        d = {
                'input_of'  : self._join_inputs,
                'output_of' : self._join_outputs,
                'slave_of'  : self._join_slaves, # not implemented
                'master_of' : self._join_masters,# not implemented
                'ancestor_of': self._join_ancestors,
                'descendant_of': self._join_descendants,
                'direction' : None,
                'group_of'  : self._join_groups,
                'member_of' : self._join_group_members,
                'has_computer':self._join_to_computer_used,
                'computer_of':self._join_computer,
                'created_by' : self._join_created_by,
                'creator_of' : self._join_creator_of,
        }
        return d
    def _get_connecting_node(
            self, index,
            joining_keyword=None, joining_value=None, **kwargs
        ):
        """
        :param querydict:
            A dictionary specifying how the current node
            is linked to other nodes.
        :param index: Index of this node within the path specification

        Valid (currently implemented) keys are:

        *   *input_of*
        *   *output_of*
        *   *descendant_of*
        *   *ancestor_of*
        *   *direction*
        *   *group_of*
        *   *member_of*
        *   *has_computer*
        *   *computer_of*
        *   *created_by*
        *   *creator_of*

        Future:

        *   *master_of*
        *   *slave_of*
        """

        if joining_keyword == 'direction':
            if joining_value > 0:
                returnval = self._aliased_path[index-joining_value], self._join_outputs
            elif joining_value < 0:
                returnval = self._aliased_path[index+joining_value], self._join_inputs
            else:
                raise Exception("Direction 0 is not valid")
        else:
            func = self._get_function_map()[joining_keyword]

            if isinstance(joining_value, int):
                returnval = (self._aliased_path[joining_value], func)
            elif isinstance(joining_value, str):
                try:
                    returnval = self._tag_to_alias_map[
                            self._get_tag_from_specification(joining_value)
                        ], func
                except KeyError:
                    raise InputValidationError(
                        'Key {} is unknown to the types I know about:\n'
                        '{}'.format(val, self._tag_to_alias_map.keys())
                    )
        return returnval

    def _get_json_compatible(self, inp):
        """

        :param inp:
            The input value that will be converted.
            Recurses into each value if **inp** is an iterable.
        """
        print inp
        if isinstance(inp, dict):
            for key, val in inp.items():
                inp[
                        self._get_json_compatible(key)
                ] = self._get_json_compatible(inp.pop(key))
        elif isinstance(inp, (list, tuple)):
            inp = [self._get_json_compatible(val) for val in inp]
        elif inspect_isclass(inp):
            if issubclass(inp, self.AiidaNode):
                return '.'.join(
                        inp._plugin_type_string.strip('.').split('.')[:-1]
                    )
            elif issubclass(inp, self.AiidaGroup):
                return 'group'
            else:
                raise InputValidationError
        else:
            try:
                inp = replacement_dict.get(inp, inp)
            except Exception as e:
                raise Exception("""
                Exception thrown: {}\n
                while replacing {}""".format(e, inp))
        return inp


    def get_json_compatible_queryhelp(self):
        """
        Makes the queryhelp a json - compatible  dictionary.
        In this way,the queryhelp can be stored in a node
        in the database and retrieved or shared.

        :returns: the json-compatible queryhelp

        All classes defined in the input are
        converted to strings specifying the type,
        for example:
        """
        from copy import deepcopy

        return deepcopy({
            'path'      :   self._path,
            'filters'   :   self._filters,
            'project'   :   self._projections,
            'order_by'  :   self._order_by,
            'limit'     :   self._limit,
            'offset'    :   self._offset,
        })

        #~ self._get_json_compatible()

    @staticmethod
    def _get_column(colname, alias):
        """
        Return the column for the projection, if the column name is specified.
        """

        if colname not in alias._sa_class_manager.mapper.c.keys():
            raise InputValidationError(
                "\n{} is not a column of {}\n".format(colname, alias)
            )
        return getattr(alias, colname)

    def _build_order(self, alias, entitytag, entityspec):

        column_name = entitytag.split('.')[0]
        attrpath = entitytag.split('.')[1:]
        if attrpath and 'cast' not in entityspec.keys():
            raise InputValidationError(
                "\n\n"
                "In order to project ({}), I have to cast the the values,\n"
                "but you have not specified the datatype to cast to\n"
                "You can do this with keyword 'cast'\n"
                "".format(entitytag)
            )


        entity = self._get_projectable_entity(alias, column_name, attrpath, **entityspec)
        order = entityspec.get('order', 'asc')
        if order == 'desc':
            entity = entity.desc()
        self._query = self._query.order_by(entity)


    def _build(self):
        """
        build the query and return a sqlalchemy.Query instance
        """

        # self.tags_location_dict is a dictionary that
        # maps the tag to its index in the list
        # this is basically the mapping between the count
        # of nodes traversed
        # and the tag used for that node
        self.tags_location_dict = {
                path['tag']:index
                for index, path
                in enumerate(self._path)
            }

        #Starting the query by receiving a session
        # Every subclass needs to have _get_session and give me the
        # right session
        firstalias = self._tag_to_alias_map[self._path[0]['tag']]
        self._query = self._get_session().query(firstalias)

        ######################### JOINS ################################

        for index, verticespec in  enumerate(self._path[1:], start=1):
            alias = self._tag_to_alias_map[verticespec['tag']]
            #looping through the queryhelp
            #~ if index:
                #There is nothing to join if that is the first table
            toconnectwith, connection_func = self._get_connecting_node(
                    index, **verticespec
                )
            edge_tag = verticespec.get('edge_tag', None)
            if edge_tag is None:
                connection_func(toconnectwith, alias)
            else:
                aliased_edge = self._tag_to_alias_map[edge_tag]
                connection_func(toconnectwith, alias, aliased_edge)

        ######################### FILTERS ##############################

        for tag, filter_specs in self._filters.items():
            try:
                alias = self._tag_to_alias_map[tag]
            except KeyError:
                # TODO Check KeyError before?
                raise InputValidationError(
                    ' You looked for tag {} among the alias list\n'
                    'The tags I know are:\n{}'
                    ''.format(tag, self._tag_to_alias_map.keys())
                )
            self._query = self._query.filter(
                    self._build_filters(alias, filter_specs)
                )

        ######################### PROJECTIONS ##########################
        # first clear the entities in the case the first item in the
        # path was not meant to be projected
        # attribute of Query instance storing entities to project:

        # Will be later set to this list:
        entities = []
        # Mapping between enitites and the tag used/ given by user:
        self.tag_to_projected_entity_dict = {}


        self.nr_of_projections = 0

        if not any(self._projections.values()):
            # If user has not set projection,
            # I will simply project the last item specified!
            # Don't change, path traversal querying
            # relies on this behavior!
            self._build_projections(self._path[-1]['tag'], items_to_project=[{'*':{}}])
        else:
            for vertice in self._path:
                self._build_projections(vertice['tag'])


        ##################### LINK-PROJECTIONS #########################

        for vertice in self._path:
            edge_tag = vertice.get('edge_tag', None)
            if edge_tag is not None:
                self._build_projections(edge_tag)

            #~ linktag = vertice.get('reverse_linktag', None)
            #~ if linktag is not None:
                #~ self._build_projections(linktag)

        ######################### ORDER ################################
        for order_spec in self._order_by:
            for tag, entities in order_spec.items():
                alias = self._tag_to_alias_map[tag]
                for entitydict in entities:
                    for entitytag, entityspec in entitydict.items():
                        self._build_order(alias, entitytag, entityspec)

        ######################### LIMIT ################################
        if self._limit is not None:
            self._query = self._query.limit(self._limit)

        ######################## OFFSET ################################
        if self._offset is not None:
            self._query = self._query.offset(self._offset)

        ################ LAST BUT NOT LEAST ############################
        #pop the entity that I added to start the query
        self._query._entities.pop(0)

        # Make a list that helps the projection postprocessing
        self._attrkeys_as_in_sql_result = {
            index_in_sql_result:attrkey
            for tag, projected_entities_dict
            in self.tag_to_projected_entity_dict.items()
            for attrkey, index_in_sql_result
            in projected_entities_dict.items()
        }

        if self.nr_of_projections > len(self._attrkeys_as_in_sql_result):
            raise InputValidationError(
                    "\nYou are projecting the same key\n"
                    "multiple times within the same node"
                )
        ######################### DONE #################################

        return self._query

    def except_if_input_to(self, calc_class):
        """
        Makes counterquery based on the own path, only selecting
        entries that have been input to *calc_class*

        :param calc_class: The calculation class to check against

        :returns: self
        """
        def build_counterquery(calc_class):
            if issubclass(calc_class, self.Node):
                orm_calc_class = calc_class
                type_spec = None
            elif issubclass(calc_class, self.AiidaNode):
                orm_calc_class = self.Node
                type_spec = calc_class._plugin_type_string
            else:
                raise Exception(
                    'You have given me {}\n'
                    'of type {}\n'
                    "and I don't know what to do with that"
                    ''.format(calc_class, type(calc_class))
                )

            input_alias_list = []
            for node in self._path:
                tag = node['tag']
                requested_cols = [
                        key

                        for item in self._projections[tag]
                        for key in item.keys()
                    ]
                if '*' in requested_cols:
                    input_alias_list.append(aliased(self._tag_to_alias_map[tag]))


            counterquery = self._get_session().query(orm_calc_class)
            if type_spec:
                counterquery = counterquery.filter(orm_calc_class.type == type_spec)
            for alias in input_alias_list:

                link = aliased(self.Link)
                counterquery = counterquery.join(
                    link,
                    orm_calc_class.id == link.output_id
                ).join(
                    alias,
                    alias.id == link.input_id)
                counterquery = counterquery.add_entity(alias)
            counterquery._entities.pop(0)
            return counterquery
        self._query = self.get_query()
        self._query = self._query.except_(build_counterquery(calc_class))
        return self


    def get_aliases(self):
        """
        :returns: the list of aliases
        """
        return self._aliased_path

    def get_alias(self, tag):
        """
        In order to continue a query by the user, this utility function
        returns the aliased ormclasses.

        :param tag: The tag for a vertice in the path
        :returns: the alias given for that vertice
        """
        tag = self._get_tag_from_specification(tag)
        return self._tag_to_alias_map[tag]



    def get_query(self):
        """

        Checks if the query instance is still valid by hashing the queryhelp.
        If not invokes :func:`QueryBuilderBase._build`.

        :returns: an instance of sqlalchemy.orm.Query

        """
        # Need_to_build is True by default.
        # It describes whether the current query
        # which is an attribute _query of this instance is still valid
        # The queryhelp_hash is used to determine
        # whether the query is still valid

        queryhelp_hash = make_hash(self.get_json_compatible_queryhelp())
        # if self._hash (which is None if this function has not been invoked
        # and is a string (hash) if it has) is the same as the queryhelp
        # I can use the query again:
        # If the query was injected I never build:
        if self._injected:
            need_to_build = False
        elif self._hash == queryhelp_hash:
            need_to_build = False
        else:
            need_to_build = True

        if need_to_build:
            query = self._build()
            self._hash = queryhelp_hash
        else:
            try:
                query = self._query
            except AttributeError:
                warnings.warn(
                    "AttributeError thrown even though I should\n"
                    "have _query as an attribute"
                )
                query = self._build()
                self._hash = queryhelp_hash
        return query


    def inject_query(self, query):
        """
        Manipulate the query an inject it back.
        This can be done to add custom filters using SQLA.
        :param query: A sqlalchemy.orm.Query instance
        """
        from sqlalchemy.orm import Query
        if not isinstance(query, Query):
            raise InputValidationError(
                "{} must be a subclass of {}".format(
                    query, Query
                )
            )
        self._query = query
        self._injected = True

    def distinct(self):
        """
        Asks for distinct rows.
        Does not execute the query!
        If you want a distinct query::

            qb = QueryBuilder(**queryhelp)
            qb.distinct().all() # or
            qb.distinct().get_results_dict()

        :returns: self
        """
        self._query = self.get_query().distinct()
        return self


    def _yield_per(self, batch_size):
        """
        :param count: Number of rows to yield per step

        Yields *count* rows at a time

        :returns: a generator
        """
        return self.get_query().yield_per(batch_size)

    def _all(self):
        return self.get_query().all()

    def _first(self):
        """
        Executes query in the backend asking for one instance.

        :returns: One row of aiida results
        """
        return self.get_query().first()

    def first(self):
        """
        Executes query asking for one instance.
        Use as follows::

            qb = QueryBuilder(**queryhelp)
            qb.first()

        :returns:
            One row of results as a list, order as given by
            order of vertices in  path and projections for vertice
        """
        resultrow = self._first()
        try:
            returnval = [
                    self._get_aiida_res(self._attrkeys_as_in_sql_result[colindex], rowitem)
                    for colindex, rowitem
                    in enumerate(resultrow)
                ]
        except TypeError:
            if resultrow is None:
                returnval = None
            elif len(self._attrkeys_as_in_sql_result) > 1:
                raise Exception(
                    "I have not received an iterable\n"
                    "but the number of projections is > 1"
                )
            # It still returns a list!
            else:
                returnval = [self._get_aiida_res(self._attrkeys_as_in_sql_result[0], resultrow)]
        return returnval



    def count(self):
        """
        Counts the number of rows returned by the backend.

        :returns: the number of rows as an integer
        """
        que = self.get_query()
        return que.count()

    def iterall(self, batch_size=100):
        """
        Same as :func:`QueryBuilderBase.all`, but returns a generator.
        Be aware that this is only safe if no commit will take place during this
        transaction. You might also want to read the SQLAlchemy documentation on
        http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.yield_per


        :param int batch_size: 
            The size of the batches to ask the backend to batch results in subcollections.
            You can optimize the speed of the query by tuning this parameter.

        :returns: a generator of lists
        """

        if batch_size is not None:
            results = self._yield_per(batch_size)
        else:
            results = self._all()
        try:
            for resultrow in results:
                yield [
                    self._get_aiida_res(self._attrkeys_as_in_sql_result[colindex], rowitem)
                    for colindex, rowitem
                    in enumerate(resultrow)
                ]
        except TypeError:
            # resultrow not an iterable:
            # Checked, result that raises exception is included
            if len(self._attrkeys_as_in_sql_result) > 1:
                raise Exception(
                    "I have not received an iterable\n"
                    "but the number of projections is > 1"
                )
            for rowitem in results:
                yield [self._get_aiida_res(self._attrkeys_as_in_sql_result[0], rowitem)]

    def all(self, batch_size=None):
        """
        Executes the full query with the order of the rows as returned by the backend.
        the order inside each row is given by the order of the vertices in the path
        and the order of the projections for each vertice in the path.

        :param int batch_size: 
            The size of the batches to ask the backend to batch results in subcollections.
            You can optimize the speed of the query by tuning this parameter.
            Leave the default (*None*) if speed is not critical or if you don't know
            what you're doing!

        :returns: a list of lists of all projected entities.
        """

        return list(self.iterall(batch_size=batch_size))


    def dict(self, batch_size=None):
        """
        Executes the full query with the order of the rows as returned by the backend.
        the order inside each row is given by the order of the vertices in the path
        and the order of the projections for each vertice in the path.

        :param int batch_size: 
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
                descendant_of='structure',
                project=['type', 'id'],  # returns type (string) and id (string)
                tag='descendant'
            )
            
            # Return the dictionaries:
            print "qb.iterdict()"
            for d in qb.iterdict():
                print '>>>', d

        results in the following output::

            qb.iterdict()
            >>> {'descendant': {
                    'type': u'calculation.job.quantumespresso.pw.PwCalculation.',
                    'id': 7716}
                }
            >>> {'descendant': {
                    'type': u'data.remote.RemoteData.',
                    'id': 8510}
                }

        """
        return list(self.iterdict(batch_size=batch_size))


    def iterdict(self, batch_size=100):
        """
        Same as :func:`QueryBuilderBase.dict`, but returns a generator.
        Be aware that this is only safe if no commit will take place during this
        transaction. You might also want to read the SQLAlchemy documentation on
        http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.yield_per


        :param int batch_size: 
            The size of the batches to ask the backend to batch results in subcollections.
            You can optimize the speed of the query by tuning this parameter.

        :returns: a generator of dictionaries
        """

        if batch_size is not None:
            results = self._yield_per(batch_size=batch_size)
        else:
            results = self._all()
        try:
            for this_result in results:
                yield {
                    tag:{
                        attrkey:self._get_aiida_res(
                                attrkey, this_result[index_in_sql_result]
                            )
                        for attrkey, index_in_sql_result
                        in projected_entities_dict.items()
                    }
                    for tag, projected_entities_dict
                    in self.tag_to_projected_entity_dict.items()
                }
        except TypeError:
            # resultrow not an iterable:
            # Checked, result that raises exception is included
            if len(self._attrkeys_as_in_sql_result) > 1:
                raise Exception(
                    "I have not received an iterable\n"
                    "but the number of projections is > 1"
                )

            for this_result in results:
                yield {
                    tag:{
                        attrkey : self._get_aiida_res(attrkey, this_result)
                        for attrkey, position in projected_entities_dict.items()
                    }
                    for tag, projected_entities_dict in self.tag_to_projected_entity_dict.items()
                }

    def get_results_dict(self):
        """
        Deprecated, use :func:`QueryBuilderBase.dict` or
        :func:`QueryBuilderBase.iterdict` instead
        """
        warnings.warn(
                "get_results_dict will be deprecated in the future"
                "User iterdict for generator or dict for list",
                DeprecationWarning
            )
        
        return self.iterdict()

    @abstractmethod
    def _get_aiida_res(self, key, res):
        """
        Some instance returned by ORM (django or SA) need to be converted
        to Aiida instances (eg nodes)

        :param key: the key that this entry would be returned with
        :param res: the result returned by the query

        :returns: an aiida-compatible instance
        """
        pass

    def inputs(self, **kwargs):
        """
        Join to inputs of previous vertice in path.

        :returns: self
        """
        join_to = self._path[-1]['tag']
        cls = kwargs.pop('cls', self.AiidaNode)
        self.append(cls=cls, input_of=join_to, autotag=True, **kwargs)
        return self

    def outputs(self, **kwargs):
        """
        Join to outputs of previous vertice in path.

        :returns: self
        """
        join_to = self._path[-1]['tag']
        cls = kwargs.pop('cls', self.AiidaNode)
        self.append(cls=cls, output_of=join_to, autotag=True, **kwargs)
        return self

    def children(self, **kwargs):
        """
        Join to children/descendants of previous vertice in path.

        :returns: self
        """
        join_to = self._path[-1]['tag']
        cls = kwargs.pop('cls', self.AiidaNode)
        self.append(cls=cls, descendant_of=join_to, autotag=True, **kwargs)
        return self

    def parents(self, **kwargs):
        """
        Join to parents/ancestors of previous vertice in path.

        :returns: self
        """
        join_to = self._path[-1]['tag']
        cls = kwargs.pop('cls', self.AiidaNode)
        self.append(cls=cls, ancestor_of=join_to, autotag=True, **kwargs)
        return self


