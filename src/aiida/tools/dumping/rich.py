from aiida.cmdline.commands.cmd_data.cmd_export import data_export

__all__ = ('RichParser', 'DEFAULT_CORE_EXPORT_MAPPING')

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


class RichParser:
    # ? If someone provides options, should the rest be dumped as rich, or not

    def __init__(self, rich_dump_all):
        self.rich_dump_all = rich_dump_all

    def from_cli(self, rich_options):
        # If all, also non-specified data types should be exported, then set the default exporter dict here
        if self.rich_dump_all:
            options_dict = DEFAULT_CORE_EXPORT_MAPPING
        else:
            options_dict = {}

        if rich_options:
            entries = rich_options.split(',')
            # print(f'ENTRIES: {entries}')
            for entry in entries:
                entry_list = entry.split(':')
                # options_dict
                # This is the case if no exporter explicitly provided, then we set it to the default exporter
                if len(entry_list[1]) == 0:
                    entry_list[1] = DEFAULT_CORE_EXPORT_MAPPING[entry_list[0]]['exporter']
                # This is the case if no fileformat explicitly provided, then we set it to the default fileformat
                if len(entry_list[2]) == 0:
                    entry_list[1] = DEFAULT_CORE_EXPORT_MAPPING[entry_list[0]]['export_format']

                if '=' in entry_list[2]:
                    entry_list[2] = entry_list[2].split('=')[1]

                # print(f'ENTRY_LIST: {entry_list}')

                options_dict[entry_list[0]] = {'exporter': entry_list[1], 'export_format': entry_list[2]}

        return options_dict

    @classmethod
    def from_config(cls): ...

    def extend_by_entry_points(self): ...

    # def __init__(self, data_types, export_functions, export_formats):
    #     # TODO: Rather than having three lists, could have a list of tuples of something
    #     # TODO: Or a dictionary with the keys being the entry points, the values tuples of (class, function, format)
    #     self.data_types = data_types
    #     self.export_functions = export_functions
    #     self.export_formats = export_formats

    # returns the different mappings?
