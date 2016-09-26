
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
    _aiida_type = "Group"
    _db_type = "group"
    _qb_label = "groups"
    _result_type = _qb_label
    _default_projections = custom_schema['columns'][_qb_label]

    def __init__(self):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        super(GroupTranslator, self).__init__()

