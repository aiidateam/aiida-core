from aiida.orm.querybuilder import QueryBuilder
from aiida.orm.implementation import Group
from aiida.orm.user import User
from aiida.orm.backend import construct_backend
from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.cmdline.utils import echo
from aiida.cmdline.params import options
import click
from aiida.cmdline.params.options.multivalue import MultipleValueOption


if not is_dbenv_loaded():
    load_dbenv()


_list_options = [
    click.option('-e', '--elements', type=click.STRING,
              cls=MultipleValueOption,
              default=None,
              help="Print all bandsdatas from structures "
              "containing desired elements"),
    click.option('-eo', '--elements-only', type=click.STRING,
              cls=MultipleValueOption,
              default=None,
              help="Print all bandsdatas from structures "
              "containing only the selected elements"),
    click.option('-f', '--formulamode',
              type=click.Choice(['hill', 'hill_compact', 'reduce', 'group', 'count', 'count_compact']),
              default='hill',
              help="Formula printing mode (if None, does not print the formula)"),
    click.option('-p', '--past-days', type=click.INT,
              default=None,
              help="Add a filter to show only bandsdatas"
              " created in the past N days"),
    click.option('-A', '--all-users', is_flag=True, default=False,
              help="show groups for all users, rather than only for the"
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
    backend = construct_backend()

    qb = QueryBuilder()
    if all_users is False:
        user = backend.users.get_automatic_user()
        qb.append(User, tag="creator", filters={"email": user.email})
    else:
        qb.append(User, tag="creator")

    data_filters = dict()
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

    entry_list = []
    for [id, ctime, label, formula] in object_list.all():
        entry_list.append([str(id), str(ctime), str(label), str(formula)])
    return entry_list

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
    column_length = 19
    columns_dict = {
        'ID'        : 'id',
        'Ctime'     : 'ctime',
        'Label'     : 'label',
        'Formula'   : 'attributes.formula'
        }
    project = [columns_dict[k] for k in columns] 
    try:
        group_pks = [g.pk for g in groups]
    except:
        group_pks=None
    entry_list = query(datatype, project, past_days, group_pks, all_users)
    vsep = " "
    if entry_list:
        to_print = ""
        to_print += vsep.join([ s.ljust(column_length)[:column_length] for s in columns]) + "\n"
        for entry in sorted(entry_list, key=lambda x: int(x[0])):
            to_print += vsep.join([ s.ljust(column_length)[:column_length] for s in entry]) + "\n"
        echo.echo(to_print)
    else:
        echo.echo_warning("No nodes of type {} where found in the database".format(datatype))
