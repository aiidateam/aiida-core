from aida.djsite.main.models import Calculation
from aida.repository.utils.files import SandboxFolder, RepositoryFolder
import json

_INPARAMS_FILE = 'inparams.json'

def add_calculation(*args, **kwargs):
    """
    I create a calculation, storing also the input parameters in the
    local repository.

    .. todo:: Add also the API for validating the input_params

    Args:
        input_params: a dictionary with the input parameters of the
            calculation, using the format described by the input plugin
            of the code.
        Any other parameter is passed to the create function of the
            aida.djsite.main.models.Calculation table.
    """

    # I don't need to copy kwargs, it is copied anyway by python
    # when calling the function. If input_params is not provided, it
    # is replaced by an empty dictionary
    input_params = kwargs.pop('input_params',{}) 

    # Possibly: validation of input_data here, depending on the calculation

    # I store the input parameters in the calculation folder
    with SandboxFolder() as f:
        with open(f.get_file_path(filename=_INPARAMS_FILE), 'w') as jsonfile:
            json.dump(input_params,fp=jsonfile)

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
    
    return calc

def get_input_params(django_calc):
    """
    Get the input parameters associated with the calculation.

    .. todo:: Understand if the exception management is sufficient.

    Args:
        django_calc: a django calculation model

    Returns:
        A dictionary with the input parameters. 
        If no file is found, an empty dictionary is returned
    """
    repo_folder = django_calc.get_repo_folder()
    inparams_filename = repo_folder.get_filename(_INPARAMS_FILE)

    try:
        with open(inparams_filename) as jsonfile:
            input_params = json.load(jsonfile)
    except IOError: # No file found, or problems reading file
        input_params = {}
    # I don't catch ValueErrors for the moment (can occur if the json is not
    # valid)

    return input_params
