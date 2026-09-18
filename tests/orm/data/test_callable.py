###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.orm.nodes.data.callable` module."""

import dataclasses
import inspect
import re

import cloudpickle
import pytest
import yaml

from aiida.orm import CallableData, load_node
from aiida.plugins.entry_point import load_entry_point_from_string


def make_parser(threshold):
    """Return a closure, which no name identifies, over the provided threshold."""

    def parse(dirpath):
        return {'above': threshold}

    return parse


@pytest.mark.parametrize(
    'value, distribution, version',
    (
        pytest.param(cloudpickle.dumps, 'cloudpickle', cloudpickle.__version__, id='installed-under-its-own-name'),
        pytest.param(yaml.safe_load, 'PyYAML', yaml.__version__, id='installed-under-another-name'),
    ),
)
def test_constructor_importable(value, distribution, version):
    """Test that an importable callable is recorded by name, without a fingerprint.

    A module is imported under one name and installed under another, and both cases are covered here because only
    the second can show whether the distribution was actually resolved rather than assumed from the import name.
    """
    node = CallableData(value)

    assert node.base.attributes.all == {
        'name': value.__qualname__,
        'module': value.__module__,
        'distribution': distribution,
        'version': version,
        'commit': None,
        'importable': True,
        'callable_entry_point': None,
        'fingerprint': None,
        'parameters': [[name, parameter.kind.name] for name, parameter in inspect.signature(value).parameters.items()],
        'source_path': inspect.getsourcefile(value),
        'source_line': inspect.getsourcelines(value)[1],
    }


def test_constructor_not_importable():
    """Test that a callable no name identifies is recorded by fingerprint instead."""
    from aiida.common import callables

    parser = make_parser(10)
    node = CallableData(parser)

    assert node.is_importable is False
    assert node.name == 'make_parser.<locals>.parse'
    assert node.distribution is None
    assert node.version is None
    assert node.fingerprint == callables.fingerprint(parser)


def test_fingerprint_distinguishes_closures():
    """Test that closures sharing a name and a source are told apart by what they capture."""
    first, second = CallableData(make_parser(10)), CallableData(make_parser(20))

    assert first.name == second.name
    assert first.get_source() == second.get_source()
    assert first.fingerprint != second.fingerprint


def test_source_is_stored_and_readable():
    """Test that the source of the callable is stored as text, and is the only thing in the repository."""
    node = CallableData(make_parser(10))

    assert node.get_source() == inspect.getsource(make_parser(10))
    assert node.base.repository.list_object_names() == [CallableData.FILENAME_SOURCE]


def test_source_unavailable():
    """Test that a callable whose source cannot be retrieved is still recorded, without one."""
    node = CallableData(cloudpickle.dumps.__reduce__)

    assert node.get_source() is None
    assert node.base.repository.list_object_names() == []


def test_parameters_record_their_kind():
    """Test that a parameter which can only be passed by keyword is not reported as positionally available.

    A name alone cannot say this, and a caller that invokes the callable positionally needs to know.
    """

    def keyword_only(*, dirpath):
        return {}

    node = CallableData(keyword_only)

    assert node.parameters == ['dirpath']
    assert node.positional_parameters == []


def test_parameters_not_inspectable():
    """Test that a callable without an inspectable signature records no parameters."""
    assert CallableData(iter).parameters is None


def test_constructor_unhashable():
    """Test that a callable which cannot be used as a dictionary key is recorded like any other.

    A class that defines ``__eq__`` has no hash, which ``@dataclass`` does by default, so this is what a parser
    carried as a small dataclass looks like.
    """

    @dataclasses.dataclass
    class Threshold:
        threshold: int = 10

        def __call__(self, dirpath):
            return {}

    node = CallableData(Threshold())

    assert node.is_importable is False
    assert node.parameters == ['dirpath']
    # `inspect.getsource` cannot reach the source of an instance, so there is none to record, and that is all.
    assert node.get_source() is None


def test_constructor_invalid():
    """Test that the constructor refuses anything that is not callable."""
    with pytest.raises(TypeError, match=r'`value` should be a callable but got: .*str.*'):
        CallableData('not-callable')


