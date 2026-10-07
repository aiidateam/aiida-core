"""Tests for :mod:`aiida.cmdline.groups.dynamic`."""

import abc
import typing as t

import click
import pydantic as pdt
import pytest
from click.testing import CliRunner

from aiida.cmdline.groups.dynamic import DynamicEntryPointCommandGroup
from aiida.cmdline.params.options.interactive import BooleanInteractiveOption
from aiida.cmdline.spec import CliParameter, PydanticCliCreateSpec


class CustomClass:
    """Test plugin class with a Pydantic CLI creation spec."""

    class Model(pdt.BaseModel):
        required_value: str = pdt.Field(title='Required value', description='Required value help.')
        optional_value: int = pdt.Field(title='Optional value', default=7)
        generated_value: str = pdt.Field(title='Generated value', default_factory=lambda: 'generated')
        positive_value: int = pdt.Field(title='Positive value', gt=0)
        enabled: bool = pdt.Field(title='Enabled', default=False)


CustomClass.cli_spec = PydanticCliCreateSpec(CustomClass.Model)


class NoCliSpecCustomClass:
    """Test plugin class which does not expose a CLI creation spec."""


class AbstractCustomClass(abc.ABC):
    """Test abstract plugin class with a CLI creation spec."""

    class Model(pdt.BaseModel):
        value: str

    cli_spec = PydanticCliCreateSpec(Model)

    @abc.abstractmethod
    def run(self) -> None:
        """Implement the plugin behavior."""


class UnstorableCustomClass:
    """Test non-storable plugin class that otherwise supports CLI creation."""

    _storable = False
    cli_spec = PydanticCliCreateSpec(pdt.BaseModel)


class HiddenCustomClass:
    """Test plugin class that supports creation but is hidden from listings."""

    cli_exposed = False

    class Model(pdt.BaseModel):
        value: str


HiddenCustomClass.cli_spec = PydanticCliCreateSpec(HiddenCustomClass.Model)


class MultiValueCliSpec:
    """CLI spec for checking repeated multi-value Click parameters."""

    def parameters(self) -> list[CliParameter]:
        return [
            CliParameter(
                name='pair',
                annotation=str,
                required=False,
                default=(),
                prompt=False,
                help='Pairs',
                short_name='-p',
                multiple=True,
                nargs=2,
            )
        ]

    def collect_interactive(
        self,
        ctx: click.Context,
        values: dict[str, t.Any],
        *,
        non_interactive: bool,
    ) -> dict[str, t.Any]:
        return values

    def validate(self, values: dict[str, t.Any]) -> pdt.BaseModel:
        return pdt.BaseModel()


class MultiValueClass:
    """Plugin used to check repeated multi-value option generation."""

    cli_spec = MultiValueCliSpec()


class CollectingCliSpec(PydanticCliCreateSpec):
    """CLI spec that records the interactive-collection mode."""

    def __init__(self, model: type[pdt.BaseModel]) -> None:
        super().__init__(model)
        self.non_interactive_values: list[bool] = []

    def parameters(self) -> list[CliParameter]:
        return [
            CliParameter(
                name='value',
                annotation=str,
                required=False,
                default='fallback',
                prompt=False,
                help='Value',
            )
        ]

    def collect_interactive(
        self,
        ctx: click.Context,
        values: dict[str, t.Any],
        *,
        non_interactive: bool,
    ) -> dict[str, t.Any]:
        self.non_interactive_values.append(non_interactive)
        if non_interactive:
            return values
        return values | {'value': 'collected'}


class CollectingCustomClass:
    """Plugin used to test interactive input collection."""

    class Model(pdt.BaseModel):
        value: str = 'fallback'


CollectingCustomClass.cli_spec = CollectingCliSpec(CollectingCustomClass.Model)


def test_list_options(entry_points):
    """Test options are generated from the entry point's resolved CLI spec."""
    entry_points.add(CustomClass, 'aiida.custom:custom')
    group = DynamicEntryPointCommandGroup(command=lambda *args, **kwargs: None, entry_point_group='aiida.custom')

    options = {}
    for decorator in group.list_options('custom'):
        command = decorator(lambda **kwargs: None)
        option = command.__click_params__[0]
        options[option.name] = option

    assert set(options) == {'required_value', 'optional_value', 'generated_value', 'positive_value', 'enabled'}
    assert options['required_value'].required
    assert options['required_value'].type.name == 'text'
    assert options['required_value'].help == 'Required value help.'
    assert options['optional_value'].default == 7
    assert options['generated_value'].default is CustomClass.Model.model_fields['generated_value'].default_factory
    assert options['positive_value'].type.name == 'integer'
    assert options['enabled'].is_flag
    assert options['enabled'].default is False
    assert isinstance(options['enabled'], BooleanInteractiveOption)


def test_boolean_option_generation(entry_points):
    """Test bool fields generate explicit positive and negative flag options."""
    entry_points.add(CustomClass, 'aiida.custom:custom')
    group = DynamicEntryPointCommandGroup(command=lambda *args, **kwargs: None, entry_point_group='aiida.custom')
    option = next(
        decorator(lambda **kwargs: None).__click_params__[0]
        for decorator in group.list_options('custom')
        if decorator(lambda **kwargs: None).__click_params__[0].name == 'enabled'
    )

    assert option.is_flag
    assert option.opts == ['--enabled']
    assert option.secondary_opts == ['--no-enabled']
    assert option.default is False
    assert isinstance(option, BooleanInteractiveOption)


