# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import json

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Column, UniqueConstraint, Table
from sqlalchemy.types import Integer, String, DateTime, Text

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy_utils.types.choice import ChoiceType

from aiida.backends.sqlalchemy.models.base import Base, _QueryProperty, _AiidaQuery
from aiida.backends.sqlalchemy.models.utils import uuid_func
from aiida.common.datastructures import (wf_states, wf_data_types,
                                         wf_data_value_types, wf_default_call)
from aiida.utils import timezone



class DbWorkflow(Base):
    __tablename__ = "db_dbworkflow"

    aiida_query = _QueryProperty(_AiidaQuery)

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid_func)

    ctime = Column(DateTime(timezone=True), default=timezone.now)
    mtime = Column(DateTime(timezone=True), default=timezone.now)

    user_id = Column(Integer, ForeignKey('db_dbuser.id'))
    user = relationship('DbUser')

    label = Column(String(255), index=True)
    description = Column(Text)

    nodeversion = Column(Integer)
    lastsyncedversion = Column(Integer)

    state = Column(ChoiceType((_, _) for _ in wf_states),
                   default=wf_states.INITIALIZED)

    report = Column(Text)

    data = relationship("DbWorkflowData", backref='parent')

    # XXX the next three attributes have "blank=False", but can be null. It may
    # be needed to add some validation for this, but only at commit time.
    # To do so: see https://stackoverflow.com/questions/28228766/running-cleaning-validation-code-before-committing-in-sqlalchemy
    module = Column(Text)
    module_class = Column(Text)
    script_path = Column(Text)

    # XXX restrict the size of this column, MD5 have a fixed size
    script_md5 = Column(String(255))  # Blank = False.

    def __init__(self, *args, **kwargs):
        super(DbWorkflow, self).__init__(*args, **kwargs)
        self.nodeversion = 1
        self.lastsyncedversion = 0

    @property
    def pk(self):
        return self.id

    def get_aiida_class(self):
        """
        Return the corresponding aiida instance of class aiida.worflow
        """
        from aiida.orm.workflow import Workflow
        return Workflow.get_subclass_from_uuid(self.uuid)

    def set_state(self, state):
        self.state = state
        self.save()

    def set_script_md5(self, md5):
        self.script_md5 = md5
        self.save()

    #    def add_data(self, dict, d_type):
    #        for k in dict.keys():
    #            p, create = self.data.get_or_create(name=k, data_type=d_type)
    #            p.set_value(dict[k])

    def add_data(self, dict, d_type):
        for k in dict.keys():
            p, create = self._get_or_create_data(name=k, data_type=d_type)
            p.set_value(dict[k])

    def _get_or_create_data(self, name, data_type):
        match_data = {name: _ for _ in self.data if _.name == name}

        if not match_data:  # create case
            dbdata = DbWorkflowData(parent_id=self.id, name=name, data_type=data_type)
            self.data.append(dbdata)
            return dbdata, True
        else:  # already existing case
            return match_data[name], False

    def _get_or_create_step(self, name, user):
        match_step = [_ for _ in self.steps if (_.name == name and _.user == user)]

        if not match_step:  # create case
            dbstep = DbWorkflowStep(parent_id=self.id, name=name, user_id=user.id)
            self.steps.append(dbstep)
            return dbstep, True
        else:  # already existing case
            return match_step[0], False

    def get_data(self, d_type):
        dict = {}
        # for p in self.data.filter(parent=self, data_type=d_type):
        for p in [_ for _ in self.data if _.data_type == d_type]:
            dict[p.name] = p.get_value()
        return dict

    def add_parameters(self, _dict, force=False):
        if not self.state == wf_states.INITIALIZED and not force:
            raise ValueError("Cannot add initial parameters to an already initialized workflow")

        self.add_data(_dict, wf_data_types.PARAMETER)

    def add_parameter(self, name, value):
        self.add_parameters({name: value})

    def get_parameters(self):
        return self.get_data(wf_data_types.PARAMETER)

    def get_parameter(self, name):
        res = self.get_parameters()
        if name in res:
            return res[name]
        else:
            raise ValueError("Error retrieving results: {0}".format(name))

    def add_results(self, _dict):
        self.add_data(_dict, wf_data_types.RESULT)

    def add_result(self, name, value):
        self.add_results({name: value})

    def get_results(self):
        return self.get_data(wf_data_types.RESULT)

    def get_result(self, name):
        res = self.get_results()
        if name in res:
            return res[name]
        else:
            raise ValueError("Error retrieving results: {0}".format(name))

    def add_attributes(self, _dict):
        self.add_data(_dict, wf_data_types.ATTRIBUTE)

    def add_attribute(self, name, value):
        self.add_attributes({name: value})

    def get_attributes(self):
        return self.get_data(wf_data_types.ATTRIBUTE)

    def get_attribute(self, name):
        res = self.get_attributes()
        if name in res:
            return res[name]
        else:
            raise ValueError("Error retrieving results: {0}".format(name))

    def clear_report(self):
        self.report = ''
        self.save()

    def append_to_report(self, _text):
        if self.report == None:
            self.report = ''
        self.report += str(timezone.now()) + "] " + _text + "\n"
        self.save()

    def get_calculations(self):
        from aiida.orm import JobCalculation
        return JobCalculation.query(workflow_step=self.steps)

    def get_sub_workflows(self):
        return DbWorkflow.objects.filter(parent_workflow_step=self.steps.all())

    def is_subworkflow(self):
        """
        Return True if this is a subworkflow, False if it is a root workflow,
        launched by the user.
        """
        return len(self.parent_workflow_step) > 0

    def finish(self):
        self.state = wf_states.FINISHED

    def __str__(self):
        simplename = self.module_class
        # node pk + type
        if self.label:
            return "{} workflow [{}]: {}".format(simplename, self.pk, self.label)
        else:
            return "{} workflow [{}]".format(simplename, self.pk)


