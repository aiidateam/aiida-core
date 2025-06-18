###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the QueryBuilder."""

import copy
import json
import uuid
import warnings
from collections import defaultdict
from datetime import date, datetime, timedelta
from itertools import chain

import pytest

from aiida import orm, plugins
from aiida.common.links import LinkType
from aiida.orm.querybuilder import _get_ormclass
from aiida.orm.utils.links import LinkQuadruple


class TestBasic:
    @pytest.mark.usefixtures('aiida_profile_clean')
    @pytest.mark.requires_psql
    def test_date_filters_support(self):
        """Verify that `datetime.date` is supported in filters."""
        from aiida.common import timezone

        # Using timezone.now() rather than datetime.now() to get a timezone-aware object rather than a naive one
        orm.Data(ctime=timezone.now() - timedelta(days=3)).store()
        orm.Data(ctime=timezone.now() - timedelta(days=1)).store()

        builder = orm.QueryBuilder().append(orm.Node, filters={'ctime': {'>': date.today() - timedelta(days=1)}})
        assert builder.count() == 1

    def test_ormclass_type_classification(self):
        """This tests the classifications of the QueryBuilder"""
        from aiida.common.exceptions import DbContentError

        # Asserting that improper declarations of the class type raise an error
        with pytest.raises(DbContentError):
            _get_ormclass(None, 'data')
        with pytest.raises(DbContentError):
            _get_ormclass(None, 'data.Data')
        with pytest.raises(DbContentError):
            _get_ormclass(None, '.')

        # Asserting that the query type string and plugin type string are returned:
        for _cls, classifiers in (
            _get_ormclass(orm.StructureData, None),
            _get_ormclass(None, 'data.core.structure.StructureData.'),
        ):
            assert classifiers[0].ormclass_type_string == orm.StructureData._plugin_type_string

        for _cls, classifiers in (
            _get_ormclass(orm.Group, None),
            _get_ormclass(None, 'group.core'),
            _get_ormclass(None, 'Group.core'),
        ):
            assert classifiers[0].ormclass_type_string.startswith('group')

        for _cls, classifiers in (
            _get_ormclass(orm.User, None),
            _get_ormclass(None, 'user'),
            _get_ormclass(None, 'User'),
        ):
            assert classifiers[0].ormclass_type_string == 'user'

        for _cls, classifiers in (
            _get_ormclass(orm.Computer, None),
            _get_ormclass(None, 'computer'),
            _get_ormclass(None, 'Computer'),
        ):
            assert classifiers[0].ormclass_type_string == 'computer'

        for _cls, classifiers in (
            _get_ormclass(orm.Data, None),
            _get_ormclass(None, 'data.Data.'),
        ):
            assert classifiers[0].ormclass_type_string == orm.Data._plugin_type_string

    def test_process_type_classification(self):
        """This tests the classifications of the QueryBuilder"""
        from aiida.engine import WorkChain
        from aiida.plugins import CalculationFactory

        ArithmeticAdd = CalculationFactory('core.arithmetic.add')  # noqa: N806

        # When passing a WorkChain class, it should return the type of the corresponding Node
        # including the appropriate filter on the process_type
        _cls, classifiers = _get_ormclass(WorkChain, None)
        assert classifiers[0].ormclass_type_string == 'process.workflow.workchain.WorkChainNode.'
        assert classifiers[0].process_type_string == 'aiida.engine.processes.workchains.workchain.WorkChain'

        # When passing a WorkChainNode, no process_type filter is applied
        _cls, classifiers = _get_ormclass(orm.WorkChainNode, None)
        assert classifiers[0].ormclass_type_string == 'process.workflow.workchain.WorkChainNode.'
        assert classifiers[0].process_type_string is None

        # Same tests for a calculation
        _cls, classifiers = _get_ormclass(ArithmeticAdd, None)
        assert classifiers[0].ormclass_type_string == 'process.calculation.calcjob.CalcJobNode.'
        assert classifiers[0].process_type_string == 'aiida.calculations:core.arithmetic.add'

    def test_get_group_type_filter(self):
        """Test the `aiida.orm.querybuilder.get_group_type_filter` function."""
        from aiida.orm.querybuilder import Classifier, _get_group_type_filter

        classifiers = Classifier('group.core')
        assert _get_group_type_filter(classifiers, False) == {'==': 'core'}
        assert _get_group_type_filter(classifiers, True) == {'like': '%'}

        classifiers = Classifier('group.core.auto')
        assert _get_group_type_filter(classifiers, False) == {'==': 'core.auto'}
        assert _get_group_type_filter(classifiers, True) == {'like': 'core.auto%'}

        classifiers = Classifier('group.pseudo.family')
        assert _get_group_type_filter(classifiers, False) == {'==': 'pseudo.family'}
        assert _get_group_type_filter(classifiers, True) == {'like': 'pseudo.family%'}

    # Tracked in issue #4281
    @pytest.mark.flaky(reruns=2)
    @pytest.mark.requires_rmq
    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_process_query(self):
        """Test querying for a process class."""
        from aiida.common.warnings import AiidaEntryPointWarning
        from aiida.engine import ExitCode, WorkChain, if_, return_, run

        class PotentialFailureWorkChain(WorkChain):
            EXIT_STATUS = 1
            EXIT_MESSAGE = 'Well you did ask for it'
            OUTPUT_LABEL = 'optional_output'
            OUTPUT_VALUE = 144

            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.input('success', valid_type=orm.Bool)
                spec.input('through_return', valid_type=orm.Bool, default=lambda: orm.Bool(False))
                spec.input('through_exit_code', valid_type=orm.Bool, default=lambda: orm.Bool(False))
                spec.exit_code(cls.EXIT_STATUS, 'EXIT_STATUS', cls.EXIT_MESSAGE)
                spec.outline(if_(cls.should_return_out_of_outline)(return_(cls.EXIT_STATUS)), cls.failure, cls.success)
                spec.output(cls.OUTPUT_LABEL, required=False)

            def should_return_out_of_outline(self):
                return self.inputs.through_return.value

            def failure(self):
                if self.inputs.success.value is False:
                    # Returning either 0 or ExitCode with non-zero status should terminate the workchain
                    if self.inputs.through_exit_code.value is False:
                        return self.EXIT_STATUS
                    else:
                        return self.exit_codes.EXIT_STATUS
                elif self.inputs.through_exit_code.value is False:
                    # Returning 0 or ExitCode with zero status should *not* terminate the workchain
                    return 0
                else:
                    return ExitCode()

            def success(self):
                self.out(self.OUTPUT_LABEL, orm.Int(self.OUTPUT_VALUE).store())

        class DummyWorkChain(WorkChain):
            pass

        # Run a simple test WorkChain
        _result = run(PotentialFailureWorkChain, success=orm.Bool(True))

        # Query for nodes associated with this type of WorkChain
        qb = orm.QueryBuilder()

        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter('always')

            qb.append(PotentialFailureWorkChain)

            # Verify some things
            assert len(w) == 1
            assert issubclass(w[-1].category, AiidaEntryPointWarning)

        # There should be one result of type WorkChainNode
        assert qb.count() == 1
        assert isinstance(qb.all()[0][0], orm.WorkChainNode)

        # Query for nodes of a different type of WorkChain
        qb = orm.QueryBuilder()

        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter('always')

            qb.append(DummyWorkChain)

            # Verify some things
            assert len(w) == 1
            assert issubclass(w[-1].category, AiidaEntryPointWarning)

        # There should be no result
        assert qb.count() == 0

        # Query for all WorkChain nodes
        qb = orm.QueryBuilder()
        qb.append(WorkChain)

        # There should be one result
        assert qb.count() == 1

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_simple_query_1(self):
        """Testing a simple query"""
        n1 = orm.Data()
        n1.label = 'node1'
        n1.base.attributes.set('foo', ['hello', 'goodbye'])
        n1.store()

        n2 = orm.CalculationNode()
        n2.label = 'node2'
        n2.base.attributes.set('foo', 1)

        n3 = orm.Data()
        n3.label = 'node3'
        n3.base.attributes.set('foo', 1.0000)  # Stored as fval
        n3.store()

        n4 = orm.CalculationNode()
        n4.label = 'node4'
        n4.base.attributes.set('foo', 'bar')

        n5 = orm.Data()
        n5.label = 'node5'
        n5.base.attributes.set('foo', None)
        n5.store()

        n2.base.links.add_incoming(n1, link_type=LinkType.INPUT_CALC, link_label='link1')
        n2.store()
        n3.base.links.add_incoming(n2, link_type=LinkType.CREATE, link_label='link2')

        n4.base.links.add_incoming(n3, link_type=LinkType.INPUT_CALC, link_label='link3')
        n4.store()
        n5.base.links.add_incoming(n4, link_type=LinkType.CREATE, link_label='link4')

        qb1 = orm.QueryBuilder()
        qb1.append(orm.Node, filters={'attributes.foo': 1.000})

        assert len(qb1.all()) == 2

        qb2 = orm.QueryBuilder()
        qb2.append(orm.Data)
        assert qb2.count() == 3

        qb2 = orm.QueryBuilder()
        qb2.append(entity_type='data.Data.')
        assert qb2.count() == 3

        qb3 = orm.QueryBuilder()
        qb3.append(orm.Node, project='label', tag='node1')
        qb3.append(orm.Node, project='label', tag='node2')
        assert qb3.count() == 4

        qb4 = orm.QueryBuilder()
        qb4.append(orm.CalculationNode, tag='node1')
        qb4.append(orm.Data, tag='node2')
        assert qb4.count() == 2

        qb5 = orm.QueryBuilder()
        qb5.append(orm.Data, tag='node1')
        qb5.append(orm.CalculationNode, tag='node2')
        assert qb5.count() == 2

        qb6 = orm.QueryBuilder()
        qb6.append(orm.Data, tag='node1')
        qb6.append(orm.Data, tag='node2')
        assert qb6.count() == 0

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_simple_query_2(self):
        from aiida.common.exceptions import MultipleObjectsError, NotExistent

        n0 = orm.Data()
        n0.label = 'hello'
        n0.description = ''
        n0.base.attributes.set('foo', 'bar')

        n1 = orm.CalculationNode()
        n1.label = 'foo'
        n1.description = 'I am FoO'

        n2 = orm.Data()
        n2.label = 'bar'
        n2.description = 'I am BaR'

        n2.base.links.add_incoming(n1, link_type=LinkType.CREATE, link_label='random_2')
        n1.base.links.add_incoming(n0, link_type=LinkType.INPUT_CALC, link_label='random_1')

        for n in (n0, n1, n2):
            n.store()

        qb1 = orm.QueryBuilder()
        qb1.append(orm.Node, filters={'label': 'hello'})
        assert len(list(qb1.all())) == 1

        qh = {
            'path': [{'cls': orm.Node, 'tag': 'n1'}, {'cls': orm.Node, 'tag': 'n2', 'with_incoming': 'n1'}],
            'filters': {
                'n1': {
                    'label': {'ilike': '%foO%'},
                },
                'n2': {
                    'label': {'ilike': 'bar%'},
                },
            },
            'project': {
                'n1': ['id', 'uuid', 'ctime', 'label'],
                'n2': ['id', 'description', 'label'],
            },
        }

        qb2 = orm.QueryBuilder(**qh)

        resdict = qb2.dict()
        assert len(resdict) == 1
        assert isinstance(resdict[0]['n1']['ctime'], datetime)

        res_one = qb2.one()
        assert 'bar' in res_one

        qh = {
            'path': [{'cls': orm.Node, 'tag': 'n1'}, {'cls': orm.Node, 'tag': 'n2', 'with_incoming': 'n1'}],
            'filters': {'n1--n2': {'label': {'like': '%_2'}}},
        }
        qb = orm.QueryBuilder(**qh)
        assert qb.count() == 1

        # Test the hashing:
        query1 = qb._impl.get_query(qb.as_dict())
        qb.add_filter('n2', {'label': 'nonexistentlabel'})
        assert qb.count() == 0

        with pytest.raises(NotExistent):
            qb.one()
        with pytest.raises(MultipleObjectsError):
            orm.QueryBuilder().append(orm.Node).one()

        query2 = qb._impl.get_query(qb.as_dict())
        query3 = qb._impl.get_query(qb.as_dict())

        assert id(query1) != id(query2)
        assert id(query2) == id(query3)

    def test_dict_multiple_projections(self):
        """Test that the `.dict()` accumulator with multiple projections returns the correct types."""
        node = orm.Data().store()
        builder = orm.QueryBuilder().append(orm.Data, filters={'id': node.pk}, project=['*', 'id'])
        results = builder.dict()

        assert isinstance(results, list)
        assert all(isinstance(value, dict) for value in results)

        dictionary = next(
            iter(results[0].values())
        )  # `results` should have the form [{'Data_1': {'*': Node, 'id': 1}}]

        assert isinstance(dictionary['*'], orm.Data)
        assert dictionary['*'].pk == node.pk
        assert dictionary['id'] == node.pk

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_operators_eq_lt_gt(self):
        nodes = [orm.Data() for _ in range(8)]

        nodes[0].base.attributes.set('fa', 1)
        nodes[1].base.attributes.set('fa', 1.0)
        nodes[2].base.attributes.set('fa', 1.01)
        nodes[3].base.attributes.set('fa', 1.02)
        nodes[4].base.attributes.set('fa', 1.03)
        nodes[5].base.attributes.set('fa', 1.04)
        nodes[6].base.attributes.set('fa', 1.05)
        nodes[7].base.attributes.set('fa', 1.06)

        for n in nodes:
            n.store()

        assert orm.QueryBuilder().append(orm.Node, filters={'attributes.fa': {'<': 1}}).count() == 0
        assert orm.QueryBuilder().append(orm.Node, filters={'attributes.fa': {'==': 1}}).count() == 2
        assert orm.QueryBuilder().append(orm.Node, filters={'attributes.fa': {'<': 1.02}}).count() == 3
        assert orm.QueryBuilder().append(orm.Node, filters={'attributes.fa': {'<=': 1.02}}).count() == 4
        assert orm.QueryBuilder().append(orm.Node, filters={'attributes.fa': {'>': 1.02}}).count() == 4
        assert orm.QueryBuilder().append(orm.Node, filters={'attributes.fa': {'>=': 1.02}}).count() == 5

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_subclassing(self):
        s = orm.StructureData()
        s.base.attributes.set('cat', 'miau')
        s.set_pbc(False)
        s.store()

        d = orm.Data()
        d.base.attributes.set('cat', 'miau')
        d.store()

        p = orm.Dict(dict={'cat': 'miau'})
        p.store()

        # Now when asking for a node with attr.cat==miau, I want 3 esults:
        qb = orm.QueryBuilder().append(orm.Node, filters={'attributes.cat': 'miau'})
        assert qb.count() == 3

        qb = orm.QueryBuilder().append(orm.Data, filters={'attributes.cat': 'miau'})
        assert qb.count() == 3

        # If I'm asking for the specific lowest subclass, I want one result
        for cls in (orm.StructureData, orm.Dict):
            qb = orm.QueryBuilder().append(cls, filters={'attributes.cat': 'miau'})
            assert qb.count() == 1

        # Now I am not allow the subclassing, which should give 1 result for each
        for cls, count in ((orm.StructureData, 1), (orm.Dict, 1), (orm.Data, 1), (orm.Node, 0)):
            qb = orm.QueryBuilder().append(cls, filters={'attributes.cat': 'miau'}, subclassing=False)
            assert qb.count() == count

        # Now I am testing the subclassing with tuples:
        qb = orm.QueryBuilder().append(cls=(orm.StructureData, orm.Dict), filters={'attributes.cat': 'miau'})
        assert qb.count() == 2
        qb = orm.QueryBuilder().append(
            entity_type=('data.core.structure.StructureData.', 'data.core.dict.Dict.'),
            filters={'attributes.cat': 'miau'},
        )
        assert qb.count() == 2
        qb = orm.QueryBuilder().append(
            cls=(orm.StructureData, orm.Dict), filters={'attributes.cat': 'miau'}, subclassing=False
        )
        assert qb.count() == 2
        qb = orm.QueryBuilder().append(
            cls=(orm.StructureData, orm.Data),
            filters={'attributes.cat': 'miau'},
        )
        assert qb.count() == 3
        qb = orm.QueryBuilder().append(
            entity_type=('data.core.structure.StructureData.', 'data.core.dict.Dict.'),
            filters={'attributes.cat': 'miau'},
            subclassing=False,
        )
        assert qb.count() == 2
        qb = orm.QueryBuilder().append(
            entity_type=('data.core.structure.StructureData.', 'data.Data.'),
            filters={'attributes.cat': 'miau'},
            subclassing=False,
        )
        assert qb.count() == 2

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_list_behavior(self):
        for _i in range(4):
            orm.Data().store()

        assert len(orm.QueryBuilder().append(orm.Node).all()) == 4
        assert len(orm.QueryBuilder().append(orm.Node, project='*').all()) == 4
        assert len(orm.QueryBuilder().append(orm.Node, project=['*', 'id']).all()) == 4
        assert len(orm.QueryBuilder().append(orm.Node, project=['id']).all()) == 4
        assert len(orm.QueryBuilder().append(orm.Node).dict()) == 4
        assert len(orm.QueryBuilder().append(orm.Node, project='*').dict()) == 4
        assert len(orm.QueryBuilder().append(orm.Node, project=['*', 'id']).dict()) == 4
        assert len(orm.QueryBuilder().append(orm.Node, project=['id']).dict()) == 4
        assert len(list(orm.QueryBuilder().append(orm.Node).iterall())) == 4
        assert len(list(orm.QueryBuilder().append(orm.Node, project='*').iterall())) == 4
        assert len(list(orm.QueryBuilder().append(orm.Node, project=['*', 'id']).iterall())) == 4
        assert len(list(orm.QueryBuilder().append(orm.Node, project=['id']).iterall())) == 4
        assert len(list(orm.QueryBuilder().append(orm.Node).iterdict())) == 4
        assert len(list(orm.QueryBuilder().append(orm.Node, project='*').iterdict())) == 4
        assert len(list(orm.QueryBuilder().append(orm.Node, project=['*', 'id']).iterdict())) == 4
        assert len(list(orm.QueryBuilder().append(orm.Node, project=['id']).iterdict())) == 4

    def test_append_validation(self):
        # So here I am giving two times the same tag
        with pytest.raises(ValueError):
            orm.QueryBuilder().append(orm.StructureData, tag='n').append(orm.StructureData, tag='n')
        # here I am giving a wrong filter specifications
        with pytest.raises(TypeError):
            orm.QueryBuilder().append(orm.StructureData, filters=['jajjsd'])
        # here I am giving a nonsensical projection:
        with pytest.raises(ValueError):
            orm.QueryBuilder().append(orm.StructureData, project=True)

        # here I am giving a nonsensical projection for the edge:
        with pytest.raises(ValueError):
            orm.QueryBuilder().append(orm.ProcessNode).append(orm.StructureData, edge_tag='t').add_projection('t', True)
        # Giving a nonsensical limit
        with pytest.raises(TypeError):
            orm.QueryBuilder().append(orm.ProcessNode).limit(2.3)
        # Giving a nonsensical offset
        with pytest.raises(TypeError):
            orm.QueryBuilder(offset=2.3)

        # So, I mess up one append, I want the QueryBuilder to clean it!
        with pytest.raises(ValueError):
            qb = orm.QueryBuilder()
            # This also checks if we correctly raise for wrong keywords
            qb.append(orm.StructureData, tag='s', randomkeyword={})

        # Now I'm checking whether this keyword appears anywhere in the internal dictionaries:

        assert 's' not in qb._projections
        assert 's' not in qb._filters
        assert 's' not in qb._tags
        assert len(qb._path) == 0
        with pytest.raises(ValueError):
            qb._tags.get(orm.StructureData)
        # So this should work now:
        qb.append(orm.StructureData, tag='s').limit(2).dict()

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_tuples(self):
        """Test appending ``cls`` tuples."""
        orm.Group(label='helloworld').store()

        qb = orm.QueryBuilder().append(orm.Group, filters={'label': 'helloworld'})
        assert qb.count() == 1

        qb = orm.QueryBuilder().append((orm.Group,), filters={'label': 'helloworld'})
        assert qb.count() == 1

        qb = orm.QueryBuilder().append(cls=(orm.Group,))
        assert qb.count() == 1

    def test_tags(self):
        qb = orm.QueryBuilder()
        qb.append(orm.Node, tag='n1')
        qb.append(orm.Node, tag='n2', edge_tag='e1', with_incoming='n1')
        qb.append(orm.Node, tag='n3', edge_tag='e2', with_incoming='n2')
        qb.append(orm.Computer, with_node='n3', tag='c1', edge_tag='nonsense')
        assert qb.get_used_tags() == ['n1', 'n2', 'e1', 'n3', 'e2', 'c1', 'nonsense']

        # Now I am testing the default tags,
        qb = (
            orm.QueryBuilder()
            .append(orm.StructureData)
            .append(orm.ProcessNode)
            .append(orm.StructureData)
            .append(orm.Dict, with_outgoing=orm.ProcessNode)
        )
        assert qb.get_used_tags() == [
            'StructureData_1',
            'ProcessNode_1',
            'StructureData_1--ProcessNode_1',
            'StructureData_2',
            'ProcessNode_1--StructureData_2',
            'Dict_1',
            'ProcessNode_1--Dict_1',
        ]
        assert qb.get_used_tags(edges=False) == [
            'StructureData_1',
            'ProcessNode_1',
            'StructureData_2',
            'Dict_1',
        ]
        assert qb.get_used_tags(vertices=False) == [
            'StructureData_1--ProcessNode_1',
            'ProcessNode_1--StructureData_2',
            'ProcessNode_1--Dict_1',
        ]
        assert qb.get_used_tags(edges=False) == [
            'StructureData_1',
            'ProcessNode_1',
            'StructureData_2',
            'Dict_1',
        ]
        assert qb.get_used_tags(vertices=False) == [
            'StructureData_1--ProcessNode_1',
            'ProcessNode_1--StructureData_2',
            'ProcessNode_1--Dict_1',
        ]

    def test_direction_keyword(self):
        """The direction keyword is a special case with the QueryBuilder append
        method, so some tests are good.
        """
        d1, d2, d3, d4 = [orm.Data().store() for _ in range(4)]
        c1, c2 = [orm.CalculationNode() for _ in range(2)]
        c1.base.links.add_incoming(d1, link_type=LinkType.INPUT_CALC, link_label='link_d1c1')
        c1.store()
        d2.base.links.add_incoming(c1, link_type=LinkType.CREATE, link_label='link_c1d2')
        d4.base.links.add_incoming(c1, link_type=LinkType.CREATE, link_label='link_c1d4')
        c2.base.links.add_incoming(d2, link_type=LinkType.INPUT_CALC, link_label='link_d2c2')
        c2.store()
        d3.base.links.add_incoming(c2, link_type=LinkType.CREATE, link_label='link_c2d3')

        # testing direction=1 for d1, which should return the outgoing
        qb = orm.QueryBuilder()
        qb.append(orm.Data, filters={'id': d1.pk})
        qb.append(orm.CalculationNode, direction=1, project='id')
        res1 = {_ for (_,) in qb.all()}

        qb = orm.QueryBuilder()
        qb.append(orm.Data, filters={'id': d1.pk}, tag='data')
        qb.append(orm.CalculationNode, with_incoming='data', project='id')
        res2 = {_ for (_,) in qb.all()}

        assert res1 == res2
        assert res1 == {c1.pk}

        # testing direction=-1, which should return the incoming
        qb = orm.QueryBuilder()
        qb.append(orm.Data, filters={'id': d2.pk})
        qb.append(orm.CalculationNode, direction=-1, project='id')
        res1 = {_ for (_,) in qb.all()}

        qb = orm.QueryBuilder()
        qb.append(orm.Data, filters={'id': d2.pk}, tag='data')
        qb.append(orm.CalculationNode, with_outgoing='data', project='id')
        res2 = {_ for (_,) in qb.all()}
        assert res1 == res2
        assert res1 == {c1.pk}

        # testing direction higher than 1
        qb = orm.QueryBuilder()
        qb.append(orm.CalculationNode, tag='c1', filters={'id': c1.pk})
        qb.append(orm.Data, with_incoming='c1', tag='d2or4')
        qb.append(orm.CalculationNode, tag='c2', with_incoming='d2or4')
        qb.append(orm.Data, tag='d3', with_incoming='c2', project='id')
        qh = qb.as_dict()  # saving query for later
        qb.append(orm.Data, direction=-4, project='id')
        res1 = {item[1] for item in qb.all()}
        assert res1 == {d1.pk}

        qb = orm.QueryBuilder(**qh)
        qb.append(orm.Data, direction=4, project='id')
        res2 = {item[1] for item in qb.all()}
        assert res2 == {d2.pk, d4.pk}

    @staticmethod
    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_all_flat():
        """Test the `flat` keyword for the `QueryBuilder.all()` method."""
        pks = []
        uuids = []
        for _ in range(10):
            node = orm.Data().store()
            pks.append(node.pk)
            uuids.append(node.uuid)

        # Single projected property
        builder = orm.QueryBuilder().append(orm.Data, project='id').order_by({orm.Data: 'id'})
        result = builder.all(flat=True)
        assert isinstance(result, list)
        assert len(result) == 10
        assert result == pks

        # Multiple projections
        builder = orm.QueryBuilder().append(orm.Data, project=['id', 'uuid']).order_by({orm.Data: 'id'})
        result = builder.all(flat=True)
        assert isinstance(result, list)
        assert len(result) == 20
        assert result == list(chain.from_iterable(zip(pks, uuids)))

    @staticmethod
    def test_first_flat():
        """Test the `flat` keyword for the `QueryBuilder.first()` method."""
        node = orm.Data().store()

        # Single projected property
        query = orm.QueryBuilder().append(orm.Data, project='id', filters={'id': node.pk})
        assert query.first(flat=True) == node.pk

        # Mutltiple projections
        query = orm.QueryBuilder().append(orm.Data, project=['id', 'uuid'], filters={'id': node.pk})
        assert query.first(flat=True) == [node.pk, node.uuid]

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_query_links(self):
        """Test querying for links"""
        d1, d2, d3, d4 = [orm.Data().store() for _ in range(4)]
        c1, c2 = [orm.CalculationNode() for _ in range(2)]
        c1.base.links.add_incoming(d1, link_type=LinkType.INPUT_CALC, link_label='link_d1c1')
        c1.store()
        d2.base.links.add_incoming(c1, link_type=LinkType.CREATE, link_label='link_c1d2')
        d4.base.links.add_incoming(c1, link_type=LinkType.CREATE, link_label='link_c1d4')
        c2.base.links.add_incoming(d2, link_type=LinkType.INPUT_CALC, link_label='link_d2c2')
        c2.store()
        d3.base.links.add_incoming(c2, link_type=LinkType.CREATE, link_label='link_c2d3')

        builder = orm.QueryBuilder().append(entity_type='link')
        assert builder.count() == 5

        builder = orm.QueryBuilder().append(entity_type='link', filters={'type': LinkType.CREATE.value})
        assert builder.count() == 3

        builder = orm.QueryBuilder().append(entity_type='link', filters={'label': 'link_d2c2'})
        assert builder.one()[0] == LinkQuadruple(d2.pk, c2.pk, LinkType.INPUT_CALC.value, 'link_d2c2')


