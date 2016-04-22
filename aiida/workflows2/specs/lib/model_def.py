import datetime, hashlib
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.schema import Index
from uuid import uuid4

Base = declarative_base()
loading_type="dynamic"
#TODO investigate lazy loading

#------------------------ Object Classes ------------------------
class Calc(Base):
    __tablename__ = "calc"

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4)
    name = Column(String)
    type = Column(String)
    state = Column(String)
    time = Column(DateTime(timezone=False), default=datetime.datetime.now)
    content = Column(JSONB)
    hash = Column(String)
    extra = Column(JSONB)

    code_id = Column(Integer, ForeignKey("code.id"))
    code = relationship("Code", backref="calcs")
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    user = relationship("User", backref=backref("calcs", lazy=loading_type))
    #master_id = Column(Integer, ForeignKey("calc.id"))
    #slaves = relationship("Calc", backref=backref("master", remote_side=[id]))
    inputs = relationship("Data", secondary="inputlink", backref=backref("takers", lazy=loading_type))
    outputs = relationship("Data", secondary="outputlink", backref=backref("givers", lazy=loading_type))
    masters = relationship("Calc", secondary="control",
                           primaryjoin="Calc.id==Control.slave_id",
                           secondaryjoin="Calc.id==Control.master_id",
                           backref="slaves")

    def __init__(self, name=None, state='New', content=None, extra=None, code=None):
        self.name = name
        self.state = state
        self.content = content
        self.extra = extra
        self.code = code
        self.hash = hashlib.sha224(str(self.content)).hexdigest()

    def __repr__(self):
        return "calc[{}]".format(self.name)

    __mapper_args__ = {'polymorphic_on': type, 'polymorphic_identity': 'calc'}


class Data(Base):
    __tablename__ = "data"

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4)
    name = Column(String)
    type = Column(String)
    state = Column(String)
    validity = Column(String)
    time = Column(DateTime(timezone=False), default=datetime.datetime.now)
    content = Column(JSONB)
    hash = Column(String)
    extra = Column(JSONB)

    #parent_id = Column(Integer, ForeignKey("calc.id"), nullable=True)   #change to False if parents are required
    #parent = relationship("Calc", backref=backref("children", lazy="dynamic"))
    #calcs = relationship("Calc", secondary="inputlink", backref=backref("inputs", lazy="dynamic"))
    roots = relationship("Data", secondary="derive",
                         primaryjoin="Data.id==Derive.fruit_id",
                         secondaryjoin="Data.id==Derive.root_id",
                         backref="fruits")

    #__table_args__ = (UniqueConstraint('parent_id', 'content_hash', name='parent_hash_uc'),)
    __mapper_args__ = {'polymorphic_on': type, 'polymorphic_identity': 'data'}

    def __init__(self, name=None, state=None, validity='New',
                 content=None, extra=None, hash=None):
        self.name = name
        self.state = state
        self.validity = validity
        self.content = content
        self.hash = hashlib.sha224(str(self.content)).hexdigest()
        self.extra = extra

    def __repr__(self):
        return "data({})".format(self.name)


class Code(Base):
    __tablename__ = "code"

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True),  default=uuid4)
    name = Column(String, unique=False) #non-unique for testing
    type = Column(String)
    state = Column(String)
    time = Column(DateTime(timezone=False), default=datetime.datetime.now)
    content = Column(JSONB)
    hash = Column(String, unique=True)
    extra = Column(JSONB)
    computer_id = Column(Integer, ForeignKey("computer.id"), nullable=True)
    computer = relationship("Computer", backref=backref("codes", lazy=loading_type))
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    user = relationship("User", backref=backref("codes", lazy=loading_type))
    wrappers = relationship("Code", secondary="relative",
                         primaryjoin="Code.id==Relative.core_id",
                         secondaryjoin="Code.id==Relative.wrapper_id",
                         backref="cores")

    def __init__(self, name=None, state=None, content=None, extra=None, computer=None,
        user=None):
        self.name = name
        self.state = state
        self.content = content
        self.extra = extra
        self.computer = computer
        self.hash = hashlib.sha224(str(self.content)).hexdigest()

    def __repr__(self):
        return "code<{}>".format(self.name)

    __mapper_args__ = {'polymorphic_on': type, 'polymorphic_identity': 'code'}


