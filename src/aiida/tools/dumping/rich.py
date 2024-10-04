from importlib_metadata import EntryPoint

from aiida.cmdline.commands.cmd_data.cmd_export import data_export

__all__ = ('RichParser', 'DEFAULT_CORE_EXPORT_MAPPING')

DEFAULT_CORE_EXPORT_MAPPING = {
    'core.array': {
        'exporter': data_export,
        'export_format': 'json'
    },
    'core.array.bands': {
        'exporter': data_export,
        'export_format': 'mpl_pdf'
    },
    'core.array.kpoints': {
        'exporter': data_export,
        'export_format': 'json'
    },
    'core.array.projection': {
        'exporter': data_export,
        'export_format': 'json'
    },
    'core.array.trajectory': {
        'exporter': data_export,
        'export_format': 'cif'
    },
    'core.array.xy': {
        'exporter': data_export,
        'export_format': 'json'
    },
    'core.base': {
        'exporter': None,
        'export_format': None
    },
    'core.bool': {
        'exporter': None,
        'export_format': None
    },
    'core.cif': {
        'exporter': data_export,
        'export_format': 'cif'
    },
    'core.code': {
        'exporter': data_export,
        'export_format': 'yaml'
    },
    'core.code.containerized': {
        'exporter': data_export,
        'export_format': 'yaml'
    },
    'core.code.installed': {
        'exporter': data_export,
        'export_format': 'yaml'
    },
    'core.code.portable': {
        'exporter': data_export,
        'export_format': 'yaml'
    },
    'core.dict': {
        'exporter': None,
        'export_format': None
    },
    'core.enum': {
        'exporter': None,
        'export_format': None
    },
    'core.float': {
        'exporter': None,
        'export_format': None
    },
    # TODO: Just use copy-tree
    'core.folder': {
        'exporter': None,
        'export_format': None
    },
    'core.int': {
        'exporter': None,
        'export_format': None
    },
    'core.jsonable': {
        'exporter': data_export,
        'export_format': 'json'  # duh
    },
    'core.list': {
        'exporter': None,
        'export_format': None
    },
    'core.numeric': {
        'exporter': None,
        'export_format': None
    },
    'core.orbital': {
        'exporter': None,
        'export_format': None
    },
    # TODO: Here, try-except existance on remote and if so, dump it here locally
    'core.remote': {
        'exporter': None,
        'export_format': None
    },
    'core.remote.stash': {
        'exporter': None,
        'export_format': None
    },
    'core.remote.stash.folder': {
        'exporter': None,
        'export_format': None
    },
    'core.singlefile': {
        'exporter': None,
        'export_format': None
    },
    'core.str': {
        'exporter': None,
        'export_format': None
    },
    'core.structure': {
        'exporter': data_export,
        'export_format': 'cif'
    },
    'core.upf': {
        'exporter': data_export,
        'export_format': 'upf'
    }
}


