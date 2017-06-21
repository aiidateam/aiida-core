# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from abc import ABCMeta, abstractmethod
from aiida.common.pluginloader import BaseFactory
from aiida.common.utils import abstractclassmethod


def CalculationFactory(module, from_abstract=False):
    """
    Return a suitable JobCalculation subclass.

    :param module: a valid string recognized as a Calculation plugin
    :param from_abstract: A boolean. If False (default), actually look only
        to subclasses of JobCalculation, not to the base Calculation class.
        If True, check for valid strings for plugins of the Calculation base class.
    """

    from aiida.orm.calculation import Calculation
    from aiida.orm.calculation.job import JobCalculation

    if from_abstract:
        return BaseFactory(module, Calculation, "aiida.orm.calculation")
    else:
        return BaseFactory(module, JobCalculation, "aiida.orm.calculation.job",
                           suffix="Calculation")


def DataFactory(module):
    """
    Return a suitable Data subclass.
    """
    from aiida.orm.data import Data

    return BaseFactory(module, Data, "aiida.orm.data")


def WorkflowFactory(module):
    """
    Return a suitable Workflow subclass.
    """
    from aiida.orm.workflow import Workflow

    return BaseFactory(module, Workflow, "aiida.workflows")


def load_node(node_id=None, pk=None, uuid=None, parent_class=None, query_with_dashes=True):
    """
    Return an AiiDA node given PK or UUID.

    :param node_id: PK (integer) or UUID (string) or a node
    :param pk: PK of a node
    :param uuid: UUID of a node, or the beginning of the uuid
    :param parent_class: if specified, checks whether the node loaded is a
        subclass of parent_class
    :param bool query_with_dashes: Specific if uuid is passed, allows to put the uuid in the correct form.
        Default=True
    :return: an AiiDA node
    :raise InputValidationError: if none or more than one of parameters is supplied
    :raise TypeError: I the wrong types are provided
    :raise NotExistent: if no matching Node is found.
    :raise MultipleObjectsError: If more than one Node was fouuund
    """
    from aiida.common.exceptions import NotExistent, MultipleObjectsError, NotExistent, InputValidationError
    # This must be done inside here, because at import time the profile
    # must have been already loaded. If you put it at the module level,
    # the implementation is frozen to the default one at import time.
    from aiida.orm.implementation import Node
    from aiida.orm.querybuilder import QueryBuilder


    # First checking if the inputs are valid:
    inputs_provided = [val is not None for val in (node_id, pk, uuid)].count(True)
    if inputs_provided == 0:
        raise InputValidationError("one of the parameters 'node_id', 'pk' and 'uuid' "
                         "has to be supplied")
    elif inputs_provided > 1:
        raise InputValidationError("only one of parameters 'node_id', 'pk' and 'uuid' "
                         "has to be supplied")

    class_ = parent_class or Node
    if not issubclass(class_,  Node):
        raise TypeError("{} is not a subclass of {}".format(class_, Node))
    # The logic is as follows: If pk is specified I will look for the pk
    # if UUID is specified for the uuid.
    # node_id can either be string -> uuid or an integer -> pk
    # Checking first if node_id specified
    if node_id is not None:
        if isinstance(node_id, (str, unicode)):
            uuid = node_id
        elif isinstance(node_id, int):
            pk = node_id
        else:
            raise TypeError("'node_id' has to be either string, unicode or "
                                 "integer, {} given".format(type(node_id)))

            #I am checking whether uuid, if supplied,  is a string
    if uuid is not None:
        if not isinstance(uuid,(str, unicode)):
            raise TypeError("'uuid' has to be string or unicode")
        # or whether the pk, if provided, is an integer
    elif pk is not None:
        if not isinstance(pk, int):
            raise TypeError("'pk' has to be an integer")
    else:
        # I really shouldn't get here
        assert True,  "Neither pk  nor uuid was provided"

    qb = QueryBuilder()
    qb.append(class_, tag='node', project='*')

    if pk:
        qb.add_filter('node',  {'id':pk})
    elif uuid:
        # Put back dashes in the right place
        start_uuid = uuid.replace('-', '')
        if query_with_dashes:
            # Essential that this is ordered from largest to smallest!
            for dash_pos in [20,16,12,8]:
                if len(start_uuid) > dash_pos:
                    start_uuid = "{}-{}".format(
                        start_uuid[:dash_pos], start_uuid[dash_pos:]
                        )

        qb.add_filter('node',{'uuid': {'like': "{}%".format(start_uuid)}})
    try:
        return qb.one()[0]
    except MultipleObjectsError:
        raise MultipleObjectsError("More than one node found")
    except NotExistent:
        raise NotExistent("No node was found")


def load_workflow(wf_id=None, pk=None, uuid=None):
    """
    Return an AiiDA workflow given PK or UUID.

    :param wf_id: PK (integer) or UUID (string) or UUID instance or a workflow
    :param pk: PK of a workflow
    :param uuid: UUID of a workflow
    :return: an AiiDA workflow
    :raises: ValueError if none or more than one of parameters is supplied
        or type of wf_id is neither string nor integer
    """
    # This must be done inside here, because at import time the profile
    # must have been already loaded. If you put it at the module level,
    # the implementation is frozen to the default one at import time.
    from aiida.orm.implementation import Workflow
    from uuid import UUID as uuid_type

    if int(wf_id is None) + int(pk is None) + int(uuid is None) == 3:
        raise ValueError("one of the parameters 'wf_id', 'pk' and 'uuid' "
                         "has to be supplied")
    if int(wf_id is None) + int(pk is None) + int(uuid is None) < 2:
        raise ValueError("only one of parameters 'wf_id', 'pk' and 'uuid' "
                         "has to be supplied")

    if wf_id is not None:
        if wf_id and isinstance(wf_id, uuid_type):
            wf_id = str(wf_id)

        if isinstance(wf_id, basestring):
            return Workflow.get_subclass_from_uuid(wf_id)
        elif isinstance(wf_id, int):
            return Workflow.get_subclass_from_pk(wf_id)
        else:
            raise ValueError("'wf_id' has to be either string, unicode, "
                             "integer or UUID instance, {} given".format(type(wf_id)))
    if pk is not None:
        if isinstance(pk, int):
            return Workflow.get_subclass_from_pk(pk)
        else:
            raise ValueError("'pk' has to be an integer")
    else:
        if uuid and isinstance(uuid, uuid_type):
            uuid = str(uuid)
        if isinstance(uuid, str) or isinstance(uuid, unicode):
            return Workflow.get_subclass_from_uuid(uuid)
        else:
            raise ValueError("'uuid' has to be a string, unicode or a UUID instance")


class BackendDelegateWithDefault(object):
    """
    This class is a helper to implement the delegation pattern [1] by
    delegating functionality (i.e. calling through) to the backend class
    which will do the actual work.


    [1] https://en.wikipedia.org/wiki/Delegation_pattern
    """
    __metaclass__ = ABCMeta

    _DEFAULT = None

    @abstractclassmethod
    def create_default(cls):
        raise NotImplementedError("The subclass should implement this")

    @classmethod
    def get_default(cls):
        if cls._DEFAULT is None:
            cls._DEFAULT = cls.create_default()
        return cls._DEFAULT

    def __init__(self, backend):
        self._backend = backend
