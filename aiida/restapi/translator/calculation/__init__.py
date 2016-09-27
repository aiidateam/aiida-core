# -*- coding: utf-8 -*-

__copyright__ = u"""Copyright (c), This file is part of
the AiiDA platform. For further information please visit
http://www.aiida.net/.. All rights reserved."""
__license__ = "MIT license, see LICENSE.txt file"
__authors__ = "The AiiDA team."
__version__ = "0.7.0"


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

    def __init__(self):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        # basic query_help object
        super(CalculationTranslator, self).__init__()

    def get_schema(self):
        return {
            "fields": {
                "ctime": {
                    "is_display": True,
                    "display_name": "Creation Time",
                    "help_text": "Created at",
                    "type": "datetime",
                },
                "dbcomputer": {
                    "is_display": False,
                    "display_name": "Computer",
                    "help_text": "Computer id on which job was submitted",
                    "type": "related",
                },
                "description": {
                    "is_display": False,
                    "display_name": "Description",
                    "help_text": "Short description on the calculation",
                    "type": "string",
                },
                "id": {
                    "is_display": True,
                    "display_name": "ID",
                    "help_text": "Calculation id",
                    "type": "integer",
                },
                "label": {
                    "is_display": False,
                    "display_name": "Label",
                    "help_text": "Calculation label",
                    "type": "string",
                },
                "mtime": {
                    "is_display": True,
                    "display_name": "Last modified Time",
                    "help_text": "Last modified datetime of the node",
                    "type": "datetime",
                },
                "state": {
                    "is_display": True,
                    "display_name": "State",
                    "help_text": "The AiiDA state of the calculation.",
                    "type": "string",
                    "valid_choices": {
                        "COMPUTED": {
                            "doc": "Calculation in the AiiDA state 'COMPUTED'"
                        },
                        "FAILED": {
                            "doc": "Calculation in the AiiDA state 'FAILED'"
                        },
                        "FINISHED": {
                            "doc": "Calculation in the AiiDA state 'FINISHED'"
                        },
                        "IMPORTED": {
                            "doc": "Calculation in the AiiDA state 'IMPORTED'"
                        },
                        "NEW": {
                            "doc": "Calculation in the AiiDA state 'NEW'"
                        },
                        "PARSING": {
                            "doc": "Calculation in the AiiDA state 'PARSING'"
                        },
                        "PARSINGFAILED": {
                            "doc": "Calculation in the AiiDA state 'PARSINGFAILED'"
                        },
                        "RETRIEVALFAILED": {
                            "doc": "Calculation in the AiiDA state 'RETRIEVALFAILED'"
                        },
                        "RETRIEVING": {
                            "doc": "Calculation in the AiiDA state 'RETRIEVING'"
                        },
                        "SUBMISSIONFAILED": {
                            "doc": "Calculation in the AiiDA state 'SUBMISSIONFAILED'"
                        },
                        "SUBMITTING": {
                            "doc": "Calculation in the AiiDA state 'SUBMITTING'"
                        },
                        "TOSUBMIT": {
                            "doc": "Calculation in the AiiDA state 'TOSUBMIT'"
                        },
                        "WITHSCHEDULER": {
                            "doc": "Calculation in the AiiDA state 'WITHSCHEDULER'"
                        }
                    }
                },
                "type": {
                    "is_display": True,
                    "display_name": "Type",
                    "help_text": "Calculation type",
                    "type": "string",
                },
                "uuid": {
                    "is_display": False,
                    "display_name": "Unique ID",
                    "help_text": "Unique id of the calculation",
                    "type": "string",
                }
            },
            "ordering": [
                "id",
                "label",
                "type",
                "state",
                "dbcomputer",
                "ctime",
                "mtime",
                "uuid"
            ]
        }
