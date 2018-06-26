from aiida.cmdline.utils import echo
from aiida.backends.utils import load_dbenv, is_dbenv_loaded


if not is_dbenv_loaded():
    load_dbenv()

def _export(node, output_fname, fileformat, other_args={}, overwrite=False):
    """
    Depending on the parameters, either print the (single) output file on screen, or
    stores the file(s) on disk.

    :param node: the Data node to print or store on disk
    :param output_fname: The filename to store the main file. If empty or None, print
            instead
    :param fileformat: a string to pass to the _exportstring method
    :param other_args: a dictionary with additional kwargs to pass to _exportstring
    :param overwrite: if False, stops if any file already exists (when output_fname
            is not empty

    :note: this function calls directly sys.exit(1) when an error occurs (or e.g. if
        check_overwrite is True and a file already exists).
    """
    print other_args
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
        echo.echo_critical("verdi: ERROR, probably a parameter is not supported by the specific format.\nError message: {}".format(message))
