
from aiida.restapi.translator.base import BaseTranslator

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
    _aiida_type = "User"
    _qb_type = "user"
    _qb_label= "users"
    _result_type = _qb_label
    _default_projections = [ 'id',
                    'first_name',
                    'last_name',
                    'email',
                    'institution',
                    'date_joined',
                    'last_login',
                    #'is_superuser',
                    'is_active',
                  ]

    def __init__(self):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        super(UserTranslator, self).__init__()

