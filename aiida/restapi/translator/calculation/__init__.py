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

class CalculationTranslator(NodeTranslator):
    """
    It prepares the query_help from user inputs which later will be
    passed to QueryBuilder to get either the list of Calculations or the
    details of one calculation

    Supported REST requests:
    - http://base_url/calculation?filters
    - http://base_url/calculation/pk
    - http://base_url/calculation/pk/io/inputs
    - http://base_url/calculation/pk/io/outputs
    - http://base_url/calculation/pk/content/attributes
    - http://base_url/calculation/pk/content/extras

    **Please NOTE that filters are allowed ONLY in first resuest to
    get calculation list

    Pk         : pk of the calculation
    Filters    : filters dictionary to apply on
                 calculations list. Not applicable to single calculation.
    order_by   : used to sort calculations list. Not applicable to
                 single calculation
    end_points : io/inputs, io/outputs, content/attributes, content/extras
    query_help : (TODO)
    kwargs: extra parameters if any.

    **Return: list of calculations or details of single calculation

    EXAMPLES:
    ex1:: get single calculation details
    ct = CalculationTranslator()
    ct.add_filters(node_pk)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.formatted_result(qb)

    ex2:: get list of calculations (use filters)
    ct = CalculationTranslator()
    ct.add_filters(filters_dict)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.get_formatted_result(qb)

    ex3:: get calculation inputs
    ct = CalculationTranslator()
    ct.get_inputs(node_pk)
    results_type = "inputs"
    ct.add_filters(filters_dict)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.get_formatted_result(qb, results_type)

    ex3:: get calculation outputs
    ct = CalculationTranslator()
    ct.get_outputs(node_pk)
    results_type = "outputs"
    ct.add_filters(filters_dict)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.get_formatted_result(qb, results_type)

    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "calculations"
    # The string name of the AiiDA class one-to-one associated to the present
    #  class
    _aiida_type = "calculation.Calculation"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = _aiida_type + '.'

    _result_type = __label__

    def __init__(self, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        # basic query_help object
        super(CalculationTranslator, self).__init__(
            Class=self.__class__, **kwargs)
