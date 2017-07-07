# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################


from aiida.orm.implementation.calculation import InlineCalculation as _IC, \
                                                                   make_inline


class InlineCalculation(_IC):
    """
    Here I put all the attributes/method that are common to all backends
    """
    def get_desc(self):
        """
        Returns a string with infos retrieved from a InlineCalculation node's 
        properties.
        :return: description string
        """
        return "{}()".format(self.get_function_name())

def optional_inline(func):
    """
    optional_inline wrapper/decorator takes a function, which can be called
    either as wrapped in InlineCalculation or a simple function, depending
    on 'store' keyworded argument (True stands for InlineCalculation, False
    for simple function). The wrapped function has to adhere to the
    requirements by make_inline wrapper/decorator.

    Usage example::

        @optional_inline
        def copy_inline(source=None):
          return {'copy': source.copy()}

    Function ``copy_inline`` will be wrapped in InlineCalculation when
    invoked in following way::

        copy_inline(source=node,store=True)

    while it will be called as a simple function when invoked::

        copy_inline(source=node)

    In any way the ``copy_inline`` will return the same results.
    """

    def wrapped_function(*args, **kwargs):
        """
        This wrapper function is the actual function that is called.
        """
        store = kwargs.pop('store', False)

        if store:
            return make_inline(func)(*args, **kwargs)[1]
        else:
            return func(*args, **kwargs)

    return wrapped_function


