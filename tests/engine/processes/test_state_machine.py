"""Tests for the process state machine."""

from aiida.engine.processes.state_machine import State, StateMachine


def test_state_map_is_built_per_class():
    """Test a subclass builds its own state map after its parent's map is built."""

    class ParentState(State):
        LABEL = 'parent'

    class ChildState(State):
        LABEL = 'child'

    class ParentStateMachine(StateMachine):
        @classmethod
        def get_states(cls):
            return (ParentState,)

    class ChildStateMachine(ParentStateMachine):
        @classmethod
        def get_states(cls):
            return (ChildState,)

    assert ParentStateMachine.get_states_map() == {'parent': ParentState}
    assert ChildStateMachine.get_states_map() == {'child': ChildState}
