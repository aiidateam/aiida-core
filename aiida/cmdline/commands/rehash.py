import click

from plum.util import load_class

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
@click.argument('classname', type=str, default='aiida.orm.node.Node')
def _rehash_cmd(classname):
    try_load_dbenv()
    from aiida.orm.querybuilder import QueryBuilder
    node_class = load_class(classname)
    qb = QueryBuilder()
    qb.append(node_class)
    for i, n in enumerate(qb.iterall()):
        if i % 100 == 0:
            click.echo('.', nl=False)
        n[0].rehash()
    click.echo('\nAll done! {} nodes re-hashed.'.format(i + 1))
