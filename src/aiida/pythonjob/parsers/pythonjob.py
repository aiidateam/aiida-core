"""Parser for an `PythonJob` job."""

import json

from aiida.parsers.parser import Parser
from aiida.node_graph.socket_spec import SocketSpec

from .utils import parse_outputs

# Map error_type from script.py to exit code label
ERROR_TYPE_TO_EXIT_CODE = {
    "IMPORT_CLOUDPICKLE_FAILED": "ERROR_IMPORT_CLOUDPICKLE_FAILED",
    "IMPORT_MPI4PY_FAILED": "ERROR_IMPORT_MPI4PY_FAILED",
    "UNPICKLE_INPUTS_FAILED": "ERROR_UNPICKLE_INPUTS_FAILED",
    "UNPICKLE_FUNCTION_FAILED": "ERROR_UNPICKLE_FUNCTION_FAILED",
    "FUNCTION_EXECUTION_FAILED": "ERROR_FUNCTION_EXECUTION_FAILED",
    "PICKLE_RESULTS_FAILED": "ERROR_PICKLE_RESULTS_FAILED",
}


class PythonJobParser(Parser):
    """Parser for an `PythonJob` job."""

    def parse(self, **kwargs):
        import pickle

        # Read outputs SocketSpec
        spec_dict = self.node.base.attributes.get("outputs_spec", {})
        self.outputs_spec = SocketSpec.from_dict(spec_dict)

        # load custom serializers
        self.serializers = self.node.base.attributes.get("serializers", {})

        # 1) Read _error.json
        try:
            with self.retrieved.base.repository.open("_error.json", "r") as ef:
                error_data = json.load(ef)
                # If error_data is non-empty, we have an error from the script
                if error_data:
                    error_type = error_data.get("error_type", "UNKNOWN_ERROR")
                    exception_message = error_data.get("exception_message", "")
                    traceback_str = error_data.get("traceback", "")

                    # Default to a generic code if we can't match a known error_type
                    exit_code_label = ERROR_TYPE_TO_EXIT_CODE.get(error_type, "ERROR_SCRIPT_FAILED")

                    # Use `.format()` to inject the exception and traceback
                    return self.exit_codes[exit_code_label].format(exception=exception_message, traceback=traceback_str)
        except OSError:
            # No _error.json file found
            pass
        except json.JSONDecodeError as exc:
            self.logger.error(f"Error reading _error.json: {exc}")
            return self.exit_codes.ERROR_INVALID_OUTPUT

        # 2) If we reach here, _error.json exists but is empty or doesn't exist at all -> no error recorded
        #    Proceed with parsing results.pickle
        try:
            with self.retrieved.base.repository.open("results.pickle", "rb") as handle:
                results = pickle.load(handle)

                outputs, exit_code = parse_outputs(
                    results,
                    output_spec=self.outputs_spec,
                    exit_codes=self.exit_codes,
                    logger=self.logger,
                    serializers=self.serializers,
                )
                if exit_code:
                    return exit_code

                # Store the outputs
                for name, value in (outputs or {}).items():
                    self.out(name, value)

        except OSError:
            return self.exit_codes.ERROR_READING_OUTPUT_FILE
        except ValueError as exception:
            self.logger.error(
                f"An error occurred when attempting to parse the output of the calculation: ValueError: {exception!s}"
            )
            return self.exit_codes.ERROR_INVALID_OUTPUT