class TestMultipleProjections:
    """Unit tests for the QueryBuilder ORM class."""

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_first_multiple_projections(self):
        """Test `first()` returns correct types and numbers for multiple projections."""
        orm.Data().store()
        orm.Data().store()

        query = orm.QueryBuilder()
        query.append(orm.User, tag='user', project=['email'])
        query.append(orm.Data, with_user='user', project=['*'])

        result = query.first()

        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], orm.Data)


class TestRepresentations:
    """Test representing the query in different formats."""

    @pytest.fixture(autouse=True)
    def init_db(self, data_regression, file_regression):
        self.regress_dict = data_regression.check
        self.regress_str = file_regression.check

    def test_str(self):
        """Test ``str(qb)`` returns the correct string."""
        qb = orm.QueryBuilder().append(orm.Data, project=['id', 'uuid']).order_by({orm.Data: 'id'})
        self.regress_str(str(qb))

    @pytest.mark.requires_psql
    def test_as_sql(self):
        """Test ``qb.as_sql(inline=False)`` returns the correct string."""
        qb = orm.QueryBuilder()
        qb.append(orm.Node, project=['uuid'], filters={'extras.tag4': 'appl_pecoal'})
        self.regress_str(qb.as_sql(inline=False))

    @pytest.mark.requires_psql
    def test_as_sql_inline(self):
        """Test ``qb.as_sql(inline=True)`` returns the correct string."""
        qb = orm.QueryBuilder()
        qb.append(orm.Node, project=['uuid'], filters={'extras.tag4': 'appl_pecoal'})
        self.regress_str(qb.as_sql(inline=True))

    @pytest.mark.requires_psql
    def test_as_sql_literal_quote(self):
        """Test that literal values can be rendered."""
        qb = orm.QueryBuilder()
        qb.append(
            plugins.DataFactory('core.structure'), project=['uuid'], filters={'extras.elements': {'contains': ['Si']}}
        )
        self.regress_str(qb.as_sql(inline=True))

    def test_as_dict(self):
        """Test ``qb.as_dict()`` returns the correct dict."""
        qb = orm.QueryBuilder()
        qb.append(orm.Node, filters={'extras.tag4': 'appl_pecoal'})
        self.regress_dict(qb.as_dict())

    def test_round_trip(self):
        """Test recreating a QueryBuilder from the ``as_dict`` representation

        We test appending a Data node and a Process node for variety, as well
        as a generic Node specifically because it translates to `entity_type`
        as an empty string (which can potentially cause problems).
        """
        qb1 = orm.QueryBuilder()
        qb1.append(orm.Node)
        qb1.append(orm.Data)
        qb1.append(orm.CalcJobNode)

        qb2 = orm.QueryBuilder.from_dict(qb1.as_dict())
        assert qb1.as_dict() == qb2.as_dict()

        qb3 = copy.deepcopy(qb1)
        assert qb1.as_dict() == qb3.as_dict()

    def test_round_trip_append(self):
        """Test the `as_dict` and `from_dict` methods,
        by seeing whether results are the same as using the append method.
        """
        g = orm.Group(label=str(uuid.uuid4())).store()
        for cls in (orm.StructureData, orm.Dict, orm.Data):
            obj = cls()
            obj.base.attributes.set('foo-qh2', 'bar')
            if cls is orm.StructureData:
                obj.set_pbc(False)
            obj.store()
            g.add_nodes(obj)

        for cls, expected_count, subclassing in (
            (orm.StructureData, 1, True),
            (orm.Dict, 1, True),
            (orm.Data, 3, True),
            (orm.Data, 1, False),
            ((orm.Dict, orm.StructureData), 2, True),
            ((orm.Dict, orm.StructureData), 2, False),
            ((orm.Dict, orm.Data), 2, False),
            ((orm.Dict, orm.Data), 3, True),
            ((orm.Dict, orm.Data, orm.StructureData), 3, False),
        ):
            qb = orm.QueryBuilder()
            qb.append(cls, filters={'attributes.foo-qh2': 'bar'}, subclassing=subclassing, project='uuid')
            assert qb.count() == expected_count

            dct = qb.as_dict()
            qb_new = orm.QueryBuilder.from_dict(dct)
            assert qb_new.count() == expected_count
            assert sorted([uuid for (uuid,) in qb.all()]) == sorted([uuid for (uuid,) in qb_new.all()])


