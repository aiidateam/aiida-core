"""Walkthrough of the design, one function per decision.

python -m poc
"""

from __future__ import annotations

import typing as t
from collections.abc import Sequence

from pydantic import ValidationError

from poc.cmdline._core.models import build_cli_model, cli_deserialize, cli_serialize
from poc.orm._core.fields import BaseField
from poc.orm.computers import Computer
from poc.orm.fields import AttributeField
from poc.orm.nodes import Bool, Data, Int, Node, Str
from poc.restapi._core.models import read_only_fields, rest_deserialize, rest_serialize, rest_validate


def show(label: str, value: t.Any) -> None:
    print(f'  {label:50} {value}')


def section(number: int, title: str, where: str) -> None:
    print(f'\n{number}. {title}\n   ({where})')


def query_view() -> None:
    """A declaration is a value; its query view is a separate object."""
    declaration, field = Int._field_declarations['value'], Int.fields.value
    show('Int._field_declarations["value"]', f'{type(declaration).__name__} -- ordinary ==, safe as a dict key')
    show('Int.fields.value    (its query view)', f'{type(field).__name__} -- == builds a filter')
    show('field.declaration is declaration', field.declaration is declaration)
    show(
        'declarations of different classes stay distinct',
        Int._field_declarations['value'] != Str._field_declarations['value'],
    )
    show('{Int value declaration: 1}[Str value declaration]', 'KeyError -- not conflated')
    show('Int.fields.value == 42', (Int.fields.value == 42).as_dict())
    show('Node.fields.label == "x"', (Node.fields.label == 'x').as_dict())
    show('(value > 1) & (label == "x")', ((Int.fields.value > 1) & (Node.fields.label == 'x')).as_dict())
    show('(label == "x") & Bool.fields.value', ((Node.fields.label == 'x') & Bool.fields.value).as_dict())
    show('QbFields / QbFieldFilters', 'aiida.orm.fields, unchanged -- only what they hold changes')


def validation_of_declaration_correctness_at_class_definition() -> None:
    """Declarations are validated when the class is defined."""
    try:

        class Broken(Data):
            _attribute_fields: t.ClassVar[Sequence[BaseField]] = (AttributeField('not an identifier', int),)
    except ValueError as exc:
        show('a name that is not an identifier', f'ValueError: {exc}')
    show('two names over one backend key', 'unrepresentable -- the name is the key')
    try:
        Node(no_such_column=1)
    except ValueError as exc:
        show('a column the schema does not have', f'ValueError: {exc}')


def _positive(value: float) -> float:
    """Reject a setpoint no thermostat could hold."""
    if value <= 0:
        msg = f'a temperature must be above absolute zero, got {value}'
        raise ValueError(msg)
    return value


def data_plugin() -> None:
    """A data plugin declares attributes, and nothing else."""

    class Trajectory(Data):
        """A data plugin, declared outside `aiida-core`."""

        _attribute_fields: t.ClassVar[Sequence[BaseField]] = (
            AttributeField('frames', list, 'The frames of the trajectory'),
            AttributeField('temperature', float, 'The thermostat setpoint', validator=_positive),
        )

        def __init__(self, frames: list, temperature: float, **kwargs: t.Any) -> None:
            super().__init__(**kwargs)
            self.base.attributes.set('frames', frames)
            self.base.attributes.set('temperature', temperature)

    trajectory = Trajectory(frames=[1, 2, 3], temperature=300.0, uuid='t-1', label='md-run')

    show('all it declares', sorted(f.name for f in Trajectory._attribute_fields))
    show(
        'no cli_* or rest_api_* option among them',
        not any(f.cli.exclude or f.rest_api.read_only for f in Trajectory._attribute_fields),
    )
    show('yet GET works', {k: v for k, v in rest_serialize(trajectory).items() if k not in ('ctime', 'attributes')})
    show('and read-only is inherited from Node', sorted(read_only_fields(Trajectory)))
    show('the CLI needs no model for it', 'a data node is exported by format, not by field')
    show('the name stays free for an accessor', 'a declaration names itself; it is not a class attribute')
    show('and it owns its own construction', 'from_model passes values; __init__ decides')
    try:
        rest_validate(Trajectory, {'label': '', 'source': None, 'attributes': {}, 'frames': [], 'temperature': -5.0})
    except ValidationError as exc:
        show('a declared validator guards writes', exc.errors()[0]['msg'])