def test_constructor_forwards_keywords():
    """Test that keyword arguments reach the node, rather than being swallowed."""
    assert CallableData(make_parser(10), label='parser').label == 'parser'


def test_constructor_not_serializable():
    """Test that a callable that is neither importable nor serializable is refused, rather than recorded blindly.

    Without a fingerprint the record could not tell it apart from any other closure of the same factory.
    """
    generator = (value for value in range(3))

    with pytest.raises(TypeError, match=r'.* could not be serialized: .*'):
        CallableData(lambda: generator)


def test_entry_point(entry_points):
    """Test that a callable a plugin registers is recorded by its entry point as well as by name."""
    entry_points.add(make_parser, 'aiida.parsers:test.callable')
    registered = load_entry_point_from_string('aiida.parsers:test.callable')

    node = CallableData(registered, entry_point='aiida.parsers:test.callable')

    assert node.callable_entry_point == 'aiida.parsers:test.callable'
    assert node.is_importable is True
    assert node.load() is registered


def test_entry_point_found_without_being_named(entry_points):
    """Test that a registered callable is recorded by its entry point even when the caller does not name one.

    The entry point is the only one of the three identifiers that survives the callable moving, so leaving it to
    whoever constructs the node to pass would make the best record depend on them knowing to.
    """
    entry_points.add(make_parser, 'aiida.parsers:test.callable')
    registered = load_entry_point_from_string('aiida.parsers:test.callable')

    assert CallableData(registered).callable_entry_point == 'aiida.parsers:test.callable'


def test_entry_point_absent_when_nothing_registers_it():
    """Test that a callable the registry cannot match is recorded without one, rather than with a guess."""
    assert CallableData(cloudpickle.dumps).callable_entry_point is None


def test_hash_ignores_where_the_callable_came_from():
    """Test that a record hashes on what the callable is, not on where this interpreter found it.

    A version bumps on any release, a commit moves with its branch, and a source location shifts when a line is
    added above the definition. Hashing those would miss the cache for a callable that has not changed.
    """
    node = CallableData(cloudpickle.dumps)
    elsewhere = CallableData(cloudpickle.dumps)

    for attribute, value in (
        (CallableData.KEY_ATTRIBUTES_DISTRIBUTION, 'somewhere-else'),
        (CallableData.KEY_ATTRIBUTES_VERSION, '99.9'),
        (CallableData.KEY_ATTRIBUTES_COMMIT, 'a' * 40),
        (CallableData.KEY_ATTRIBUTES_SOURCE_PATH, '/somewhere/else.py'),
        (CallableData.KEY_ATTRIBUTES_SOURCE_LINE, 12345),
    ):
        elsewhere.base.attributes.set(attribute, value)

    assert elsewhere.store().base.caching.compute_hash() == node.store().base.caching.compute_hash()


def test_hash_follows_what_the_callable_is():
    """Test that the identity of the callable does reach the hash, so two different ones stay apart."""
    node = CallableData(cloudpickle.dumps).store()
    other = CallableData(cloudpickle.loads).store()

    assert other.base.caching.compute_hash() != node.base.caching.compute_hash()

    # Two closures from one factory share a name, a source text and a source location; what they capture is all
    # that separates them, and the fingerprint is what carries that into the hash.
    closure = CallableData(make_parser(10)).store()
    same_factory = CallableData(make_parser(20)).store()

    assert closure.base.caching.compute_hash() != same_factory.base.caching.compute_hash()


def test_entry_point_unregistered():
    """Test that an entry point which is not registered is refused, rather than recorded as a dangling reference."""
    with pytest.raises(ValueError, match=r'the entry point `aiida.parsers:nope.missing` could not be loaded: .*'):
        CallableData(make_parser, entry_point='aiida.parsers:nope.missing')


def test_entry_point_mismatch(entry_points):
    """Test that an entry point which resolves to a different object is refused."""
    entry_points.add(make_parser, 'aiida.parsers:test.callable')

    with pytest.raises(ValueError, match=r'the entry point `aiida.parsers:test.callable` refers to .*, not to .*'):
        CallableData(make_parser(10), entry_point='aiida.parsers:test.callable')


def test_load_importable():
    """Test that an importable callable is reconstructed from its record."""
    assert CallableData(cloudpickle.dumps).load() is cloudpickle.dumps


