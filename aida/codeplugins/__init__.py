import re
import importlib
import sys

def create_calc_input(calc_id, infile_dir):
    """
    Creates all necessary input files for the calculation with ID
    calc_id. 
    
    Args:
        calc_id: the id of the calculation in the database.
            Note that the calculation and all related M2M fields should
            be already set in the database.
            The advantage of asking for the calc_id is that (in the 
            future) the same function can be used also on the client side,
            and the data from the database are retrieved through API
            requests).
        infile_dir: The files are generated in the directory infile_dir.
            The directory must already exist, and should be empty 
            (files may be overwritten). The advantage of having this
            parameter is that this function can be used also before
            submitting the calculation to verify that the
            automatically-generated input file is as expected.
    """
    ### TODO: in the future, do not depend on aidadb but call suitable
    ### routines, independent of if we are on the server or on the client
    # I import it here, otherwise if done above it generates a circular
    # dependency
    from aida.djsite.main.models import Calc
    calc = Calc.objects.get(id=calc_id)
    
    input_plugin_name = _get_plugin_module_name(calc.code.type.title)
    input_plugin = importlib.import_module(input_plugin_name,
                                           package='aida.codeplugins')
    
    return input_plugin.create_calc_input(calc, infile_dir)
      
def _get_plugin_module_name(code_type_title):
    """
    Converts the code type title, as retrieved from the CodeType table
    in the database, to a suitable module name to be imported.
    
    Rules (applied in this order):
    1. everything is converted to lower case
    2. any character which is not a letter, a number, a underscore or
       a / is removed (spaces included)
    3. slashes (/) are converted to dots. Note that also groups of
       slashes (///) are converted to a single dot. 
    4. adds a dot in front of everything to indicate a relative import.

    Args:
        code_type_title: the title of the code type as found in the 
            CodeType table

    Returns: 
        a string with the module name.

    >>> _get_plugin_module_name('Quantum Espresso/pw')
    quantumespresso.pw
    """
    module_name = code_type_title.lower()
    leave_only_allowed_chars = re.compile('[^0-9a-z_/]+')
    module_name = leave_only_allowed_chars.sub('',module_name)

    put_dots = re.compile('/+')
    module_name = put_dots.sub('.',module_name)

    return '.'+module_name