def validation_of_attribute_value_on_set() -> None:
    """A declared validator runs wherever a value enters."""
    body = {
        'label': 'localhost',
        'description': '',
        'hostname': 'localhost',
        'transport_type': 'core.local',
        'scheduler_type': 'core.direct',
        'mpirun_command': [],
    }
    show('PUT with a good hostname', type(rest_validate(Computer, body)).__name__)
    try:
        rest_validate(Computer, {**body, 'hostname': 'local host'})
    except ValidationError as exc:
        show('PUT with a bad one', exc.errors()[0]['msg'])
    show('why the declaration and not __init__', 'a PUT replaces values; it never constructs')
    show('so it runs for POST and CLI import too', 'every layer model wires the same check in')

    node = Int(42, uuid='u-2', label='fine')
    for how, write in (
        ('node.label = ...', lambda: setattr(node, 'label', 'two\nlines')),
        ('base.columns.set(...)', lambda: node.base.columns.set('label', 'two\nlines')),
    ):
        try:
            write()
        except ValueError as exc:
            show(f'and for a direct write, {how}', f'ValueError: {exc}')
    node.base.attributes.set('undeclared', 'anything')
    show('an undeclared key has nothing to check', 'undeclared' in node.base.attributes.all)


def cli_round_trip() -> None:
    """ORM object -> CLI model -> YAML, and back."""
    computer = Computer(
        uuid='u-1',
        label='localhost',
        hostname='localhost.localdomain',
        transport_type='core.local',
        scheduler_type='core.direct',
        mpirun_command=['mpirun', '-np', '4'],
    )

    payload = cli_serialize(computer)
    rebuilt = cli_deserialize(Computer, payload)

    show('what `verdi computer export` writes', payload)
    show('and `verdi computer import` rebuilds', f'{rebuilt.label} {rebuilt.backend_entity.mpirun_command}')
    show('lossless', cli_serialize(rebuilt) == payload)
    show('published under its declared name', 'no aliases; the file follows the fields')
    show('rendered by pydantic, not by us', 'a list stays a list; the file follows the values')
    show('excluded by cli_exclude', 'uuid -- a fresh import carries no identity')
    show('the model class, for options and schema', build_cli_model(Computer).__name__)


def rest_requests() -> None:
    """GET and POST, over the same declarations."""
    stored = Int(42, uuid='u-1', label='the answer')

    # GET /nodes/u-1 -- the read model, so identity is included
    body = rest_serialize(stored)
    show('GET  -> body', {k: v for k, v in body.items() if k != 'ctime'})
    show('     read model includes identity', 'uuid' in body)

    # POST /nodes -- the write model, so identity is refused rather than ignored
    posted = rest_deserialize(Int, {'label': 'from a client', 'value': 7, 'source': None, 'attributes': {}})
    show('POST -> ORM object', f'{posted!r} label={posted.label!r}')
    show('     write model excludes', sorted(read_only_fields(Int)))
    try:
        rest_deserialize(Int, {'label': 'x', 'value': 7, 'source': None, 'attributes': {}, 'uuid': 'smuggled'})
    except ValidationError as exc:
        show('POST with a read-only field', f'{type(exc).__name__}: {exc.errors()[0]["type"]}')
    show('constructed by Entity.from_model', 'no override -- Int is field-shaped')
    show('from_model only passes values', "what to do with them is `__init__`'s business")


#: Each section, with the module it is about. The docstring is the section title.
SECTIONS: t.Final = (
    (query_view, 'poc.orm._core.qb_fields'),
    (validation_of_declaration_correctness_at_class_definition, 'poc.orm._core.entities'),
    (data_plugin, 'poc.orm.nodes.data'),
    (cli_round_trip, 'poc.cmdline._core.models'),
    (validation_of_attribute_value_on_set, 'poc.orm._core.fields'),
    (rest_requests, 'poc.restapi._core.models'),
)


def main() -> None:
    for number, (run, where) in enumerate(SECTIONS, start=1):
        section(number, (run.__doc__ or '').rstrip('.'), where)
        run()


if __name__ == '__main__':
    main()