@pytest.mark.parametrize(
    ('cmd_name', 'listed', 'resolvable'),
    (
        pytest.param('custom', True, True, id='supported'),
        pytest.param('no_cli_spec', False, False, id='no-cli-spec'),
        pytest.param('abstract', False, False, id='abstract'),
        pytest.param('unstorable', False, False, id='unstorable'),
        pytest.param('hidden', False, True, id='hidden'),
        pytest.param('non_existent', False, False, id='unknown'),
    ),
)
def test_subcommand_exposure(entry_points, cmd_name, listed, resolvable):
    """Test command discovery and resolution according to CLI support and exposure."""
    entry_points.add(CustomClass, 'aiida.custom:custom')
    entry_points.add(NoCliSpecCustomClass, 'aiida.custom:no_cli_spec')
    entry_points.add(AbstractCustomClass, 'aiida.custom:abstract')
    entry_points.add(UnstorableCustomClass, 'aiida.custom:unstorable')
    entry_points.add(HiddenCustomClass, 'aiida.custom:hidden')
    group = DynamicEntryPointCommandGroup(
        command=lambda *args, **kwargs: None,
        name='create',
        entry_point_group='aiida.custom',
    )
    context = click.Context(group)

    assert (cmd_name in group.list_commands(context)) is listed

    if resolvable:
        assert group.get_command(context, cmd_name) is not None
    else:
        with pytest.raises(click.exceptions.UsageError):
            group.get_command(context, cmd_name)


def test_command_invocation_validates_and_passes_model(entry_points):
    """Test a generated command validates values and passes the model to its callback."""
    entry_points.add(CustomClass, 'aiida.custom:custom')
    received: list[tuple[type[t.Any], CustomClass.Model]] = []

    def callback(ctx: click.Context, cls: type[t.Any], model: CustomClass.Model) -> None:
        received.append((cls, model))

    group = DynamicEntryPointCommandGroup(
        command=callback,
        name='create',
        entry_point_group='aiida.custom',
    )
    command = group.get_command(click.Context(group), 'custom')
    assert command is not None

    result = CliRunner().invoke(
        command,
        [
            '--non-interactive',
            '--required-value',
            'hello',
            '--positive-value',
            '3',
        ],
    )

    assert result.exit_code == 0, result.output
    assert len(received) == 1
    cls, model = received[0]
    assert cls is CustomClass
    assert model.required_value == 'hello'
    assert model.optional_value == 7
    assert model.generated_value == 'generated'
    assert model.positive_value == 3
    assert model.enabled is False


def test_command_invocation_reports_model_validation_error(entry_points):
    """Test Pydantic validation errors are presented as a Click parameter error."""
    entry_points.add(CustomClass, 'aiida.custom:custom')
    group = DynamicEntryPointCommandGroup(
        command=lambda *args, **kwargs: None,
        name='create',
        entry_point_group='aiida.custom',
    )
    command = group.get_command(click.Context(group), 'custom')
    assert command is not None

    result = CliRunner().invoke(
        command,
        [
            '--non-interactive',
            '--required-value',
            'hello',
            '--positive-value',
            '0',
        ],
    )

    assert result.exit_code == 2
    assert '--positive-value' in result.output
    assert 'greater than 0' in result.output


def test_multiple_nargs_are_applied_to_generated_options(entry_points):
    """Test generated Click options preserve repeated multi-value parameter metadata."""
    entry_points.add(MultiValueClass, 'aiida.custom:multi')
    group = DynamicEntryPointCommandGroup(command=lambda *args, **kwargs: None, entry_point_group='aiida.custom')
    option = group.list_options('multi')[0](lambda **kwargs: None).__click_params__[0]

    assert option.opts == ['-p', '--pair']
    assert option.multiple
    assert option.nargs == 2


@pytest.mark.parametrize(
    ('options', 'expected_value', 'non_interactive'),
    (
        pytest.param([], 'collected', False, id='interactive'),
        pytest.param(['--non-interactive'], 'fallback', True, id='non-interactive'),
    ),
)
def test_interactive_collection(entry_points, options, expected_value, non_interactive):
    """Test generated commands pass parsed values and interaction mode to the CLI spec."""
    entry_points.add(CollectingCustomClass, 'aiida.custom:collecting')
    cli_spec = CollectingCustomClass.cli_spec
    cli_spec.non_interactive_values.clear()
    received = []

    def callback(ctx: click.Context, cls: type[t.Any], model: pdt.BaseModel) -> None:
        received.append((cls, model))

    group = DynamicEntryPointCommandGroup(
        command=callback,
        name='create',
        entry_point_group='aiida.custom',
    )
    command = group.get_command(click.Context(group), 'collecting')
    assert command is not None

    result = CliRunner().invoke(command, options)

    assert result.exit_code == 0, result.output
    assert cli_spec.non_interactive_values == [non_interactive]
    assert received[0][0] is CollectingCustomClass
    assert received[0][1].value == expected_value