@pytest.mark.requires_psql
def test_analyze_query():
    """Test the query plan is correctly generated."""
    qb = orm.QueryBuilder()
    # include literal values in test
    qb.append(orm.Data, filters={'extras.key': {'contains': ['x', 1]}})
    analysis_str = qb.analyze_query(verbose=True)
    assert isinstance(analysis_str, str), analysis_str
    assert 'uuid' in analysis_str, analysis_str


class TestQueryBuilderCornerCases:
    """In this class corner cases of QueryBuilder are added."""

    def test_computer_json(self):
        """In this test we check the correct behavior of QueryBuilder when
        retrieving the _metadata with no content.
        Note that they are in JSON format in both backends. Forcing the
        decoding of a None value leads to an exception (this was the case
        under Django).
        """
        n1 = orm.CalculationNode()
        n1.label = 'node2'
        n1.base.attributes.set('foo', 1)
        n1.store()

        # Checking the correct retrieval of _metadata which is
        # a JSON field (in both backends).
        qb = orm.QueryBuilder()
        qb.append(orm.CalculationNode, project=['id'], tag='calc')
        qb.append(orm.Computer, project=['id', 'metadata'], outerjoin=True, with_node='calc')
        qb.all()

    def test_empty_filters(self):
        """Test that an empty filter is correctly handled."""
        count = orm.Data.collection.count()
        qb = orm.QueryBuilder().append(orm.Data, filters={})
        assert qb.count() == count
        qb = orm.QueryBuilder().append(orm.Data, filters={'or': [{}, {}]})
        assert qb.count() == count

    @pytest.mark.usefixtures('suppress_internal_deprecations')
    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_abstract_code_filtering(self, aiida_localhost, aiida_code, tmp_path):
        """Test that querying for AbstractCode correctly returns all code instances.

        This tests the fix for issue #6687, where QueryBuilder couldn't find codes
        when looking for AbstractCode due to a node_type mismatch.
        """
        installed_code = aiida_code(
            'core.code.installed',
            label='installed-code',
            computer=aiida_localhost,
            filepath_executable='/bin/bash',
        )
        (tmp_path / 'fake_exec').touch()
        portable_code = aiida_code(
            'core.code.portable',
            label='portable-code',
            filepath_executable='fake_exec',
            filepath_files=tmp_path,
        )
        legacy_code = aiida_code(
            'core.code',
            label='legacy-code',
            remote_computer_exec=(aiida_localhost, '/bin/bash'),
        )

        qb = orm.QueryBuilder

        # Verify specific code type queries work as expected
        installed_results = qb().append(orm.InstalledCode).all(flat=True)
        assert installed_code in installed_results
        assert len(installed_results) == 1

        portable_results = qb().append(orm.PortableCode).all(flat=True)
        assert portable_code in portable_results
        assert len(portable_results) == 1

        # Using orm.Code actually matches all codes.
        # for backwards compatibility reasons we will not fix this.
        legacy_results = qb().append(orm.Code).all(flat=True)
        assert legacy_code in legacy_results
        assert len(legacy_results) == 3

        # Turning off subclassing should however only match the one legacy Code
        legacy_results = qb().append(orm.Code, subclassing=False).all(flat=True)
        assert legacy_code in legacy_results
        assert len(legacy_results) == 1

        # AbstractCode query should find all code types
        abstract_results = qb().append(orm.AbstractCode).all(flat=True)
        assert (
            installed_code in abstract_results
        ), f'InstalledCode not found with AbstractCode query. Result: {abstract_results}'
        assert (
            portable_code in abstract_results
        ), f'PortableCode not found with AbstractCode query. Result: {abstract_results}'
        assert legacy_code in abstract_results, f'Code not found with AbstractCode query. Result: {abstract_results}'
        assert len(abstract_results) == 3

        # AbstractCode with basic filtering
        qb_filtered = qb().append(orm.AbstractCode, filters={'label': 'installed-code'})
        filtered_results = qb_filtered.all(flat=True)
        assert installed_code in filtered_results
        assert len(filtered_results) == 1

        # QB should find no codes if subclassing is False
        subclassing_off_results = qb().append(orm.AbstractCode, subclassing=False).all(flat=True)
        assert len(subclassing_off_results) == 0


