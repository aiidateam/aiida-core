from __future__ import annotations

import pathlib
import typing as t

from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.common.folders import Folder
from aiida.common.lang import override
from aiida.engine import CalcJob, CalcJobProcessSpec
from aiida.orm import FolderData, List, RemoteData, SinglefileData, Str, to_aiida_type

from aiida.pythonjob.calculations.common import (
    ATTR_DESERIALIZERS,
    ATTR_INPUTS_SPEC,
    FunctionProcessMixin,
    add_common_function_io,
)
from aiida.pythonjob.data.deserializer import deserialize_to_raw_python_data

__all__ = ("PythonJob",)


class PythonJob(FunctionProcessMixin, CalcJob):
    """CalcJob to run a Python function on a remote computer.

    Supports two modes:
    1) Loading a pickled function object (``function_data.pickled_function``).
    2) Embedding raw source code for the function (``function_data.source_code``).
    """

    _internal_retrieve_list: list[str] = []
    _retrieve_singlefile_list: list[str] = []
    _retrieve_temporary_list: list[str] = []

    _DEFAULT_INPUT_FILE = "script.py"
    _DEFAULT_OUTPUT_FILE = "aiida.out"
    _DEFAULT_PARENT_FOLDER_NAME = "./parent_folder/"
    _SOURCE_CODE_KEY = "source_code"

    label_template = "PythonJob<{name}>"
    default_name = "anonymous_function"

    @classmethod
    def define(cls, spec: CalcJobProcessSpec) -> None:  # type: ignore[override]
        super().define(spec)
        add_common_function_io(spec)
        spec.outputs.dynamic = True

        # Additional, job-specific inputs
        spec.input(
            "parent_folder",
            valid_type=(RemoteData, FolderData, SinglefileData),
            required=False,
            help="Use a local or remote folder as parent folder (for restarts and similar)",
        )
        spec.input(
            "parent_folder_name",
            valid_type=Str,
            required=False,
            serializer=to_aiida_type,
            help=(
                "Default name of the subfolder to create in the working directory "
                "where the files from parent_folder are placed."
            ),
        )
        spec.input(
            "parent_output_folder",
            valid_type=Str,
            default=None,
            required=False,
            serializer=to_aiida_type,
            help="Name of the subfolder inside 'parent_folder' from which to copy files",
        )
        spec.input_namespace(
            "upload_files",
            valid_type=(FolderData, SinglefileData),
            required=False,
            help="The folder/files to upload",
        )
        spec.input_namespace(
            "copy_files",
            valid_type=(RemoteData,),
            required=False,
            help="The folder/files to copy from the remote computer",
        )
        spec.input(
            "additional_retrieve_list",
            valid_type=List,
            default=None,
            required=False,
            serializer=to_aiida_type,
            help="Additional filenames to retrieve from the remote working directory",
        )

        # Defaults and options
        spec.inputs["metadata"]["options"]["parser_name"].default = "pythonjob.pythonjob"
        spec.inputs["metadata"]["options"]["input_filename"].default = cls._DEFAULT_INPUT_FILE
        spec.inputs["metadata"]["options"]["output_filename"].default = cls._DEFAULT_OUTPUT_FILE
        spec.inputs["metadata"]["options"]["resources"].default = {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        }

        # Exit codes (job-specific)
        spec.exit_code(
            310,
            "ERROR_READING_OUTPUT_FILE",
            invalidates_cache=True,
            message="The output file could not be read.",
        )
        spec.exit_code(
            323,
            "ERROR_IMPORT_CLOUDPICKLE_FAILED",
            invalidates_cache=True,
            message="Importing cloudpickle failed.\n{exception}\n{traceback}",
        )
        spec.exit_code(
            324,
            "ERROR_UNPICKLE_INPUTS_FAILED",
            invalidates_cache=True,
            message="Failed to unpickle inputs.\n{exception}\n{traceback}",
        )
        spec.exit_code(
            325,
            "ERROR_UNPICKLE_FUNCTION_FAILED",
            invalidates_cache=True,
            message="Failed to unpickle user function.\n{exception}\n{traceback}",
        )
        spec.exit_code(
            326,
            "ERROR_FUNCTION_EXECUTION_FAILED",
            invalidates_cache=True,
            message="Function execution failed.\n{exception}\n{traceback}",
        )
        spec.exit_code(
            327,
            "ERROR_PICKLE_RESULTS_FAILED",
            invalidates_cache=True,
            message="Failed to pickle results.\n{exception}\n{traceback}",
        )
        spec.exit_code(
            328,
            "ERROR_SCRIPT_FAILED",
            invalidates_cache=True,
            message="The script failed for an unknown reason.\n{exception}\n{traceback}",
        )
        spec.exit_code(
            329,
            "ERROR_IMPORT_MPI4PY_FAILED",
            invalidates_cache=True,
            message="Trying to run with MPI support, but importing mpi4py failed.\n{exception}\n{traceback}",
        )

    @override
    def _setup_db_record(self) -> None:
        super()._setup_db_record()
        # Preserve raw source (if provided) for reproducibility
        if "source_code" in self.inputs.function_data:
            self.node.base.attributes.set(self._SOURCE_CODE_KEY, self.inputs.function_data.source_code)

    def _gather_parent_transfers(self) -> tuple[list[tuple], list[tuple]]:
        """Build remote/local copy lists for the optional ``parent_folder``.

        Returns: ``(remote_list, local_copy_list)``
        """
        remote_list: list[tuple] = []
        local_copy_list: list[tuple] = []

        source = self.inputs.get("parent_folder", None)
        if source is None:
            return remote_list, local_copy_list

        # Determine subfolder name in the working directory
        parent_folder_name = (
            self.inputs.parent_folder_name.value
            if "parent_folder_name" in self.inputs
            else self._DEFAULT_PARENT_FOLDER_NAME
        )

        if isinstance(source, RemoteData):
            dirpath_remote = pathlib.Path(source.get_remote_path())
            if self.inputs.parent_output_folder is not None:
                dirpath_remote /= self.inputs.parent_output_folder.value
            remote_list.append((source.computer.uuid, str(dirpath_remote), parent_folder_name))
        elif isinstance(source, FolderData):
            dirname = self.inputs.parent_output_folder.value if self.inputs.parent_output_folder is not None else ""
            local_copy_list.append((source.uuid, dirname, parent_folder_name))
        elif isinstance(source, SinglefileData):
            local_copy_list.append((source.uuid, source.filename, source.filename))
        else:  # pragma: no cover - defensive
            raise TypeError(f"Unsupported parent_folder type: {type(source)!r}")

        return remote_list, local_copy_list

    def _gather_uploads(self) -> list[tuple]:
        local_copy_list: list[tuple] = []
        if "upload_files" not in self.inputs:
            return local_copy_list
        for key, src in self.inputs.upload_files.items():
            new_key = key.replace("_dot_", ".")
            if isinstance(src, FolderData):
                local_copy_list.append((src.uuid, "", new_key))
            elif isinstance(src, SinglefileData):
                local_copy_list.append((src.uuid, src.filename, src.filename))
            else:
                raise ValueError(
                    f"Input file/folder '{key}' of type {type(src)} is not supported. "
                    "Only AiiDA SinglefileData and FolderData are allowed."
                )
        return local_copy_list

    def _gather_remote_copies(self) -> list[tuple]:
        remote_list: list[tuple] = []
        if "copy_files" not in self.inputs:
            return remote_list
        for key, src in self.inputs.copy_files.items():
            new_key = key.replace("_dot_", ".")
            dirpath_remote = pathlib.Path(src.get_remote_path())
            remote_list.append((src.computer.uuid, str(dirpath_remote), new_key))
        return remote_list

    # ---- Core API -------------------------------------------------------
    def prepare_for_submission(self, folder: Folder) -> CalcInfo:
        """Prepare the calculation for submission.

        1) Write the python script (source vs pickled function).
        2) Serialize the inputs (to pickle) and stage any required files.
        """
        import cloudpickle as pickle

        from aiida.pythonjob.calculations.utils import generate_script_py

        dirpath = pathlib.Path(folder._abspath)

        # Deserialize function inputs to raw Python values
        inputs: dict[str, t.Any] = dict(self.inputs.function_inputs or {})
        deserializers = self.node.base.attributes.get(ATTR_DESERIALIZERS, {})
        input_values = deserialize_to_raw_python_data(inputs, deserializers=deserializers)

        # Build the Python script
        source_code = self.node.base.attributes.get(self._SOURCE_CODE_KEY, None)
        pickled_function = self.inputs.function_data.pickled_function
        function_name = self.get_function_name()
        script_content = generate_script_py(
            pickled_function=pickled_function,
            source_code=source_code,
            function_name=function_name,
            withmpi=self.inputs.metadata.options.get("withmpi", False),
        )

        # Write the script
        with folder.open(self.options.input_filename, "w", encoding="utf8") as handle:
            handle.write(script_content)

        # Staging strategy
        symlink = True
        remote_copy_list: list[tuple] = []
        local_copy_list: list[tuple] = []
        remote_symlink_list: list[tuple] = []
        remote_list = remote_symlink_list if symlink else remote_copy_list

        # Parent folder transfers
        parent_remote, parent_local = self._gather_parent_transfers()
        remote_list.extend(parent_remote)
        local_copy_list.extend(parent_local)

        # Upload additional files
        local_copy_list.extend(self._gather_uploads())

        # Copy remote data if any
        remote_list.extend(self._gather_remote_copies())

        # Create a pickle file for the user input values
        filename = "inputs.pickle"
        inputs_spec = self.node.base.attributes.get(ATTR_INPUTS_SPEC, {})
        if inputs_spec:
            input_values = {"__inputs_spec__": inputs_spec, "__inputs__": input_values}
        with folder.open(filename, "wb") as handle:
            pickle.dump(input_values, handle)

        # If using a pickled function, also stage it
        if pickled_function:
            function_pkl_fname = "function.pkl"
            with folder.open(function_pkl_fname, "wb") as handle:
                handle.write(pickled_function)

        # Stage the inputs pickle via a transient SinglefileData to leverage AiiDA transport
        file_data = SinglefileData(file=f"{dirpath}/{filename}")
        file_data.store()
        local_copy_list.append((file_data.uuid, file_data.filename, filename))

        codeinfo = CodeInfo()
        if self.options.get("withmpi", False):
            codeinfo.cmdline_params = [self.options.input_filename]
        else:
            codeinfo.stdin_name = self.options.input_filename
        codeinfo.stdout_name = self.options.output_filename
        codeinfo.code_uuid = self.inputs.code.uuid

        calcinfo = CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = local_copy_list
        calcinfo.remote_copy_list = remote_copy_list
        calcinfo.remote_symlink_list = remote_symlink_list
        calcinfo.retrieve_list = ["results.pickle", self.options.output_filename, "_error.json"]
        if self.inputs.additional_retrieve_list is not None:
            calcinfo.retrieve_list += self.inputs.additional_retrieve_list.get_list()
        calcinfo.retrieve_list += self._internal_retrieve_list

        calcinfo.retrieve_temporary_list = self._retrieve_temporary_list
        calcinfo.retrieve_singlefile_list = self._retrieve_singlefile_list

        return calcinfo
