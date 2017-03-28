# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.restapi.translator.node import NodeTranslator

class CodeTranslator(NodeTranslator):
    """
    It prepares the query_help from user inputs which later will be
    passed to QueryBuilder to get either the list of Codes or the
    details of one code

    Supported REST requests:
    - http://base_url/code?filters
    - http://base_url/code/pk
    - http://base_url/code/pk/io/inputs
    - http://base_url/code/pk/io/outputs
    - http://base_url/code/pk/content/attributes
    - http://base_url/code/pk/content/extras

    **Please NOTE that filters are allowed ONLY in first resuest to
    get code list

    Pk         : pk of the code
    Filters    : filters dictionary to apply on
                 codes list. Not applicable to single code.
    order_by   : used to sort codes list. Not applicable to
                 single code
    end_points : io/inputs, io/outputs, content/attributes, content/extras
    query_help : (TODO)
    kwargs: extra parameters if any.

    **Return: list of codes or details of single code

    EXAMPLES:
    ex1:: get single code details
    ct = CodeTranslator()
    ct.add_filters(node_pk)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.formatted_result(qb)

    ex2:: get list of codes (use filters)
    ct = CodeTranslator()
    ct.add_filters(filters_dict)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.get_formatted_result(qb)

    ex3:: get code inputs
    ct = CodeTranslator()
    ct.get_inputs(node_pk)
    results_type = "inputs"
    ct.add_filters(filters_dict)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.get_formatted_result(qb, results_type)

    ex3:: get code outputs
    ct = CodeTranslator()
    ct.get_outputs(node_pk)
    results_type = "outputs"
    ct.add_filters(filters_dict)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.get_formatted_result(qb, results_type)

    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "codes"
    # The string name of the AiiDA class one-to-one associated to the present
    #  class
    _aiida_type = "code.Code"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = _aiida_type + '.'

    _result_type = __label__

    def __init__(self, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        super(CodeTranslator, self).__init__(Class=self.__class__, **kwargs)
