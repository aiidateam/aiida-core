###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to manage nodes for the SQLA backend."""

from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import CheckConstraint, Column, UniqueConstraint
from sqlalchemy.sql.schema import ForeignKey, Index
from sqlalchemy.types import DateTime, Integer, String, Text

from aiida.common import timezone
from aiida.common.utils import get_new_uuid
from aiida.storage.psql_dos.models.base import Base


class DbNode(Base):
    """Database model to store data for :py:class:`aiida.orm.Node`.

    Each node can be categorized according to its ``node_type``,
    which indicates what kind of data or process node it is.
    Additionally, process nodes also have a ``process_type`` that further indicates what is the specific plugin it uses.

    Nodes can also store two kind of properties:

    - ``attributes`` are determined by the ``node_type``,
      and are set before storing the node and can't be modified afterwards.
    - ``extras``, on the other hand,
      can be added and removed after the node has been stored and are usually set by the user.

    Ownership (owned data containers, ``orm-container-spec.md`` sections 2-3):

    - ``owner_id`` is an indexed, nullable FK to ``db_dbnode.id``. NULL
      means a standalone node; non-null means an exclusively owned node.
      There is no separate ownership-mode flag.
    - ``container_element_type`` stores the container's locked element
      ``node_type`` identifier, or NULL when unset (a container that never
      held an element, which may still be stored). Once established it
      stays locked, including after removing every element.
    - Membership edges live in ``db_dbmembership`` and must agree with
      ``owner_id``; both are created atomically in one transaction and
      are immutable once stored.

    """

    __tablename__ = 'db_dbnode'

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=get_new_uuid, nullable=False, unique=True)
    node_type = Column(String(255), default='', nullable=False, index=True)
    process_type = Column(String(255), index=True)
    label = Column(String(255), nullable=False, default='', index=True)
    description = Column(Text(), nullable=False, default='')
    ctime = Column(DateTime(timezone=True), default=timezone.now, nullable=False, index=True)
    mtime = Column(DateTime(timezone=True), default=timezone.now, onupdate=timezone.now, nullable=False, index=True)
    attributes = Column(JSONB, default=dict)
    extras = Column(JSONB, default=dict)
    repository_metadata = Column(JSONB, nullable=False, default=dict)
    dbcomputer_id = Column(
        Integer,
        ForeignKey('db_dbcomputer.id', deferrable=True, initially='DEFERRED', ondelete='RESTRICT'),
        nullable=True,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey('db_dbuser.id', deferrable=True, initially='DEFERRED', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    # NOTE: the default NO ACTION (not RESTRICT) is deliberate. RESTRICT cannot be deferred: SQLite processes
    # RESTRICT immediately even for deferred constraints and PostgreSQL forbids deferring it, which would make
    # whole-subtree single-statement deletes impossible. NO ACTION keeps the same safeguard (deleting a referenced
    # row while referencers remain fails) with end-of-transaction timing under the deferred constraint.
    owner_id = Column(
        Integer,
        ForeignKey('db_dbnode.id', deferrable=True, initially='DEFERRED'),
        nullable=True,
        index=True,
    )
    container_element_type = Column(String(255), nullable=True, index=True)

    # TODO SP: The 'passive_deletes=all' argument here means that SQLAlchemy
    # won't take care of automatic deleting in the DbLink table. This still
    # isn't exactly the same behaviour than with Django. The solution to
    # this is probably a ON DELETE inside the DB. On removing node with id=x,
    # we would remove all link with x as an output.

    dbcomputer = relationship('DbComputer', backref=backref('dbnodes', passive_deletes='all', cascade='merge'))
    user = relationship(
        'DbUser',
        backref=backref(
            'dbnodes',
            passive_deletes='all',
            cascade='merge',
        ),
    )

    # outputs via db_dblink table
    outputs_q = relationship(
        'DbNode',
        secondary='db_dblink',
        primaryjoin='DbNode.id == DbLink.input_id',
        secondaryjoin='DbNode.id == DbLink.output_id',
        backref=backref('inputs_q', passive_deletes=True, lazy='dynamic'),
        lazy='dynamic',
        passive_deletes=True,
    )

    __table_args__ = (
        Index(
            'ix_pat_db_dbnode_label', label, postgresql_using='btree', postgresql_ops={'label': 'varchar_pattern_ops'}
        ),
        Index(
            'ix_pat_db_dbnode_node_type',
            node_type,
            postgresql_using='btree',
            postgresql_ops={'node_type': 'varchar_pattern_ops'},
        ),
        Index(
            'ix_pat_db_dbnode_process_type',
            process_type,
            postgresql_using='btree',
            postgresql_ops={'process_type': 'varchar_pattern_ops'},
        ),
    )

    @property
    def outputs(self):
        return self.outputs_q.all()

    @property
    def inputs(self):
        return self.inputs_q.all()

    def get_simple_name(self, invalid_result=None):
        """Return a string with the last part of the type name.

        If the type is empty, use 'Node'.
        If the type is invalid, return the content of the input variable
        ``invalid_result``.

        :param invalid_result: The value to be returned if the node type is
            not recognized.
        """
        thistype = self.node_type
        # Fix for base class
        if thistype == '':
            thistype = 'node.Node.'
        if not thistype.endswith('.'):
            return invalid_result
        thistype = thistype[:-1]  # Strip final dot
        return thistype.rpartition('.')[2]

    @property
    def pk(self):
        return self.id

    def __str__(self):
        """Get string object out of DbNode object."""
        simplename = self.get_simple_name(invalid_result='Unknown')
        # node pk + type
        if self.label:
            return f'{simplename} node [{self.pk}]: {self.label}'
        return f'{simplename} node [{self.pk}]'


class DbLink(Base):
    """Database model to store links between :py:class:`aiida.orm.Node`.

    Each entry in this table contains not only the ``id`` information of the two nodes that are linked,
    but also some extra properties of the link themselves.
    This includes the ``type`` of the link (see the :ref:`topics:provenance:concepts` section for all possible types)
    as well as a ``label`` which is more specific and typically determined by
    the procedure generating the process node that links the data nodes.
    """

    __tablename__ = 'db_dblink'

    id = Column(Integer, primary_key=True)
    input_id = Column(
        Integer, ForeignKey('db_dbnode.id', deferrable=True, initially='DEFERRED'), nullable=False, index=True
    )
    output_id = Column(
        Integer,
        ForeignKey('db_dbnode.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
        nullable=False,
        index=True,
    )

    # https://docs.sqlalchemy.org/en/14/errors.html#relationship-x-will-copy-column-q-to-column-p-which-conflicts-with-relationship-s-y
    input = relationship('DbNode', primaryjoin='DbLink.input_id == DbNode.id', overlaps='inputs_q,outputs_q')
    output = relationship('DbNode', primaryjoin='DbLink.output_id == DbNode.id', overlaps='inputs_q,outputs_q')

    label = Column(String(255), nullable=False, index=True)
    type = Column(String(255), nullable=False, index=True)

    # A calculation can have both a 'return' and a 'create' link to
    # a single data output node, which would violate the unique constraint
    # defined below, since the difference in link type is not considered.
    # The distinction between the type of a 'create' and a 'return' link is not
    # implemented at the moment, so the unique constraint is disabled.
    __table_args__ = (
        # I cannot add twice the same link
        # I want unique labels among all inputs of a node
        # UniqueConstraint('output_id', 'label'),
        Index(
            'ix_pat_db_dblink_label', label, postgresql_using='btree', postgresql_ops={'label': 'varchar_pattern_ops'}
        ),
        Index('ix_pat_db_dblink_type', type, postgresql_using='btree', postgresql_ops={'type': 'varchar_pattern_ops'}),
    )

    def __str__(self):
        return '{} ({}) --> {} ({})'.format(
            self.input.get_simple_name(invalid_result='Unknown node'),
            self.input.pk,
            self.output.get_simple_name(invalid_result='Unknown node'),
            self.output.pk,
        )


class DbMembership(Base):
    """Database model for owned-data-container membership edges.

    Each row is a containment edge from an immediate owner container
    (``owner_id``) to one exclusively owned child node (``child_id``).
    ``position`` persists element order for both lists and dictionaries;
    database row order is not meaningful. ``key`` persists the string
    dictionary key and stays NULL for ordered-list entries.

    Quantities, layout, and constraints:

    - ``owner_id``: FK to ``db_dbnode.id``, NOT NULL, indexed, default
      NO ACTION (deferred; RESTRICT is unusable here, see the note on
      ``DbNode.owner_id``). Deletion planning must expand to the full
      ownership unit explicitly; database cascades alone are not sufficient.
    - ``child_id``: FK to ``db_dbnode.id``, NOT NULL, indexed, unique
      (exactly one membership row per owned child), default NO ACTION (deferred).
    - ``position``: integer ``>= 0`` (CHECK), unique per owner.
    - ``key``: nullable string; uniqueness per owner applies to non-null
      keys (NULL entries never collide under the unique constraint).
      Non-string keys are rejected in Python, never coerced.
    - ``owner_id != child_id`` (CHECK); longer cycles are rejected by
      transactional validation in ``aiida.storage.ownership`` since
      recursive constraints cannot be expressed declaratively.
    - The matching ``db_dbnode.owner_id`` reference on the child row must
      agree with this edge; both are written atomically in one transaction.
    - Stored rows are immutable: updates are rejected at the backend
      contract level (no triggers). Element-type homogeneity is enforced
      by exact ``node_type`` string comparison without loading plugins.
    """

    __tablename__ = 'db_dbmembership'

    id = Column(Integer, primary_key=True)
    owner_id = Column(
        Integer,
        ForeignKey('db_dbnode.id', deferrable=True, initially='DEFERRED'),
        nullable=False,
        index=True,
    )
    child_id = Column(
        Integer,
        ForeignKey('db_dbnode.id', deferrable=True, initially='DEFERRED'),
        nullable=False,
        index=True,
    )
    position = Column(Integer, nullable=False)
    key = Column(String(255), nullable=True, index=True)

    __table_args__ = (
        UniqueConstraint('child_id', name='uq_db_dbmembership_child_id'),
        UniqueConstraint('owner_id', 'position', name='uq_db_dbmembership_owner_id_position'),
        UniqueConstraint('owner_id', 'key', name='uq_db_dbmembership_owner_id_key'),
        CheckConstraint('position >= 0', name='ck_db_dbmembership_position_nonnegative'),
        CheckConstraint('owner_id != child_id', name='ck_db_dbmembership_no_self_ownership'),
    )

    def __str__(self):
        return f'membership owner={self.owner_id} -> child={self.child_id} position={self.position} key={self.key}'
