from aida.common.classes.structure import Structure as BaseStructure
from aida.djsite.main.models import Structure, Element
import json

def add_structure(in_structure,title,user,dim=3,parents=None):
    """
    Adds a new structrure to the database.
    
    Args:
        in_structure: Any structure that is accepted by the __init__ method
            of the aida.common.classes.structure.Structure class (e.g. a
            Structure class, a raw structure, an ase object, ...)
        title: a string as a title
        user: a suitable django user
        dim: the dimensionality (0, 1, 2, or 3)
        parents: if provided, a list of aida.djsite.main.model.Struc to be
            set as parents of this structure.

    Returns:
        the aida.djsite.main.model.Struc Django model that was saved.
    """
    # Whatever the input format, I convert it to an internal structure
    the_structure = BaseStructure(in_structure)

    django_structure = Structure.objects.create(title=title,user=user,dim=dim,
        formula=the_structure.get_formula(),
        detail=json.dumps(the_structure.get_raw()))

    for el in tuple(set(the_structure.get_elements())):
        el_django = Element.objects.get(title=el)
        django_structure.element.add(el_django)
    
    django_structure.save()
    return django_structure
    
    
