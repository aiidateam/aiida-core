from aida.common.classes.structure import Sites
from aida.djsite.main.models import Structure, Element
from aida.repository.utils.files import SandboxFolder, RepositoryFolder
import json

_SITES_FILE='sites.json'

def add_structure(sites,user,dim=3):
    """
    Adds a new structrure to the database.
    
    .. todo:: decide whether to use the **kwargs method used also in the
        add_calculation function in the aida.repository.calculation module.

    Args:
        sites: Any object that is accepted by the __init__ method
            of the aida.common.classes.structure.Sites class (e.g. a
            Sites class, a raw_sites dictionary, an ase object, ...)
        user: a suitable django user
        dim: the dimensionality (0, 1, 2, or 3)

    Returns:
        the aida.djsite.main.model.Structure Django model that was saved.
    """
    # Whatever the input format, I convert it to an internal Sites object
    internal_sites = Sites(sites)
    
    # Create a new sandbox folder
    with SandboxFolder() as f:
        with open(f.get_file_path(filename=_SITES_FILE), 'w') as jsonfile:
            json.dump(internal_sites.get_raw(),fp=jsonfile)

        django_structure = Structure.objects.create(user=user,dim=dim,
            formula=internal_sites.get_formula())

        for symbol in tuple(set(internal_sites.get_elements())):
            elem_django = Element.objects.get(symbol=symbol)
            django_structure.elements.add(elem_django)

        django_structure.save()

        # I move the data in place. In case of any kind of error, I first
        # delete the entry from the database
        #
        # .. todo:: To understand if it is safer/better to use database
        # transactions, adding to this function the
        # @transaction.commit_on_success
        # decorator provided by django. This depends on whether the different
        # database backends support transactions or not.
        try:
            repo_folder = django_structure.get_repo_folder()
            repo_folder.replace_with_folder(srcdir=f.abspath,move=True)
        except Exception as e:
            django_structure.delete()
            raise e
    
    return django_structure

def get_sites(structure):
    """
    Get the Sites object connected to a structure of the database.

    Args:
        structure: a django Structure model

    .. todo:: Exception managing (see also comments in the code)

    Returns:
        the Sites object.
    """
    repo_folder = structure.get_repo_folder()
    sites_filename = repo_folder.get_filename(_SITES_FILE)

    # .. todo:: catch IOError here and raise RepositoryConsistencyError
    # (to be defined)
    with open(sites_filename) as jsonfile:
        raw_sites = json.load(jsonfile)

    # I convert the raw format into an internal structure
    # .. todo:: catch Errors while decoding the raw_sites
    sites = Sites(raw_sites)
    
    return sites
    
    
