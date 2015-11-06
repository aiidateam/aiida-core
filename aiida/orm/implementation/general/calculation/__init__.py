# -*- coding: utf-8 -*-

def from_type_to_pluginclassname(typestr):
    """
    Return the string to pass to the load_plugin function, starting from
    the 'type' field of a Node.
    """
    # Fix for base class
    if typestr == "":
        typestr = "node.Node."
    if not typestr.endswith("."):
        raise DbContentError("The type name '{}' is not valid!".format(
            typestr))
    return typestr[:-1]  # Strip final dot


