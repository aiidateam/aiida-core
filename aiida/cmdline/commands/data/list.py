from aiida.orm.implementation import Group
from aiida.orm.user import User
from aiida.orm.backend import construct_backend
from aiida.cmdline.params import options
import click
from aiida.cmdline.params.options.multivalue import MultipleValueOption


_list_options = [
    click.option('-e', '--elements', type=click.STRING,
              cls=MultipleValueOption,
              default=None,
              help="Print only the objects that"
              " contain desired elements"),
    click.option('-eo', '--elements-only', type=click.STRING,
              cls=MultipleValueOption,
              default=None,
              help="Print only the objects that"
              " contain only the selected elements"),
    click.option('-f', '--formulamode',
              type=click.Choice(['hill', 'hill_compact', 'reduce', 'group', 'count', 'count_compact']),
              default='hill',
              help="Formula printing mode (if None, does not print the formula)"),
    click.option('-p', '--past-days', type=click.INT,
              default=None,
              help="Add a filter to show only datas"
              " created in the past N days"),
    click.option('-A', '--all-users', is_flag=True, default=False,
              help="show for all users, rather than only for the"
              "current user"),
    options.GROUPS(),
]

def list_options(func):
    for option in reversed(_list_options):
        func = option(func)

    return func


def query(datatype, project, past_days, group_pks, all_users):
    """
    Perform the query
    """
    from aiida.orm.querybuilder import QueryBuilder
    backend = construct_backend()

    qb = QueryBuilder()
    if all_users is False:
        user = backend.users.get_automatic_user()
        qb.append(User, tag="creator", filters={"email": user.email})
    else:
        qb.append(User, tag="creator")

    data_filters = {}
    query_past_days(data_filters, past_days)
    qb.append(datatype, tag="data", created_by="creator",
                filters=data_filters, project=project)

    group_filters = {}
    query_group(group_filters, group_pks)
    if group_filters:
        qb.append(Group, tag="group", filters=group_filters,
                    group_of="data")

    qb.order_by({datatype: {'ctime': 'asc'}})

    object_list = qb.distinct()

    return object_list.all()

def query_past_days(filters, past_days):
    """
    Subselect to filter data nodes by their age.

    :param filters: the filters to be enriched.
    :param args: a namespace with parsed command line parameters.
    """
    from aiida.utils import timezone
    import datetime
    if past_days is not None:
        now = timezone.now()
        n_days_ago = now - datetime.timedelta(days=past_days)
        filters.update({"ctime": {'>=': n_days_ago}})
    return filters

def query_group(filters, group_pks):
    """
    Subselect to filter data nodes by their group.

    :param q_object: a query object
    :param args: a namespace with parsed command line parameters.
    """
    if group_pks is not None:
        filters.update({"id": {"in": group_pks}})
 
def _list(datatype, columns, elements, elements_only, formulamode,
          past_days, groups, all_users):
    """
    List stored objects
    """
    columns_dict = {
        'ID'        : 'id',
        'Id'        : 'id',
        'Ctime'     : 'ctime',
        'Label'     : 'label',
        'Formula'   : 'attributes.formula',
        'Kinds'     : 'attributes.kinds',
        'Sites'     : 'attributes.sites',
        'Formulae'  : 'attributes.formulae',
        'Source'    : 'attributes.source',
        }
    project = [columns_dict[k] for k in columns] 
    try:
        group_pks = [g.pk for g in groups]
    except:
        group_pks=None
    return query(datatype, project, past_days, group_pks, all_users)
    
