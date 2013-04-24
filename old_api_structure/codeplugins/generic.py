"""
This module implements a generic input plugin, which should be flexible
enough for a generic code (to be used mainly for new codes or codes under
development, for which a suitable plugin doesn't exist or has to written yet).
"""

def create_calc_input(calc, infile_dir):
    """
    Creates the calculation input for a generic code for which there
    is no specific plugin.
    """
    raise NotImplementedError
