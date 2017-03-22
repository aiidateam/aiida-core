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

class ComputerTranslator(BaseTranslator):
    """
    It prepares the query_help from user inputs which later will be
    passed to QueryBuilder to get either the list of Computers or the
    details of one computer

    Supported REST requests:
    - http://base_url/computer?filters
    - http://base_url/computer/pk

    **Please NOTE that filters are not allowed to get computer details

    Pk         : pk of the computer
    Filters    : filters dictionary to apply on
                 computer list. Not applicable to single computer.
    order_by   : used to sort computer list. Not applicable to
                 single computer
    end_points : NA
    query_help : (TODO)
    kwargs: extra parameters if any.

    **Return: list of computers or details of single computer

    EXAMPLES:
    ex1::
    ct = ComputerTranslator()
    ct.add_filters(node_pk)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.formatted_result(qb)

    ex2::
    ct = ComputerTranslator()
    ct.add_filters(filters_dict)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.formatted_result(qb)

    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "computers"
    # The string name of the AiiDA class one-to-one associated to the present
    #  class
    _aiida_type = "computer.Computer"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = 'computer'

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
        super(ComputerTranslator, self).__init__(Class=self.__class__,
                                                 **kwargs)