class TestAttributes:
    @pytest.mark.requires_psql
    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_attribute_existence(self):
        # I'm storing a value under key whatever:
        val = 1.0
        res_uuids = set()
        n1 = orm.Data()
        n1.base.attributes.set('whatever', 3.0)
        n1.base.attributes.set('test_case', 'test_attribute_existence')
        n1.store()

        # I want all the nodes where whatever is smaller than 1. or there is no such value:

        qb = orm.QueryBuilder()
        qb.append(
            orm.Data,
            filters={
                'or': [{'attributes': {'!has_key': 'whatever'}}, {'attributes.whatever': {'<': val}}],
            },
            project='uuid',
        )
        res_query = {str(_[0]) for _ in qb.all()}
        assert res_query == res_uuids

    @pytest.mark.requires_psql
    def test_attribute_type(self):
        key = 'value_test_attr_type'
        n_int, n_float, n_str, n_str2, n_bool, n_arr = [orm.Data() for _ in range(6)]
        n_int.base.attributes.set(key, 1)
        n_float.base.attributes.set(key, 1.0)
        n_bool.base.attributes.set(key, True)
        n_str.base.attributes.set(key, '1')
        n_str2.base.attributes.set(key, 'one')
        n_arr.base.attributes.set(key, [4, 3, 5])

        for n in (n_str2, n_str, n_int, n_float, n_bool, n_arr):
            n.store()

        # Here I am testing which values contain a number 1.
        # Both 1 and 1.0 are legitimate values if ask for either 1 or 1.0
        for val in (1.0, 1):
            qb = orm.QueryBuilder().append(orm.Node, filters={f'attributes.{key}': val}, project='uuid')
            res = [str(_) for (_,) in qb.all()]
            assert set(res) == set((n_float.uuid, n_int.uuid))
            qb = orm.QueryBuilder().append(orm.Node, filters={f'attributes.{key}': {'>': 0.5}}, project='uuid')
            res = [str(_) for (_,) in qb.all()]
            assert set(res) == set((n_float.uuid, n_int.uuid))
            qb = orm.QueryBuilder().append(orm.Node, filters={f'attributes.{key}': {'<': 1.5}}, project='uuid')
            res = [str(_) for (_,) in qb.all()]
            assert set(res) == set((n_float.uuid, n_int.uuid))
        # Now I am testing the boolean value:
        qb = orm.QueryBuilder().append(orm.Node, filters={f'attributes.{key}': True}, project='uuid')
        res = [str(_) for (_,) in qb.all()]
        assert set(res) == set((n_bool.uuid,))

        qb = orm.QueryBuilder().append(orm.Node, filters={f'attributes.{key}': {'like': '%n%'}}, project='uuid')
        res = [str(_) for (_,) in qb.all()]
        assert set(res) == set((n_str2.uuid,))
        qb = orm.QueryBuilder().append(orm.Node, filters={f'attributes.{key}': {'ilike': 'On%'}}, project='uuid')
        res = [str(_) for (_,) in qb.all()]
        assert set(res) == set((n_str2.uuid,))
        qb = orm.QueryBuilder().append(orm.Node, filters={f'attributes.{key}': {'like': '1'}}, project='uuid')
        res = [str(_) for (_,) in qb.all()]
        assert set(res) == set((n_str.uuid,))
        qb = orm.QueryBuilder().append(orm.Node, filters={f'attributes.{key}': {'==': '1'}}, project='uuid')
        res = [str(_) for (_,) in qb.all()]
        assert set(res) == set((n_str.uuid,))
        qb = orm.QueryBuilder().append(orm.Node, filters={f'attributes.{key}': {'of_length': 3}}, project='uuid')
        res = [str(_) for (_,) in qb.all()]
        assert set(res) == set((n_arr.uuid,))


class TestQueryBuilderLimitOffsets:
    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_ordering_limits_offsets_of_results_general(self):
        # Creating 10 nodes with an attribute that can be ordered
        for i in range(10):
            n = orm.Data()
            n.base.attributes.set('foo', i)
            n.store()

        qb = orm.QueryBuilder().append(orm.Node, project='attributes.foo').order_by({orm.Node: 'ctime'})

        res = next(zip(*qb.all()))
        assert res == tuple(range(10))

        # Now applying an offset:
        qb.offset(5)
        res = next(zip(*qb.all()))
        assert res == tuple(range(5, 10))

        # Now also applying a limit:
        qb.limit(3)
        res = next(zip(*qb.all()))
        assert res == tuple(range(5, 8))

        # Specifying the order  explicitly the order:
        qb = (
            orm.QueryBuilder()
            .append(orm.Node, project='attributes.foo')
            .order_by({orm.Node: {'ctime': {'order': 'asc'}}})
        )

        res = next(zip(*qb.all()))
        assert res == tuple(range(10))

        # Now applying an offset:
        qb.offset(5)
        res = next(zip(*qb.all()))
        assert res == tuple(range(5, 10))

        # Now also applying a limit:
        qb.limit(3)
        res = next(zip(*qb.all()))
        assert res == tuple(range(5, 8))

        # Reversing the order:
        qb = (
            orm.QueryBuilder()
            .append(orm.Node, project='attributes.foo')
            .order_by({orm.Node: {'ctime': {'order': 'desc'}}})
        )

        res = next(zip(*qb.all()))
        assert res == tuple(range(9, -1, -1))

        # Now applying an offset:
        qb.offset(5)
        res = next(zip(*qb.all()))
        assert res == tuple(range(4, -1, -1))

        # Now also applying a limit:
        qb.limit(3)
        res = next(zip(*qb.all()))
        assert res == tuple(range(4, 1, -1))