class Computer(Base):
    __tablename__ = "computer"

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True),  default=uuid4)
    name = Column(String, unique=True)
    type = Column(String)
    state = Column(String)
    time = Column(DateTime(timezone=False), default=datetime.datetime.now)
    content = Column(JSONB)
    hash = Column(String, unique=True)
    extra = Column(JSONB)

    def __init__(self, name=None, state=None, content=None, extra=None):
        self.name = name
        self.state = state
        self.content = content
        self.extra = extra
        self.hash = hashlib.sha224(str(self.content)).hexdigest()

    def __repr__(self):
        return "Computer <{}>".format(self.name)

    __mapper_args__ = {'polymorphic_on': type, 'polymorphic_identity': 'computer'}


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True),  default=uuid4)
    name = Column(String, unique=True)
    type = Column(String)
    state = Column(String)
    time = Column(DateTime(timezone=False), default=datetime.datetime.now)
    content = Column(JSONB)
    hash = Column(String, unique=True)
    extra = Column(JSONB)

    def __init__(self, name=None, state=None, content=None, extra=None):
        self.name = name
        self.state = state
        self.content = content
        self.extra = extra
        self.hash = hashlib.sha224(str(self.content)).hexdigest()

    def __repr__(self):
        return "User <{}>".format(self.name)

    __mapper_args__ = {'polymorphic_on': type, 'polymorphic_identity': 'user'}

# -------------- Link Classes --------------------------

class InputLink(Base):
    """
    Link between a in input data and a calc, for a m2m relationship
    """
    __tablename__ = "inputlink"

    input_id = Column(Integer, ForeignKey("data.id"), primary_key=True)
    taker_id = Column(Integer, ForeignKey("calc.id"), primary_key=True)
    type = Column(String)
    label = Column(String)
    time = Column(DateTime(timezone=False), default=datetime.datetime.now)
    extra = Column(JSONB)
    input = relationship("Data", backref=backref('taker_links', lazy=loading_type))
    taker = relationship("Calc", backref=backref('input_links', lazy=loading_type))
    __mapper_args__ = {'polymorphic_on': type, 'polymorphic_identity': 'inputlink'}

    def __init__(self, d=None, c=None, label=None):
        self.input = d
        self.taker = c
        self.label = label

    def __repr__(self):
        return "<InputLink {0} {1} -> {2}>".format(self.label, self.input, self.taker)


class OutputLink(Base):
    """
    Link for connecting a calc to the data it returns. This is not always the same as the data it creates (children)
    """
    __tablename__ = "outputlink"

    giver_id = Column(Integer, ForeignKey("calc.id"), primary_key=True)
    output_id = Column(Integer, ForeignKey("data.id"), primary_key=True)
    type = Column(String)
    label = Column(String)
    time = Column(DateTime(timezone=False), default=datetime.datetime.now)
    extra = Column(JSONB)
    giver = relationship("Calc", backref=backref('output_links', lazy=loading_type))
    output = relationship("Data", backref=backref('giver_links', lazy=loading_type))
    __mapper_args__ = {'polymorphic_on': type, 'polymorphic_identity': 'outputlink'}

    def __init__(self, c=None, d=None, label=None):
        self.label = label
        self.giver = c
        self.output = d

    def __repr__(self):
        return "<OutputLink {0} {1} -> {2}>".format(self.label, self.giver, self.output)


