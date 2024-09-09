# TODO: Use singledispatch to adapt functionality of method based on the type
# Derived data types from

from __future__ import annotations

from aiida import orm
from pathlib import Path
import logging
import yaml


LOGGER = logging.getLogger(__name__)


class DataDumper:
    def __init__(
        self,
        data_node: orm.Data | None = None,
        overwrite: bool = False,
    ) -> None:
        self.data_node = data_node
        self.overwrite = overwrite  # ? Does this make sense here

    def generate_output_name(self):
        pass

    def dump(self, data_node, output_path: str | Path | None = None):
        LOGGER.report(f'{type(data_node)}: <{data_node}>')

        # ? If not set upon instantiation, set here for easy later access.
        if self.data_node is None:
            self.data_node = data_node

        if isinstance(data_node, orm.StructureData):
            self._dump_structuredata(output_path=output_path)

        elif isinstance(data_node, orm.AbstractCode):
            self._dump_code(output_path=output_path)

        elif isinstance(data_node, orm.SinglefileData):
            pass
            # self._dump_singlefile(output_path=output_path)

        elif isinstance(data_node, orm.FolderData):
            pass
            # self._dump_folderdata(output_path=output_path)

        elif isinstance(data_node, orm.RemoteData):
            pass
            # self._dump_folderdata(output_path=output_path)

        elif isinstance(data_node, orm.JsonableData):
            pass
            # self._dump_jsonable(output_path=output_path)

    def _dump_structuredata(
        self, output_path: Path | None = None, file_name: str | Path | None = None, file_format: str = 'cif'
    ):
        # ? There also exists a CifData file type

        structure_data = self.data_node

        if output_path is None:
            output_path = Path.cwd() / 'structure'

        output_path.mkdir(exist_ok=True, parents=True)

        if file_name is None:
            file_name = f'{structure_data.get_formula()}-{structure_data.pk}.{file_format}'

        # LOGGER.report(output_path, file_name)

        try:
            structure_data.export(path=output_path / file_name, fileformat=file_format, overwrite=True)
        except OSError as exc:
            raise exc

    def _dump_code(self, output_path: Path | None = None, file_name: str | Path | None = None):
        code = self.data_node

        if output_path is None:
            output_path = Path.cwd() / 'code'

        output_path.mkdir(exist_ok=True, parents=True)

        code_data = {}

        # ? Copied over from `cmd_code`
        # ? In some cases, `verdi code export` does not contain the relevant `Computer` attached to it
        for key in code.Model.model_fields.keys():
            value = getattr(code, key).label if key == 'computer' else getattr(code, key)

            if value is not None:
                code_data[key] = str(value)

        if file_name is None:
            file_name = f"{code_data['label']}@{code_data['computer']}.yaml"

        code_file = output_path / file_name

        if not code_file.is_file():
            code_file.write_text(yaml.dump(code_data, sort_keys=False), 'utf-8')

    def _dump_computer(self):
        # `Computer` not derived from orm.Data
        pass

    def _dump_user_info(self): ...
