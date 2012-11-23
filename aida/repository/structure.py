from aida.common.classes.structure import Structure as BaseStructure
from aida.djsite.main.models import Structure, Element
from aida.repository.utils.files import SandboxFolder, RepositoryFolder
import json

def add_structure(in_structure,user,dim=3):
    """
    Adds a new structrure to the database.
    
    Args:
        in_structure: Any structure that is accepted by the __init__ method
            of the aida.common.classes.structure.Structure class (e.g. a
            Structure class, a raw structure, an ase object, ...)
        user: a suitable django user
        dim: the dimensionality (0, 1, 2, or 3)

    Returns:
        the aida.djsite.main.model.Structure Django model that was saved.
    """
    # Whatever the input format, I convert it to an internal structure
    the_structure = BaseStructure(in_structure)
    
    # Create a new sandbox folder
    with SandboxFolder() as f:
        with open(f.get_file_path(filename='structure.json'), 'w') as jsonfile:
            json.dump(the_structure.get_raw(),fp=jsonfile)

        django_structure = Structure.objects.create(user=user,dim=dim,
            formula=the_structure.get_formula())

        for symbol in tuple(set(the_structure.get_elements())):
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

def get_structure(django_structure):
    """
    Get a structure from the database and/or repository and return it as
    an aida Structure object.

    Args:
        django_structure: a django Structure model

    .. todo:: Exception managing (see also comments in the code)

    Returns:
        the Structure object.
    """
    repo_folder = django_structure.get_repo_folder()
    structure_filename = repo_folder.get_filename('structure.json')

    # .. todo:: catch IOError here and raise RepositoryConsistencyError
    # (to be defined)
    with open(structure_filename) as jsonfile:
        raw_structure = json.load(jsonfile)

    # I convert the raw format into an internal structure
    # .. todo:: catch Errors while decoding the raw_structure
    the_structure = BaseStructure(raw_structure)
    
    return the_structure
    
    