class DbWorkflowData(Base):
    __tablename__ = "db_dbworkflowdata"

    id = Column(Integer, primary_key=True)

    parent_id = Column(Integer, ForeignKey('db_dbworkflow.id'))

    name = Column(String(255))  # Blank = false
    time = Column(DateTime(timezone=True), default=timezone.now)
    data_type = Column(String(255), default=wf_data_types.PARAMETER)  # blank = false
    value_type = Column(String(255), default=wf_data_value_types.NONE)  # blank = false
    json_value = Column(Text)

    aiida_obj_id = Column(Integer, ForeignKey('db_dbnode.id'), nullable=True)
    aiida_obj = relationship("DbNode")

    __table_args__ = (
        UniqueConstraint("parent_id", "name", "data_type"),
    )

    def get_or_create(self, **kwargs):  # this is to emulate the django method
        from sqlalchemy.sql.expression import ClauseElement
        instance = self.query().filter_by(kwargs).first()
        if instance:
            return instance, False
        else:
            params = dict((k, v) for k, v in kwargs.iteritems() if not isinstance(v, ClauseElement))
            instance = model(**params)
            session.add(instance)
            return instance, True

    def set_value(self, arg):
        from aiida.orm import Node
        try:
            if isinstance(arg, Node) or issubclass(arg.__class__, Node):
                if arg.pk is None:
                    raise ValueError("Cannot add an unstored node as an attribute of a Workflow!")
                self.aiida_obj = arg.dbnode
                self.value_type = wf_data_value_types.AIIDA
                self.save()
            else:
                self.json_value = json.dumps(arg)
                self.value_type = wf_data_value_types.JSON
                self.save()
        except:
            raise ValueError("Cannot set the parameter {}".format(self.name))

    def get_value(self):
        if self.value_type == wf_data_value_types.JSON:
            return json.loads(self.json_value)
        elif self.value_type == wf_data_value_types.AIIDA:
            return self.aiida_obj.get_aiida_class()
        elif self.value_type == wf_data_value_types.NONE:
            return None
        else:
            raise ValueError("Cannot rebuild the parameter {}".format(self.name))

    def __str__(self):
        return "Data for workflow {} [{}]: {}".format(
            self.parent.module_class, self.parent.id, self.name)


