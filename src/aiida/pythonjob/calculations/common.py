"""Common helpers and mixins shared by PyFunction and PythonJob."""

from __future__ import annotations

from typing import Any, MutableMapping

from aiida.orm import Data, Str, to_aiida_type

from aiida.pythonjob.data.deserializer import deserialize_to_raw_python_data

# Attribute keys stored on ProcessNode.base.attributes
ATTR_INPUTS_SPEC = "inputs_spec"
ATTR_OUTPUTS_SPEC = "outputs_spec"
ATTR_SERIALIZERS = "serializers"
ATTR_DESERIALIZERS = "deserializers"


def add_common_function_io(spec) -> None:
    """Attach inputs common to both in-process and remote Python execution.

    Works with both :class:`~aiida.engine.ProcessSpec` and
    :class:`~aiida.engine.CalcJobProcessSpec`.
    """
    spec.input_namespace("function_data", dynamic=True, required=True)
    spec.input(
        "metadata.inputs_spec",
        valid_type=dict,
        required=False,
        help="Specification for the inputs.",
    )
    spec.input(
        "metadata.outputs_spec",
        valid_type=dict,
        required=False,
        help="Specification for the outputs.",
    )
    spec.input("process_label", valid_type=Str, serializer=to_aiida_type, required=False)

    spec.input_namespace("function_inputs", valid_type=Data, required=False)

    spec.input(
        "metadata.deserializers",
        valid_type=dict,
        required=False,
        help="Deserializers to convert input AiiDA nodes to raw Python data.",
    )
    spec.input(
        "metadata.serializers",
        valid_type=dict,
        required=False,
        help="Serializers to convert raw Python data to AiiDA nodes.",
    )
    spec.exit_code(
        320,
        "ERROR_DESERIALIZE_INPUTS_FAILED",
        invalidates_cache=True,
        message="Failed to deserialize inputs.\n{exception}\n{traceback}",
    )
    spec.exit_code(
        321,
        "ERROR_INVALID_OUTPUT",
        invalidates_cache=True,
        message="The output file contains invalid output.",
    )
    spec.exit_code(
        322,
        "ERROR_RESULT_OUTPUT_MISMATCH",
        invalidates_cache=True,
        message="The number of results does not match the number of outputs.",
    )

    spec.inputs.validator = validate_function_inputs


def validate_function_inputs(inputs: MutableMapping[str, Any], _):
    """Validate that ``function_inputs`` can be deserialized.

    Uses ``metadata.deserializers`` if provided. Raises if invalid.
    """
    deserializers = inputs.get("metadata", {}).get("deserializers", {})
    function_inputs = inputs.get("function_inputs", {})
    # This should raise if any datum cannot be deserialized.
    deserialize_to_raw_python_data(function_inputs, deserializers=deserializers, dry_run=True)


class FunctionProcessMixin:
    """Mixin providing common metadata handling and labeling logic.

    Place this mixin **before** :class:`~aiida.engine.Process`/``CalcJob`` in the MRO.
    """

    label_template: str = "{name}"
    default_name: str = "anonymous_function"

    def _extract_declared_name(self) -> str | None:  # pragma: no cover - trivial
        """Try to read a user-declared function name from inputs.

        Subclasses may extend this (e.g. by inspecting a pickled function).
        """
        try:
            if "name" in self.inputs.function_data:
                return self.inputs.function_data.name
        except Exception:
            pass
        return None

    def get_function_name(self) -> str:  # used by both PyFunction and PythonJob
        return self._extract_declared_name() or self.default_name

    def _build_process_label(self) -> str:  # called by AiiDA engine
        if "process_label" in self.inputs:
            return self.inputs.process_label.value
        return self.label_template.format(name=self.get_function_name())

    def _setup_metadata(self, metadata: dict) -> None:  # type: ignore[override]
        """Store common metadata on the ProcessNode and forward the rest."""
        self.node.base.attributes.set(ATTR_INPUTS_SPEC, metadata.pop("inputs_spec", {}))
        self.node.base.attributes.set(ATTR_OUTPUTS_SPEC, metadata.pop("outputs_spec", {}))
        self.node.base.attributes.set(ATTR_SERIALIZERS, metadata.pop("serializers", {}))
        self.node.base.attributes.set(ATTR_DESERIALIZERS, metadata.pop("deserializers", {}))
        super()._setup_metadata(metadata)
