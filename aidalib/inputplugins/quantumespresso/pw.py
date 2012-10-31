from aidalib.inputplugins.exceptions import InputValidationError
import json

def create_calc_input(calc, infile_dir):
    """
    Create the necessary input files in infile_dir for calculation calc.
    
    Args:
        calc: the calculation object for which we want to create the 
            input file structure.
        infile_dir: the directory where we want to create the files.

    Returns:
        retrieve_output: a list of files, directories or patterns to be
            retrieved from the cluster scratch dir and copied in the
            permanent aida repository.
        cmdline_params: a (possibly empty) string with the command line
            parameters to pass to the code.
        stdin: a string with the file name to be used as standard input,
            or None if no stdin redirection is required. 
            Note: if you want to pass a string, create a file with the 
            string and use that file as stdin.
        stdout: a string with the file name to which the standard output
            should be redirected, or None if no stdout redirection is
            required. 
        stderrt: a string with the file name to which the standard error
            should be redirected, or None if no stderr redirection is
            required. 
        preexec: a (possibly empty) string containing commands that may be
            required to be run before the code executes.
        postexec: a (possibly empty) string containing commands that may be
            required to be run after the code has executed.
    """
    retrieve_output = ['aida.out', 'out/data-file.xml'] 
    cmdline_params = "" # possibly -npool and similar
    stdin = 'aida.in'
    stdout = 'aida.out'
    stderr = None
    preexec = ""
    postexec = ""

#    try:
#        input_data = json.loads(calc.data)
        

    return (retrieve_output, cmdline_params, stdin, stdout, stderr,
            preexec, postexec)

