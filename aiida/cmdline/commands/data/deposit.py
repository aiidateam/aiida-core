import click
from aiida.cmdline.params import arguments

_deposit_options = [
     click.option('-d', '--database', 'database',
                  type=click.Choice(['tcod']),
                  default='tcod',
                  help="Label of the database for deposition."),
     click.option('--deposition-type',
                  type=click.Choice(['published', 'prepublication', 'personal']),
                  default='published',
                  help="Type of the deposition."),
     click.option('-u', '--username', type=click.STRING,
                  default=None,
                  help="Depositor's username."),
     click.option('-p', '--password', is_flag=True,
                  default=False,
                  help="Depositor's password."),
     click.option('--user-email', type=click.STRING,
                  default=None,
                  help="Depositor's e-mail address."),
     click.option('--title', type=click.STRING,
                  default=None,
                  help="Title of the publication."),
     click.option('--author-name', type=click.STRING,
                  default=None,
                  help="Full name of the publication author."),
     click.option('--author-email', type=click.STRING,
                  default=None,
                  help="E-mail address of the publication author."),
     click.option('--url', type=click.STRING,
                  default=None,
                  help="URL of the deposition API."),
     click.option('--code', type=click.STRING,
                  default=None,
                  help="Label of the code to be used for the deposition."
                       " Default: cif_cod_deposit."),
     click.option('--computer', type=click.STRING,
                  default=None,
                  help="Name of the computer to be used for deposition."),
     click.option('--replace', type=click.INT,
                  default=None,
                  help="ID of the structure to be redeposited (replaced), if any."),
     click.option('-m', '--message', type=click.STRING,
                  default=None,
                  help="Description of the change (relevant for redepositions only)."),
     click.option('--reduce-symmetry/--no-reduce-symmetry', 'reduce_symmetry',
                  is_flag=True,
                  default=None,
                  help='Do (default) or do not perform symmetry reduction.'),
     click.option('--parameter-data', type=click.INT,
                  default=None,
                  help="ID of the ParameterData to be exported alongside the"
                       " StructureData instance. By default, if StructureData"
                       " originates from a calculation with single"
                       " ParameterData in the output, aforementioned"
                       " ParameterData is picked automatically. Instead, the"
                       " option is used in the case the calculation produces"
                       " more than a single instance of ParameterData."),
     click.option('--dump-aiida-database/--no-dump-aiida-database',
                  'dump_aiida_database', is_flag=True,
                  default=None,
                  help='Export (default) or do not export AiiDA database to the CIF file.'),
     click.option('--exclude-external-contents/--no-exclude-external-contents', 'exclude_external_contents', is_flag=True,
                  default=None,
                  help='Do not (default) or do save the contents for external resources even if URIs are provided'),
     click.option('--gzip/--no-gzip', 'gzip', is_flag=True,
                  default=None,
                  help='Do or do not (default) gzip large files.'),
     click.option('--gzip-threshold', type=click.INT,
                  default=None,
                  help="Specify the minimum size of exported file which should"
                       " be gzipped."),
     arguments.NODE(),
]

def deposit_options(func):
    for option in reversed(_deposit_options):
        func = option(func)

    return func


from aiida.cmdline import delayed_load_node as load_node

def deposit_tcod(node, deposit_type, parameter_data=None, **kwargs):
    """
    Deposition plugin for TCOD.
    """
    from aiida.tools.dbexporters.tcod import deposit
    parameters = None
    if parameter_data is not None:
        from aiida.orm import DataFactory
        ParameterData = DataFactory('parameter')
        parameters = load_node(parameter_data, sub_class=ParameterData)

    return deposit(node, deposit_type, parameters, **kwargs)