table_workflowstep_calc = Table(
    'db_dbworkflowstep_calculations', Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('dbworkflowstep_id', Integer, ForeignKey('db_dbworkflowstep.id')),
    Column('dbnode_id', Integer, ForeignKey('db_dbnode.id')),
    UniqueConstraint('dbworkflowstep_id', 'dbnode_id')
)

table_workflowstep_subworkflow = Table(
    'db_dbworkflowstep_sub_workflows', Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('dbworkflowstep_id', Integer, ForeignKey('db_dbworkflowstep.id')),
    Column('dbworkflow_id', Integer, ForeignKey('db_dbworkflow.id')),
    UniqueConstraint('dbworkflowstep_id', 'dbworkflow_id')
)


class DbWorkflowStep(Base):
    __tablename__ = "db_dbworkflowstep"

    id = Column(Integer, primary_key=True)

    parent_id = Column(Integer, ForeignKey('db_dbworkflow.id'))
    parent = relationship("DbWorkflow", backref='steps')

    user_id = Column(Integer, ForeignKey('db_dbuser.id'))
    user = relationship('DbUser')

    name = Column(String(255))  # Blank = false
    time = Column(DateTime(timezone=True), default=timezone.now)
    nextcall = Column(String(255), default=wf_default_call)  # Blank = false

    state = Column(ChoiceType((_, _) for _ in wf_states), default=wf_states.CREATED)

    calculations = relationship("DbNode", secondary=table_workflowstep_calc,
                                backref="workflow_step")
    sub_workflows = relationship("DbWorkflow",
                                 secondary=table_workflowstep_subworkflow,
                                 backref="parent_workflow_step")

    __table_args__ = (
        UniqueConstraint('parent_id', 'name'),
    )

    def add_calculation(self, step_calculation):
        from aiida.orm import JobCalculation
        if (not isinstance(step_calculation, JobCalculation)):
            raise ValueError("Cannot add a non-Calculation object to a workflow step")

        try:
            self.calculations.append(step_calculation.dbnode)
        except:
            raise ValueError("Error adding calculation to step")

    def get_calculations(self, state=None):
        dbnodes = self.calculations
        calcs = [_.get_aiida_class() for _ in dbnodes]
        if (state == None):
            return calcs
        else:
            return [_ for _ in calcs if _.get_state() == state]

    def remove_calculations(self):
        self.calculations.all().delete()

    def add_sub_workflow(self, sub_wf):
        from aiida.orm import Workflow
        if not issubclass(sub_wf.__class__, Workflow) and \
                not isinstance(sub_wf, Workflow):
            raise ValueError("Cannot add a workflow not of type Workflow")
        try:
            self.sub_workflows.append(sub_wf.dbworkflowinstance)
        except:
            raise ValueError("Error adding calculation to step")

    def get_sub_workflows(self):
        return [_.get_aiida_class() for _ in self.sub_workflows]

    def remove_sub_workflows(self):
        self.sub_workflows.all().delete()

    def is_finished(self):
        return self.state == wf_states.FINISHED

    def set_nextcall(self, _nextcall):
        self.nextcall = _nextcall
        self.save()

    def set_state(self, _state):
        self.state = _state
        self.save()

    def reinitialize(self):
        self.set_state(wf_states.INITIALIZED)

    def finish(self):
        self.set_state(wf_states.FINISHED)

    def __str__(self):
        return "Step {} for workflow {} [{}]".format(
            self.name, self.parent.module_class, self.parent.id)
