# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.orm.implementation.general.calculation.inline import (
    InlineCalculation)

from aiida.orm.data import Data
from aiida.common.exceptions import ModificationNotAllowed
from aiida.common.links import LinkType
from aiida.utils.calculation import add_source_info

# TODO: right now this is a basic copy from the django version, only with the
# transaction part ported to sqla. This might be a good idea to abstract just
# the transaction part in some way, and have this be generic.



def make_inline(func):
    def wrapped_function(*args, **kwargs):
        """
        This wrapper function is the actual function that is called.
        """

        # Note: if you pass a lambda function, the name will be <lambda>; moreover
        # if you define a function f, and then do "h=f", h.__name__ will
        # still return 'f'!
        function_name = func.__name__
        if not function_name.endswith('_inline'):
            raise ValueError("The function name that is wrapped must end "
                             "with '_inline', while its name is '{}'".format(
                function_name))

        if args:
            print args
            raise ValueError("Arguments of inline function should be "
                             "passed as key=value")

        # Check the input values
        for k, v in kwargs.iteritems():
            if not isinstance(v, Data):
                raise TypeError("Input data to a wrapped inline calculation "
                                "must be Data nodes")
                # kwargs should always be strings, no need to check
                # if not isinstance(k, basestring):
                #    raise TypeError("")

        # Create the calculation (unstored)
        c = InlineCalculation()
        # Add data input nodes as links
        for k, v in kwargs.iteritems():
            c.add_link_from(v, label=k)

        # Try to get the source code
        add_source_info(c, func)

        # Run the wrapped function
        retval = func(**kwargs)

        # Check the output values
        if not isinstance(retval, dict):
            raise TypeError("The wrapped function did not return a dictionary")
        for k, v in retval.iteritems():
            if not isinstance(k, basestring):
                raise TypeError("One of the key of the dictionary returned by "
                                "the wrapped function is not a string: "
                                "'{}'".format(k))
            if not isinstance(v, Data):
                raise TypeError("One of the values (for key '{}') of the "
                                "dictionary returned by the wrapped function "
                                "is not a Data node".format(k))
            if v.is_stored:
                raise ModificationNotAllowed(
                    "One of the values (for key '{}') of the "
                    "dictionary returned by the wrapped function "
                    "is already stored! Note that this node (and "
                    "any other side effect of the function) are "
                    "not going to be undone!".format(k))

        # Add link to output data nodes
        for k, v in retval.iteritems():
            v.add_link_from(c, label=k, link_type=LinkType.RETURN)

        # I call store_all for the Inline calculation;
        # this will store also the inputs, if neeced.
        c.store_all(with_transaction=False)
        # As c is already stored, I just call store (and not store_all)
        # on each output
        for v in retval.itervalues():
            v.store(with_transaction=False)

        # Return the calculation and the return values
        return c, retval

    return wrapped_function