class TestQueryBuilderJoins:
    def test_joins_node_incoming(self):
        # Creating n1, who will be a parent:
        parent = orm.Data()
        parent.label = 'mother'
        parent.store()

        good_child = orm.CalculationNode()
        good_child.label = 'good_child'
        good_child.base.attributes.set('is_good', True)

        bad_child = orm.CalculationNode()
        bad_child.label = 'bad_child'
        bad_child.base.attributes.set('is_good', False)

        unrelated = orm.CalculationNode()
        unrelated.label = 'unrelated'
        unrelated.store()

        good_child.base.links.add_incoming(parent, link_type=LinkType.INPUT_CALC, link_label='parent')
        bad_child.base.links.add_incoming(parent, link_type=LinkType.INPUT_CALC, link_label='parent')
        good_child.store()
        bad_child.store()

        # Using a standard inner join
        qb = orm.QueryBuilder()
        qb.append(orm.Node, tag='parent')
        qb.append(orm.Node, tag='children', project='label', filters={'attributes.is_good': True})
        assert qb.count() == 1

        qb = orm.QueryBuilder()
        qb.append(orm.Node, tag='parent')
        qb.append(orm.Node, tag='children', outerjoin=True, project='label', filters={'attributes.is_good': True})
        assert qb.count() == 1

    def test_joins_node_incoming2(self):
        # Creating n1, who will be a parent:

        students = [orm.Data() for i in range(10)]
        advisors = [orm.CalculationNode() for i in range(3)]
        for i, a in enumerate(advisors):
            a.label = f'advisor {i}'
            a.base.attributes.set('advisor_id', i)

        for n in advisors + students:
            n.store()

        # advisor 0 get student 0, 1
        for i in (0, 1):
            students[i].base.links.add_incoming(advisors[0], link_type=LinkType.CREATE, link_label=f'is_advisor_{i}')

        # advisor 1 get student 3, 4
        for i in (3, 4):
            students[i].base.links.add_incoming(advisors[1], link_type=LinkType.CREATE, link_label=f'is_advisor_{i}')

        # advisor 2 get student 5, 6, 7
        for i in (5, 6, 7):
            students[i].base.links.add_incoming(advisors[2], link_type=LinkType.CREATE, link_label=f'is_advisor_{i}')

        # let's add a differnt relationship than advisor:
        students[9].base.links.add_incoming(advisors[2], link_type=LinkType.CREATE, link_label='lover')

        assert (
            orm.QueryBuilder()
            .append(orm.Node)
            .append(orm.Node, edge_filters={'label': {'like': 'is\\_advisor\\_%'}}, tag='student')
            .count()
            == 7
        )

        for adv_id, number_students in zip(list(range(3)), (2, 2, 3)):
            assert (
                orm.QueryBuilder()
                .append(orm.Node, filters={'attributes.advisor_id': adv_id})
                .append(orm.Node, edge_filters={'label': {'like': 'is\\_advisor\\_%'}}, tag='student')
                .count()
                == number_students
            )

    def test_joins_user_group(self):
        # Create another user
        new_email = 'newuser@new.n'
        user = orm.User(email=new_email).store()

        # Create a group that belongs to that user
        group = orm.Group(label='node_group')
        group.user = user
        group.store()

        # Search for the group of the user
        qb = orm.QueryBuilder()
        qb.append(orm.User, tag='user', filters={'id': {'==': user.pk}})
        qb.append(orm.Group, with_user='user', filters={'id': {'==': group.pk}})
        assert qb.count() == 1, 'The expected group that belongs to the selected user was not found.'

        # Search for the user that owns a group
        qb = orm.QueryBuilder()
        qb.append(orm.Group, tag='group', filters={'id': {'==': group.pk}})
        qb.append(orm.User, with_group='group', filters={'id': {'==': user.pk}})

        assert qb.count() == 1, 'The expected user that owns the selected group was not found.'

    def test_joins_user_authinfo(self):
        """Test querying for user with particular authinfo"""
        user = orm.User(email='email@new.com').store()
        computer = orm.Computer(
            label='new', hostname='localhost', transport_type='core.local', scheduler_type='core.direct'
        ).store()
        authinfo = computer.configure(user)
        qb = orm.QueryBuilder()
        qb.append(orm.AuthInfo, tag='auth', filters={'id': {'==': authinfo.pk}})
        qb.append(orm.User, with_authinfo='auth')
        assert qb.count() == 1, 'The expected user that owns the selected authinfo was not found.'
        assert qb.one()[0].pk == user.pk

    def test_joins_authinfo(self):
        """Test querying for AuthInfo with specific computer/user."""
        user = orm.User(email=str(uuid.uuid4())).store()
        computer = orm.Computer(
            label=str(uuid.uuid4()), hostname='localhost', transport_type='core.local', scheduler_type='core.direct'
        ).store()
        authinfo = computer.configure(user)

        # Search for the user of the authinfo
        qb = orm.QueryBuilder()
        qb.append(orm.User, tag='user', filters={'id': {'==': user.pk}})
        qb.append(orm.AuthInfo, with_user='user', filters={'id': {'==': authinfo.pk}})
        assert qb.count() == 1, 'The expected user that owns the selected authinfo was not found.'

        # Search for the computer of the authinfo
        qb = orm.QueryBuilder()
        qb.append(orm.Computer, tag='computer', filters={'id': {'==': computer.pk}})
        qb.append(orm.AuthInfo, with_computer='computer', filters={'id': {'==': authinfo.pk}})
        assert qb.count() == 1, 'The expected computer that owns the selected authinfo was not found.'

    def test_joins_group_node(self):
        """This test checks that the querying for the nodes that belong to a group works correctly (using QueryBuilder).
        This is important for the Django backend with the use of aldjemy for the Django to SQLA schema translation.
        Since this is not backend specific test (even if it is mainly used to test the querying of Django backend
        with QueryBuilder), we keep it at the general tests (ran by both backends).
        """
        new_email = 'newuser@new.n2'
        user = orm.User(email=new_email).store()

        # Create a group that belongs to that user
        group = orm.Group(label='node_group_2')
        group.user = user
        group.store()

        # Create nodes and add them to the created group
        n1 = orm.Data()
        n1.label = 'node1'
        n1.base.attributes.set('foo', ['hello', 'goodbye'])
        n1.store()

        n2 = orm.CalculationNode()
        n2.label = 'node2'
        n2.base.attributes.set('foo', 1)
        n2.store()

        n3 = orm.Data()
        n3.label = 'node3'
        n3.base.attributes.set('foo', 1.0000)  # Stored as fval
        n3.store()

        n4 = orm.CalculationNode()
        n4.label = 'node4'
        n4.base.attributes.set('foo', 'bar')
        n4.store()

        group.add_nodes([n1, n2, n3, n4])

        # Check that the nodes are in the group
        qb = orm.QueryBuilder()
        qb.append(orm.Node, tag='node', project=['id'])
        qb.append(orm.Group, with_node='node', filters={'id': {'==': group.pk}})
        assert qb.count() == 4, 'There should be 4 nodes in the group'
        id_res = qb.all(flat=True)
        for curr_id in [n1.pk, n2.pk, n3.pk, n4.pk]:
            assert curr_id in id_res

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_joins_group_node_distinct(self):
        """Test that when protecting only the group for a join on nodes, only unique groups are returned.

        Regression test for #5535
        """
        group = orm.Group(label='mygroup').store()
        node_a = orm.Data().store()
        node_b = orm.Data().store()
        group.add_nodes([node_a, node_b])

        # First join the group on the data
        query = orm.QueryBuilder()
        query.append(orm.Group, project='id', tag='group')
        query.append(orm.Data, with_group='group')
        query.distinct()

        assert query.count() == 1
        assert query.all(flat=True) == [group.pk]

        # Then reverse and join the data on the group
        query = orm.QueryBuilder()
        query.append(orm.Data, tag='node')
        query.append(orm.Group, with_node='node', project='uuid')
        query.distinct()

        assert query.all(flat=True) == [group.uuid]
        assert query.count() == 1


