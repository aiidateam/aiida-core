# -*- coding: utf-8 -*-

__copyright__ = u"""Copyright (c), This file is part of
the AiiDA platform. For further information please visit
http://www.aiida.net/.. All rights reserved."""
__license__ = "MIT license, see LICENSE.txt file"
__authors__ = "The AiiDA team."
__version__ = "0.7.1"


from aiida.restapi.translator.node import NodeTranslator

class DataTranslator(NodeTranslator):
    """
    It prepares the query_help from user inputs which later will be
    passed to QueryBuilder to get either the list of Datas or the
    details of one data node.

    Supported REST requests:
    - http://base_url/data?filters
    - http://base_url/data/pk
    - http://base_url/data/pk/io/inputs
    - http://base_url/data/pk/io/outputs
    - http://base_url/data/pk/content/attributes
    - http://base_url/data/pk/content/extras

    **Please NOTE that filters are allowed ONLY in first resuest to
    get data nodes list

    Pk         : pk of the data
    Filters    : filters dictionary to apply on
                 data node list. Not applicable to single data node.
    order_by   : used to sort data node list. Not applicable to
                 single data node
    end_points : io/inputs, io/outputs, content/attributes, content/extras
    query_help : (TODO)
    kwargs: extra parameters if any.

    **Return: list of data nodes or details of single data node

    EXAMPLES:
    ex1:: get single data node details
    ct = DataTranslator()
    ct.add_filters(node_pk)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.formatted_result(qb)

    ex2:: get list of data nodes (use filters)
    ct = DataTranslator()
    ct.add_filters(filters_dict)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.get_formatted_result(qb)

    ex3:: get data node inputs
    ct = DataTranslator()
    ct.get_inputs(node_pk)
    results_type = "inputs"
    ct.add_filters(filters_dict)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.get_formatted_result(qb, results_type)

    ex3:: get data node outputs
    ct = DataTranslator()
    ct.get_outputs(node_pk)
    results_type = "outputs"
    ct.add_filters(filters_dict)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.get_formatted_result(qb, results_type)

    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "data"
    # The string name of the AiiDA class one-to-one associated to the present
    #  class
    _aiida_type = "data.Data"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = _aiida_type + '.'

    _result_type = __label__

    def __init__(self, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """

        super(DataTranslator, self).__init__(Class=self.__class__, **kwargs)
