from pathlib import Path
import yaml


class DumpConfigParser:

    @staticmethod
    def parse_config_file(config_file: str | Path | None) -> dict:

        if isinstance(config_file, (str, Path)):
            with open(config_file, 'r') as file:
                config = yaml.safe_load(file)
        else:
            config = yaml.safe_load(config_file)

        general_kwargs = {
            'path': Path(config.get('path', Path.cwd())),
            'overwrite': config.get('overwrite', False),
            'dry_run': config.get('dry_run', False),
        }

        processdumper_kwargs = {
            "include_inputs": config.get('include_inputs', True),
            "include_outputs": config.get('include_outputs', True),
            "include_attributes": config.get('include_attributes', True),
            "include_extras": config.get('include_extras', False),
            "flat": config.get('flat', False),
            "calculations_hidden": config.get('calculations_hidden', True),
        }

        datadumper_kwargs = {
            "also_raw": config.get('also_raw', False),
            "also_rich": config.get('also_rich', True),
            "data_hidden": config.get('data_hidden', True),
        }

        collection_kwargs = {
            "should_dump_processes": config.get('dump_processes', True),
            "should_dump_data": config.get('dump_data', True),
            "only_top_level_workflows": config.get('only_top_level_workflows', True),
        }

        rich_kwargs = {
            "rich_dump_all": config.get('rich_dump_all', True),
        }

        rich_options = config.get('rich_options', None)

        return {
            'general_kwargs': general_kwargs,
            'processdumper_kwargs': processdumper_kwargs,
            'datadumper_kwargs': datadumper_kwargs,
            'collection_kwargs': collection_kwargs,
            'rich_kwargs': rich_kwargs,
            'rich_options': rich_options,
        }
