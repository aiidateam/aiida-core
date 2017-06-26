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
The QueryBuilder: A class that allows you to query the AiiDA database, independent from backend.
Note that the backend implementation is enforced and handled with a composition model!
:func:`QueryBuilder` is the frontend class that the user can use. It inherits from *object* and contains
backend-specific functionality. Backend specific functionality is provided by the implementation classes.

These inherit from :func:`aiida.backends.general.querybuilder_interface.QueryBuilderInterface`,
an interface classes which enforces the implementation of its defined methods.
An instance of one of the implementation classes becomes a member of the :func:`QueryBuilder` instance
when instantiated by the user.
"""

# Warnings are issued for deprecations:
import warnings
# Checking for correct input with the inspect module
from inspect import isclass as inspect_isclass
from aiida.orm.node import Node

# The SQLAlchemy functionalities:
from sqlalchemy import and_, or_, not_, func as sa_func, select, join
from sqlalchemy.types import Integer
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import cast

## AIIDA modules:
# For exception handling
from aiida.common.exceptions import InputValidationError, ConfigurationError
# The way I get column as a an attribute to the orm class
from aiida.backends.utils import _get_column



class QueryBuilder(object):
    """
    QueryBuilder: The class to query the AiiDA database. Usage::

        from aiida.orm.querybuilder import QueryBuilder
        qb = QueryBuilder()
        # Querying nodes:
        qb.append(Node)
        # retrieving the results:
        results = qb.all()
    """

    # This tag defines how edges are tagged (labeled) by the QueryBuilder default
    # namely tag of first entity + _EDGE_TAG_DELIM + tag of second entity
    _EDGE_TAG_DELIM = '--'
    _VALID_PROJECTION_KEYS = ('func', 'cast')


    def __init__(self, *args, **kwargs):
        """
        Instantiates a QueryBuilder instance.

        Which backend is used decided here based on backend-settings (taken from the user profile).
        This cannot be overriden so far by the user.


        :param bool with_dbpath:
            Whether to use the DbPath table (if existing) to query ancestor-descendant relations.
            The default now is True. Set to False if you want to use the recursive functionality.
            This gives you the ability to project the path which constructed on the fly.
            It also allows to have the AiiDA instance without the DbPath, which can consume
            a lot of memory for heavy usage of AiiDA.
            Check :func:`QueryBuilder.set_with_dbpath` for details.
        :param bool expand_path:
            If set to True (default is False) allows to project the path when querying
            ancestor-descendant relationships. This can cause the query to be much slower,
            which is why it's optional.
            Check :func:`QueryBuilder.set_expand_path` for details
        :param bool debug:
            Turn on debug mode. This feature prints information on the screen about the stages
            of the QueryBuilder. Does not affect results.
        :param list path:
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
        :param int limit:
            Limit the number of rows to this number. Check :func:`QueryBuilder.limit`
            for more information.
        :param int offset:
            Set an offset for the results returned. Details in :func:`QueryBuilder.offset`.
        :param order_by:
            How to order the results. As the 2 above, can be set also at later stage,
            check :func:`QueryBuilder.order_by` for more information.

        """
        from aiida.backends.settings import BACKEND
        from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA

        # Deciding on the implementation:
        # For the future, one could decide on also having a user keyword.
        if BACKEND == BACKEND_SQLA:
            from aiida.backends.sqlalchemy.querybuilder_sqla import QueryBuilderImplSQLA
            self._impl = QueryBuilderImplSQLA()
        elif BACKEND == BACKEND_DJANGO:
            from aiida.backends.djsite.querybuilder_django.querybuilder_django import QueryBuilderImplDjango
            self._impl = QueryBuilderImplDjango()
        elif BACKEND is None:
            raise ConfigurationError("settings.BACKEND has not been set.\n"
                             "Hint: Have you called aiida.load_dbenv?")
        else:
            raise ConfigurationError("Unknown settings.BACKEND: {}".format(
                BACKEND))


        if args:
            raise InputValidationError(
                    "Arguments are not accepted\n"
                    "when instantiating a QueryBuilder instance"
                )

        # A list storing the path being traversed by the query
        self._path = []

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
        # everything with classes one needs a map, that also defines classes
        # as tags, to allow the following example:

        # qb = QueryBuilder()
        # qb.append(PwCalculation)
        # qb.append(StructureData, input_of=PwCalculation)

        # The cls_to_tag_map in this case would be:
        # {PwCalculation:'PwCalculation', StructureData:'StructureData'}
        # Keep in mind that it needs to be checked (and this is done) whether the class
        # is used twice. In that case, the user has to provide a tag!
        self._cls_to_tag_map = {}

        # Hashing the the internal queryhelp allows me to avoid to build a query again, if i have used
        # it already.
        # Example:

        ## User is building a query:
        # qb = QueryBuilder().append(.....)
        ## User asks for the first results:
        # qb.first()
        ## User asks for all results, of the same query:
        # qb.all()
        # In above example, I can reuse the query, and to track whether somethis was changed
        # I record a hash:
        self._hash = None
        ## The hash being None implies that the query will be build (Check the code in .get_query
        # The user can inject a query, this keyword stores whether this was done.
        # Check QueryBuilder.inject_query
        self._injected = False

        # Setting debug levels:
        self.set_debug(kwargs.pop('debug',False))

        # The internal _with_dbpath attributes reports whether I need to do something with the path.
        # I.e. check, loads, etc, implementation left to backend implementation.
        self.set_with_dbpath(kwargs.pop('with_dbpath', True))
        # Whether expanding the path when using recursive functionality
        self.set_expand_path(kwargs.pop('expand_path',False))


        # One can apply the path as a keyword. Allows for jsons to be given to the QueryBuilder.
        path = kwargs.pop('path', [])
        if not isinstance(path, (tuple, list)):
            raise InputValidationError(
                    "Path needs to be a tuple or a list"
                )
        # If the user specified a path, I use the append method to analyze, see QueryBuilder.append
        for path_spec in path:
            if isinstance(path_spec, dict):
                self.append(**path_spec)
            #~ except TypeError as e:
            elif isinstance(path_spec, basestring):
                # Maybe it is just a string,
                # I assume user means the type
                self.append(type=path_spec)
            else:
                # Or a class, let's try
                self.append(cls=path_spec)

        # Projections. The user provides a dictionary, but the specific checks is
        # left to QueryBuilder.add_project.
        projection_dict = kwargs.pop('project', {})
        if not isinstance(projection_dict, dict):
            raise InputValidationError("You need to provide the projections as dictionary")
        for key, val in projection_dict.items():
            self.add_projection(key, val)

        # For filters, I also expect a dictionary, and the checks are done lower.
        filter_dict = kwargs.pop('filters', {})
        if not isinstance(filter_dict, dict):
            raise InputValidationError("You need to provide the filters as dictionary")
        for key, val in filter_dict.items():
            self.add_filter(key, val)

        # The limit is caps the number of results returned, and can also be set with QueryBuilder.limit
        self.limit(kwargs.pop('limit', None))

        # The offset returns results after the offset
        self.offset(kwargs.pop('offset', None))

        # The user can also specify the order.
        self._order_by = {}
        order_spec = kwargs.pop('order_by', None)
        if order_spec:
            self.order_by(order_spec)

        # I've gone through all the keywords, popping each item
        # If kwargs is not empty, there is a problem:
        if kwargs:
            valid_keys = ('path', 'filters', 'project', 'limit', 'offset', 'order_by', 'with_dbpath')
            raise InputValidationError(
                    "Received additional keywords: {}"
                    "\nwhich I cannot process"
                    "\nValid keywords are: {}"
                    "".format(kwargs.keys(), valid_keys)
            )


    def __str__(self):
        """
        When somebody hits: print(QueryBuilder) or print(str(QueryBuilder))
        I want to print the SQL-query. Because it looks cool...
        """

        from aiida.common.setup import get_profile_config
        from aiida.backends import settings

        engine = get_profile_config(settings.AIIDADB_PROFILE)["AIIDADB_ENGINE"]

        if engine.startswith("mysql"):
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
        For testing purposes, I want to check whether the implementation gives the currect
        ormclass back. Just relaying to the implementation, details for this function
        in the interface.
        """
        return self._impl.get_ormclass(cls, ormclasstype)

    def _get_unique_tag(self, ormclasstype):
        """
        Using the function get_tag_from_type, I get a tag.
        I increment an index that is appended to that tag until I have an unused tag.
        This function is called in :func:`QueryBuilder.append` when autotag is set to True.

        :param str ormclasstype:
            The string that defines the type of the AiiDA ORM class.
            For subclasses of Node, this is the Node._plugin_type_string, for other they are
            as defined as returned by :func:`QueryBuilder._get_ormclass`.

        :returns: A tag, as a string.
        """
        def get_tag_from_type(ormclasstype):
            """
            Assign a tag to the given
            vertice of a path, based mainly on the type
            *   data.structure.StructureData -> StructureData
            *   data.structure.StructureData. -> StructureData
            *   calculation.job.quantumespresso.pw.PwCalculation. -. PwCalculation
            *   node.Node. -> Node
            *   Node -> Node
            *   computer -> computer
            *   etc.

            :param str ormclasstype:
                The string that defines the type of the AiiDA ORM class.
                For subclasses of Node, this is the Node._plugin_type_string, for other they are
                as defined as returned by :func:`QueryBuilder._get_ormclass`.
            :returns: A tag, as a string.
            """
            return ormclasstype.rstrip('.').split('.')[-1] or "node"

        basetag = get_tag_from_type(ormclasstype)
        tags_used = self._tag_to_alias_map.keys()
        for i in range(1, 100):
            tag = '{}_{}'.format(basetag, i)
            if tag not in tags_used:
                return tag
        raise Exception("Cannot find a tag after 100 tries")





    def append(self, cls=None, type=None, tag=None,
                filters=None, project=None, subclassing=True,
                edge_tag=None, edge_filters=None, edge_project=None,
                outerjoin=False, **kwargs
        ):
        """
        Any iterative procedure to build the path for a graph query
        needs to invoke this method to append to the path.

        :param cls: The Aiida-class (or backend-class) defining the appended vertice
        :param str type: The type of the class, if cls is not given
        :param bool autotag:
            Whether to find automatically a unique tag. If this is set to True (default False),

        :param str tag:
            A unique tag. If none is given, I will create a unique tag myself.
        :param filters:
            Filters to apply for this vertice.
            See :meth:`.add_filter`, the method invoked in the background, or usage examples for details.
        :param project:
            Projections to apply. See usage examples for details.
            More information also in :meth:`.add_projection`.
        :param bool subclassing:
            Whether to include subclasses of the given class
            (default **True**).
            E.g. Specifying a  Calculation as cls will include JobCalculations, InlineCalculations, etc..
        :param bool outerjoin:
            If True, (default is False), will do a left outerjoin
            instead of an inner join
        :param str edge_tag:
            The tag that the edge will get. If nothing is specified
            (and there is a meaningful edge) the default is tag1--tag2 with tag1 being the entity joining
            from and tag2 being the entity joining to (this entity).
        :param str edge_filters:
            The filters to apply on the edge. Also here, details in :meth:`.add_filter`.
        :param str edge_project:
            The project from the edges. API-details in :meth:`.add_projection`.

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

        if kwargs.pop('link_tag', None) is not None:
            raise DeprecationWarning("link_tag is deprecated, use edge_tag instead")
        if kwargs.pop('autotag', None) is not None:
            raise DeprecationWarning("autotag=True is now the default behavior, this keyword is deprecated")

        ormclass, ormclasstype, query_type_string = self._get_ormclass(cls, type)
        ############################### TAG #################################
        # Let's get a tag
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
            if tag in self._tag_to_alias_map.keys():
                raise InputValidationError(
                        "\n"
                        "This tag ({}) is already in use\n"
                        "\n".format(tag)
                    )
        else:
            tag = self._get_unique_tag(ormclasstype)

        # Checks complete
        # This is where I start doing changes to self!
        # Now, several things can go wrong along the way, so I need to split into
        # atomic blocks that I can reverse if something goes wrong.
        ################ TAG MAPPING #################################
        # TODO check with duplicate classes

        # Let's fill the cls_to_tag_map so that one can specify
        # this vertice in a joining specification later
        # First this only makes sense if a class was specified:

        l_class_added_to_map = False
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
                l_class_added_to_map = True


        ######################## ALIASING ##############################
        try:
            #~ alias =
            #~ self._aliased_path.append(alias)
            self._tag_to_alias_map[tag] = aliased(ormclass)
        except Exception as e:
            if self._debug:
                print "DEBUG: Exception caught in append1, cleaning up"
                print "  ", e
            if l_class_added_to_map:
                self._cls_to_tag_map.pop(cls)
            self._tag_to_alias_map.pop(tag, None)
            raise e



        ################# FILTERS ######################################

        try:
            self._filters[tag] = {}
            # I have to add a filter on column type.
            # This so far only is necessary for AiidaNodes
            # GROUPS?
            if query_type_string is not None:
                plugin_type_string = ormclasstype
                self._add_type_filter(tag, query_type_string, plugin_type_string, subclassing)
            # The order has to be first _add_type_filter and then add_filter.
            # If the user adds a query on the type column, it overwrites what I did

            #if the user specified a filter, add it:
            if filters is not None:
                self.add_filter(tag, filters)
        except Exception as e:
            if self._debug:
                print "DEBUG: Exception caught in append (part filters), cleaning up"
                print "  ", e
            if l_class_added_to_map:
                self._cls_to_tag_map.pop(cls)
            self._tag_to_alias_map.pop(tag)
            self._filters.pop(tag)
            raise e


        #################### PROJECTIONS ##############################

        try:
            self._projections[tag] = []
            if project is not None:
                self.add_projection(tag, project)
        except Exception as e:
            if self._debug:
                print "DEBUG: Exception caught in append (part projections), cleaning up"
                print "  ", e
            if l_class_added_to_map:
                self._cls_to_tag_map.pop(cls)
            self._tag_to_alias_map.pop(tag, None)
            self._filters.pop(tag)
            self._projections.pop(tag)
            raise e


        ################## JOINING #####################################


        try:
            # Get the functions that are implemented:
            spec_to_function_map = self._get_function_map().keys()
            joining_keyword = kwargs.pop('joining_keyword', None)
            joining_value = kwargs.pop('joining_value', None)

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


        except Exception as e:
            if self._debug:
                print "DEBUG: Exception caught in append (part joining), cleaning up"
                print "  ", e
            if l_class_added_to_map:
                self._cls_to_tag_map.pop(cls)
            self._tag_to_alias_map.pop(tag, None)
            self._filters.pop(tag)
            self._projections.pop(tag)
            # There's not more to clean up here!
            raise e


        ############################# EDGES #################################
        # See if this requires a link:

        # This variable lets me know if there is an edge (i.e. a many to many relationship)
        edge_exists = False
        if len(self._path) > 0:
            try:
                if joining_keyword in ('input_of', 'output_of'):
                    aliased_edge = aliased(self._impl.Link)
                    edge_exists = True
                elif joining_keyword in ('ancestor_of', 'descendant_of'):
                    edge_exists = True
                    if self._with_dbpath:
                        aliased_edge = aliased(self._impl.Path)
                    else:

                        # An aliased_edge is created on the fly if I'm not using
                        # the DbPath with a recursive query.
                        # I don't have a way (yet) to add filters here,
                        # since aliased_edge is None.
                        # Every filter on the path should be dealt inside the function
                        # ._join_ancestor... _join_descendant
                        aliased_edge = None



                if edge_exists:
                    # Ok, so here we are joining through a m2m relationship,
                    # e.g. input or output.
                    # This means that the user might want to query by that edge or project something
                    if self._debug:
                        print "DEBUG: Choosing an edge_tag"
                    if edge_tag is None:
                        edge_destination_tag = self._get_tag_from_specification(joining_value)
                        edge_tag = edge_destination_tag + self._EDGE_TAG_DELIM + tag
                    else:
                        if edge_tag in self._tag_to_alias_map.keys():
                            raise InputValidationError(
                                "The tag {} is already in use".format(edge_tag)
                            )
                    if self._debug:
                        print "   I have chosen", edge_tag

                    self._tag_to_alias_map[edge_tag] = aliased_edge

                    # Filters on links:
                    self._filters[edge_tag] = {}
                    if edge_filters is not None:
                        self.add_filter(edge_tag, edge_filters)

                    # Projections on links
                    self._projections[edge_tag] = {}
                    if edge_project is not None:
                        self.add_projection(edge_tag, edge_project)
            except Exception as e:
                if self._debug:
                    print "DEBUG: Exception caught in append (part joining), cleaning up"
                    print "  ", e
                if l_class_added_to_map:
                    self._cls_to_tag_map.pop(cls)
                self._tag_to_alias_map.pop(tag, None)
                self._filters.pop(tag)
                self._projections.pop(tag)
                if edge_exists:
                    self._tag_to_alias_map.pop(edge_tag)
                    self._filters.pop(edge_tag)
                    self._projections.pop(edge_tag)
                # There's not more to clean up here!
                raise e


            ################### EXTENDING THE PATH #################################


        path_extension = dict(
                type=ormclasstype, tag=tag, joining_keyword=joining_keyword,
                joining_value=joining_value, outerjoin=outerjoin,
            )
        if edge_exists:
            path_extension.update(dict(edge_tag=edge_tag))
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


        if not isinstance(filter_spec, dict):
            raise InputValidationError(
                    "Filters have to be passed as dictionaries"
                )

        tag = self._get_tag_from_specification(tagspec)
        self._filters[tag].update(filter_spec)

    def _add_type_filter(
            self, tagspec, query_type_string,
            plugin_type_string, subclassing):
        """
        Add a filter on the type based on the query_type_string
        """
        tag = self._get_tag_from_specification(tagspec)

        if subclassing:
            node_type_flt = {'like':'{}%'.format(query_type_string)}
        else:
            node_type_flt = {'==':plugin_type_string}

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

        The above example will project the uuid and the kinds-attribute of all matching structures.
        There are 2 (so far) special keys.

        The single star *\** will project the *ORM-instance*::

            qb = QueryBuilder()
            qb.append(StructureData, tag='struc')
            # Will project the ORM instance
            qb.add_projection('struc', '*')
            print type(qb.first()[0])
            # >>> aiida.orm.data.structure.StructureData

        The double start *\*\** projects all possible projections of this entity:

            QueryBuilder().append(StructureData,tag='s', project='**').limit(1).dict()[0]['s'].keys()

            # >>> u'user_id, description, ctime, label, extras, mtime, id, attributes, dbcomputer_id, nodeversion, type, public, uuid'

        Be aware that the result of *\*\** depends on the backend implementation.

        """
        tag = self._get_tag_from_specification(tag_spec)
        _projections = []
        if self._debug:
            print "DEBUG: Adding projection of", tag_spec
            print "   projection", projection_spec
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
        if self._debug:
            print "   projections have become:", _projections
        self._projections[tag] = _projections


    def _get_projectable_entity(self, alias, column_name, attrpath, **entityspec):

        if len(attrpath) or column_name in ('attributes', 'extras'):

            entity = self._impl.get_projectable_attribute(
                        alias, column_name, attrpath, **entityspec
                    )
        else:
            entity = _get_column(column_name, alias)
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

        if self._debug:
            print tag,items_to_project
        if not items_to_project:
            return

        alias = self._tag_to_alias_map[tag]

        self.tag_to_projected_entity_dict[tag] = {}

        for projectable_spec in items_to_project:
            for projectable_entity_name, extraspec in projectable_spec.items():
                if projectable_entity_name == '**':
                    # Need to expand
                    entity_names = self._impl.modify_expansions(alias, [
                            str(c).replace(alias.__table__.name+'.','')
                            for c
                            in alias.__table__.columns
                        ])
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

    def set_debug(self, debug):
        """
        Run in debug mode. This does not affect functionality, but prints intermediate stages
        when creating a query on screen.

        :param bool debug: Turn debug on or off
        """
        if not isinstance(debug, bool):
            return InputValidationError("I expect a boolean")
        self._debug = debug

        return self

    def set_with_dbpath(self, l_with_dbpath):
        """
        Sets whether I will use a DbPath table when querying ancestor-dependant relationships.
        If set to False (default behavior now is True) I will use recursive queries.
        You can check the source code of _join_ancestors_recursive and _join_descendants_recursive
        for details.
        This option allows to run AiiDA without a DbPath table, saving memory, especially for
        heavy usage. Of course, if left to True, there needs to be a table with the triggers set.
        Note that this feature behaves the same for the whole query.
        You cannot query on ancestor-descendant relationship using the DbPath and another using
        the recursive functionality within the same query.

        :param bool l_with_dbpath: True to use DbPath, False to use recursive queries.
        """

        if not isinstance(l_with_dbpath, bool):
            raise InputValidationError("I expect a boolean")
        self._with_dbpath = l_with_dbpath
        if self._with_dbpath:
            self._impl.prepare_with_dbpath()
        return self

    def set_expand_path(self, l_expand_path):
        """
        Turn this feature on if you want to project the path when querying ancestor-descenendant
        relationships.
        This implies the use of the recursive feature, that you *have to* turn on, as an exception
        will be raise otherwise (see :func:`QueryBuilder.set_with_dbpath`
        Note that you set the use of recursive feature by setting off the use of the path::

            from aiida.orm.querybuilder import QueryBuilder
            from aiida.orm.data.structure import StructureData
            qb = QueryBuilder()
            qb.set_with_dbpath(False) # Setting of the use of DbPath, and enabling recursive queries.
            qb.set_expand_path(True)  # enabling the projection on a path
            # Now I create a query that search for all descendant of  structure pk=23:
            qb.append(StructureData, tag='ancestor', filters={'id':23})
            qb.append(Calculation, tag='desc', edge_project='path', descendant_of='ancestor')
            # will return the paths:
            qb.all()


        ..note:
            There is no way project the path when using the DbPath table,
            since it is not stored explicitly.
        """
        if not isinstance(l_expand_path, bool):
            raise InputValidationError("I expect a boolean")

        self._expand_path = l_expand_path

        if self._expand_path and self._with_dbpath:
            raise NotImplementedError("It is not implemented to expand the path when using the DbPath table.\n"
                "Set with_dbpath to False to use that functionality")
        return self

    def limit(self, limit):
        """
        Set the limit (nr of rows to return)

        :param int limit: integers of number of rows of rows to return
        """

        if (limit is not None) and (not isinstance(limit, int)):
            raise InputValidationError("The limit has to be an integer, or None")
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
        if (offset is not None) and (not isinstance(offset, int)):
            raise InputValidationError("offset has to be an integer, or None")
        self._offset = offset
        return self


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
                    column = _get_column(column_name, alias)
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
                        self._impl.get_filter_expr(
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

    def _join_outputs(self, joined_entity, entity_to_join, aliased_edge, isouterjoin):
        """
        :param joined_entity: The (aliased) ORMclass that is an input
        :param entity_to_join: The (aliased) ORMClass that is an output.

        **joined_entity** and **entity_to_join** are joined with a link
        from **joined_entity** as input to **enitity_to_join** as output
        (**enitity_to_join** is an *output_of* **joined_entity**)
        """
        self._check_dbentities(
                (joined_entity, self._impl.Node),
                (entity_to_join, self._impl.Node),
                'output_of'
            )

        self._query = self._query.join(
                aliased_edge,
                aliased_edge.input_id == joined_entity.id,
                isouter=isouterjoin
        ).join(
                entity_to_join,

             aliased_edge.output_id == entity_to_join.id,
                isouter=isouterjoin
        )

    def _join_inputs(self, joined_entity, entity_to_join, aliased_edge,isouterjoin):
        """
        :param joined_entity: The (aliased) ORMclass that is an output
        :param entity_to_join: The (aliased) ORMClass that is an input.

        **joined_entity** and **entity_to_join** are joined with a link
        from **joined_entity** as output to **enitity_to_join** as input
        (**enitity_to_join** is an *input_of* **joined_entity**)
        """

        self._check_dbentities(
                (joined_entity, self._impl.Node),
                (entity_to_join, self._impl.Node),
                'input_of'
            )
        self._query = self._query.join(
                aliased_edge,
                aliased_edge.output_id == joined_entity.id,
            ).join(
                entity_to_join,
                aliased_edge.input_id == entity_to_join.id,
                isouter=isouterjoin
        )

    def _join_descendants_recursive(self, joined_entity, entity_to_join, isouterjoin, filter_dict, edge_tag):
        """
        joining descendants using the recursive functionality
        :TODO: Move the filters to be done inside the recursive query (for example on depth)
        :TODO: Pass an option to also show the path, if this is wanted.
        """

        self._check_dbentities(
                (joined_entity, self._impl.Node),
                (entity_to_join, self._impl.Node),
                'descendant_of_beta'
            )

        link1 = aliased(self._impl.Link)
        link2 = aliased(self._impl.Link)
        node1 = aliased(self._impl.Node)
        in_recursive_filters = self._build_filters(node1, filter_dict)

        walk = select([
                link1.input_id.label('ancestor_id'),
                link1.output_id.label('descendant_id'),
                cast(0, Integer).label('depth'),
                # Un-commenting the next line will allow to store the path as
                # an array:
                #~ array([DbNode.id]).label('path')   #Arrays can only be used with postgres
            ]).select_from(
                join(
                    node1, link1, link1.input_id==node1.id
                )
            ).where(in_recursive_filters).cte(recursive=True)

        aliased_walk = aliased(walk)


        descendants_beta = aliased(aliased_walk.union_all(
            select([
                    aliased_walk.c.ancestor_id.label('ancestor_id'),
                    link2.output_id.label('descendant_id'),
                    (aliased_walk.c.depth + cast(1, Integer)).label('current_depth'),
                    #~ (walk.c.path+array([node_aliased.id])).label('path')
                    #, As above, but if arrays are supported
                    # This is the way to reconstruct the path (the sequence of nodes traversed)
                ]).select_from(
                    join(
                        aliased_walk,
                        link2,
                        link2.input_id == aliased_walk.c.descendant_id,
                    )
                )
            )) #.alias()

        self._tag_to_alias_map[edge_tag] = descendants_beta.c

        self._query = self._query.join(
                descendants_beta,
                descendants_beta.c.ancestor_id == joined_entity.id
            ).join(
                entity_to_join,
                descendants_beta.c.descendant_id == entity_to_join.id,
                isouter=isouterjoin
            )
    def _join_descendants_recursive_project_path(self, joined_entity, entity_to_join, isouterjoin, filter_dict, edge_tag):
        """
        joining descendants using the recursive functionality, and project the dbpath.
        Use with care, since this slows the query down substantially.
        :TODO: Move the filters to be done inside the recursive query (for example on depth)
        :TODO: Pass an option to also show the path, if this is wanted.
        """
        from sqlalchemy.dialects.postgresql import array

        self._check_dbentities(
                (joined_entity, self._impl.Node),
                (entity_to_join, self._impl.Node),
                'descendant_of_beta'
            )

        link1 = aliased(self._impl.Link)
        link2 = aliased(self._impl.Link)
        node1 = aliased(self._impl.Node)
        in_recursive_filters = self._build_filters(node1, filter_dict)

        walk = select([
                link1.input_id.label('ancestor_id'),
                link1.output_id.label('descendant_id'),
                cast(0, Integer).label('depth'),
                array([link1.input_id, link1.output_id]).label('path')   #Arrays can only be used with postgres
            ]).select_from(
                join(
                    node1, link1, link1.input_id==node1.id
                )
            ).where(in_recursive_filters).cte(recursive=True)

        aliased_walk = aliased(walk)


        descendants_beta = aliased(aliased_walk.union_all(
            select([
                    aliased_walk.c.ancestor_id.label('ancestor_id'),
                    link2.output_id.label('descendant_id'),
                    (aliased_walk.c.depth + cast(1, Integer)).label('current_depth'),
                    (aliased_walk.c.path+array([link2.output_id])).label('path')
                    #, As above, but if arrays are supported
                    # This is the way to reconstruct the path (the sequence of nodes traversed)
                ]).select_from(
                    join(
                        aliased_walk,
                        link2,
                        link2.input_id == aliased_walk.c.descendant_id,
                    )
                )
            )) #.alias()

        self._tag_to_alias_map[edge_tag] = descendants_beta.c

        self._query = self._query.join(
                descendants_beta,
                descendants_beta.c.ancestor_id == joined_entity.id
            ).join(
                entity_to_join,
                descendants_beta.c.descendant_id == entity_to_join.id,
                isouter=isouterjoin
            )


    def _join_ancestors_recursive(self, joined_entity, entity_to_join, isouterjoin, filter_dict, edge_tag):
        """
        joining ancestors using the recursive functionality
        :TODO: Move the filters to be done inside the recursive query (for example on depth)
        :TODO: Pass an option to also show the path, if this is wanted.

        """
        self._check_dbentities(
                (joined_entity, self._impl.Node),
                (entity_to_join, self._impl.Node),
                'descendant_of_beta'
            )

        link1 = aliased(self._impl.Link)
        link2 = aliased(self._impl.Link)
        node1 = aliased(self._impl.Node)
        in_recursive_filters = self._build_filters(node1, filter_dict)

        walk = select([
                link1.input_id.label('ancestor_id'),
                link1.output_id.label('descendant_id'),
                cast(0, Integer).label('depth'),
                # Un-commenting the next line will allow to store the path as
                # an array:
                #~ array([DbNode.id]).label('path')   #Arrays can only be used with postgres
            ]).select_from(
                join(
                    node1, link1, link1.output_id==node1.id
                )
            ).where(in_recursive_filters).cte(recursive=True)

        aliased_walk = aliased(walk)


        ancestors_recursive = aliased(aliased_walk.union_all(
            select([
                    link2.input_id.label('ancestor_id'),
                    aliased_walk.c.descendant_id.label('descendant_id'),
                    (aliased_walk.c.depth + cast(1, Integer)).label('current_depth'),
                    #~ (walk.c.path+array([node_aliased.id])).label('path')
                    #, As above, but if arrays are supported
                    # This is the way to reconstruct the path (the sequence of nodes traversed)
                ]).select_from(
                    join(
                        aliased_walk,
                        link2,
                        link2.output_id == aliased_walk.c.ancestor_id,
                    )
                )
            ))

        self._tag_to_alias_map[edge_tag] = ancestors_recursive.c

        self._query = self._query.join(
                ancestors_recursive,
                ancestors_recursive.c.descendant_id == joined_entity.id
            ).join(
                entity_to_join,
                ancestors_recursive.c.ancestor_id == entity_to_join.id,
                isouter=isouterjoin
            )


    def _join_ancestors_recursive_projecting_path(self, joined_entity, entity_to_join, isouterjoin, filter_dict, edge_tag):
        """
        joining ancestors using the recursive functionality, this will also show the path that is being traversed.
        Use with caution, this is very slow!
        :TODO: Move the filters to be done inside the recursive query (for example on depth)
        """
        from sqlalchemy.dialects.postgresql import array


        self._check_dbentities(
                (joined_entity, self._impl.Node),
                (entity_to_join, self._impl.Node),
                'descendant_of_beta'
            )

        link1 = aliased(self._impl.Link)
        link2 = aliased(self._impl.Link)
        node1 = aliased(self._impl.Node)
        in_recursive_filters = self._build_filters(node1, filter_dict)

        walk = select([
                link1.input_id.label('ancestor_id'),
                link1.output_id.label('descendant_id'),
                cast(0, Integer).label('depth'),
                array([link1.output_id, link1.input_id]).label('path')   #Arrays can only be used with postgres
            ]).select_from(
                join(
                    node1, link1, link1.output_id==node1.id
                )
            ).where(in_recursive_filters).cte(recursive=True)

        aliased_walk = aliased(walk)


        ancestors_recursive = aliased(aliased_walk.union_all(
            select([
                    link2.input_id.label('ancestor_id'),
                    aliased_walk.c.descendant_id.label('descendant_id'),
                    (aliased_walk.c.depth + cast(1, Integer)).label('current_depth'),
                    (aliased_walk.c.path+array([link2.input_id])).label('path')
                ]).select_from(
                    join(
                        aliased_walk,
                        link2,
                        link2.output_id == aliased_walk.c.ancestor_id,
                    )
                )
            ))

        self._tag_to_alias_map[edge_tag] = ancestors_recursive.c

        self._query = self._query.join(
                ancestors_recursive,
                ancestors_recursive.c.descendant_id == joined_entity.id
            ).join(
                entity_to_join,
                ancestors_recursive.c.ancestor_id == entity_to_join.id,
                isouter=isouterjoin
            )

    def _join_descendants_u_dbpath(self, joined_entity, entity_to_join, aliased_path, isouterjoin):
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
                (joined_entity, self._impl.Node),
                (entity_to_join, self._impl.Node),
                'descendant_of'
            )

        self._query = self._query.join(
                aliased_path,
                aliased_path.parent_id == joined_entity.id
            ).join(
                entity_to_join,
                aliased_path.child_id == entity_to_join.id,
                isouter=isouterjoin
        )

    def _join_ancestors_u_dbpath(self, joined_entity, entity_to_join, aliased_path, isouterjoin):
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
                (joined_entity, self._impl.Node),
                (entity_to_join, self._impl.Node),
                'ancestor_of'
            )
        #~ aliased_path = aliased(self.Path)
        self._query = self._query.join(
                aliased_path,
                aliased_path.child_id == joined_entity.id
            ).join(
                entity_to_join,
                aliased_path.parent_id == entity_to_join.id,
                isouter=isouterjoin
        )

    def _join_group_members(self, joined_entity, entity_to_join, isouterjoin):
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
                (joined_entity, self._impl.Group),
                (entity_to_join, self._impl.Node),
                'member_of'
            )
        aliased_group_nodes = aliased(self._impl.table_groups_nodes)
        self._query = self._query.join(
                aliased_group_nodes,
                aliased_group_nodes.c.dbgroup_id == joined_entity.id
            ).join(
                entity_to_join,
                entity_to_join.id == aliased_group_nodes.c.dbnode_id,
                isouter=isouterjoin
        )

    def _join_groups(self, joined_entity, entity_to_join, isouterjoin):
        """
        :param joined_entity: The (aliased) node in the database
        :param entity_to_join: The (aliased) Group

        **joined_entity** and **entity_to_join** are
        joined via the table_groups_nodes table.
        from **joined_entity** as node to **enitity_to_join** as group.
        (**enitity_to_join** is an *group_of* **joined_entity**)
        """
        self._check_dbentities(
                (joined_entity, self._impl.Node),
                (entity_to_join, self._impl.Group),
                'group_of'
            )
        aliased_group_nodes = aliased(self._impl.table_groups_nodes)
        self._query = self._query.join(
                aliased_group_nodes,
                aliased_group_nodes.c.dbnode_id == joined_entity.id
            ).join(
                entity_to_join,
                entity_to_join.id == aliased_group_nodes.c.dbgroup_id,
                isouter=isouterjoin
        )

    def _join_creator_of(self, joined_entity, entity_to_join, isouterjoin):
        """
        :param joined_entity: the aliased node
        :param entity_to_join: the aliased user to join to that node
        """
        self._check_dbentities(
                (joined_entity, self._impl.Node),
                (entity_to_join, self._impl.User),
                'creator_of'
            )
        self._query = self._query.join(
                entity_to_join,
                entity_to_join.id == joined_entity.user_id,
                isouter=isouterjoin
            )
    def _join_created_by(self, joined_entity, entity_to_join, isouterjoin):
        """
        :param joined_entity: the aliased user you want to join to
        :param entity_to_join: the (aliased) node or group in the DB to join with
        """
        self._check_dbentities(
                (joined_entity, self._impl.User),
                (entity_to_join, self._impl.Node),
                'created_by'
            )
        self._query = self._query.join(
                entity_to_join,
                entity_to_join.user_id == joined_entity.id,
                isouter=isouterjoin
            )

    def _join_to_computer_used(self, joined_entity, entity_to_join, isouterjoin):
        """
        :param joined_entity: the (aliased) computer entity
        :param entity_to_join: the (aliased) node entity

        """
        self._check_dbentities(
                (joined_entity, self._impl.Computer),
                (entity_to_join, self._impl.Node),
                'has_computer'
            )
        self._query = self._query.join(
                entity_to_join,
                entity_to_join.dbcomputer_id == joined_entity.id,
                isouter=isouterjoin
        )

    def _join_computer(self, joined_entity, entity_to_join, isouterjoin):
        """
        :param joined_entity: An entity that can use a computer (eg a node)
        :param entity_to_join: aliased dbcomputer entity


        """
        self._check_dbentities(
                (joined_entity, self._impl.Node),
                (entity_to_join, self._impl.Computer),
                'computer_of'
            )
        self._query = self._query.join(
                entity_to_join,
                joined_entity.dbcomputer_id == entity_to_join.id,
                isouter=isouterjoin
        )

    def _get_function_map(self):
        d = {
                'input_of'  : self._join_inputs,
                'output_of' : self._join_outputs,
                'slave_of'  : self._join_slaves, # not implemented
                'master_of' : self._join_masters,# not implemented
                'direction' : None,
                'group_of'  : self._join_groups,
                'member_of' : self._join_group_members,
                'has_computer':self._join_to_computer_used,
                'computer_of':self._join_computer,
                'created_by' : self._join_created_by,
                'creator_of' : self._join_creator_of,
        }
        if self._with_dbpath:
            d['ancestor_of'] = self._join_ancestors_u_dbpath
            d['descendant_of'] = self._join_descendants_u_dbpath
        else:
            if self._expand_path:
                d['ancestor_of'] = self._join_ancestors_recursive_projecting_path
                d['descendant_of'] = self._join_descendants_recursive_project_path
            else:
                d['ancestor_of'] = self._join_ancestors_recursive
                d['descendant_of'] = self._join_descendants_recursive
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
        In this way,the queryhelp can be stored
        in the database or a json-object, retrieved or shared and used later.
        See this usage::

            qb = QueryBuilder(limit=3).append(StructureData, project='id').order_by({StructureData:'id'})
            queryhelp  = qb.get_json_compatible_queryhelp()

            # Now I could save this dictionary somewhere and use it later:

            qb2=QueryBuilder(**queryhelp)

            # This is True if no change has been made to the database.
            # Note that such a comparison can only be True if the order of results is enforced
            qb.all()==qb2.all()

        :returns: the json-compatible queryhelp
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


        #~ return

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
        self._query = self._impl.get_session().query(firstalias)

        ######################### JOINS ################################
        #~ print self._query
        #~ print '\n\n\n'
        #~ raw_input()

        for index, verticespec in  enumerate(self._path[1:], start=1):
            alias = self._tag_to_alias_map[verticespec['tag']]
            #looping through the queryhelp
            #~ if index:
                #There is nothing to join if that is the first table
            toconnectwith, connection_func = self._get_connecting_node(
                    index, **verticespec
                )
            edge_tag = verticespec.get('edge_tag', None)
            isouterjoin = verticespec.get('outerjoin')

            if ( verticespec['joining_keyword'] in ('descendant_of', 'ancestor_of')) and not(self._with_dbpath):
                filter_dict = self._filters.get(verticespec['joining_value'], {})
                connection_func(toconnectwith, alias, isouterjoin=isouterjoin, filter_dict=filter_dict, edge_tag=edge_tag)
            elif edge_tag is None:
                connection_func(toconnectwith, alias, isouterjoin=isouterjoin)
            else:
                aliased_edge = self._tag_to_alias_map[edge_tag]
                connection_func(toconnectwith, alias, aliased_edge, isouterjoin=isouterjoin)
            #~ print self._query
            #~ print '\n\n\n'
            #~ raw_input()
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
        if self._debug:
            print "DEBUG:"
            print "   Printing the content of self._projections"
            print "  ", self._projections
            print

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

            for vertice in self._path[1:]:
                edge_tag = vertice.get('edge_tag', None)
                if self._debug:
                    print "DEBUG: Checking projections for edges:"
                    print "   This is edge", edge_tag, "from",vertice.get('tag'), ",",vertice.get('joining_keyword'), 'of', vertice.get('joining_value')
                if edge_tag is not None:
                    self._build_projections(edge_tag)

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


            counterquery = self._imp._get_session().query(orm_calc_class)
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


    def get_used_tags(self, vertices=True, edges=True):
        """
        Returns a list of all the vertices that are being used.
        Some parameter allow to select only subsets.
        :param bool vertices: Defaults to True. If True, adds the tags of vertices to the returned list
        :param bool edges: Defaults to True. If True,  adds the tags of edges to the returnend list.

        :returns: A list of all tags, including (if there is) also the tag give for the edges
        """

        given_tags = []
        for path in self._path:
            if vertices:
                given_tags.append(path['tag'])
            if edges and 'edge_tag' in path:
                given_tags.append(path['edge_tag'])
        return given_tags

    def get_query(self):
        """
        Instantiates and manipulates a sqlalchemy.orm.Query instance if this is needed.
        First,  I check if the query instance is still valid by hashing the queryhelp.
        In this way, if a user asks for the same query twice, I am not recreating an instance.

        :returns: an instance of sqlalchemy.orm.Query that is specific to the backend used.

        """
        from aiida.common.hashing import make_hash

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
        if self._hash is None:
            need_to_build = True
        elif self._injected:
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
        self._query = self.get_query().distinct()
        return self


    def first(self):
        """
        Executes query asking for one instance.
        Use as follows::

            qb = QueryBuilder(**queryhelp)
            qb.first()

        :returns:
            One row of results as a list
        """
        query = self.get_query()
        resultrow = self._impl.first(query)
        try:
            returnval = [
                    self._impl.get_aiida_res(self._attrkeys_as_in_sql_result[colindex], rowitem)
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
                returnval = [self._impl.get_aiida_res(self._attrkeys_as_in_sql_result[0], resultrow)]
        return returnval


    def one(self):
        """
        Executes the query asking for exactly one results. Will raise an exception if this is not the case
        :raises: MultipleObjectsError if more then one row can be returned
        :raises: NotExistent if no result was found
        """
        from aiida.common.exceptions import MultipleObjectsError, NotExistent
        self.limit(2)
        res = self.all()
        if len(res) > 1:
            raise MultipleObjectsError("More than one result was found")
        elif len(res) == 0:
            raise NotExistent("No result was found")
        return res[0]


    def count(self):
        """
        Counts the number of rows returned by the backend.

        :returns: the number of rows as an integer
        """
        query = self.get_query()
        return self._impl.count(query)

    def iterall(self, batch_size=100):
        """
        Same as :meth:`.all`, but returns a generator.
        Be aware that this is only safe if no commit will take place during this
        transaction. You might also want to read the SQLAlchemy documentation on
        http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.yield_per


        :param int batch_size:
            The size of the batches to ask the backend to batch results in subcollections.
            You can optimize the speed of the query by tuning this parameter.

        :returns: a generator of lists
        """


        query = self.get_query()

        for item in self._impl.iterall(query, batch_size, self._attrkeys_as_in_sql_result):
            yield item
        return

    def iterdict(self, batch_size=100):
        """
        Same as :meth:`.dict`, but returns a generator.
        Be aware that this is only safe if no commit will take place during this
        transaction. You might also want to read the SQLAlchemy documentation on
        http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.yield_per


        :param int batch_size:
            The size of the batches to ask the backend to batch results in subcollections.
            You can optimize the speed of the query by tuning this parameter.

        :returns: a generator of dictionaries
        """

        query = self.get_query()
        for item in self._impl.iterdict(query, batch_size, self.tag_to_projected_entity_dict):
            yield item




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



    def get_results_dict(self):
        """
        Deprecated, use :meth:`.dict` instead
        """
        warnings.warn(
                "get_results_dict will be deprecated in the future"
                "User iterdict for generator or dict for list",
                DeprecationWarning
            )

        return self.dict()

    def inputs(self, **kwargs):
        """
        Join to inputs of previous vertice in path.

        :returns: self
        """
        join_to = self._path[-1]['tag']
        cls = kwargs.pop('cls', Node)
        self.append(cls=cls, input_of=join_to, autotag=True, **kwargs)
        return self

    def outputs(self, **kwargs):
        """
        Join to outputs of previous vertice in path.

        :returns: self
        """
        join_to = self._path[-1]['tag']
        cls = kwargs.pop('cls', Node)
        self.append(cls=cls, output_of=join_to, autotag=True, **kwargs)
        return self

    def children(self, **kwargs):
        """
        Join to children/descendants of previous vertice in path.

        :returns: self
        """
        join_to = self._path[-1]['tag']
        cls = kwargs.pop('cls', Node)
        self.append(cls=cls, descendant_of=join_to, autotag=True, **kwargs)
        return self

    def parents(self, **kwargs):
        """
        Join to parents/ancestors of previous vertice in path.

        :returns: self
        """
        join_to = self._path[-1]['tag']
        cls = kwargs.pop('cls', Node)
        self.append(cls=cls, ancestor_of=join_to, autotag=True, **kwargs)
        return self


