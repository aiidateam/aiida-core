"""Unit tests for the LazyChoice click parameter type."""

from importlib import metadata

import click
import pytest
from packaging import version

from aiida.cmdline import LazyChoice

CLICK_VERSION = version.Version(metadata.version('click'))


@pytest.fixture
def simple_choices():
    """Fixture providing a simple list of string choices."""
    return ('option1', 'option2', 'option3')


@pytest.fixture
def choice_getter(simple_choices):
    """Fixture providing a callable that returns simple choices."""

    def get_choices():
        return simple_choices

    return get_choices


@pytest.fixture
def counting_choice_getter():
    """Fixture providing a callable that counts how many times it's called."""
    call_count = {'count': 0}

    def get_choices():
        call_count['count'] += 1
        return (f'choice_{call_count["count"]}',)

    get_choices.call_count = call_count
    return get_choices


def test_init_with_non_callable_raises_typeerror():
    """Test that LazyChoice raises TypeError when initialized with non-callable."""
    with pytest.raises(TypeError, match='Must pass a callable, got'):
        LazyChoice(['option1', 'option2'])

    with pytest.raises(TypeError, match='Must pass a callable, got'):
        LazyChoice('not_callable')

    with pytest.raises(TypeError, match='Must pass a callable, got'):
        LazyChoice(123)


def test_lazy_evaluation(counting_choice_getter):
    """Test that choices are evaluated lazily."""
    lazy_choice = LazyChoice(counting_choice_getter)

    # Should not have been called yet
    assert counting_choice_getter.call_count['count'] == 0

    # First access should trigger evaluation
    choices = lazy_choice.choices
    assert counting_choice_getter.call_count['count'] == 1
    assert choices == ('choice_1',)

    # Second access should use cached result
    choices2 = lazy_choice.choices
    assert counting_choice_getter.call_count['count'] == 1  # Should not increment
    assert choices2 == choices


def test_convert_method():
    """Test the convert method delegates to click.Choice."""

    def get_choices():
        return ('valid', 1, '2')

    lazy_choice = LazyChoice(get_choices)
    param = click.Option(['-t', '--test'])
    ctx = click.Context(click.Command('test'))

    # Valid choices should work, regardless of type
    assert 'valid' == lazy_choice.convert('valid', param, ctx)
    assert 1 == lazy_choice.convert(1, param, ctx)
    # The following one only seems to works with click>=8.2
    if CLICK_VERSION >= version.Version('8.2.0'):
        assert 1 == lazy_choice.convert('1', param, ctx)

    # Invalid choice should raise click.BadParameter
    with pytest.raises(click.BadParameter):
        lazy_choice.convert('invalid', param, ctx)


def test_repr_uninitialised(choice_getter):
    """Test __repr__ when LazyChoice is not yet initialized."""
    lazy_choice = LazyChoice(choice_getter)
    assert repr(lazy_choice) == 'LazyChoice(UNINITIALISED)'


def test_repr_initialised(choice_getter):
    """Test __repr__ after LazyChoice has been initialized."""
    lazy_choice = LazyChoice(choice_getter)
    # Trigger initialization
    _ = lazy_choice.choices

    assert repr(lazy_choice) == "LazyChoice(['option1', 'option2', 'option3'])"


def test_generic_type_support():
    """Test that LazyChoice supports generic types."""

    def get_int_choices():
        return (1, 2, 3)

    def get_str_choices():
        return ('a', 'b', 'c')

    int_lazy_choice = LazyChoice[int](get_int_choices)
    str_lazy_choice = LazyChoice[str](get_str_choices)

    assert int_lazy_choice.choices == (1, 2, 3)
    assert str_lazy_choice.choices == ('a', 'b', 'c')


def test_empty_choices():
    """Test LazyChoice with empty choices."""

    def get_empty_choices():
        return ()

    lazy_choice = LazyChoice(get_empty_choices)
    assert lazy_choice.choices == ()
    assert repr(lazy_choice) == 'LazyChoice([])'


def test_choices_with_different_types():
    """Test LazyChoice with mixed type choices."""

    def get_mixed_choices():
        return ('string', 42, True, None)

    lazy_choice = LazyChoice(get_mixed_choices)
    assert lazy_choice.choices == ('string', 42, True, None)


def test_exception_in_get_choices():
    """Test behavior when get_choices callable raises an exception."""

    def failing_get_choices():
        raise ValueError('Something went wrong')

    lazy_choice = LazyChoice(failing_get_choices)

    with pytest.raises(ValueError, match='Something went wrong'):
        _ = lazy_choice.choices


def test_get_metavar():
    """Test get_metavar method returns expected format."""

    def get_choices():
        return ('short', 'medium', 'long')

    lazy_choice = LazyChoice(get_choices)
    param = click.Option(['-s', '--size'])
    ctx = None
    if CLICK_VERSION >= version.Version('8.2.0'):
        ctx = click.Context(click.Command('test'))

    # get_metavar should return the choices in the expected format
    metavar = lazy_choice.get_metavar(param, ctx=ctx)
    assert isinstance(metavar, str)
    # The exact format depends on click's implementation, but should contain the choices
    assert 'short' in metavar


def test_get_missing_message():
    """Test get_missing_message method returns appropriate message."""

    def get_choices():
        return ('red', 'green', 'blue')

    lazy_choice = LazyChoice(get_choices)
    param = click.Option(['-c', '--color'], required=True)
    ctx = None
    if CLICK_VERSION >= version.Version('8.2.0'):
        ctx = click.Context(click.Command('test'))

    message = lazy_choice.get_missing_message(param, ctx=ctx)
    assert isinstance(message, str)
    for choice in get_choices():
        assert choice in message
