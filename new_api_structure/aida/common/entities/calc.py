class Calc(object):
    """
    The class to store calculation objects.
    Properties:
    * code
    * plugin # default: code.default_plugin
    * in_datas # to undestand how to implement this, probably a
               # through table with 
               # calc_uuid, data_uuid, name
               # where name is the name of the input parameter that
               # will be used by the code plugin to distinguish between
               # different parameters.
               # Here, the name can be non-unique - one can pass more
               # than one data with name 'pseudo' for instance.
               #
               # another implementation: unique names, and we also add
               # another 'index' column, by default it is zero.
               # Possibly, save in_datas in the calculations, and out_datas
               # as a 'parent_calc' attribute of each out_data. Still,
               # the through table is needed for efficiency IMHO.

    Read also some comments on how to save/create/copy objects in the 
    Data class.

    Methods [names to be modified to be the same of the Data class]:
    * store()
    * set_backend()
    * get_status()
    * get_out_data()
    * get_in_data()
    * set_in_data('name', DataObject) # To append a new input parameter
                                      # before launching the calculation
    Example:
    c = Calc()
    s = Data(type='structure', ...)
    c.set_in_data('cell', s)
    """
    pass
