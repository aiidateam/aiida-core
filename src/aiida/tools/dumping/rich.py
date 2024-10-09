from aiida.cmdline.commands.cmd_data.cmd_export import data_export
from rich.pretty import pprint

__all__ = ('rich_from_cli', 'rich_from_config', 'DEFAULT_CORE_EXPORT_MAPPING')

DEFAULT_CORE_EXPORT_MAPPING = {
    'core.array': {'exporter': data_export, 'export_format': 'json'},
    'core.array.bands': {'exporter': data_export, 'export_format': 'mpl_pdf'},
    'core.array.kpoints': {'exporter': data_export, 'export_format': 'json'},
    'core.array.projection': {'exporter': data_export, 'export_format': 'json'},
    'core.array.trajectory': {'exporter': data_export, 'export_format': 'cif'},
    'core.array.xy': {'exporter': data_export, 'export_format': 'json'},
    'core.base': {'exporter': None, 'export_format': None},
    'core.bool': {'exporter': None, 'export_format': None},
    'core.cif': {'exporter': data_export, 'export_format': 'cif'},
    'core.code': {'exporter': data_export, 'export_format': 'yaml'},
    'core.code.containerized': {'exporter': data_export, 'export_format': 'yaml'},
    'core.code.installed': {'exporter': data_export, 'export_format': 'yaml'},
    'core.code.portable': {'exporter': data_export, 'export_format': 'yaml'},
    'core.dict': {'exporter': None, 'export_format': None},
    'core.enum': {'exporter': None, 'export_format': None},
    'core.float': {'exporter': None, 'export_format': None},
    # TODO: Just use copy-tree
    'core.folder': {'exporter': None, 'export_format': None},
    'core.int': {'exporter': None, 'export_format': None},
    'core.jsonable': {
        'exporter': data_export,
        'export_format': 'json',  # duh
    },
    'core.list': {'exporter': None, 'export_format': None},
    'core.numeric': {'exporter': None, 'export_format': None},
    'core.orbital': {'exporter': None, 'export_format': None},
    # TODO: Here, try-except existance on remote and if so, dump it here locally
    'core.remote': {'exporter': None, 'export_format': None},
    'core.remote.stash': {'exporter': None, 'export_format': None},
    'core.remote.stash.folder': {'exporter': None, 'export_format': None},
    'core.singlefile': {'exporter': None, 'export_format': None},
    'core.str': {'exporter': None, 'export_format': None},
    'core.structure': {'exporter': data_export, 'export_format': 'cif'},
    'core.upf': {'exporter': data_export, 'export_format': 'upf'},
}


def rich_from_cli(rich_spec, rich_dump_all):
    # If all, also non-specified data types should be exported, then set the default exporter dict here
    if rich_dump_all:
        options_dict = DEFAULT_CORE_EXPORT_MAPPING
    else:
        options_dict = {}

    if rich_spec:
        entries = rich_spec.split(',')
        # print(f'ENTRIES: {entries}')
        for entry in entries:
            entry_list = entry.split(':')
            entry_point = entry_list[0]

            # This is the case if no exporter explicitly provided, then we set it to the default exporter
            exporter = entry_list[1] or DEFAULT_CORE_EXPORT_MAPPING[entry_point]['exporter']

            # This is the case if no fileformat explicitly provided, then we set it to the default fileformat
            export_format = entry_list[2] or DEFAULT_CORE_EXPORT_MAPPING[entry_point]['export_format']

            # If it is provided, then the assignment is done with an equal sign and we resolve it
            if '=' in export_format:
                export_format = export_format.split('=')[1]

            # print(f'ENTRY_LIST: {entry_list}')

            options_dict[entry_point] = {'exporter': exporter, 'export_format': export_format}

    return options_dict


def rich_from_config(rich_spec, rich_dump_all):

    if rich_dump_all:
        options_dict = DEFAULT_CORE_EXPORT_MAPPING
    else:
        options_dict = {}

    for entry_point, spec in rich_spec.items():
        export_format = spec.get('format') or DEFAULT_CORE_EXPORT_MAPPING[entry_point]['export_format']
        exporter = spec.get('exporter') or DEFAULT_CORE_EXPORT_MAPPING[entry_point]['exporter']

        options_dict[entry_point] = {'exporter': exporter, 'export_format': export_format}

    return options_dict