class QueryBuilderPath:
    @pytest.fixture(autouse=True)
    def init_db(self, backend):
        self.backend = backend

    @staticmethod
    def get_all_parents(node_pks, return_values=('id',)):
        """Get all the parents of given nodes

        :param node_pks: one node pk or an iterable of node pks
        :return: a list of aiida objects with all the parents of the nodes
        """
        from aiida.orm import Node, QueryBuilder

        q_build = QueryBuilder()
        q_build.append(Node, tag='low_node', filters={'id': {'in': node_pks}})
        q_build.append(Node, with_descendants='low_node', project=return_values)
        return q_build.all()

    def test_query_path(self):
        n1 = orm.Data()
        n1.label = 'n1'
        n2 = orm.CalculationNode()
        n2.label = 'n2'
        n3 = orm.Data()
        n3.label = 'n3'
        n4 = orm.Data()
        n4.label = 'n4'
        n5 = orm.CalculationNode()
        n5.label = 'n5'
        n6 = orm.Data()
        n6.label = 'n6'
        n7 = orm.CalculationNode()
        n7.label = 'n7'
        n8 = orm.Data()
        n8.label = 'n8'
        n9 = orm.Data()
        n9.label = 'n9'

        # I create a strange graph, inserting links in a order
        # such that I often have to create the transitive closure
        # between two graphs
        n3.base.links.add_incoming(n2, link_type=LinkType.CREATE, link_label='link1')
        n2.base.links.add_incoming(n1, link_type=LinkType.INPUT_CALC, link_label='link2')
        n5.base.links.add_incoming(n3, link_type=LinkType.INPUT_CALC, link_label='link3')
        n5.base.links.add_incoming(n4, link_type=LinkType.INPUT_CALC, link_label='link4')
        n4.base.links.add_incoming(n2, link_type=LinkType.CREATE, link_label='link5')
        n7.base.links.add_incoming(n6, link_type=LinkType.INPUT_CALC, link_label='link6')
        n8.base.links.add_incoming(n7, link_type=LinkType.CREATE, link_label='link7')

        for node in [n1, n2, n3, n4, n5, n6, n7, n8, n9]:
            node.store()

        # There are no parents to n9, checking that
        assert set([]) == set(self.get_all_parents([n9.pk]))
        # There is one parent to n6
        assert {(_,) for _ in (n6.pk,)} == {tuple(_) for _ in self.get_all_parents([n7.pk])}
        # There are several parents to n4
        assert {(_.pk,) for _ in (n1, n2)} == {tuple(_) for _ in self.get_all_parents([n4.pk])}
        # There are several parents to n5
        assert {(_.pk,) for _ in (n1, n2, n3, n4)} == {tuple(_) for _ in self.get_all_parents([n5.pk])}

        # Yet, no links from 1 to 8
        assert (
            orm.QueryBuilder()
            .append(orm.Node, filters={'id': n1.pk}, tag='anc')
            .append(orm.Node, with_ancestors='anc', filters={'id': n8.pk})
            .count()
            == 0
        )

        assert (
            orm.QueryBuilder()
            .append(orm.Node, filters={'id': n8.pk}, tag='desc')
            .append(orm.Node, with_descendants='desc', filters={'id': n1.pk})
            .count()
            == 0
        )

        n6.base.links.add_incoming(n5, link_type=LinkType.CREATE, link_label='link1')
        # Yet, now 2 links from 1 to 8
        assert (
            orm.QueryBuilder()
            .append(orm.Node, filters={'id': n1.pk}, tag='anc')
            .append(orm.Node, with_ancestors='anc', filters={'id': n8.pk})
            .count()
            == 2
        )

        assert (
            orm.QueryBuilder()
            .append(orm.Node, filters={'id': n8.pk}, tag='desc')
            .append(orm.Node, with_descendants='desc', filters={'id': n1.pk})
            .count()
            == 2
        )

        assert (
            orm.QueryBuilder()
            .append(orm.Node, filters={'id': n8.pk}, tag='desc')
            .append(
                orm.Node,
                with_descendants='desc',
                filters={'id': n1.pk},
                edge_filters={'depth': {'<': 6}},
            )
            .count()
            == 2
        )
        assert (
            orm.QueryBuilder()
            .append(orm.Node, filters={'id': n8.pk}, tag='desc')
            .append(
                orm.Node,
                with_descendants='desc',
                filters={'id': n1.pk},
                edge_filters={'depth': 5},
            )
            .count()
            == 2
        )
        assert (
            orm.QueryBuilder()
            .append(orm.Node, filters={'id': n8.pk}, tag='desc')
            .append(
                orm.Node,
                with_descendants='desc',
                filters={'id': n1.pk},
                edge_filters={'depth': {'<': 5}},
            )
            .count()
            == 0
        )

        # TODO write a query that can filter certain paths by traversed ID
        qb = (
            orm.QueryBuilder()
            .append(
                orm.Node,
                filters={'id': n8.pk},
                tag='desc',
            )
            .append(orm.Node, with_descendants='desc', edge_project='path', filters={'id': n1.pk})
        )
        queried_path_set = {frozenset(p) for (p,) in qb.all()}

        paths_there_should_be = {
            frozenset([n1.pk, n2.pk, n3.pk, n5.pk, n6.pk, n7.pk, n8.pk]),
            frozenset([n1.pk, n2.pk, n4.pk, n5.pk, n6.pk, n7.pk, n8.pk]),
        }

        assert queried_path_set == paths_there_should_be

        qb = (
            orm.QueryBuilder()
            .append(orm.Node, filters={'id': n1.pk}, tag='anc')
            .append(orm.Node, with_ancestors='anc', filters={'id': n8.pk}, edge_project='path')
        )

        assert {frozenset(p) for (p,) in qb.all()} == {
            frozenset([n1.pk, n2.pk, n3.pk, n5.pk, n6.pk, n7.pk, n8.pk]),
            frozenset([n1.pk, n2.pk, n4.pk, n5.pk, n6.pk, n7.pk, n8.pk]),
        }

        # This part of the test is no longer possible as the nodes have already been stored and the previous parts of
        # the test rely on this, which means however, that here, no more links can be added as that will raise.

        # n7.base.links.add_incoming(n9, link_type=LinkType.INPUT_CALC, link_label='link0')
        # # Still two links...

        # self.assertEqual(
        #     orm.QueryBuilder().append(orm.Node, filters={
        #         'id': n1.pk
        #     }, tag='anc').append(orm.Node, with_ancestors='anc', filters={
        #         'id': n8.pk
        #     }).count(), 2)

        # self.assertEqual(
        #     orm.QueryBuilder().append(orm.Node, filters={
        #         'id': n8.pk
        #     }, tag='desc').append(orm.Node, with_descendants='desc', filters={
        #         'id': n1.pk
        #     }).count(), 2)
        # n9.base.links.add_incoming(n5, link_type=LinkType.CREATE, link_label='link6')
        # # And now there should be 4 nodes

        # self.assertEqual(
        #     orm.QueryBuilder().append(orm.Node, filters={
        #         'id': n1.pk
        #     }, tag='anc').append(orm.Node, with_ancestors='anc', filters={
        #         'id': n8.pk
        #     }).count(), 4)

        # self.assertEqual(
        #     orm.QueryBuilder().append(orm.Node, filters={
        #         'id': n8.pk
        #     }, tag='desc').append(orm.Node, with_descendants='desc', filters={
        #         'id': n1.pk
        #     }).count(), 4)

        # qb = orm.QueryBuilder().append(
        #     orm.Node, filters={
        #         'id': n1.pk
        #     }, tag='anc').append(
        #         orm.Node, with_ancestors='anc', filters={'id': n8.pk}, edge_tag='edge')
        # qb.add_projection('edge', 'depth')
        # self.assertTrue(set(next(zip(*qb.all()))), set([5, 6]))
        # qb.add_filter('edge', {'depth': 5})
        # self.assertTrue(set(next(zip(*qb.all()))), set([5]))


class TestConsistency:
    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_create_node_and_query(self):
        """Testing whether creating nodes within a iterall iteration changes the results."""
        for _i in range(100):
            n = orm.Data()
            n.store()

        for idx, _item in enumerate(
            orm.QueryBuilder().append(orm.Node, project=['id', 'label']).iterall(batch_size=10)
        ):
            if idx % 10 == 10:
                n = orm.Data()
                n.store()
        assert idx == 99
        assert len(orm.QueryBuilder().append(orm.Node, project=['id', 'label']).all(batch_size=10)) > 99

    def test_len_results(self):
        """Test whether the len of results matches the count returned.
        See also https://github.com/aiidateam/aiida-core/issues/1600
        SQLAlchemy has a deduplication strategy that leads to strange behavior, tested against here
        """
        parent = orm.CalculationNode().store()
        # adding 5 links going out:
        for inode in range(5):
            output_node = orm.Data().store()
            output_node.base.links.add_incoming(parent, link_type=LinkType.CREATE, link_label=f'link_{inode}')
        for projection in ('id', '*'):
            qb = orm.QueryBuilder()
            qb.append(orm.CalculationNode, filters={'id': parent.pk}, tag='parent', project=projection)
            qb.append(orm.Data, with_incoming='parent')
            assert len(qb.all()) == qb.count()

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_iterall_except(self):
        """Test ``QueryBuilder.iterall`` uses a transaction and if interrupted, changes are reverted.

        In this test, 10 nodes are created which are then looped over and for each one, another node is stored, but
        before the loop can finish, an exception is raised. At then, the number of nodes should still be ten as the new
        ones that were being created in the transaction should have been reverted.
        """
        assert orm.QueryBuilder().append(orm.Data).count() == 0

        count = 10

        for _ in range(count):
            orm.Data().store()

        try:
            for index, _ in enumerate(orm.QueryBuilder().append(orm.Data).iterall()):
                orm.Data().store()
                if index >= count - 2:
                    raise RuntimeError('some error')
        except RuntimeError:
            pass

        assert orm.QueryBuilder().append(orm.Data).count() == count

    def test_iterall_with_mutation(self):
        """Test that nodes can be mutated while being iterated using ``QueryBuilder.iterall``.

        This is a regression test for https://github.com/aiidateam/aiida-core/issues/5672 .
        """
        count = 10
        pks = []

        for _ in range(count):
            node = orm.Data().store()
            pks.append(node.pk)

        # Ensure that batch size is smaller than the total rows yielded
        for [node] in orm.QueryBuilder().append(orm.Data).iterall(batch_size=2):
            node.base.extras.set('key', 'value')

        for pk in pks:
            assert orm.load_node(pk).base.extras.get('key') == 'value'

    # TODO: This test seems to hang (or takes a looong time), specifically in
    # pydantic/_internal/_core_utils.py:400
    @pytest.mark.requires_psql
    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_iterall_with_store(self):
        """Test that nodes can be stored while being iterated using ``QueryBuilder.iterall``.

        This is a regression test for https://github.com/aiidateam/aiida-core/issues/5802 .
        """
        count = 10
        pks = []
        pk_clones = []

        for _ in range(count):
            node = orm.Int().store()
            pks.append(node.pk)

        # Ensure that batch size is smaller than the total rows yielded
        for [node] in orm.QueryBuilder().append(orm.Int).iterall(batch_size=2):
            clone = orm.Int(node.value).store()
            pk_clones.append(clone.pk)

        for pk, pk_clone in zip(pks, sorted(pk_clones)):
            assert orm.load_node(pk) == orm.load_node(pk_clone)

    # TODO: This test seems to hang (or takes a looong time)
    @pytest.mark.requires_psql
    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_iterall_with_store_group(self):
        """Test that nodes can be stored and added to groups while being iterated using ``QueryBuilder.iterall``.

        This is a regression test for https://github.com/aiidateam/aiida-core/issues/5802 .
        """
        count = 10
        pks = []
        pks_clone = []

        for index in range(count):
            node = orm.Int(index).store()
            pks.append(node.pk)

        # Ensure that batch size is smaller than the total rows yielded
        for [node] in orm.QueryBuilder().append(orm.Int).iterall(batch_size=2):
            clone = copy.deepcopy(node)
            clone.store()
            pks_clone.append((clone.value, clone.pk))
            group = orm.Group(label=str(node.uuid)).store()
            group.add_nodes([node])

        # Need to sort the cloned pks based on the value, because the order of ``iterall`` is not guaranteed
        for pk, pk_clone in zip(pks, [e[1] for e in sorted(pks_clone)]):
            assert orm.load_node(pk) == orm.load_node(pk_clone)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_iterall_persistence(self, manager):
        """Test that mutations made during ``QueryBuilder.iterall`` context are automatically committed and persisted.

        This is a regression test for https://github.com/aiidateam/aiida-core/issues/6133 .
        """
        count = 10

        # Create number of nodes with specific extra
        for _ in range(count):
            node = orm.Data().store()
            node.base.extras.set('testing', True)

        query = orm.QueryBuilder().append(orm.Data, filters={'extras': {'has_key': 'testing'}})
        assert query.count() == count

        # Unload and reload the storage, which will reset the session and check that the nodes with extras still exist
        manager.reset_profile_storage()
        manager.get_profile_storage()
        assert query.count() == count

        # Delete the extras and check that the query now matches 0
        for [node] in orm.QueryBuilder().append(orm.Data).iterall(batch_size=2):
            node.base.extras.delete('testing')

        assert query.count() == 0

        # Finally, reset the storage again and verify the changes have been persisted
        manager.reset_profile_storage()
        manager.get_profile_storage()
        assert query.count() == 0


