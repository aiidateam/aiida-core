###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Container declarations shared by the graph behavior suites.

Tasks take and return owned containers (:class:`DataList`/:class:`DataDict`);
graphs wire them through placements, nested graphs, and boundary
passthrough, including empty and nested containers.

Python ORM containers (``list[Int]``/``typing.List[Int]`` and
``dict[str, Int]``/``typing.Dict[str, Int]``) store as owned containers
while task bodies receive plain ``list``/``dict`` values retaining ``Int``
members. Plain ``list[int]``/``dict[str, int]`` behavior is unchanged.
"""

import typing as t

from aiida.engine.processes.graphs.lowering import graph, task
from aiida.orm import DataDict, DataList
from aiida.orm.nodes.data.int import Int


@task
def pack_list(x: int, y: int) -> DataList:
    """Pack two integers as an owned list."""
    return DataList([Int(x), Int(y)])


@task
def list_sum(values: DataList) -> int:
    """Sum the owned integers; node-typed inputs arrive as nodes."""
    assert isinstance(values, DataList)
    return sum(member.value for member in values)


@task
def list_length(values: DataList) -> int:
    """Count the owned elements; empty containers count zero."""
    assert isinstance(values, DataList)
    return len(values)


@task
def pack_dict(a: int, b: int) -> DataDict:
    """Pack two integers as an owned mapping."""
    return DataDict({'a': Int(a), 'b': Int(b)})


@task
def dict_sum(values: DataDict) -> int:
    """Sum the owned values; node-typed inputs arrive as nodes."""
    assert isinstance(values, DataDict)
    return sum(member.value for member in values.values())


@task
def pack_nested(w: int, x: int, y: int, z: int) -> DataList:
    """Pack two owned lists as one nested list."""
    return DataList([DataList([Int(w), Int(x)]), DataList([Int(y), Int(z)])])


@task
def nested_sum(values: DataList) -> int:
    """Sum every integer of a nested list."""
    assert isinstance(values, DataList)
    total = 0
    for inner in values:
        assert isinstance(inner, DataList)
        for member in inner:
            total += member.value
    return total


@task
def empty_list() -> DataList:
    """Return an empty owned list."""
    return DataList()


@task
def empty_dict() -> DataDict:
    """Return an empty owned mapping."""
    return DataDict()


@graph
def list_chain(x: int, y: int) -> int:
    """Pack a list in one placement and consume it in the next."""
    packed = pack_list(x=x, y=y)
    return list_sum(values=packed)


@graph
def list_passthrough(values: DataList) -> DataList:
    """Pass an owned list straight to outputs."""
    return values


@graph
def dict_chain(a: int, b: int) -> int:
    """Pack a mapping in one placement and consume it in the next."""
    packed = pack_dict(a=a, b=b)
    return dict_sum(values=packed)


@graph
def dict_passthrough(values: DataDict) -> DataDict:
    """Pass an owned mapping straight to outputs."""
    return values


@graph
def inner_sum(values: DataList) -> int:
    """Sum an owned list inside a nested graph."""
    return list_sum(values=values)


@graph
def outer_sum(values: DataList) -> int:
    """Delegate an owned list to a nested graph."""
    return inner_sum(values=values)


@graph
def nested_chain(w: int, x: int, y: int, z: int) -> int:
    """Pack a nested list in one placement and consume it in the next."""
    packed = pack_nested(w=w, x=x, y=y, z=z)
    return nested_sum(values=packed)


@graph
def empty_list_graph() -> DataList:
    """Return an empty owned list from a task."""
    return empty_list()


@graph
def empty_dict_graph() -> DataDict:
    """Return an empty owned mapping from a task."""
    return empty_dict()


@graph
def empty_length() -> int:
    """Count an empty owned list through task chaining."""
    empty = empty_list()
    return list_length(values=empty)


@task
def pack_py_list(x: int, y: int) -> list[Int]:
    """Pack two integers as a Python list of owned nodes."""
    return [Int(x), Int(y)]


@task
def py_list_sum(values: list[Int]) -> int:
    """Sum a Python list of owned integers; runtime values stay a plain list."""
    assert type(values) is list
    assert all(isinstance(member, Int) for member in values)
    return sum(member.value for member in values)


@task
def pack_typing_list(x: int, y: int) -> t.List[Int]:  # noqa: UP006 - legacy spelling maps the same way
    """Pack two integers as a legacy-spelled list of owned nodes."""
    return [Int(x), Int(y)]


@task
def typing_list_sum(values: t.List[Int]) -> int:  # noqa: UP006 - legacy spelling maps the same way
    """Sum a legacy-spelled list of owned integers; runtime values stay a plain list."""
    assert type(values) is list
    assert all(isinstance(member, Int) for member in values)
    return sum(member.value for member in values)


@task
def pack_py_dict(a: int, b: int) -> dict[str, Int]:
    """Pack two integers as a Python mapping of owned nodes."""
    return {'a': Int(a), 'b': Int(b)}


@task
def py_dict_sum(values: dict[str, Int]) -> int:
    """Sum a Python mapping of owned integers; runtime values stay a plain dict."""
    assert type(values) is dict
    assert all(isinstance(member, Int) for member in values.values())
    return sum(member.value for member in values.values())


@task
def pack_typing_dict(a: int, b: int) -> t.Dict[str, Int]:  # noqa: UP006 - legacy spelling maps the same way
    """Pack two integers as a legacy-spelled mapping of owned nodes."""
    return {'a': Int(a), 'b': Int(b)}


@task
def typing_dict_sum(values: t.Dict[str, Int]) -> int:  # noqa: UP006 - legacy spelling maps the same way
    """Sum a legacy-spelled mapping of owned integers; runtime values stay a plain dict."""
    assert type(values) is dict
    assert all(isinstance(member, Int) for member in values.values())
    return sum(member.value for member in values.values())


@task
def empty_py_list() -> list[Int]:
    """Return an empty Python list of owned nodes."""
    return []


@task
def empty_py_dict() -> dict[str, Int]:
    """Return an empty Python mapping of owned nodes."""
    return {}


@graph
def py_list_chain(x: int, y: int) -> int:
    """Pack a Python list in one placement and consume it in the next."""
    packed = pack_py_list(x=x, y=y)
    return py_list_sum(values=packed)


@graph
def typing_list_chain(x: int, y: int) -> int:
    """Pack a legacy-spelled list in one placement and consume it in the next."""
    packed = pack_typing_list(x=x, y=y)
    return typing_list_sum(values=packed)


@graph
def py_dict_chain(a: int, b: int) -> int:
    """Pack a Python mapping in one placement and consume it in the next."""
    packed = pack_py_dict(a=a, b=b)
    return py_dict_sum(values=packed)


@graph
def typing_dict_chain(a: int, b: int) -> int:
    """Pack a legacy-spelled mapping in one placement and consume it in the next."""
    packed = pack_typing_dict(a=a, b=b)
    return typing_dict_sum(values=packed)


@graph
def py_list_consume(values: list[Int]) -> int:
    """Consume a Python list graph input directly."""
    return py_list_sum(values=values)


@graph
def py_dict_consume(values: dict[str, Int]) -> int:
    """Consume a Python mapping graph input directly."""
    return py_dict_sum(values=values)


@graph
def empty_py_list_graph() -> list[Int]:
    """Return an empty Python list from a task."""
    return empty_py_list()


@graph
def empty_py_dict_graph() -> dict[str, Int]:
    """Return an empty Python mapping from a task."""
    return empty_py_dict()
