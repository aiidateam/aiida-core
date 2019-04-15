# -*- coding: utf-8 -*-
"""
Imports used for the QueryBuilder.
See
:func:`querybuilder_base.QueryBuilderBase`,
:func:`querybuilder_django.QueryBuilder`,
:func:`querybuilder_sa.QueryBuilder`,
for details of implementation of querying functionalities.

SQLAlchemy's functionalities can be extended using SA's FunctionElement class
and @compiles decorator.
Compile a function that postgresql has implemented, but SQLAlchemy has not
"""

from sqlalchemy import (
    Column, Table, ForeignKey, UniqueConstraint,create_engine,
    select, func, join, and_, or_, not_, except_, case, exists,
    text
)

from sqlalchemy.types import (
    Integer, String, DateTime, Float, Boolean, Text,
)
from sqlalchemy.orm import (
    relationship,
    backref,
    column_property,
    sessionmaker,
    foreign, mapper, aliased
)
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import Cast
from sqlalchemy.dialects.postgresql import UUID, JSONB
# TO COMPILE MY OWN FUNCTIONALITIES:
from sqlalchemy.sql.expression import FunctionElement, cast
from sqlalchemy.ext.compiler import compiles

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0.1"

class jsonb_array_length(FunctionElement):
    name = 'jsonb_array_len'

@compiles(jsonb_array_length)
def compile(element, compiler, **kw):
    """
    Get length of array defined in a JSONB column
    """
    return "jsonb_array_length(%s)" % compiler.process(element.clauses)

class jsonb_typeof(FunctionElement):
    name = 'jsonb_typeof'

@compiles(jsonb_typeof  )
def compile(element, compiler, **kw):
    """
    Get length of array defined in a JSONB column
    """
    return "jsonb_typeof(%s)" % compiler.process(element.clauses)
