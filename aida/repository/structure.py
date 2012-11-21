from aida.common.classes.structure import Structure as BaseStructure
from aida.djsite.main.models import Structure, Element
from aida.repository.utils.files import (
    SandboxFolder, move_folder_to_repo, get_filename_from_repo)
import json

def add_structure(in_structure,user,dim=3,parents=None):
    """
    Adds a new structrure to the database.
    
    Args:
        in_structure: Any structure that is accepted by the __init__ method
            of the aida.common.classes.structure.Structure class (e.g. a
            Structure class, a raw structure, an ase object, ...)
        user: a suitable django user
        dim: the dimensionality (0, 1, 2, or 3)
        parents: if provided, a list of aida.djsite.main.model.Structure to be
            set as parents of this structure.

    Returns:
        the aida.djsite.main.model.Structure Django model that was saved.
    """
    # Whatever the input format, I convert it to an internal structure
    the_structure = BaseStructure(in_structure)
    
    # Create a new sandbox folder
    f = SandboxFolder()

    with open(f.get_file_path(filename='structure.json'), 'w') as jsonfile:
        json.dump(the_structure.get_raw(),fp=jsonfile)

    django_structure = Structure.objects.create(user=user,dim=dim,
        formula=the_structure.get_formula())

    for symbol in tuple(set(the_structure.get_elements())):
        elem_django = Element.objects.get(symbol=symbol)
        django_structure.elements.add(elem_django)
    
    django_structure.save()

    repofolder_path = move_folder_to_repo(src=f.abspath,section='structures',
                                          uuid=django_structure.uuid)
    
    return django_structure

def get_structure(django_structure):
    """
    Get a structure from the database and/or repository and return it as
    an aida Structure object.

    Args:
        django_structure: a django Structure model

    .. todo:: Probably, to be moved as a method of the structure object?

    .. todo:: Exception managing (see also comments in the code)

    Returns:
        the Structure object.
    """
    structure_filename = get_filename_from_repo('structure.json', 'structures',
         django_structure.uuid)

    # .. todo:: catch IOError here and raise RepositoryConsistencyError
    # (to be defined)
    with open(structure_filename) as jsonfile:
        raw_structure = json.load(jsonfile)

    # I convert the raw format into an internal structure
    # .. todo:: catch Errors while decoding the raw_structure
    the_structure = BaseStructure(raw_structure)
    
    return the_structure
    
    
