###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Closed container types and explicit storage error policy.

* The supported container set is finite and closed (``DataList``/``DataDict`` only, no third-party
  containers): the storage identifier mapping in ``aiida.storage.ownership`` is the single source of
  truth and backend dispatch, class loading and QueryBuilder agree on it.
* ``BackendContainer.store`` explicitly rejects the data path; containers persist only through
  ``store_container`` (``backend.store_container_subtree``).
* Whole-container provenance links through the normal public API work: adding an incoming link from a
  regular (non-container) node to a stored container must not be rejected by backend type checking.
"""

import pytest

from aiida.common.exceptions import IntegrityError
from aiida.orm import CalculationNode, Container, Data, DataDict, DataList, Int, QueryBuilder, load_node

pytestmark = pytest.mark.usefixtures('aiida_profile_clean')


def test_storage_mapping_matches_orm_types():
    """The shared storage mapping agrees with the concrete ORM ``node_type`` strings (no drift)."""
    from aiida.storage import ownership as ownership_contract

    assert DataList.class_node_type == ownership_contract.LIST_NODE_TYPE
    assert DataDict.class_node_type == ownership_contract.DICT_NODE_TYPE
    assert ownership_contract.CONTAINER_NODE_TYPES == frozenset({DataList.class_node_type, DataDict.class_node_type})
    assert ownership_contract.container_kind_for(DataList.class_node_type) == 'list'
    assert ownership_contract.container_kind_for(DataDict.class_node_type) == 'dict'
    assert not ownership_contract.is_container_node_type(Data.class_node_type)
    assert ownership_contract.is_ownable_node_type(DataList.class_node_type)


def test_backend_dispatch_consistent(backend):
    """Backend ``create``/``get`` dispatch agrees on the closed container set (no ORM import)."""
    from uuid import uuid4

    from aiida.storage import ownership as ownership_contract

    user = backend.users.create(email=f'{uuid4().hex}@localhost').store()
    for node_type in ownership_contract.CONTAINER_NODE_TYPES:
        entity = backend.nodes.create(node_type=node_type, user=user)
        assert type(entity).__name__.endswith('Container')
        assert entity.node_type == node_type

    plain = backend.nodes.create(node_type=Int.class_node_type, user=user)
    assert 'Container' not in type(plain).__name__
    assert not ownership_contract.is_container_node_type(plain.node_type)


def test_class_loading_resolves_closed_set():
    """``load_node_class`` resolves exactly the closed container set (stdlib fallback otherwise)."""
    from aiida.orm.utils.node import load_node_class

    assert load_node_class(DataList.class_node_type) is DataList
    assert load_node_class(DataDict.class_node_type) is DataDict


def test_backend_store_rejected_for_containers():
    """The generic backend ``store`` path explicitly rejects containers (use ``store_container``)."""
    container = DataList([Int(1)])
    with pytest.raises(IntegrityError):
        container.backend_entity.store()
    # The dedicated container path still works.
    container.store()
    assert container.is_stored


def test_whole_container_link_via_public_api():
    """A stored container accepts an incoming provenance link from a regular node via public API."""
    from aiida.common.links import LinkType

    container = DataList([Int(1)])
    container.store()
    calc = CalculationNode().store()
    container.base.links.add_incoming(calc, link_type=LinkType.CREATE, link_label='result')
    incoming = container.base.links.get_incoming(link_type=LinkType.CREATE).all()
    assert len(incoming) == 1
    assert incoming[0].node.uuid == calc.uuid


def test_querybuilder_base_and_concrete_results():
    """``Data`` includes containers; ``Container`` matches only the concrete containers."""
    leaf = Int(1)
    leaf.store()
    listed = DataList([Int(2)])
    listed.store()
    mapping = DataDict({'a': Int(3)})
    mapping.store()
    pks = {leaf.pk, listed.pk, mapping.pk}

    def _pks(cls, subclassing=True):
        builder = QueryBuilder().append(cls, filters={'id': {'in': sorted(pks)}}, subclassing=subclassing)
        return {node.pk for node in builder.all(flat=True)}

    assert _pks(Data) == pks
    assert _pks(Container) == {listed.pk, mapping.pk}
    assert _pks(DataList) == {listed.pk}
    assert _pks(DataDict) == {mapping.pk}
    # Exact (non-subclassing) queries still match the concrete stored type strings.
    assert _pks(DataList, subclassing=False) == {listed.pk}
    assert _pks(DataDict, subclassing=False) == {mapping.pk}
    # Reloading through the closed dispatch preserves concrete types.
    assert isinstance(load_node(listed.pk), DataList)
    assert isinstance(load_node(mapping.pk), DataDict)
