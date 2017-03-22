# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.restapi.translator.base import BaseTranslator
from aiida.restapi.common.config import custom_schema

class GroupTranslator(BaseTranslator):
    """
    It prepares the query_help from user inputs which later will be
    passed to QueryBuilder to get either the list of Groups or the
    details of one group

    Supported REST requests:
    - http://base_url/group?filters
    - http://base_url/group/pk

    **Please NOTE that filters are not allowed to get group details

    Pk         : pk of the group
    Filters    : filters dictionary to apply on
                 group list. Not applicable to single group.
    order_by   : used to sort group list. Not applicable to
                 single group
    end_points : NA
    query_help : (TODO)
    kwargs: extra parameters if any.

    **Return: list of groups or details of single group

    EXAMPLES:
    ex1::
    ct = GroupTranslator()
    ct.add_filters(node_pk)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.formatted_result(qb)

    ex2::
    ct = GroupTranslator()
    ct.add_filters(filters_dict)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.formatted_result(qb)

    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "groups"
    # The string name of the AiiDA class one-to-one associated to the present
    #  class
    _aiida_type = "group.Group"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = 'group'

    _result_type = __label__

    # Extract the default projections from custom_schema if they are defined
    if 'columns' in custom_schema:
        _default_projections = custom_schema['columns'][__label__]
    else:
        _default_projections = ['**']


    def __init__(self, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        super(GroupTranslator, self).__init__(Class=self.__class__, **kwargs)

