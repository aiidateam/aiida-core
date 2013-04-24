from aida.djsite.main.models import Calculation
from aida.repository.utils.files import SandboxFolder, RepositoryFolder
import json

_INDATA_FILE = 'input_data.json'

def add_calculation(*args, **kwargs):
    """
    I create a calculation, storing also the input parameters in the
    local repository.

    Note that many to many relationships are added by this function to the 
    database for what concerns structures and potentials.

    .. todo:: Add also the API for validating the input_data

    .. todo:: add also dependencies here!

    Args:
        input_params: a dictionary with the input parameters of the
            calculation, using the format described by the input plugin
            of the code.
        structure_list: a (sorted) list of structures to be attached to the
            calculation. The order may be used by the input plugin.
        potential_list: a (sorted) list of potentials to be attached to the
            calculation. The order may be used by the input plugin.
        Any other parameter is passed to the create function of the
            aida.djsite.main.models.Calculation table.
    """
    input_data = {}

    # I don't need to copy kwargs, it is copied anyway by python
    # when calling the function. If input_params is not provided, it
    # is replaced by an empty dictionary
    input_data['input_params'] = kwargs.pop('input_params',{}) 

    # Possibly: validation of input_data here, depending on the calculation

    # Retrieve further data
    structure_list = kwargs.pop('structure_list',[])     
    potential_list = kwargs.pop('potential_list',[])     
    input_data['structure_list'] = [s.uuid for s in structure_list]
    input_data['potential_list'] = [s.uuid for s in potential_list]

    # I store the input parameters in the calculation folder
    with SandboxFolder() as f:
        with open(f.get_filename(filename=_INDATA_FILE), 'w') as jsonfile:
            json.dump(input_data,fp=jsonfile)

        # I create the calculation using the remaining kwargs
        calc = Calculation.objects.create(*args, **kwargs)

        # If we are here, the calculation was saved in the DB. So we can
        # retrieve the UUID and store the input_data in the local repository.
        # As discussed also in aida.repository.structure.add_structure,
        # understand if it is safer/better to use database
        # transactions
        try:
            repo_folder = calc.get_repo_folder()
            repo_folder.replace_with_folder(srcdir=f.abspath,move=True)
        except Exception as e:
            calc.delete()
            raise e

    # I add the M2M relationships
    calc.instructures.add(*structure_list)
    calc.inpotentials.add(*potential_list)
    
    return calc

def get_input_data(django_calc):
    """
    Get the input data associated with the calculation.

    .. todo:: Understand if the exception management is sufficient. Maybe
        it is better to let the exception be raised?

    Args:
        django_calc: a django calculation model

    Returns:
        A dictionary with the input parameters. 
        If no file is found, an empty dictionary is returned
    """
    repo_folder = django_calc.get_repo_folder()
    indata_filename = repo_folder.get_filename(_INDATA_FILE)

    try:
        with open(indata_filename) as jsonfile:
            input_data = json.load(jsonfile)
    except IOError: # No file found, or problems reading file
        input_data = {}
    # I don't catch ValueErrors for the moment (can occur if the json is not
    # valid)

    return input_data
