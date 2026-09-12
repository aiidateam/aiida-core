from aiida.node_graph.task import Task
from aiida.node_graph.task_spec import TaskSpec
from aiida.node_graph.socket_spec import namespace
from aiida.node_graph.executor import RuntimeExecutor
from aiida.node_graph.executors.tests import test_enum
from aiida.node_graph import task
from math import pow


@task()
def test_float(value: float, t=1) -> float:
    return float(value)


@task()
def test_string(value: str, t=1) -> str:
    return str(value)


@task()
def test_add(x: float, y: float, t=1) -> float:
    return x + y


@task()
def test_sqrt(x: float, t=1) -> float:
    import math

    return math.sqrt(x)


class TestEnum(Task):

    _default_spec = TaskSpec(
        identifier="node_graph.test_enum",
        catalog="Test",
        inputs=namespace(),
        outputs=namespace(
            result=object,
        ),
        executor=RuntimeExecutor.from_callable(test_enum),
        base_class_path="node_graph.tasks.tests.TestEnum",
    )

    def create_properties(self):
        self.add_property("node_graph.int", "t", default=1)
        self.add_property(
            "node_graph.enum",
            "function",
            default="pow",
            options=[
                ["pow", "pow", "pow function"],
                ["sqrt", "sqrt", "sqrt function"],
            ],
        )


class TestEnumUpdate(Task):

    _default_spec = TaskSpec(
        identifier="node_graph.test_enum_update",
        catalog="Test",
        inputs=namespace(),
        outputs=namespace(
            result=object,
        ),
        executor=RuntimeExecutor.from_callable(pow),
        base_class_path="node_graph.tasks.tests.TestEnumUpdate",
    )

    def create_properties(self):
        self.add_property("node_graph.int", "t", default=1)
        self.add_property(
            "node_graph.enum",
            "function",
            default="pow",
            options=[
                ["pow", "pow", "pow function"],
                ["sqrt", "sqrt", "sqrt function"],
            ],
            update=self.update_spec,
        )

    def update_spec(self):
        import importlib
        from dataclasses import replace

        if self.properties["function"].value in ["pow"]:
            input_spec = namespace(
                x=float,
                y=float,
            )
        elif self.properties["function"].value in ["sqrt"]:
            input_spec = namespace(
                x=float,
            )
        func = getattr(
            importlib.import_module("math"),
            self.properties["function"].content,
        )
        executor = RuntimeExecutor.from_callable(func)
        self.spec = replace(self.spec, inputs=input_spec, executor=executor)
        self._materialize_from_spec()
