


from sqlalchemy import (
    Column,ForeignKey, UniqueConstraint,create_engine,
    Integer, String, DateTime, Float, Boolean, Text,
    select, func, join, and_, or_, not_, except_
)

from sqlalchemy.orm import (
    relationship,
    backref,
    column_property,
    sessionmaker,
    foreign, mapper, aliased
)


from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql.expression import FunctionElement

from sqlalchemy.ext.compiler import compiles

class jsonb_array_length(FunctionElement):
    name = 'jsonb_array_len'

@compiles(jsonb_array_length)
def compile(element, compiler, **kw):
    """
    Compile a function that postgresql has implemented, but SQLAlchemy has not
    """
    return "jsonb_array_length(%s)" % compiler.process(element.clauses)
