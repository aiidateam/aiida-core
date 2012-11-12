from aida.common.classes.structure import Structure
from aida.djsite.main.models import Struc, Element
import json

def add_structure(in_struc,title,user,dim=3,parents=None):
    """
    Adds a new structrure to the database.
    
    Args:
        structure: Any structure that is accepted by the __init__ method
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
    the_struc = Structure(in_struc)

    django_struc = Struc.objects.create(title=title,user=user,dim=dim,
                                        formula=the_struc.get_formula(),
                                        detail=json.dumps(the_struc.get_raw()))

    for el in tuple(set(the_struc.get_elements())):
        el_django = Element.objects.get(title=el)
        django_struc.element.add(el_django)
    
    django_struc.save()
    return django_struc
    
    
