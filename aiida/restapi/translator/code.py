
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
    _aiida_type = "Code"
    _qb_type = "code.Code."
    _qb_label = "codes"
    _result_type = _qb_label

    def __init__(self):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        # basic query_help object
        super(CodeTranslator, self).__init__()

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
                    "help_text": "Short description on the code",
                    "type": "string",
                },
                "id": {
                    "is_display": True,
                    "display_name": "ID",
                    "help_text": "Code id",
                    "type": "integer",
                },
                "label": {
                    "is_display": True,
                    "display_name": "Label",
                    "help_text": "Code label",
                    "type": "string",
                },
                "mtime": {
                    "is_display": True,
                    "display_name": "Last modified Time",
                    "help_text": "Last modified datetime of the node",
                    "type": "datetime",
                },
                "type": {
                    "is_display": True,
                    "display_name": "Type",
                    "help_text": "Code type",
                    "type": "string",
                },
                "uuid": {
                    "is_display": False,
                    "display_name": "Unique ID",
                    "help_text": "Unique id of the code",
                    "type": "string",
                }
            },
            "ordering": [
                "id",
                "label",
                "type",
                "dbcomputer",
                "ctime",
                "mtime",
                "uuid"
            ],
        }
