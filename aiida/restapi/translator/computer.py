
from aiida.restapi.translator.base import BaseTranslator

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
    _aiida_type = "Computer"
    _qb_type = "computer"
    _qb_label = "computer"
    _result_type = _qb_label
    _default_projections = [ 'id',
                    'name',
                    'hostname',
                    'description',
                    'enabled',
                    'scheduler_type',
                    'transport_type',
                    'transport_params',
                    'uuid'
                  ]

    def __init__(self):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        super(ComputerTranslator, self).__init__()