class TestManager:
    @pytest.fixture(autouse=True)
    def init_db(self, backend):
        self.backend = backend

    def test_statistics(self):
        """Test if the statistics query works properly.

        I try to implement it in a way that does not depend on the past state.
        """

        def store_and_add(n, statistics):
            n.store()
            statistics['total'] += 1
            statistics['types'][n._plugin_type_string] += 1
            statistics['ctime_by_day'][n.ctime.strftime('%Y-%m-%d')] += 1

        qmanager = self.backend.query()
        current_db_statistics = qmanager.get_creation_statistics()
        types = defaultdict(int)
        types.update(current_db_statistics['types'])
        ctime_by_day = defaultdict(int)
        ctime_by_day.update(current_db_statistics['ctime_by_day'])

        expected_db_statistics = {'total': current_db_statistics['total'], 'types': types, 'ctime_by_day': ctime_by_day}

        store_and_add(orm.Data(), expected_db_statistics)
        store_and_add(orm.Dict(), expected_db_statistics)
        store_and_add(orm.Dict(), expected_db_statistics)
        store_and_add(orm.CalculationNode(), expected_db_statistics)

        new_db_statistics = qmanager.get_creation_statistics()
        # I only check a few fields
        new_db_statistics = {k: v for k, v in new_db_statistics.items() if k in expected_db_statistics}

        expected_db_statistics = {
            k: dict(v) if isinstance(v, defaultdict) else v for k, v in expected_db_statistics.items()
        }

        assert new_db_statistics == expected_db_statistics

    def test_statistics_default_class(self):
        """Test if the statistics query works properly.

        I try to implement it in a way that does not depend on the past state.
        """

        def store_and_add(n, statistics):
            n.store()
            statistics['total'] += 1
            statistics['types'][n._plugin_type_string] += 1
            statistics['ctime_by_day'][n.ctime.strftime('%Y-%m-%d')] += 1

        current_db_statistics = self.backend.query().get_creation_statistics()
        types = defaultdict(int)
        types.update(current_db_statistics['types'])
        ctime_by_day = defaultdict(int)
        ctime_by_day.update(current_db_statistics['ctime_by_day'])

        expected_db_statistics = {'total': current_db_statistics['total'], 'types': types, 'ctime_by_day': ctime_by_day}

        store_and_add(orm.Data(), expected_db_statistics)
        store_and_add(orm.Dict(), expected_db_statistics)
        store_and_add(orm.Dict(), expected_db_statistics)
        store_and_add(orm.CalculationNode(), expected_db_statistics)

        new_db_statistics = self.backend.query().get_creation_statistics()
        # I only check a few fields
        new_db_statistics = {k: v for k, v in new_db_statistics.items() if k in expected_db_statistics}

        expected_db_statistics = {
            k: dict(v) if isinstance(v, defaultdict) else v for k, v in expected_db_statistics.items()
        }

        assert new_db_statistics == expected_db_statistics


class TestDoubleStar:
    """In this test class we check if QueryBuilder returns the correct results
    when double star is provided as projection.
    """

    def test_authinfo(self, aiida_localhost):
        user = orm.User(email=str(uuid.uuid4())).store()
        authinfo = aiida_localhost.configure(user)
        result = (
            orm.QueryBuilder()
            .append(orm.AuthInfo, tag='auth', filters={'id': {'==': authinfo.pk}}, project=['**'])
            .dict()
        )
        assert len(result) == 1
        assert result[0]['auth']['id'] == authinfo.pk

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_statistics_default_class(self, aiida_localhost):
        expected_dict = {
            'description': aiida_localhost.description,
            'scheduler_type': aiida_localhost.scheduler_type,
            'hostname': aiida_localhost.hostname,
            'uuid': aiida_localhost.uuid,
            'label': aiida_localhost.label,
            'transport_type': aiida_localhost.transport_type,
            'id': aiida_localhost.pk,
            'metadata': aiida_localhost.metadata,
        }

        qb = orm.QueryBuilder()
        qb.append(orm.Computer, project=['**'])
        # We expect one result
        assert qb.count() == 1

        # Get the one result record and check that the returned
        # data are correct
        res = next(iter(qb.dict()[0].values()))
        assert res == expected_dict

        # Ask the same query as above using QueryBuilder.as_dict()
        qh = {'project': {'computer': ['**']}, 'path': [{'tag': 'computer', 'cls': orm.Computer}]}
        qb = orm.QueryBuilder(**qh)
        # We expect one result
        assert qb.count() == 1

        # Get the one result record and check that the returned
        # data are correct
        res = next(iter(qb.dict()[0].values()))
        assert res == expected_dict


