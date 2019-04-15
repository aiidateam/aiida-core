# -*- coding: utf-8 -*-

from aiida.backends.sqlalchemy import session

from aiida.orm.implementation.general.calculation.inline import InlineCalculation

from aiida.orm.data import Data
from aiida.common.exceptions import ModificationNotAllowed

# TODO: right now this is a basic copy from the django version, only with the
# transaction part ported to sqla. This might be a good idea to abstract just
# the transaction part in some way, and have this be generic.

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__authors__ = "The AiiDA team."
__version__ = "0.6.0.1"

def make_inline(func):

    def wrapped_function(*args, **kwargs):
        """
        This wrapper function is the actual function that is called.
        """
        import inspect

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
                #kwargs should always be strings, no need to check
                #if not isinstance(k, basestring):
                #    raise TypeError("")

        # Create the calculation (unstored)
        c = InlineCalculation()
        # Add data input nodes as links
        for k, v in kwargs.iteritems():
            c._add_link_from(v, label=k)

        # Try to get the source code
        source_code, first_line = inspect.getsourcelines(func)
        try:
            with open(inspect.getsourcefile(func)) as f:
                source = f.read()
        except IOError:
            source = None
        c._set_attr("source_code", "".join(source_code))
        c._set_attr("first_line_source_code", first_line)
        c._set_attr("source_file", source)
        c._set_attr("function_name", function_name)

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
            if v._is_stored:
                raise ModificationNotAllowed(
                    "One of the values (for key '{}') of the "
                    "dictionary returned by the wrapped function "
                    "is already stored! Note that this node (and "
                    "any other side effect of the function) are "
                    "not going to be undone!".format(k))

        # Add link to output data nodes
        for k, v in retval.iteritems():
            v._add_link_from(c, label=k)

        with session.begin(subtransactions=True):
            # I call store_all for the Inline calculation;
            # this will store also the inputs, if neeced.
            c.store_all(with_transaction=False)
            # As c is already stored, I just call store (and not store_all)
            # on each output
            for v in retval.itervalues():
                v.store(with_transaction=False)

        # Return the calculation and the return values
        return (c, retval)

    return wrapped_function
