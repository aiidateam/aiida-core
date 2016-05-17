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
from abc import abstractmethod, ABCMeta
from inspect import isclass as inspect_isclass
from sa_init import aliased, and_, or_, not_, func as sa_func
from aiida.common.exceptions import InputValidationError
from aiida.common.utils import flatten_list


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

    NODE_TYPE = 'node.Node'
    LINKLABEL_DEL = '--'
    VALID_PROJECTION_KEYS = ('func', 'cast')


    def __init__(self, *args, **kwargs):

        # A list storing the path being traversed by the query
        self.path = []

        # The list of unique labels
        # self.label_list = []# not needed any more

        # A list of unique aliases in same order as path
        self.aliased_path = []

        # A dictionary label:alias of ormclass
        # redundant but makes life easier
        self.label_to_alias_map = {}

        # A dictionary label: filter specification for this alias
        self.filters = {}

        # A dictionary label: projections for this alias
        self.projections = {}

        # A dictionary for classes passed to the label given to them
        # Everything is specified with unique labels, which are strings.
        # But somebody might not care about giving labels, so to do
        # everything with classes one needs a map
        # qb = QueryBuilder(path = [PwCalculation])
        # qb.append(StructureData, input_of=PwCalculation

        # The cls_to_label_map in this case would be:
        # {PwCalculation:'PwCalculation', StructureData:'StructureData'}

        self.cls_to_label_map = {}

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

        self._limit = False
        self.limit(kwargs.pop('limit', False))

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

    def __repr__(self):
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

    def order_by(self, order_by):
        """
        Set the entity to order by

        :param order_by:
            This is a list of items, where each item is a dictionary specifies
            what to sort for an entity

        In each dictionary in that list,
        keys represent valid labels of entities (tables),
        values are list of columns
        """

        self._order_by = []

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
            for key,items_to_order_by in order_spec.items():
                if not isinstance(items_to_order_by, (tuple, list)):
                    items_to_order_by = [items_to_order_by]
                label = self._get_label_from_specification(key)
                _order_spec[label] = []
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
                    for k,v in item_to_order_by.items():
                        if isinstance(v, basestring):
                            item_to_order_by[k] = {'dtype':v}
                    _order_spec[label].append(item_to_order_by)

            self._order_by.append(_order_spec)
        return self


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
                ormclasstype = self.NODE_TYPE
                ormclass = cls
            elif issubclass(cls, self.AiidaNode):
                ormclasstype = cls._plugin_type_string or self.NODE_TYPE
                ormclass = self.Node
            # Groups:
            elif issubclass(cls, self.Group):
                ormclasstype = 'group'
                ormclass = cls
            elif issubclass(cls, self.AiidaGroup):
                ormclasstype = 'group'
                ormclass = self.Group
            # Computers:
            elif issubclass(cls, self.Computer):
                ormclasstype = 'computer'
                ormclass = cls
            elif issubclass(cls, self.AiidaComputer):
                ormclasstype = 'computer'
                ormclass = self.Computer

            elif issubclass(cls, self.User):
                ormclasstype = 'user'
                ormclass = cls
            else:
                raise InputValidationError(
                        "\n\n\n"
                        "I do not know what to do with {}"
                        "\n\n\n".format(cls)
                    )
        # If it is not a class
        else:
            if ormclasstype == 'group':
                ormclass = self.Group
            elif ormclasstype == 'computer':
                ormclass = self.Computer
            elif ormclasstype == 'user':
                ormclass = self.User
            elif ormclasstype in ('node', self.NODE_TYPE):
                ormclass = self.Node
                ormclasstype = self.NODE_TYPE
            elif ormclasstype.startswith('data') or ormclasstype.startswith('calculation'):
                # Ok, here I am just going to trust the user that he provided the
                # correct input to filter by type for specific nodes:
                ormclass = self.Node
                ormclasstype = ormclasstype
            else:
                # The user has specified a certain type that I cannot explicitly
                # determine what it is
                # Last resort is using the factories.
                from aiida.orm import DataFactory, CalculationFactory
                from aiida.common.exceptions import MissingPluginError

                cls = None
                for Factory in (DataFactory, CalculationFactory):
                    try:
                        cls = Factory(ormclasstype)
                        ormclasstype = cls._plugin_type_string
                        ormclass = self.Node
                    except MissingPluginError:
                        continue

                if cls is None:
                    # Nothing was found using the factories!
                    raise InputValidationError(
                        "\n\nYou gave me type={}\n"
                        "But there is no class that can be loaded\n"
                        "as such using CalculationFactory and DataFactory"
                        "\n".format(ormclasstype)
                    )
        return ormclass, ormclasstype

    def _get_autolabel(self, ormclasstype):
        baselabel = self._get_label_from_type(ormclasstype)
        labels_used = self.label_to_alias_map.keys()
        for i in range(1, 100):
            label = '{}_{}'.format(baselabel, i)
            if label not in labels_used:
                return label


    def _get_label_from_type(self, ormclasstype):
        """
        Assign a label to the given
        vertice of a path, based mainly on the type
        *   data.structure.StructureData -> StructureData
        *   data.structure.StructureData. -> StructureData
        *   calculation.job.quantumespresso.pw.PwCalculation. -. PwCalculation
        *   node.Node. -> Node
        *   Node -> Node
        *   computer -> computer
        """
        return ormclasstype.rstrip('.').split('.')[-1]


    def append(self, cls=None, type=None, label=None,
                autolabel=False, filters=None, project=None, subclassing=True,
                linklabel=None, linkfilters=None, linkproject=None, **kwargs
        ):
        """
        Any iterative procedure to build the path for a graph query
        needs to invoke this method to append to the path.

        :param cls: The Aiida-class (or backend-class) defining the appended vertice
        :param type: The type of the class, if cls is not given
        :param label:
            A unique label. If none is given, will take the classname.
            See keyword autolabel to achieve unique label.
        :param filters:
            Filters to apply for this vertice.
            See usage examples for details.
        :param autolabel:
            Whether to search for a unique label,
            (default **False**). If **True**, will find a unique label.
            Cannot be set to **True** if label is specified.
        :param subclassing:
            Whether to include subclasses of the given class
            (default **True**).
            E.g. Specifying JobCalculation will include PwCalculation

        A small usage example how this can be invoked::

            qb = QueryBuilder() # Instantiating empty querybuilder instance
            qb.append(cls=StructureData) # First item is StructureData node
            # Note that also qb.append(StructureData) would work.
            qb.append(cls=PwCalculation, output_of=StructureData) # The
            # next node in the path is a PwCalculation, with
            # a structure joined as an input
            # Note that qb.append(PwCalculation) would have worked as

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

        ormclass, ormclasstype = self._get_ormclass(cls, type)
        ######################## LABEL #################################
        # Let's get a label
        user_defined_label = False
        if label:
            if self.LINKLABEL_DEL in label:
                raise InputValidationError(
                    "Label cannot contain {}\n"
                    "since this is used as a delimiter for links"
                    "".format(self.LINKLABEL_DEL)
                )
            label = label
            user_defined_label = True
        elif autolabel:
            label = self._get_autolabel(ormclasstype)
        else:
            label = self._get_label_from_type(ormclasstype)
        # Check if the label is not yet used:
        if label in self.label_to_alias_map.keys():
            if user_defined_label:
                raise InputValidationError(
                    "\n"
                    "This label ({}) is already in use\n"
                    "\n".format(label)
                )
            else:
                raise InputValidationError(
                    "\n"
                    "You did not specify a label, so I am making one myself\n"
                    "based on the class/type you gave me\n"
                    "The label that I made ({}) is already in use\n"
                    "please specify a label or set autolabel to true"
                    "".format(label)
                )

        ################ LABEL MAPPING #################################
        # Let's fill the cls_to_label_map so that one can specify
        # this vertice in a joining specification later
        # First this only makes sense if a class was specified:
        if cls:
            if cls in self.cls_to_label_map.keys():
                # In this case, this class already stands for another
                # label that was used before.
                # This means that the first label will be the correct
                # one. This is dangerous and maybe should be avoided in
                # the future
                pass

            else:
                self.cls_to_label_map[cls] = label
            # TODO check with duplicate classes


        ######################## ALIASING ##############################
        alias = aliased(ormclass)
        self.aliased_path.append(alias)
        self.label_to_alias_map[label] = alias



        ################# FILTERS ######################################
        self.filters[label] = {}
        #if the user specified a filter, add it:
        if filters is not None:
            self.add_filter(label, filters)

        # I have to add a filter on column type.
        # This so far only is necessary for AiidaNodes
        # GROUPS?
        if issubclass(ormclass, self.Node):
            self._add_type_filter(label, ormclasstype, subclassing)

        ##################### PROJECTIONS ##############################
        self.projections[label] = []

        if project is not None:
            self.add_projection(label, project)




        ################## JOINING #####################################

        # Get the functions that are implemented:
        spec_to_function_map = self._get_function_map().keys()


        joining_keyword = kwargs.pop('joining_keyword', None)
        joining_value = kwargs.pop('joining_value', None)
        reverse_linklabel = kwargs.pop('reverse_linklabel', None)


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
                                    'cls', 'type', 'label',
                                    'autolabel', 'filters', 'project'
                                ]
                            )
                    )
            elif joining_keyword:
                raise InputValidationError(
                        "\n\n\n"
                        "You already specified joining specification {}\n"
                        "But you now also want to specify {}"
                        "\n\n\n".format(joining_keyword, k)
                    )
            else:
                joining_keyword = key
                joining_value = self._get_label_from_specification(val)
        # the default is just a direction keyword and value 1
        # meaning that this vertice is linked to the previous
        # vertice as output
        if joining_keyword is None:
            joining_keyword = 'direction'
            joining_value = 1

        ############################# LINKS ####################################
        # See if this requires a link:
        if joining_keyword in ('input_of', 'output_of', 'direction') and len(self.path)>0:
            # Ok, so here we are joining one node to another, as input or output
            # This means that the user might want to query by label or project
            # on a label column.
            # Since the label of this vertice is unique the label, e.g. 'calc1'
            # the label '<>calc1' will also be unique if '<>' is a protected
            # substring.
            if linklabel is None:
                if joining_keyword in ('input_of', 'output_of'):
                    link_to_label = self._get_label_from_specification(joining_value)
                elif joining_keyword == 'direction':
                    link_to_label = self.path[-abs(joining_value)]['label']
                linklabel = link_to_label + self.LINKLABEL_DEL + label
                reverse_linklabel = label + self.LINKLABEL_DEL + link_to_label
            aliased_link = aliased(self.Link)
            self.label_to_alias_map[linklabel] = aliased_link



            if reverse_linklabel is not None:
                self.label_to_alias_map[reverse_linklabel] = aliased_link
                self.filters[reverse_linklabel] = {}
                self.projections[reverse_linklabel] = {}

            # Filters on links:
            self.filters[linklabel] = {}
            if linkfilters is not None:
                self.add_filter(linklabel, linkfilters)

            # Projections on links
            self.projections[linklabel] = {}
            if linkproject is not None:
                self.add_projection(linklabel, linkproject)


        ################### EXTENDING THE PATH #################################


        path_extension = dict(
                type=ormclasstype, label=label, joining_keyword=joining_keyword,
                joining_value=joining_value
            )
        if linklabel is not None:
            path_extension.update(dict(linklabel=linklabel))
            if reverse_linklabel is not None:
                path_extension.update(dict(reverse_linklabel=reverse_linklabel))

        self.path.append(path_extension)
        return self

    def add_filter(self, labelspec, filter_spec):
        """
        Adding a filter to my filters.

        :param labelspec:
            The label, which has to exist already as a key
            in self.filters
        :param dict filter_spec:
            The specifications for the filter, has to be adictionary
        """


        if not isinstance(filter_spec, dict):
            raise InputValidationError(
                    "Filters have to be passed as dictionaries"
                )

        label = self._get_label_from_specification(labelspec)
        self.filters[label].update(filter_spec)

    def _add_type_filter(self, labelspec, ormclasstype, subclassing=True):

        label = self._get_label_from_specification(labelspec)

        if subclassing:
            if ormclasstype == self.NODE_TYPE:
                # User looking for every node, so I will put no filter
                node_type_flt = None
            else:
                node_type_flt = {
                    'like':'{}.%'.format(
                        '.'.join(ormclasstype.rstrip('.').split('.')[:-1])
                    )
                }
        else:
            if ormclasstype == self.NODE_TYPE:
                # User looking only for unsubclassed nodes,
                # which does not make sense, but that is not
                # my problem
                node_type_flt = {'==':self.NODE_TYPE}
            else:
                node_type_flt = {'==':ormclasstype}
        if node_type_flt is not None:
            self.add_filter(labelspec, {'type':node_type_flt})

    def add_projection(self, label_spec, projection_spec):
        """
        Adds a projection
        
        :param label_spec: A valid specification for a label
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
            qb.append(StructureData, label='struc')
            qb.add_projection('struc', 'id') # Will project the id
            # OR
            qb.add_projection('struc', ['id', 'attributes.kinds'])
            # OR
            # I want to cast the kinds to a JSON-object (will return
            # a dictionary:
            qb.add_projection(
                    'struc',
                    [
                        'id',
                        {'attributes.kinds':{'cast':'j'}},
                    ]
                )
            # OR 
            # In this example, the order is not specified any more,
            # but it is valid input if you don't care about the order of the 
            # results:
            qb.add_projection(
                    'struc',
                    {
                        'id':{}, 
                        {'attributes.kinds':{'cast':'j'}},
                    }
                )
        """
        label = self._get_label_from_specification(label_spec)
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
                    if key not in self.VALID_PROJECTION_KEYS:
                        raise InputValidationError(
                            "{} is not a valid key {}".format(
                                key, self.VALID_PROJECTION_KEYS)
                        )
                        if not isinstance(val, basestring):
                            raise InputValidationError(
                                "{} has to be a string".format(val)
                            )
            _projections.append(_thisprojection)
        self.projections[label] = _projections


    def _get_projectable_entity(self, alias, column_name, attrpath, **entityspec):

        column = self.get_column(column_name, alias)
        if len(attrpath) or column_name in ('attributes', 'extras'):

            entity = self._get_projectable_attribute(
                        alias, column, attrpath, **entityspec
                    )
        else:
            entity = column
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
            self.que = self.que.add_entity(alias)
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
            self.que =  self.que.add_columns(entity_to_project)




    def _build_projections(self, label):
        items_to_project = self.projections.get(label, [])

        # Sort of spaghetti, but possible speedup
        if not items_to_project:
            return

        alias = self.label_to_alias_map[label]
        self.label_to_projected_entity_dict[label] = {}

        for projectable_spec in items_to_project:
            for projectable_entity_name, extraspec in projectable_spec.items():
                self._add_to_projections(
                        alias, projectable_entity_name, **extraspec
                    )

                self.label_to_projected_entity_dict[label][
                        projectable_entity_name
                    ] = self.nr_of_projections
                self.nr_of_projections += 1


    def _get_label_from_specification(self, specification):
        if isinstance(specification, basestring):
            if specification in self.label_to_alias_map.keys():
                label = specification
            else:
                raise InputValidationError(
                        "Label {} is not among my known labels\n"
                        "   My labels are: {}"
                        "\n\n".format(
                                specification, self.label_to_alias_map.keys()
                            )
                    )
        else:
            if specification in self.cls_to_label_map.keys():
                label = self.cls_to_label_map[specification]
            else:
                raise InputValidationError(
                    "\nYou specified as a class for which I have to find a label\n"
                    "The classes that I can do this for are:{}\n"
                    "The labels I have are: {}\n"
                    "\n".format(
                        specification, self.cls_to_label_map.keys(),
                        self.label_to_alias_map.keys()
                    )
                )
        return label

    def limit(self, limit):
        """
        Set the limit (nr of rows to return)

        :param limit: integers of nr of rows to return, or False if no limit
        """

        if limit:
            if not isinstance(limit, int):
                raise InputValidationError("limit has to be an integer")
        self._limit = limit
        return self



    @staticmethod
    @abstractmethod
    def _get_session():
        pass


    @classmethod
    def _get_filter_expr_from_column(cls, operator, value, database_entity):
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
    def _get_filter_expr(cls, operator, value, db_column, attr_key, is_attribute):
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

        if operator.startswith('~'):
            negation = True
            operator = operator.lstrip('~')
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
                                    db_column, attr_key,
                                    is_attribute=is_attribute
                                )
                        )
            if operator == 'and':
                expr = and_(*expressions_for_this_path)
            elif operator == 'or':
                 expr = or_(*expressions_for_this_path)

        if is_attribute:
            expr = cls._get_filter_expr_from_attributes(operator, value, db_column, attr_key)
        else:
            expr = cls._get_filter_expr_from_column(operator, value, db_column)
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
            if path_spec in  ('and', 'or', '~or', '~and'):
                subexpressions = [
                    self._build_filters(alias, sub_filter_spec)
                    for sub_filter_spec in filter_operation_dict
                ]
                if path_spec == 'and':
                    expressions.append(and_(*subexpressions))
                elif path_spec == 'or':
                    expressions.append(or_(*subexpressions))
                elif path_spec == '~and':
                    expressions.append(not_(and_(*subexpressions)))
                elif path_spec == '~or':
                    expressions.append(not_(or_(*subexpressions)))
            else:
                column_name = path_spec.split('.')[0]
                column =  self.get_column(column_name, alias)
                attr_key = path_spec.split('.')[1:]
                is_attribute = (
                    attr_key or
                    column_name in ('attributes', 'extras')
                )
                #~ is_attribute = bool(attr_key)
                if not isinstance(filter_operation_dict, dict):
                    filter_operation_dict = {'==':filter_operation_dict}
                [
                    expressions.append(
                        self._get_filter_expr(
                            operator, value, column, attr_key,
                            is_attribute=is_attribute
                        )
                    )
                    for operator, value
                    in filter_operation_dict.items()
                ]
        return and_(*expressions)

    #~ @abstractmethod
    #~ def _build_filters(self, alias, filter_spec):
        #~ pass

    def _join_slaves(self, joined_entity, entity_to_join):
        raise NotImplementedError(
                "Master - slave relationships are not implemented"
            )
        #~ call = aliased(Call)
        #~ self.que = self.que.join(call,  call.caller_id == joined_entity.id)
        #~ self.que = self.que.join(
                #~ entity_to_join,
                #~ call.called_id == entity_to_join.id
            #~ )

    def _join_masters(self, joined_entity, entity_to_join):
        raise NotImplementedError(
                "Master - slave relationships are not implemented"
            )
        #~ call = aliased(Call)
        #~ self.que = self.que.join(call,  call.called_id == joined_entity.id)
        #~ self.que = self.que.join(
                #~ entity_to_join,
                #~ call.caller_id == entity_to_join.id
            #~ )

    def _join_outputs(self, joined_entity, entity_to_join, aliased_link):
        """
        :param joined_entity: The (aliased) ORMclass that is an input
        :param entity_to_join: The (aliased) ORMClass that is an output.

        **joined_entity** and **entity_to_join** are joined with a link
        from **joined_entity** as input to **enitity_to_join** as output
        (**enitity_to_join** is an *output_of* **joined_entity**)
        """
        #~ aliased_link = aliased(self.Link)
        self.que = self.que.join(
                aliased_link,
                aliased_link.input_id == joined_entity.id
        ).join(
                entity_to_join,
                aliased_link.output_id == entity_to_join.id
        )

    def _join_inputs(self, joined_entity, entity_to_join, aliased_link):
        """
        :param joined_entity: The (aliased) ORMclass that is an output
        :param entity_to_join: The (aliased) ORMClass that is an input.

        **joined_entity** and **entity_to_join** are joined with a link
        from **joined_entity** as output to **enitity_to_join** as input
        (**enitity_to_join** is an *input_of* **joined_entity**)
        """
        aliased_link = aliased(self.Link)
        self.que = self.que.join(
                aliased_link,
                aliased_link.output_id == joined_entity.id
        ).join(
                entity_to_join,
                aliased_link.input_id == entity_to_join.id
        )

    def _join_descendants(self, joined_entity, entity_to_join):
        """
        :param joined_entity: The (aliased) ORMclass that is an ancestor
        :param entity_to_join: The (aliased) ORMClass that is a descendant.

        **joined_entity** and **entity_to_join** are
        joined via the DbPath table.
        from **joined_entity** as parent to **enitity_to_join** as child
        (**enitity_to_join** is a *descendant_of* **joined_entity**)
        """
        aliased_path = aliased(self.Path)
        self.que = self.que.join(
                aliased_path,
                aliased_path.parent_id == joined_entity.id
        ).join(
                entity_to_join,
                aliased_path.child_id == entity_to_join.id
        )

    def _join_ancestors(self, joined_entity, entity_to_join):
        """
        :param joined_entity: The (aliased) ORMclass that is a descendant
        :param entity_to_join: The (aliased) ORMClass that is an ancestor.

        **joined_entity** and **entity_to_join**
        are joined via the DbPath table.
        from **joined_entity** as child to **enitity_to_join** as parent
        (**enitity_to_join** is an *ancestor_of* **joined_entity**)
        """
        aliased_path = aliased(self.Path)
        self.que = self.que.join(
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
        aliased_group_nodes = aliased(self.table_groups_nodes)
        self.que = self.que.join(
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
        aliased_group_nodes = aliased(self.table_groups_nodes)
        self.que = self.que.join(
                aliased_group_nodes,
                aliased_group_nodes.c.dbnode_id == joined_entity.id
        ).join(
                entity_to_join,
                entity_to_join.id == aliased_group_nodes.c.dbgroup_id
        )
    def _join_user(self, joined_entity, entity_to_join):
        """
        :param joined_entity: the user
        :param entity_to_join: the dbnode that joins to that user
        """
        self.que = self.que.join(
                entity_to_join,
                entity_to_join.id == joined_entity.user_id
            )
    def _join_node_to_user(self, joined_entity, entity_to_join):
        """
        :param joined_entity: the (aliased) node or group in the DB
        :param entity_to_join: the user you want to join with
        """
        self.que = self.que.join(
                entity_to_join,
                entity_to_join.user_id == joined_entity.id
            )

    def _join_to_computer_used(self, joined_entity, entity_to_join):
        self.que = self.que.join(
                entity_to_join,
                entity_to_join.dbcomputer_id == joined_entity.id
        )

    def _join_computer(self, joined_entity, entity_to_join):
        """
        :param joined_entity: An entity that can use a computer (eg a node)
        :param entity: aliased dbcomputer entity


        """
        self.que = self.que.join(
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
                'runs_on'   : self._join_to_computer_used,
                'computer_of':self._join_computer,
                'used_by'   : self._join_node_to_user,
                'user_of'   : self._join_user,
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
        *   *runs_on*
        *   *computer_of*
        *   *used_by*
        *   *user_of*

        Future:

        *   *master_of*
        *   *slave_of*
        """

        if joining_keyword == 'direction':
            if joining_value > 0:
                returnval = self.aliased_path[index-joining_value], self._join_outputs
            elif joining_value < 0:
                returnval = self.aliased_path[index+joining_value], self._join_inputs
            else:
                raise Exception("Direction 0 is not valid")
        else:
            func = self._get_function_map()[joining_keyword]

            if isinstance(joining_value, int):
                returnval = (self.aliased_path[joining_value], func)
            elif isinstance(joining_value, str):
                try:
                    returnval = self.label_to_alias_map[
                            self._get_label_from_specification(joining_value)
                        ], func
                except KeyError:
                    raise InputValidationError(
                        'Key {} is unknown to the types I know about:\n'
                        '{}'.format(val, self.label_to_alias_map.keys())
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
            'path'      :   self.path,
            'filters'   :   self.filters,
            'project'   :   self.projections,
            'limit'     :   self._limit,
            'order_by'  :   self._order_by,
        })
        
        #~ self._get_json_compatible()
        
    def get_column(self, colname, alias):
        """
        Return the column for the projection, if the column name is specified.
        """
        try:
            return getattr(alias, colname)
        except (KeyError, AttributeError):
            raise InputValidationError(
                '\n{} is not a column of {}\n'.format(colname, alias)
            )

    def _build_order(self, alias, entitylabel, entityspec):

        column_name = entitylabel.split('.')[0]
        attrpath = entitylabel.split('.')[1:]
        if attrpath and 'cast' not in entityspec.keys():
            raise InputValidationError(
                "\n\n"
                "In order to project ({}), I have to cast the the values,\n"
                "but you have not specified the datatype to cast to\n"
                "You can do this with keyword 'cast'\n"
                "".format(entitylabel)
            )
                
                
        entity = self._get_projectable_entity(alias, column_name, attrpath, **entityspec)
        order = entityspec.get('order', 'asc')
        if order == 'desc':
            entity = entity.desc()
        self.que = self.que.order_by(entity)


    def _build(self):
        """
        build the query and return a sqlalchemy.Query instance
        """

        # self.labels_location_dict is a dictionary that
        # maps the label to its index in the list
        # this is basically the mapping between the count
        # of nodes traversed
        # and the label used for that node
        self.labels_location_dict = {
                path['label']:index
                for index, path
                in enumerate(self.path)
            }

        #Starting the query by receiving a session
        # Every subclass needs to have _get_session and give me the
        # right session
        firstalias = self.label_to_alias_map[self.path[0]['label']]
        self.que = self._get_session().query(firstalias)

        ######################### JOINS ################################

        for index, verticespec in  enumerate(self.path[1:], start=1):
            alias = self.label_to_alias_map[verticespec['label']]
            #looping through the queryhelp
            #~ if index:
                #There is nothing to join if that is the first table
            toconnectwith, connection_func = self._get_connecting_node(
                    index, **verticespec
                )
            linklabel = verticespec.get('linklabel', None)
            if linklabel is None:
                connection_func(toconnectwith, alias)
            else:
                link = self.label_to_alias_map[linklabel]
                connection_func(toconnectwith, alias, link)

        ######################### FILTERS ##############################

        for label, filter_specs in self.filters.items():
            try:
                alias = self.label_to_alias_map[label]
            except KeyError:
                # TODO Check KeyError before?
                raise InputValidationError(
                    ' You looked for label {} among the alias list\n'
                    'The labels I know are:\n{}'
                    ''.format(label, self.label_to_alias_map.keys())
                )
            self.que = self.que.filter(
                    self._build_filters(alias, filter_specs)
                )

        ######################### PROJECTIONS ##########################
        # first clear the entities in the case the first item in the
        # path was not meant to be projected
        # attribute of Query instance storing entities to project:

        # Will be later set to this list:
        entities = []
        # Mapping between enitites and the label used/ given by user:
        self.label_to_projected_entity_dict = {}

        if not any(self.projections.values()):
            # If user has not set projection,
            # I will simply project the last item specified!
            # Don't change, path traversal querying
            # relies on this behavior!
            self.add_projection(self.path[-1]['label'], '*')

        self.nr_of_projections = 0

        for vertice in self.path:
            self._build_projections(vertice['label'])


        ##################### LINK-PROJECTIONS #########################

        for vertice in self.path:
            linklabel = vertice.get('linklabel', None)
            if linklabel is not None:
                self._build_projections(linklabel)

            linklabel = vertice.get('reverse_linklabel', None)
            if linklabel is not None:
                self._build_projections(linklabel)

        ######################### ORDER ################################
        for order_spec in self._order_by:
            for label, entities in order_spec.items():
                alias = self.label_to_alias_map[label]
                for entitydict in entities:
                    for entitylabel, entityspec in entitydict.items():
                        self._build_order(alias, entitylabel, entityspec)

        ######################### LIMIT ################################
        if self._limit:
            self.que = self.que.limit(self._limit)

        ################ LAST BUT NOT LEAST ############################
        #pop the entity that I added to start the query
        self.que._entities.pop(0)

        ######################### DONE #################################

        return self.que

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
            for node in self.path:
                label = node['label']
                requested_cols = [
                        key 
                        
                        for item in self.projections[label]
                        for key in item.keys()
                    ]
                if '*' in requested_cols:
                    input_alias_list.append(aliased(self.label_to_alias_map[label]))
                    
                    
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
        self.que = self.get_query()
        self.que = self.que.except_(build_counterquery(calc_class))
        return self


    def get_aliases(self):
        return self.aliased_path



    def get_query(self):
        """
        Checks if query instance is set as attribute of instance,
        if not invokes :func:`QueryBuilderBase._build`.
        :returns: an instance of sqlalchemy.orm.Query
        """
        if hasattr(self, 'que'):
            return self.que
        return self._build()

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
        attrkeys_as_in_sql_result = {
            index_in_sql_result:attrkey
            for label, projected_entities_dict
            in self.label_to_projected_entity_dict.items()
            for attrkey, index_in_sql_result
            in projected_entities_dict.items()
        }

        try:
            returnval = [
                    self._get_aiida_res(attrkeys_as_in_sql_result[colindex], rowitem)
                    for colindex, rowitem
                    in enumerate(resultrow)
                ]
        except TypeError:
            assert(
                len(attrkeys_as_in_sql_result)==1,
                "I have not received an iterable, but the number of projections is > 1"
            )
            # It still returns a list!
            returnval = [self._get_aiida_res(attrkeys_as_in_sql_result[0], resultrow)]
        return returnval


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
        self.que = self.get_query().distinct()
        return self


    def yield_per(self, count):
        """
        :param count: Number of rows to yield per step

        Yields *count* rows at a time

        :returns: a generator
        """
        return self.get_query().yield_per(count)

    def count(self):
        """
        Counts the number of rows returned by the backend.

        :returns: the number of rows as an integer
        """
        que = self.get_query()
        return que.count()

    def all(self):
        """
        Executes the full query.
        The order of the rows is as returned by the backend,
        the order inside each row is given by the order of the path
        and the order of the projections for each vertice in the path.

        :returns: a generator for all projected entities (each being a list).
        """

        results = self.yield_per(100)
        attrkeys_as_in_sql_result = {
            index_in_sql_result:attrkey
            for label, projected_entities_dict
            in self.label_to_projected_entity_dict.items()
            for attrkey, index_in_sql_result
            in projected_entities_dict.items()
        }

        try:
            for resultrow in results:
                yield [
                    self._get_aiida_res(attrkeys_as_in_sql_result[colindex], rowitem)
                    for colindex, rowitem
                    in enumerate(resultrow)
                ]
        except TypeError:
            # resultrow not an iterable:
            # Checked, result that raises exception is included
            assert(
                len(attrkeys_as_in_sql_result)==1,
                "I have not received an iterable, but the number of projections is > 1"
            )

            for rowitem in results:
                yield [self._get_aiida_res(attrkeys_as_in_sql_result[0], rowitem)]

    def get_results_dict(self):
        """
        Calls :func:`QueryBuilderBase.yield_per`.
        Loops through the results and constructs for each row a dictionary
        of results.
        In this dictionary (one for each row) the key is the unique label in the path
        and the value is another dictionary of key-value pairs where the key is the entity
        (column) and the value the database entry.
        Instances of an ORMclass are replaced with Aiidaclasses invoking
        the DbNode.get_aiida_class method (key is '*').

        :returns: a generator returning the results as an iterable of dictionaries.
        """

        try:
            for this_result in self.yield_per(100):
                yield {
                    label:{
                        attrkey:self._get_aiida_res(
                                attrkey, this_result[index_in_sql_result]
                            )
                        for attrkey, index_in_sql_result
                        in projected_entities_dict.items()
                    }
                    for label, projected_entities_dict
                    in self.label_to_projected_entity_dict.items()
                }
        except TypeError:
            # resultrow not an iterable:
            # Checked, result that raises exception is included
            assert(
                self.nr_of_projections==1,
                "I have not received an iterable, but the number of projections is > 1"
            )
            for this_result in self.yield_per(100):
                yield {
                    label:{
                        attrkey : self._get_aiida_res(attrkey, this_result)
                        for attrkey, position in projected_entities_dict.items()
                    }
                    for label, projected_entities_dict in self.label_to_projected_entity_dict.items()
                }
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
        join_to = self.path[-1]['label']
        cls = kwargs.pop('cls', self.AiidaNode)
        self.append(cls=cls, input_of=join_to, autolabel=True, **kwargs)
        return self

    def outputs(self, **kwargs):
        """
        Join to outputs of previous vertice in path.

        :returns: self
        """
        join_to = self.path[-1]['label']
        cls = kwargs.pop('cls', self.AiidaNode)
        self.append(cls=cls, output_of=join_to, autolabel=True, **kwargs)
        return self

    def children(self, **kwargs):
        """
        Join to children/descendants of previous vertice in path.

        :returns: self
        """
        join_to = self.path[-1]['label']
        cls = kwargs.pop('cls', self.AiidaNode)
        self.append(cls=cls, descendant_of=join_to, autolabel=True, **kwargs)
        return self

    def parents(self, **kwargs):
        """
        Join to parents/ancestors of previous vertice in path.

        :returns: self
        """
        join_to = self.path[-1]['label']
        cls = kwargs.pop('cls', self.AiidaNode)
        self.append(cls=cls, ancestor_of=join_to, autolabel=True, **kwargs)
        return self


