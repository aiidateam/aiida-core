import sys

import click

from plumpy.utils import load_object as load_class
from plumpy.exceptions import ClassNotFoundException

from aiida import try_load_dbenv
from aiida.cmdline.baseclass import VerdiCommand


class Rehash(VerdiCommand):
    """
    Re-hash all nodes.
    """
    def run(self, *args):
        ctx = _rehash_cmd.make_context('rehash', list(args))
        with ctx:
            _rehash_cmd.invoke(ctx)

    def complete(self, subargs_idx, subargs):
        """
        No completion after 'verdi rehash'.
        """
        print ""

@click.command('rehash')
@click.option('--all', '-a', is_flag=True, help='Rehash all nodes of the given Node class.')
@click.option('--class-name', type=str, default='aiida.orm.node.Node', help='Restrict nodes which are re-hashed to instances of this class.')
@click.argument('pks', type=int, nargs=-1)
def _rehash_cmd(all, class_name, pks):
    try_load_dbenv()
    from aiida.orm.querybuilder import QueryBuilder

    # Get the Node class to match
    try:
        node_class = load_class(class_name)
    except ClassNotFoundException:
        click.echo("Could not load class '{}'.\nAborted!".format(class_name))
        sys.exit(1)

    # Add the filters for the class and PKs.
    qb = QueryBuilder()
    qb.append(node_class, tag='node')
    if pks:
        qb.add_filter('node', {'id': {'in': pks}})
    else:
        if not all:
            click.echo("Nothing specified, nothing re-hashed.\nExplicitly specify the PK of the nodes, or use '--all'.")
            return

    if not qb.count():
        click.echo('No matching nodes found.')
        return
    for i, (node,) in enumerate(qb.iterall()):
        if i % 100 == 0:
            click.echo('.', nl=False)
        node.rehash()
    click.echo('\nAll done! {} node(s) re-hashed.'.format(i + 1))
