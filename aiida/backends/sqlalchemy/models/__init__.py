# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"

# This variable identifies the schema version of this file.
# Every time you change the schema below in *ANY* way, REMEMBER TO CHANGE
# the version here in the migration file and update migrations/__init__.py.
# See the documentation for how to do all this.
#
# The version is checked at code load time to verify that the code schema
# version and the DB schema version are the same. (The DB schema version
# is stored in the DbSetting table and the check is done in the
# load_dbenv() function).
SCHEMA_VERSION = 0.1



# This is convenience so that one can import all ORM classes from one module
# from aiida.backends.sqlalchemy.models import *
# Also, only by import
from comment import DbComment
from computer import DbComputer
from group import DbGroup
from lock import DbLock
from log import DbLog
from node import DbNode, DbLink, DbPath, DbCalcState
from settings import DbSetting
from user import DbUser
from workflow import DbWorkflow, DbWorkflowData, DbWorkflowStep

from sqlalchemy.orm import aliased, mapper
from sqlalchemy import select, func, join, and_
from sqlalchemy.sql.expression import cast
from sqlalchemy.types import Integer
from sqlalchemy.dialects.postgresql import array

node_aliased = aliased(DbNode)

walk = select([
        DbNode.id.label('ancestor_id'),
        DbNode.id.label('descendant_id'),
        cast(-1, Integer).label('depth'),
        #~ array([DbNode.id]).label('path')   #Arrays can only be used with postgres
    ]).select_from(DbNode).cte(recursive=True) #, name="incl_aliased3")


descendants_beta = walk.union_all(
    select([
            walk.c.ancestor_id,
            node_aliased.id,
            walk.c.depth + cast(1, Integer),
            #~ (walk.c.path+array([node_aliased.id])).label('path')
            #, As above, but if arrays are supported
            # This is the way to reconstruct the path (the sequence of nodes traversed)
        ]).select_from(
            join(
                node_aliased,
                DbLink,
                DbLink.output_id==node_aliased.id,
            )
        ).where(
            and_(
                DbLink.input_id == walk.c.descendant_id,
            )
        )
    )


class DbPathBeta(object):
    
    def __init__(self, start, end, depth):
        self.start = start
        self.out = end
        self.depth = depth

mapper(DbPathBeta, descendants_beta)
