from aiida.cmdline.utils import echo
from aiida.backends.utils import load_dbenv, is_dbenv_loaded
import click
from aiida.cmdline.params import arguments
from aiida.cmdline.params import options


_export_options = [
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
    click.option('--gzip/--no-gzip', is_flag=True,
                 default=None,
                 help='Do or do not (default) gzip large files.'),
    click.option('--gzip-threshold', type=click.INT,
                 default=None,
                 help="Specify the minimum size of exported file which should"
                      " be gzipped."),
    click.option('-o', '--output', type=click.STRING,
                 default=None,
                 help="If present, store the output directly on a file "
                      "with the given name. It is essential to use this option "
                      "if more than one file needs to be created."),
    options.FORCE(help="If passed, overwrite files without checking."),
    arguments.NODE(),
]

def export_options(func):
    for option in reversed(_export_options):
        func = option(func)

    return func


if not is_dbenv_loaded():
    load_dbenv()

def _export(node, output_fname, fileformat, other_args={}, overwrite=False):
    """
    Depending on the parameters, either print the (single) output file on
    screen, or store the file(s) on disk.

    :param node: the Data node to print or store on disk
    :param output_fname: The filename to store the main file. If empty or
    None, print instead
    :param fileformat: a string to pass to the _exportstring method
    :param other_args: a dictionary with additional kwargs to pass to _exportstring
    :param overwrite: if False, stops if any file already exists (when output_fname
            is not empty

    :note: this function calls directly sys.exit(1) when an error occurs (or e.g. if
        check_overwrite is True and a file already exists).
    """
    try:
        if output_fname:
            try:
                node.export(
                    output_fname, fileformat=fileformat, overwrite=overwrite, **other_args)
            except OSError as e:
                echo.echo_critical ("verdi: ERROR while exporting file:\n" + e.message)
        else:
            filetext, extra_files = node._exportstring(
                fileformat, main_file_name=output_fname, **other_args)
            if extra_files:
                echo.echo_critical ("This format requires to write more than one file.\n"
                                    "You need to pass the -o option to specify a file name.")
            else:
                print filetext
    except TypeError as e:
        # This typically occurs for parameters that are passed down to the
        # methods in, e.g., BandsData, but they are not accepted
        echo.echo_critical("verdi: ERROR, probably a parameter is not "
                           "supported by the specific format.\nError "
                           "message: {}".format(e.message))