class Control(Base):
    __tablename__ = "control"

    master_id = Column(Integer, ForeignKey("calc.id"), primary_key=True)
    slave_id = Column(Integer, ForeignKey("calc.id"), primary_key=True)
    type = Column(String)
    time = Column(DateTime(timezone=False), default=datetime.datetime.now)
    extra = Column(JSONB)
    master = relationship("Calc", primaryjoin="Control.master_id==Calc.id", backref='slave_controls')
    slave = relationship("Calc", primaryjoin="Control.slave_id==Calc.id", backref='master_controls')
    __mapper_args__ = {'polymorphic_on': type, 'polymorphic_identity': 'control'}

    def __init__(self, n1=None, n2=None):
        self.master = n1
        self.slave = n2

    def __repr__(self):
        return "<Control {0} -> {1}>".format(self.caller, self.helper)


class Derive(Base):
    __tablename__ = "derive"

    root_id = Column(Integer, ForeignKey("data.id"), primary_key=True)
    fruit_id = Column(Integer, ForeignKey("data.id"), primary_key=True)
    type = Column(String)
    time = Column(DateTime(timezone=False), default=datetime.datetime.now)
    extra = Column(JSONB)
    #label = Column(String)
    root = relationship("Data", primaryjoin="Derive.root_id==Data.id", backref='fruit_derivations')
    fruit = relationship("Data", primaryjoin="Derive.fruit_id==Data.id", backref='root_derivations')
    __mapper_args__ = {'polymorphic_on': type, 'polymorphic_identity': 'derive'}

    def __init__(self, n1=None, n2=None):
        self.root = n1
        self.fruit = n2

    def __repr__(self):
        return "<Derive {0} -> {1}>".format(self.root, self.fruit)


class Relative(Base):
    __tablename__ = "relative"

    core_id = Column(Integer, ForeignKey("code.id"), primary_key=True)
    wrapper_id = Column(Integer, ForeignKey("code.id"), primary_key=True)
    type = Column(String)
    time = Column(DateTime(timezone=False), default=datetime.datetime.now)
    extra = Column(JSONB)
    #label = Column(String)
    core = relationship("Code", primaryjoin="Relative.core_id==Code.id", backref='wrapper_relations')
    wrapper = relationship("Code", primaryjoin="Relative.wrapper_id==Code.id", backref='core_relations')
    __mapper_args__ = {'polymorphic_on': type, 'polymorphic_identity': 'relative'}

    def __init__(self, n1=None, n2=None):
        self.core = n1
        self.wrapper = n2

    def __repr__(self):
        return "<Relative {0} -> {1}>".format(self.core, self.wrapper)


#--------------- Subclasses --------------------------

class Create(OutputLink):
    """
    A Data can only be Created by one parent calculation, but then given as an output by many others.
    """
    def __repr__(self):
        return "<Create {0} {1} -> {2}>".format(self.label, self.giver, self.output)
    __mapper_args__ = {'polymorphic_identity': 'create'}


class Return(OutputLink):
    """
    """
    def __repr__(self):
        return "<Return {0} {1} -> {2}>".format(self.label, self.giver, self.output)
    __mapper_args__ = {'polymorphic_identity': 'return'}


class Recall(Control):
    """
    """
    def __repr__(self):
        return "<Call {0} -> {1}>".format(self.master, self.slave)
    __mapper_args__ = {'polymorphic_identity': 'recall'}


class Call(Control):
    """
    A Calc can only be called once, the first time it is created due to a call from the first caller.
    """
    def __repr__(self):
        return "<Summon {0} -> {1}>".format(self.master, self.slave)
    __mapper_args__ = {'polymorphic_identity': 'call'}


class Suspend(Control):
    """
    """
    def __repr__(self):
        return "<Suspend {0} -> {1}>".format(self.master, self.slave)
    __mapper_args__ = {'polymorphic_identity': 'summon'}


class Equivalent(Derive):
    """
    """
    def __repr__(self):
        return "<Equivalent {0} -> {1}>".format(self.root, self.fruit)
    __mapper_args__ = {'polymorphic_identity': 'equivalent'}


class Include(Derive):
    """
    """
    def __repr__(self):
        return "<Include {0} -> {1}>".format(self.root, self.fruit)
    __mapper_args__ = {'polymorphic_identity': 'include'}


#------------------ Indexing ------------------
### indexing for faster queries, needs testing
#Index('my_index', Data.content, postgresql_using='gin')
