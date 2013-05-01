def conv_to_fortran(val):
    """
    val: the value to be read and converted to a Fortran-friendly string.
    """   
    # Note that bool should come before integer, because a boolean matches also
    # isinstance(...,int)
    if (isinstance(val,bool)):
        if val:
            val_str='.true.'
        else:
            val_str='.false.'
    elif (isinstance(val,int)): 
        val_str = "%d" % val
    elif (isinstance(val,float)):
        val_str = ("%18.10e" % val).replace('e','d')
    elif (isinstance(val,basestring)):
        val_str="'%s'" % val
    else:
        raise ValueError

    return val_str

def get_input_data_text(key,val):
    """
    Given a key and a value, return a string (possibly multiline for arrays)
    with the text to be added to the input file.
    
    Args:
        key: the flag name
        val: the flag value. If it is an array, a line for each element
            is produced, with variable indexing starting from 1.
            Each value is formatted using the conv_to_fortran function.
    """
    # I don't try to do iterator=iter(val) and catch TypeError because
    # it would also match strings
    if hasattr(val,'__iter__'):
        # a list/array/tuple of values
        list_of_strings = [
            "  {0}({2}) = {1}\n".format(key, conv_to_fortran(itemval),
                                        idx+1)
            for idx, itemval in enumerate(val)]
        return "".join(list_of_strings)
    else:
        # single value
        return "  {0} = {1}\n".format(key, conv_to_fortran(val))