class TestJsonFilters:
    @staticmethod
    def assert_match(data, filters, is_match):
        orm.Dict(data).store()
        qb = orm.QueryBuilder().append(orm.Dict, filters=filters)
        assert qb.count() in {0, 1}
        found = qb.count() == 1
        assert found == is_match

    @pytest.mark.parametrize(
        'data,filters,is_match',
        (
            # contains different types of element
            ({'arr': [1, '2', None]}, {'attributes.arr': {'contains': [1]}}, True),
            ({'arr': [1, '2', None]}, {'attributes.arr': {'contains': ['2']}}, True),
            ({'arr': [1, '2', None]}, {'attributes.arr': {'contains': [None]}}, True),
            # contains multiple elements of various types
            ({'arr': [1, '2', None]}, {'attributes.arr': {'contains': [1, None]}}, True),
            # contains non-exist elements
            ({'arr': [1, '2', None]}, {'attributes.arr': {'contains': [114514]}}, False),
            # contains empty set
            ({'arr': [1, '2', None]}, {'attributes.arr': {'contains': []}}, True),
            ({'arr': []}, {'attributes.arr': {'contains': []}}, True),
            # nested arrays
            ({'arr': [[1, 0], [0, 2]]}, {'attributes.arr': {'contains': [[1, 0]]}}, True),
            ({'arr': [[2, 3], [0, 1], []]}, {'attributes.arr': {'contains': [[1, 0]]}}, True),
            ({'arr': [[2, 3], [1]]}, {'attributes.arr': {'contains': [[4]]}}, False),
            ({'arr': [[1, 0], [0, 2]]}, {'attributes.arr': {'contains': [[3]]}}, False),
            ({'arr': [[1, 0], [0, 2]]}, {'attributes.arr': {'contains': [3]}}, False),
            ({'arr': [[1, 0], [0, 2]]}, {'attributes.arr': {'contains': [[2]]}}, True),
            ({'arr': [[1, 0], [0, 2]]}, {'attributes.arr': {'contains': [2]}}, False),
            ({'arr': [[1, 0], [0, 2], 3]}, {'attributes.arr': {'contains': [[3]]}}, False),
            ({'arr': [[1, 0], [0, 2], 3]}, {'attributes.arr': {'contains': [3]}}, True),
            # negations
            ({'arr': [1, '2', None]}, {'attributes.arr': {'!contains': [1]}}, False),
            ({'arr': [1, '2', None]}, {'attributes.arr': {'!contains': []}}, False),
            ({'arr': [1, '2', None]}, {'attributes.arr': {'!contains': [114514]}}, True),
            ({'arr': [1, '2', None]}, {'attributes.arr': {'!contains': [1, 114514]}}, True),
            # when attr_key does not exist, `contains`` returns `NULL`
            ({'arr': [1, '2', None]}, {'attributes.x': {'!contains': []}}, False),
            ({'arr': [1, '2', None]}, {'attributes.x': {'contains': []}}, False),
        ),
        ids=json.dumps,
    )
    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_json_filters_contains_arrays(self, data, filters, is_match):
        """Test QueryBuilder filter `contains` for JSON array fields"""
        self.assert_match(data, filters, is_match)

    @pytest.mark.parametrize(
        'data,filters,is_match',
        (
            # when attr_key does not exist, `contains`` returns `NULL`
            (
                {
                    'dict': {
                        'k1': 1,
                        'k2': '2',
                        'k3': None,
                    }
                },
                {'attributes.foobar': {'!contains': {}}},
                False,
            ),
            (
                {
                    'dict': {
                        'k1': 1,
                        'k2': '2',
                        'k3': None,
                    }
                },
                {'attributes.foobar': {'contains': {}}},
                False,
            ),
            # contains different types of values
            (
                {
                    'dict': {
                        'k1': 1,
                        'k2': '2',
                        'k3': None,
                    }
                },
                {'attributes.dict': {'contains': {'k1': 1}}},
                True,
            ),
            (
                {
                    'dict': {
                        'k1': 1,
                        'k2': '2',
                        'k3': None,
                    }
                },
                {'attributes.dict': {'contains': {'k1': 1, 'k2': '2'}}},
                True,
            ),
            (
                {
                    'dict': {
                        'k1': 1,
                        'k2': '2',
                        'k3': None,
                    }
                },
                {'attributes.dict': {'contains': {'k3': None}}},
                True,
            ),
            # contains empty set
            (
                {
                    'dict': {
                        'k1': 1,
                        'k2': '2',
                        'k3': None,
                    }
                },
                {'attributes.dict': {'contains': {}}},
                True,
            ),
            # nested dicts
            (
                {'dict': {'k1': {'k2': {'kx': 1, 'k3': 'secret'}, 'kxx': None}, 'kxxx': 'vxxx'}},
                {'attributes.dict': {'contains': {'k1': {'k2': {'k3': 'secret'}}}}},
                True,
            ),
            (
                {
                    'dict': {
                        'k1': [
                            0,
                            1,
                            {
                                'k2': [
                                    '0',
                                    {
                                        'kkk': 'vvv',
                                        'k3': 'secret',
                                    },
                                    '2',
                                ]
                            },
                            3,
                        ],
                        'kkk': 'vvv',
                    }
                },
                {
                    'attributes.dict': {
                        'contains': {
                            'k1': [
                                {
                                    'k2': [
                                        {
                                            'k3': 'secret',
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                },
                True,
            ),
            # doesn't contain non-exist entries
            (
                {
                    'dict': {
                        'k1': 1,
                        'k2': '2',
                        'k3': None,
                    }
                },
                {'attributes.dict': {'contains': {'k1': 1, 'k': 'v'}}},
                False,
            ),
            # negations
            (
                {
                    'dict': {
                        'k1': 1,
                        'k2': '2',
                        'k3': None,
                    }
                },
                {'attributes.dict': {'!contains': {'k1': 1}}},
                False,
            ),
            (
                {
                    'dict': {
                        'k1': 1,
                        'k2': '2',
                        'k3': None,
                    }
                },
                {'attributes.dict': {'!contains': {'k1': 1, 'k': 'v'}}},
                True,
            ),
            (
                {
                    'dict': {
                        'k1': 1,
                        'k2': '2',
                        'k3': None,
                    }
                },
                {'attributes.dict': {'!contains': {}}},
                False,
            ),
        ),
        ids=json.dumps,
    )
    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_json_filters_contains_object(self, data, filters, is_match):
        """Test QueryBuilder filter `contains` for JSON object fields"""
        self.assert_match(data, filters, is_match)

    @pytest.mark.parametrize(
        'data,filters,is_match',
        (
            ({'dict': {'k1': 1, 'k2': '2', 'k3': None}}, {'attributes.dict': {'has_key': 'k1'}}, True),
            ({'dict': {'k1': 1, 'k2': '2', 'k3': None}}, {'attributes.dict': {'has_key': 'k2'}}, True),
            ({'dict': {'k1': 1, 'k2': '2', 'k3': None}}, {'attributes.dict': {'has_key': 'k3'}}, True),
            ({'dict': {'k1': 1, 'k2': '2', 'k3': None}}, {'attributes.dict': {'!has_key': 'k1'}}, False),
            ({'dict': {'k1': 1, 'k2': '2', 'k3': None}}, {'attributes.dict': {'!has_key': 'k2'}}, False),
            ({'dict': {'k1': 1, 'k2': '2', 'k3': None}}, {'attributes.dict': {'!has_key': 'k3'}}, False),
            ({'dict': {'k1': 1, 'k2': '2', 'k3': None}}, {'attributes.dict': {'has_key': 'non-exist'}}, False),
            ({'dict': {'k1': 1, 'k2': '2', 'k3': None}}, {'attributes.dict': {'!has_key': 'non-exist'}}, True),
            ({'dict': 0xFA15ED1C7}, {'attributes.dict': {'has_key': 'dict'}}, False),
            ({'dict': 0xFA15ED1C7}, {'attributes.dict': {'!has_key': 'dict'}}, True),
        ),
    )
    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_json_filters_has_key(self, data, filters, is_match):
        self.assert_match(data, filters, is_match)

    @pytest.mark.parametrize(
        'filters,matches',
        (
            # type match
            ({'attributes.text': {'of_type': 'string'}}, 1),
            ({'attributes.integer': {'of_type': 'number'}}, 1),
            ({'attributes.float': {'of_type': 'number'}}, 1),
            ({'attributes.true': {'of_type': 'boolean'}}, 1),
            ({'attributes.false': {'of_type': 'boolean'}}, 1),
            ({'attributes.null': {'of_type': 'null'}}, 2),
            ({'attributes.list': {'of_type': 'array'}}, 1),
            ({'attributes.dict': {'of_type': 'object'}}, 1),
            # equality match
            ({'attributes.text': {'==': 'abcXYZ'}}, 1),
            ({'attributes.integer': {'==': 1}}, 1),
            ({'attributes.float': {'==': 1.1}}, 1),
            ({'attributes.true': {'==': True}}, 1),
            ({'attributes.false': {'==': False}}, 1),
            ({'attributes.list': {'==': [1, 2]}}, 1),
            ({'attributes.list2': {'==': ['a', 'b']}}, 1),
            ({'attributes.dict': {'==': {'key-1': 1, 'key-none': None}}}, 1),
            # equality non-match
            ({'attributes.text': {'==': 'lmn'}}, 0),
            ({'attributes.integer': {'==': 2}}, 0),
            ({'attributes.float': {'==': 2.2}}, 0),
            ({'attributes.true': {'==': False}}, 0),
            ({'attributes.false': {'==': True}}, 0),
            ({'attributes.list': {'==': [1, 3]}}, 0),
            # text regexes
            ({'attributes.text': {'like': 'abcXYZ'}}, 1),
            ({'attributes.text': {'like': 'abcxyz'}}, 0),
            ({'attributes.text': {'ilike': 'abcxyz'}}, 1),
            ({'attributes.text': {'like': 'abc%'}}, 1),
            ({'attributes.text': {'like': 'abc_YZ'}}, 1),
            (
                {
                    'attributes.text2': {
                        'like': 'abc\\_XYZ'  # Literal match
                    }
                },
                1,
            ),
            ({'attributes.text2': {'like': 'abc_XYZ'}}, 2),
            # integer comparisons
            ({'attributes.float': {'<': 1}}, 0),
            ({'attributes.float': {'<': 2}}, 1),
            ({'attributes.float': {'>': 2}}, 0),
            ({'attributes.float': {'>': 0}}, 1),
            ({'attributes.integer': {'<': 1}}, 0),
            ({'attributes.integer': {'<': 2}}, 1),
            ({'attributes.integer': {'>': 2}}, 0),
            ({'attributes.integer': {'>': 0}}, 1),
            # float comparisons
            ({'attributes.float': {'<': 0.99}}, 0),
            ({'attributes.float': {'<': 2.01}}, 1),
            ({'attributes.float': {'>': 2.01}}, 0),
            ({'attributes.float': {'>': 0.01}}, 1),
            ({'attributes.integer': {'<': 0.99}}, 0),
            ({'attributes.integer': {'<': 2.01}}, 1),
            ({'attributes.integer': {'>': 2.01}}, 0),
            ({'attributes.integer': {'>': 0.01}}, 1),
            # array operators
            ({'attributes.list': {'of_length': 0}}, 0),
            ({'attributes.list': {'of_length': 2}}, 1),
            ({'attributes.list': {'longer': 3}}, 0),
            ({'attributes.list': {'longer': 1}}, 1),
            ({'attributes.list': {'shorter': 1}}, 0),
            ({'attributes.list': {'shorter': 3}}, 1),
            # in operator
            ({'attributes.text': {'in': ['x', 'y', 'z']}}, 0),
            ({'attributes.text': {'in': ['x', 'y', 'abcXYZ']}}, 1),
            ({'attributes.integer': {'in': [5, 6, 7]}}, 0),
            ({'attributes.integer': {'in': [1, 2, 3]}}, 1),
        ),
        ids=json.dumps,
    )
    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_json_filters(self, filters, matches):
        """Test QueryBuilder filtering for JSON fields."""
        orm.Dict(
            {
                'text': 'abcXYZ',
                'text2': 'abc_XYZ',
                'integer': 1,
                'float': 1.1,
                'true': True,
                'false': False,
                'null': None,
                'list': [1, 2],
                'list2': ['a', 'b'],
                'dict': {
                    'key-1': 1,
                    'key-none': None,
                },
            },
        ).store()
        orm.Dict({'text2': 'abcxXYZ'}).store()

        qbuilder = orm.QueryBuilder()
        qbuilder.append(orm.Dict, filters=filters)
        assert qbuilder.count() == matches

    @pytest.mark.parametrize(
        'filters,matches',
        (
            ({'label': {'like': 'abc_XYZ'}}, 2),
            ({'label': {'like': 'abc\\_XYZ'}}, 1),
            ({'label': {'like': 'abcxXYZ'}}, 1),
            ({'label': {'like': 'abc%XYZ'}}, 2),
        ),
        ids=json.dumps,
    )
    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_column_filters(self, filters, matches):
        """Test querying directly those stored in the columns"""
        dict1 = orm.Dict(
            {
                'text2': 'abc_XYZ',
            }
        ).store()
        dict2 = orm.Dict({'text2': 'abcxXYZ'}).store()
        dict1.label = 'abc_XYZ'
        dict2.label = 'abcxXYZ'
        qbuilder = orm.QueryBuilder()
        qbuilder.append(orm.Dict, filters=filters)
        assert qbuilder.count() == matches

    @pytest.mark.parametrize(
        'key,cast_type',
        (
            ('text', 't'),
            ('integer', 'i'),
            ('float', 'f'),
        ),
    )
    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_json_order_by(self, key, cast_type):
        """Test QueryBuilder ordering by JSON field keys."""
        dict1 = orm.Dict(
            {
                'text': 'b',
                'integer': 2,
                'float': 2.2,
            }
        ).store()
        dict2 = orm.Dict(
            {
                'text': 'a',
                'integer': 1,
                'float': 1.1,
            }
        ).store()
        dict3 = orm.Dict(
            {
                'text': 'c',
                'integer': 3,
                'float': 3.3,
            }
        ).store()
        qbuilder = orm.QueryBuilder()
        qbuilder.append(orm.Dict, tag='dict', project=['id']).order_by(
            {'dict': {f'attributes.{key}': {'order': 'asc', 'cast': cast_type}}}
        )
        assert qbuilder.all(flat=True) == [dict2.pk, dict1.pk, dict3.pk]