def test_load_module_gone():
    """Test that a record whose module is not installed here says so, and says what to install.

    This is what an archive from another machine looks like when the package that defined the callable is missing.
    """
    node = CallableData(cloudpickle.dumps)
    node.base.attributes.set(CallableData.KEY_ATTRIBUTES_MODULE, 'nope_not_installed')

    expected = (
        f'`dumps` could not be imported from `nope_not_installed`. '
        f'Install `cloudpickle=={cloudpickle.__version__}` and try again.'
    )

    with pytest.raises(ValueError, match=re.escape(expected)):
        node.load()


def test_load_module_gone_without_a_distribution():
    """Test that a record which never resolved a distribution does not tell the reader to install a module path.

    The dotted module name is not something any index can resolve, so naming it after `Install` would send someone
    off to install a package that does not exist.
    """
    node = CallableData(cloudpickle.dumps)
    node.base.attributes.set(CallableData.KEY_ATTRIBUTES_MODULE, 'nope_not_installed')
    node.base.attributes.set(CallableData.KEY_ATTRIBUTES_DISTRIBUTION, None)

    with pytest.raises(ValueError, match=r'.*Make sure the package that provides `nope_not_installed` is installed.*'):
        node.load()


def test_load_entry_point_gone(entry_points):
    """Test that a record whose entry point is no longer registered says so, rather than raising from the plugin."""
    entry_points.add(make_parser, 'aiida.parsers:test.callable')
    node = CallableData(
        load_entry_point_from_string('aiida.parsers:test.callable'), entry_point='aiida.parsers:test.callable'
    )
    entry_points.remove('aiida.parsers:test.callable')

    with pytest.raises(ValueError, match=r'`aiida.parsers:test.callable` could not be loaded: .*'):
        node.load()


def test_load_not_importable():
    """Test that a record of a callable no name identifies refuses to reconstruct it."""
    node = CallableData(make_parser(10))

    with pytest.raises(ValueError, match=r'.*was not importable when it was recorded.*'):
        node.load()


def test_live_callable():
    """Test that the recorded callable is reachable from the instance that recorded it, and from no other."""
    parser = make_parser(10)
    node = CallableData(parser).store()

    assert node.live_callable is parser
    assert load_node(node.pk).live_callable is None


def test_store_and_load():
    """Test that the record survives a round trip through the database."""
    node = CallableData(make_parser(10)).store()
    loaded = load_node(node.pk)

    assert loaded.base.attributes.all == node.base.attributes.all
    assert loaded.get_source() == node.get_source()


def module_level_recorded(value):
    """Importable by name, so an archived record of it can be loaded again anywhere this module is installed."""
    return value


def test_survives_an_archive_round_trip(aiida_profile, tmp_path):
    """Test that what crosses an archive is the record, and that it still loads what a name can recover.

    An archive is the case the record exists for: it carries no checkpoint and so no payload, which is what keeps
    executable bytes out of something people share. A callable a name recovers is reconstructed from the record on
    the other side; one that no name recovers is not, and says so.
    """
    from aiida.tools.archive import create_archive, import_archive

    def factory(offset):
        def closure(value):
            return value + offset

        return closure

    importable = CallableData(module_level_recorded).store()
    unnameable = CallableData(factory(10)).store()

    # Everything to compare against is read now, since the nodes themselves do not survive resetting the storage.
    importable_uuid, unnameable_uuid = importable.uuid, unnameable.uuid
    expected = {
        importable_uuid: dict(sorted(importable.base.attributes.all.items())),
        unnameable_uuid: dict(sorted(unnameable.base.attributes.all.items())),
    }
    sources = {uuid: load_node(uuid).get_source() for uuid in expected}

    filename = str(tmp_path / 'export.aiida')
    create_archive([importable, unnameable], filename=filename)

    aiida_profile.reset_storage()
    import_archive(filename)

    for uuid, attributes in expected.items():
        node = load_node(uuid)
        assert dict(sorted(node.base.attributes.all.items())) == attributes
        assert node.get_source() == sources[uuid]

    assert load_node(importable_uuid).load() is module_level_recorded

    with pytest.raises(ValueError, match=r'.*was not importable when it was recorded.*'):
        load_node(unnameable_uuid).load()
