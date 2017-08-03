# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
class jsonb_array_length(FunctionElement):
    name = 'jsonb_array_len'

@compiles(jsonb_array_length)
def compile(element, compiler, **kw):
    """
    Get length of array defined in a JSONB column
    """
    return "jsonb_array_length(%s)" % compiler.process(element.clauses)


class array_length(FunctionElement):
    name = 'array_len'

@compiles(array_length)
def compile(element, compiler, **kw):
    """
    Get length of array defined in a JSONB column
    """
    return "array_length(%s)" % compiler.process(element.clauses)



class jsonb_typeof(FunctionElement):
    name = 'jsonb_typeof'

@compiles(jsonb_typeof  )
def compile(element, compiler, **kw):
    """
    Get length of array defined in a JSONB column
    """
    return "jsonb_typeof(%s)" % compiler.process(element.clauses)

def _get_column(colname, alias):
    """
    Return the column for the projection, if the column name is specified.
    """

    try:
        return getattr(alias, colname)
    except:
        raise InputValidationError(
            "\n{} is not a column of {}\n"
            "Valid columns are:\n"
            "{}".format(
                    colname, alias,
                    '\n'.join(alias._sa_class_manager.mapper.c.keys())
                )
        )