# Dynamically generated entry_points via
# entry_points_from_importlib = [
#     EntryPoint(
#         name='quantumespresso.force_constants',
#         value='aiida_quantumespresso.data.force_constants:ForceConstantsData',
#         group='aiida.data',
#     ),
#     EntryPoint(
#         name='quantumespresso.hubbard_structure',
#         value='aiida_quantumespresso.data.hubbard_structure:HubbardStructureData',
#         group='aiida.data',
#     ),
#     EntryPoint(name='core.array', value='aiida.orm.nodes.data.array.array:ArrayData', group='aiida.data'),
#     EntryPoint(name='core.array.bands', value='aiida.orm.nodes.data.array.bands:BandsData', group='aiida.data'),
#     EntryPoint(name='core.array.kpoints', value='aiida.orm.nodes.data.array.kpoints:KpointsData', group='aiida.data'),
#     EntryPoint(
#         name='core.array.projection', value='aiida.orm.nodes.data.array.projection:ProjectionData', group='aiida.data'
#     ),
#     EntryPoint(
#         name='core.array.trajectory', value='aiida.orm.nodes.data.array.trajectory:TrajectoryData', group='aiida.data'
#     ),
#     EntryPoint(name='core.array.xy', value='aiida.orm.nodes.data.array.xy:XyData', group='aiida.data'),
#     EntryPoint(name='core.base', value='aiida.orm.nodes.data:BaseType', group='aiida.data'),
#     EntryPoint(name='core.bool', value='aiida.orm.nodes.data.bool:Bool', group='aiida.data'),
#     EntryPoint(name='core.cif', value='aiida.orm.nodes.data.cif:CifData', group='aiida.data'),
#     EntryPoint(name='core.code', value='aiida.orm.nodes.data.code.legacy:Code', group='aiida.data'),
#     EntryPoint(
#         name='core.code.containerized',
#         value='aiida.orm.nodes.data.code.containerized:ContainerizedCode',
#         group='aiida.data',
#     ),
#     EntryPoint(
#         name='core.code.installed', value='aiida.orm.nodes.data.code.installed:InstalledCode', group='aiida.data'
#     ),
#     EntryPoint(name='core.code.portable', value='aiida.orm.nodes.data.code.portable:PortableCode', group='aiida.data'),
#     EntryPoint(name='core.dict', value='aiida.orm.nodes.data.dict:Dict', group='aiida.data'),
#     EntryPoint(name='core.enum', value='aiida.orm.nodes.data.enum:EnumData', group='aiida.data'),
#     EntryPoint(name='core.float', value='aiida.orm.nodes.data.float:Float', group='aiida.data'),
#     EntryPoint(name='core.folder', value='aiida.orm.nodes.data.folder:FolderData', group='aiida.data'),
#     EntryPoint(name='core.int', value='aiida.orm.nodes.data.int:Int', group='aiida.data'),
#     EntryPoint(name='core.jsonable', value='aiida.orm.nodes.data.jsonable:JsonableData', group='aiida.data'),
#     EntryPoint(name='core.list', value='aiida.orm.nodes.data.list:List', group='aiida.data'),
#     EntryPoint(name='core.numeric', value='aiida.orm.nodes.data.numeric:NumericType', group='aiida.data'),
#     EntryPoint(name='core.orbital', value='aiida.orm.nodes.data.orbital:OrbitalData', group='aiida.data'),
#     EntryPoint(name='core.remote', value='aiida.orm.nodes.data.remote.base:RemoteData', group='aiida.data'),
#     EntryPoint(
#         name='core.remote.stash', value='aiida.orm.nodes.data.remote.stash.base:RemoteStashData', group='aiida.data'
#     ),
#     EntryPoint(
#         name='core.remote.stash.folder',
#         value='aiida.orm.nodes.data.remote.stash.folder:RemoteStashFolderData',
#         group='aiida.data',
#     ),
#     EntryPoint(name='core.singlefile', value='aiida.orm.nodes.data.singlefile:SinglefileData', group='aiida.data'),
#     EntryPoint(name='core.str', value='aiida.orm.nodes.data.str:Str', group='aiida.data'),
#     EntryPoint(name='core.structure', value='aiida.orm.nodes.data.structure:StructureData', group='aiida.data'),
#     EntryPoint(name='core.upf', value='aiida.orm.nodes.data.upf:UpfData', group='aiida.data'),
#     EntryPoint(name='pseudo', value='aiida_pseudo.data.pseudo.pseudo:PseudoPotentialData', group='aiida.data'),
#     EntryPoint(name='pseudo.jthxml', value='aiida_pseudo.data.pseudo.jthxml:JthXmlData', group='aiida.data'),
#     EntryPoint(name='pseudo.psf', value='aiida_pseudo.data.pseudo.psf:PsfData', group='aiida.data'),
#     EntryPoint(name='pseudo.psml', value='aiida_pseudo.data.pseudo.psml:PsmlData', group='aiida.data'),
#     EntryPoint(name='pseudo.psp8', value='aiida_pseudo.data.pseudo.psp8:Psp8Data', group='aiida.data'),
#     EntryPoint(name='pseudo.upf', value='aiida_pseudo.data.pseudo.upf:UpfData', group='aiida.data'),
#     EntryPoint(name='pseudo.vps', value='aiida_pseudo.data.pseudo.vps:VpsData', group='aiida.data'),
# ]


class RichParser:
    # ? If someone provides options, should the rest be dumped as rich, or not

    @classmethod
    def from_cli(cls, rich_options):
        options_dict = RichParser.parse_rich_options(rich_options)
        return options_dict

    # options_dict = self.
    @staticmethod
    def parse_rich_options(rich_options):
        options_dict = {}
        if rich_options:
            components = rich_options.split(':')
            type_value = None
            export_value = None
            format_value = None

            for component in components:
                if '=' in component:
                    key, value = component.split('=', 1)
                    if key == 'type':
                        type_value = value
                    elif key == 'export':
                        export_value = value
                    elif key == 'format':
                        format_value = value
                else:
                    if type_value is None:
                        type_value = component
                    elif export_value is None:
                        # TODO: this is only for core data types
                        export_value = DEFAULT_CORE_EXPORT_MAPPING[type_value]
                    elif format_value is None:
                        # format_value = component
                        format_value = DEFAULT_CORE_EXPORT_MAPPING[type_value]

            if type_value:
                options_dict[type_value] = (export_value, format_value)

        return options_dict

    @classmethod
    def from_config(cls): ...

    def extend_by_entry_points(self): ...

    def __init__(self, data_types, export_functions, export_formats):
        # TODO: Rather than having three lists, could have a list of tuples of something
        # TODO: Or a dictionary with the keys being the entry points, the values tuples of (class, function, format)
        self.data_types = data_types
        self.export_functions = export_functions
        self.export_formats = export_formats

    # returns the different mappings?
