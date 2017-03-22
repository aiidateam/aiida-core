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

class UserTranslator(BaseTranslator):
    """
    It prepares the query_help from user inputs which later will be
    passed to QueryBuilder to get either the list of Users or the
    details of one user

    Supported REST requests:
    - http://base_url/user?filters
    - http://base_url/user/pk

    **Please NOTE that filters are not allowed to get user details

    Pk         : pk of the user
    Filters    : filters dictionary to apply on
                 user list. Not applicable to single user.
    order_by   : used to sort user list. Not applicable to
                 single user
    end_points : NA
    query_help : (TODO)
    kwargs: extra parameters if any.

    **Return: list of users or details of single user

    EXAMPLES:
    ex1::
    ct = UserTranslator()
    ct.add_filters(node_pk)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.formatted_result(qb)

    ex2::
    ct = UserTranslator()
    ct.add_filters(filters_dict)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.formatted_result(qb)

    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "users"
    # The string name of the AiiDA class one-to-one associated to the present
    #  class
    _aiida_type = "user.User"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = 'user'

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
        super(UserTranslator, self).__init__(Class=self.__class__, **kwargs)

