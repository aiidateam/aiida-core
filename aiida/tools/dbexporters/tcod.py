# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

from aiida.orm import DataFactory

aiida_executable_name = '_aiidasubmit.sh'

tcod_loops = {
    '_tcod_file': [
        '_tcod_file_id',
        '_tcod_file_name',
        '_tcod_file_md5sum',
        '_tcod_file_sha1sum',
        '_tcod_file_URI',
        '_tcod_file_role',
        '_tcod_file_contents',
        '_tcod_file_content_encoding',
    ],
    '_tcod_computation': [
        '_tcod_computation_step',
        '_tcod_computation_command',
        '_tcod_computation_uuid',
        '_tcod_computation_environment',
        '_tcod_computation_stdout',
        '_tcod_computation_stderr',
    ],
    '_tcod_content_encoding': [
        '_tcod_content_encoding_id',
        '_tcod_content_encoding_layer_id',
        '_tcod_content_encoding_layer_type',
    ],
    '_audit_conform': [
        '_audit_conform_dict_location',
        '_audit_conform_dict_name',
        '_audit_conform_dict_version',
    ]
}

def cif_encode_contents(content,gzip=False,gzip_threshold=1024):
    """
    Encodes data for usage in CIF text field in a ``best possible`` way:
    binary data is encoded using Base64 encoding; text with non-ASCII
    symbols, too long lines or lines starting with semicolons (';')
    is encoded using Quoted-printable encoding.

    :param content: the content to be encoded
    :return content: encoded content
    :return encoding: a string specifying used encoding (None, 'base64',
        'ncr', 'quoted-printable')
    """
    import re
    method = None
    if len(content) == 0:
        # content is empty
        method = None
    elif gzip and len(content) >= gzip_threshold:
        # content is larger than some arbitrary value and should be gzipped
        method = 'gzip+base64'
    elif float(len(re.findall('[^\x09\x0A\x0D\x20-\x7E]',content)))/len(content) > 0.25:
        # contents are assumed to be binary
        method = 'base64'
    elif re.search('.{2048}.',content) is not None:
        # lines are too long
        method = 'quoted-printable'
    elif len(re.findall('[^\x09\x0A\x0D\x20-\x7E]',content)) > 0:
        # contents have non-ASCII symbols
        method = 'quoted-printable'
    elif re.search('^;',content) is not None or re.search('\n;',content) is not None:
        # content has lines starting with semicolon (';')
        method = 'quoted-printable'
    elif re.search('\t',content) is not None:
        # content has TAB symbols, which may be lost during the
        # parsing of TCOD CIF file
        method = 'quoted-printable'
    elif content == '.' or content == '?':
        method = 'quoted-printable'
    else:
        method = None

    if method == 'base64':
        from aiida.orm.data.cif import encode_textfield_base64
        content = encode_textfield_base64(content)
    elif method == 'quoted-printable':
        from aiida.orm.data.cif import encode_textfield_quoted_printable
        content = encode_textfield_quoted_printable(content)
    elif method == 'ncr':
        from aiida.orm.data.cif import encode_textfield_ncr
        content = encode_textfield_ncr(content)
    elif method == 'gzip+base64':
        from aiida.orm.data.cif import encode_textfield_gzip_base64
        content = encode_textfield_gzip_base64(content)

    return content,method

def cif_decode_contents(content,method):
    """
    Decodes contents of encoded CIF text field.

    :param content: the content to be decoded
    :param method: method, which was used for encoding the contents
    :return: decoded content
    :raises ValueError: if the encoding method is unknown
    """
    if method == 'base64':
        from aiida.orm.data.cif import decode_textfield_base64
        content = decode_textfield_base64(content)
    elif method == 'quoted-printable':
        from aiida.orm.data.cif import decode_textfield_quoted_printable
        content = decode_textfield_quoted_printable(content)
    elif method == 'ncr':
        from aiida.orm.data.cif import decode_textfield_ncr
        content = decode_textfield_ncr(content)
    elif method == 'gzip+base64':
        from aiida.orm.data.cif import decode_textfield_gzip_base64
        content = decode_textfield_gzip_base64(content)
    elif method is not None:
        raise ValueError("Unknown content encoding: '{}'".format(method))

    return content

def _get_calculation(node):
    """
    Gets the parent (immediate) calculation, attached as the input of
    the node.

    :param node: an instance of subclass of :py:class:`aiida.orm.node.Node`
    :return: an instance of subclass of
        :py:class:`aiida.orm.calculation.Calculation`
    :raises ValueError: if the node has more than one calculation attached.
    """
    from aiida.orm.calculation import Calculation
    if len(node.get_inputs(type=Calculation)) == 1:
        return node.get_inputs(type=Calculation)[0]
    elif len(node.get_inputs(type=Calculation)) == 0:
        return None
    else:
        raise ValueError("Node {} seems to have more than one "
                         "parent (immediate) calculation -- exporter "
                         "does not know which one of them produced the "
                         "node".format(node))

def _assert_same_parents(a,b):
    """
    Checks whether two supplied nodes have the same immediate parent.
    Can be used to check whether two data nodes originate from the same
    calculation.

    :param a: an instance of subclass of :py:class:`aiida.orm.node.Node`
    :param b: an instance of subclass of :py:class:`aiida.orm.node.Node`

    :raises ValueError: if the condition is not met.
    """
    if a is None or b is None:
        return
    if _get_calculation(a) is None or _get_calculation(b) is None:
        raise ValueError("Either the exported node or parameters does "
                         "not originate from a calculation -- this is "
                         "not allowed, as the proper relation between "
                         "these two objects can not be traced")
    if _get_calculation(a).pk != _get_calculation(b).pk:
        raise ValueError("Exported node and parameters must "
                         "originate from the same calculation")

def _inline_to_standalone_script(calc):
    """
    Create executable bash script for execution of inline script.
    """
    input_dict = calc.get_inputs_dict()
    args = ["{}=Node.get_subclass_from_uuid('{}')".format(x,input_dict[x].uuid)
            for x in input_dict.keys()]
    args_string = "\n    ,".join(sorted(args))
    return """#!/usr/bin/env runaiida
{}

for key,value in {}(
    {}
    ).iteritems():
    value.store()
END
""".format(calc.get_attr('source_file').encode('utf-8'),
           calc.get_attr('function_name','f'),
           args_string)

def _collect_calculation_data(calc):
    """
    Recursively collects calculations from the tree, starting at given
    calculation.
    """
    from aiida.orm.data import Data
    from aiida.orm.calculation import Calculation
    from aiida.orm.calculation.job import JobCalculation
    from aiida.orm.calculation.inline import InlineCalculation
    import os
    calcs_now = []
    for d in calc.get_inputs(type=Data):
        for c in d.get_inputs(type=Calculation):
            calcs = _collect_calculation_data(c)
            calcs_now.extend(calcs)

    files_in = []
    files_out = []
    this_calc = {
        'uuid' : calc.uuid,
        'files': [],
    }

    if isinstance(calc,JobCalculation):
        retrieved_abspath = calc.get_retrieved_node().get_abs_path()
        files_in  = _collect_files(calc._raw_input_folder.abspath)
        files_out = _collect_files(os.path.join(retrieved_abspath,'path'))
        this_calc['env'] = calc.get_environment_variables()
        this_calc['stdout'] = calc.get_scheduler_output()
        this_calc['stderr'] = calc.get_scheduler_error()
    else:
        # Calculation is InlineCalculation
        import hashlib
        script = _inline_to_standalone_script(calc)
        files_in.append({
            'name'    : aiida_executable_name,
            'contents': script,
            'md5'     : hashlib.md5(script).hexdigest(),
            'sha1'    : hashlib.sha1(script).hexdigest(),
            'type'    : 'file',
            })

    for f in files_in:
        if os.path.basename(f['name']) == aiida_executable_name:
            f['role'] = 'script'
        else:
            f['role'] = 'input'
        this_calc['files'].append(f)

    for f in files_out:
        if os.path.basename(f['name']) != calc._SCHED_OUTPUT_FILE and \
           os.path.basename(f['name']) != calc._SCHED_ERROR_FILE:
            f['role'] = 'output'
            this_calc['files'].append(f)

    calcs_now.append(this_calc)
    return calcs_now

def _collect_files(base,path=''):
    """
    Recursively collects files from the tree, starting at a given path.
    """
    from aiida.common.folders import Folder
    from aiida.common.utils import md5_file,sha1_file
    import os
    if os.path.isdir(os.path.join(base,path)):
        folder = Folder(os.path.join(base,path))
        files_now = []
        if path != '':
            if not path.endswith(os.sep):
                path = "{}{}".format(path,os.sep)
            if path != '':
                files_now.append({
                    'name': path,
                    'type': 'folder',
                })
        for f in folder.get_content_list():
            files = _collect_files(base,path=os.path.join(path,f))
            files_now.extend(files)
        return files_now
    else:
        with open(os.path.join(base,path)) as f:
            return [{
                'name': path,
                'contents': f.read(),
                'md5': md5_file(os.path.join(base,path)),
                'sha1': sha1_file(os.path.join(base,path)),
                'type': 'file',
                }]

def extend_with_cmdline_parameters(parser,expclass="Data"):
    """
    Provides descriptions of command line options, that are used to control
    the process of exporting data to TCOD CIF files.

    :param parser: an argparse.Parser instance
    :param expclass: name of the exported class to be shown in help string
        for the command line options
    """
    import argparse
    parser.add_argument('--reduce-symmetry', action='store_true',
                        dest='reduce_symmetry',
                        help='Perform symmetry reduction.')
    parser.add_argument('--no-reduce-symmetry',
                        '--dont-reduce-symmetry',
                        action='store_false',
                        dest='reduce_symmetry',
                        help="Do not perform symmetry reduction. "
                             "Default option.")
    parser.add_argument('--parameter-data', type=int, default=None,
                        help="ID of the ParameterData to be exported "
                             "alongside the {} instance. "
                             "By default, if {} originates from "
                             "a calculation with single ParameterData "
                             "in the output, aforementioned "
                             "ParameterData is picked automatically. "
                             "Instead, the option is used in the case "
                             "the calculation produces more than a "
                             "single instance of "
                             "ParameterData.".format(expclass,expclass))
    parser.add_argument('--dump-aiida-database', action='store_true',
                        default=True,
                        dest='dump_aiida_database',
                        help="Export AiiDA database to the CIF file. " +
                             "Default option.")
    parser.add_argument('--no-dump-aiida-database',
                        '--dont-dump-aiida-database',
                        action='store_false',
                        dest='dump_aiida_database',
                        help="Do not export AiiDA database to the CIF " +
                             "file.")
    parser.add_argument('--exclude-external-contents', action='store_true',
                        dest='exclude_external_contents',
                        help="Do not save contents for external " +
                             "resources if URIs are provided. " +
                             "Default option.")
    parser.add_argument('--no-exclude-external-contents',
                        '--dont-exclude-external-contents',
                        action='store_false',
                        dest='exclude_external_contents',
                        help="Save contents for external resources " +
                             "even if URIs are provided.")
    parser.add_argument('--gzip', action='store_true', dest='gzip',
                        help="Gzip large files.")
    parser.add_argument('--no-gzip', '--dont-gzip', action='store_false',
                        dest='gzip',
                        help="Do not gzip any files. Default option.")
    parser.add_argument('--gzip-threshold', type=int, default=1024,
                        help="Specify the minimum size of exported " +
                             "file which should be gzipped. " +
                             "Default 1024.")

def _collect_tags(node,calc,parameters=None,
                  dump_aiida_database=True,
                  exclude_external_contents=False,
                  gzip=False,
                  gzip_threshold=1024):
    """
    Retrieve metadata from attached calculation and pseudopotentials
    and prepare it to be saved in TCOD CIF.
    """
    from aiida.cmdline.commands.exportfile import serialize_dict
    import os,json
    tags = dict()

    tags['_audit_creation_method']   = "AiiDA version {}".format(__version__)
    tags['_audit_conform_dict_name'] = [ "cif_tcod.dic", "cif_dft.dic" ]
    tags['_audit_conform_dict_version'] = [ "0.004", "0.004" ]
    tags['_audit_conform_dict_location'] = [
        "http://www.crystallography.net/tcod/cif/dictionaries/cif_tcod.dic",
        "http://www.crystallography.net/tcod/cif/dictionaries/cif_dft.dic"
    ]

    # Collecting metadata from input files:

    calc_data = []
    if calc is not None:
        calc_data = _collect_calculation_data(calc)

    for tag in tcod_loops['_tcod_computation'] + tcod_loops['_tcod_file']:
        tags[tag] = []

    export_files = []

    sn = 0
    fn = 0
    for step in calc_data:
        tags['_tcod_computation_step'].append(sn)
        tags['_tcod_computation_command'].append(
            'cd {}; ./{}'.format(sn,aiida_executable_name))
        tags['_tcod_computation_uuid'].append(step['uuid'])
        if 'env' in step:
            tags['_tcod_computation_environment'].append(
                "\n".join(["%s=%s" % (key,step['env'][key]) for key in step['env']]))
        else:
            tags['_tcod_computation_environment'].append('')
        if 'stdout' in step and \
           cif_encode_contents(step['stdout'])[1] is not None:
            raise ValueError("Standard output of computation step {} "
                             "can not be stored in a CIF file: "
                             "encoding is required, but not currently "
                             "supported".format(sn))
        if 'stderr' in step and \
           cif_encode_contents(step['stderr'])[1] is not None:
            raise ValueError("Standard error of computation step {} "
                             "can not be stored in a CIF file: "
                             "encoding is required, but not currently "
                             "supported".format(sn))
        if 'stdout' in step:
            tags['_tcod_computation_stdout'].append(step['stdout'])
        else:
            tags['_tcod_computation_stdout'].append('')
        if 'stderr' in step:
            tags['_tcod_computation_stderr'].append(step['stderr'])
        else:
            tags['_tcod_computation_stderr'].append('')

        export_files.append( {'name': "{}{}".format(sn,os.sep),
                              'type': 'folder'} )

        for f in step['files']:
            f['name'] = os.path.join(str(sn),f['name'])
        export_files.extend( step['files'] )

        sn = sn + 1

    # Creating importable AiiDA database dump in CIF tags

    if dump_aiida_database:
        import json
        from aiida.common.folders import SandboxFolder
        from aiida.cmdline.commands.exportfile import export_tree
        from aiida.orm.data.cif import encode_textfield_base64

        with SandboxFolder() as folder:
            export_tree( [node.dbnode], folder=folder, silent=True)
            files = _collect_files(folder.abspath)
            with open(folder.get_abs_path('data.json')) as f:
                data = json.loads(f.read())
            md5_to_url = {}
            if exclude_external_contents:
                for pk in data['node_attributes']:
                    n = data['node_attributes'][pk]
                    if 'md5' in n.keys() and 'url' in n.keys():
                        md5_to_url[n['md5']] = n['url']

            for f in files:
                f['name'] = os.path.join('aiida',f['name'])
                if f['type'] == 'file' and f['md5'] in md5_to_url.keys():
                    f['uri'] = md5_to_url[f['md5']]

            export_files.extend( files )

    # Describing seen files in _tcod_file_* loop

    encodings = list()

    fn = 0
    for f in export_files:
        # ID and name
        tags['_tcod_file_id'].append(fn)
        tags['_tcod_file_name'].append(f['name'])

        # Checksums
        md5sum = None
        sha1sum = None
        if f['type'] == 'file':
            md5sum = f['md5']
            sha1sum = f['sha1']
        else:
            md5sum = '.'
            sha1sum = '.'
        tags['_tcod_file_md5sum'].append(md5sum)
        tags['_tcod_file_sha1sum'].append(sha1sum)

        # Content, encoding and URI
        contents = '?'
        encoding = None
        if 'uri' in f.keys():
            contents = '.'
            tags['_tcod_file_URI'].append(f['uri'])
        else:
            tags['_tcod_file_URI'].append('?')
            if f['type'] == 'file':
                contents,encoding = \
                    cif_encode_contents(f['contents'],
                                        gzip=gzip,
                                        gzip_threshold=gzip_threshold)
            else:
                contents = '.'

        if encoding is None:
            encoding = '.'
        elif encoding not in encodings:
            encodings.append(encoding)
        tags['_tcod_file_contents'].append(contents)
        tags['_tcod_file_content_encoding'].append(encoding)

        # Role
        role = '?'
        if 'role' in f.keys():
            role = f['role']
        tags['_tcod_file_role'].append(role)

        fn = fn + 1

    # Describing the encodings

    if encodings:
        for tag in tcod_loops['_tcod_content_encoding']:
            tags[tag] = []
    for encoding in encodings:
        layers = encoding.split('+')
        for i in range(0,len(layers)):
            tags['_tcod_content_encoding_id'].append(encoding)
            tags['_tcod_content_encoding_layer_id'].append(i+1)
            tags['_tcod_content_encoding_layer_type'].append(layers[i])

    # Collecting code-specific data

    from aiida.common.pluginloader import BaseFactory, existing_plugins
    from aiida.tools.dbexporters.tcod_plugins import BaseTcodtranslator

    plugin_path = "aiida.tools.dbexporters.tcod_plugins"
    plugins = list()

    if calc is not None and parameters is not None:
        for plugin in existing_plugins(BaseTcodtranslator,plugin_path):
            cls = BaseFactory(plugin,BaseTcodtranslator,plugin_path)
            if calc._plugin_type_string.endswith(cls._plugin_type_string + '.'):
                plugins.append(cls)

    from aiida.common.exceptions import MultipleObjectsError

    if len(plugins) > 1:
        raise MultipleObjectsError("more than one plugin found for "
                                   "{}".calc._plugin_type_string)

    if len(plugins) == 1:
        plugin = plugins[0]
        translated_tags = translate_calculation_specific_values(parameters,
                                                                plugin)
        tags.update(translated_tags)

    return tags

def trajectory_to_structure_inline(node,parameters):
    """
    Convert :py:class:`aiida.orm.data.array.trajectory.TrajectoryData`
    instance to :py:class:`aiida.orm.data.structure.StructureData`.

    :param node: a
        :py:class:`aiida.orm.data.array.trajectory.TrajectoryData` instance
    :param parameters: a
        :py:class:`aiida.orm.data.parameter.ParameterData` instance, having
        a single field ``step`` defined, which indicates which trajectory
        step has to be extracted and converted.
    :return: dict with :py:class:`aiida.orm.data.structure.StructureData`.

    :note: can be used as inline calculation.
    """
    step = parameters.get_attr('step')
    structure = node.step_to_structure(step)
    return {'structure': structure}

def structure_to_cif_inline(node):
    """
    Convert :py:class:`aiida.orm.data.structure.StructureData` instance to
    :py:class:`aiida.orm.data.cif.CifData`.

    :param node: a :py:class:`aiida.orm.data.structure.StructureData`
        instance.
    :return: dict with :py:class:`aiida.orm.data.cif.CifData`

    :note: can be used as inline calculation.
    """
    CifData = DataFactory('cif')
    cif = CifData(ase=node.get_ase())
    formula = node.get_formula(mode='hill',separator=' ')
    for i in cif.values.keys():
        cif.values[i]['_symmetry_space_group_name_H-M']  = 'P 1'
        cif.values[i]['_symmetry_space_group_name_Hall'] = 'P 1'
        cif.values[i]['_symmetry_Int_Tables_number']     = 1
        cif.values[i]['_cell_formula_units_Z']           = 1
        cif.values[i]['_chemical_formula_sum']           = formula
    return {'cif': cif}

def convert_and_refine_inline(node):
    """
    Refine (reduce) the cell of :py:class:`aiida.orm.data.cif.CifData`,
    find and remove symmetrically equivalent atoms.

    :param node: a :py:class:`aiida.orm.data.cif.CifData` instance.
    :return: dict with :py:class:`aiida.orm.data.cif.CifData`

    :note: can be used as inline calculation.
    """
    from aiida.orm.data.structure import ase_refine_cell
    CifData = DataFactory('cif')
    aseatoms,symmetry = ase_refine_cell(node.get_ase())
    cif = CifData(ase=aseatoms)
    for i in cif.values.keys():
        cif.values[i]['_symmetry_space_group_name_H-M']  = symmetry['hm']
        cif.values[i]['_symmetry_space_group_name_Hall'] = symmetry['hall']
        cif.values[i]['_symmetry_Int_Tables_number']     = symmetry['tables']
        ref_datablock = node.values.first_block()
        if i in node.values.keys():
            index = node.values.keys().index(i)
            ref_datablock = node.values.items()[index][1]
        if '_chemical_formula_sum' in ref_datablock.keys():
            cif.values[i]['_chemical_formula_sum'] = \
                ref_datablock['_chemical_formula_sum']
    return {'cif': cif}

def add_metadata_inline(what,node=None,parameters=None,args=None):
    """
    Add metadata of original exported node to the produced TCOD CIF.

    :param what: an original exported node.
    :param node: a :py:class:`aiida.orm.data.cif.CifData` instance.
    :param parameters: a :py:class:`aiida.orm.data.parameter.ParameterData`
        instance, produced by the same calculation as the original exported
        node.
    :param args: a :py:class:`aiida.orm.data.parameter.ParameterData`
        instance, containing parameters for the control of metadata
        collection and inclusion in the produced
        :py:class:`aiida.orm.data.cif.CifData`.
    :return: dict with :py:class:`aiida.orm.data.cif.CifData`
    :raises ValueError: if tags present in
        ``args.get_dict()['additional_tags']`` are not valid CIF tags.

    :note: can be used as inline calculation.
    """
    from aiida.orm.data.cif import pycifrw_from_cif
    CifData = DataFactory('cif')

    if not node:
        node = what

    calc = _get_calculation(what)

    datablocks = []
    loops = {}
    dataname = node.values.keys()[0]
    datablock = dict()
    for tag in node.values[dataname].keys():
        datablock[tag] = node.values[dataname][tag]
    datablocks.append(datablock)
    for loop in node.values[dataname].loops:
        loops[loop.keys()[0]] = loop.keys()

    # Unpacking the kwargs from ParameterData
    kwargs = {}
    additional_tags = {}
    if args:
        kwargs = args.get_dict()
        additional_tags = kwargs.pop('additional_tags',{})

    tags = _collect_tags(what,calc,parameters=parameters,**kwargs)
    loops.update(tcod_loops)

    for datablock in datablocks:
        for k,v in dict(tags.items() + additional_tags.items()).iteritems():
            if not k.startswith('_'):
                raise ValueError("Tag '{}' does not seem to start with "
                                 "an underscode ('_'): all CIF tags must "
                                 "start with underscores".format(k))
            if not isinstance(v,list):
                v = [v]
            datablock[k] = v

    values = pycifrw_from_cif(datablocks,loops)
    cif = CifData(values=values)

    return {'cif': cif}

def export_cif(what,**kwargs):
    cif = export_cifnode(what,**kwargs)
    return cif._exportstring('cif')

def export_values(what,**kwargs):
    cif = export_cifnode(what,**kwargs)
    return cif.values

def export_cifnode(what,parameters=None,trajectory_index=None,store=False,
                   reduce_symmetry=False,**kwargs):
    """
    The main exporter function. Exports given coordinate-containing \*Data
    node to :py:class:`aiida.orm.data.cif.CifData` node, ready to be
    exported to TCOD.

    Currently supported data types:

    * :py:class:`aiida.orm.data.cif.CifData`
    * :py:class:`aiida.orm.data.structure.StructureData` (converted to
      :py:class:`aiida.orm.data.cif.CifData` beforehand)
    * :py:class:`aiida.orm.data.array.trajectory.TrajectoryData`
      (converted to :py:class:`aiida.orm.data.cif.CifData` via
      :py:class:`aiida.orm.data.structure.StructureData`)

    :param what: data node to be exported.
    :param parameters: a :py:class:`aiida.orm.data.parameter.ParameterData`
        instance, produced by the same calculation as the original exported
        node.
    :param trajectory_index: a step to be converted and exported in case a
        :py:class:`aiida.orm.data.array.trajectory.TrajectoryData` is
        exported.
    :param store: boolean indicating whether to store intermediate nodes or
        not. Default False.
    :param dump_aiida_database: boolean indicating whether to include the
        dump of AiiDA database (containing only transitive closure of the
        exported node). Default True.
    :param exclude_external_contents: boolean indicating whether to exclude
        nodes from AiiDA database dump, that are taken from external
        repositores and have a URL link allowing to refetch their contents.
        Default False.
    :param gzip: boolean indicating whether to Gzip large CIF text fields.
        Default False.
    :param gzip_threshold: integer indicating the maximum size (in bytes) of
        uncompressed CIF text fields when the **gzip** option is in action.
        Default 1024.
    :return: a :py:class:`aiida.orm.data.cif.CifData` node.
    """
    from aiida.orm.calculation.inline import make_inline
    CifData        = DataFactory('cif')
    StructureData  = DataFactory('structure')
    TrajectoryData = DataFactory('array.trajectory')
    ParameterData  = DataFactory('parameter')

    calc = _get_calculation(what)

    if parameters is not None:
        if not isinstance( parameters, ParameterData ):
            raise ValueError("Supplied parameters are not an "
                             "instance of ParameterData")
    elif calc is not None:
        params = calc.get_outputs(type=ParameterData)
        if len(params) == 1:
            parameters = params[0]
        elif len(params) > 0:
            raise ValueError("Calculation {} has more than "
                             "one ParameterData output, please "
                             "specify which one to use with "
                             "an option parameters='' when "
                             "calling export_cif()".format(calc))

    if parameters is not None:
        _assert_same_parents(what,parameters)

    node = what

    # Convert node to CifData (if required)

    if isinstance(node,TrajectoryData):
        conv = None
        param = ParameterData(dict={'step': trajectory_index})
        if store:
            _,conv = make_inline(trajectory_to_structure_inline)(node=node,
                                                                 param=param)
        else:
            conv = trajectory_to_structure_inline(node,param)
        node = conv['structure']

    if isinstance(node,StructureData):
        conv = None
        if store:
            _,conv = make_inline(structure_to_cif_inline)(node=node)
        else:
            conv = structure_to_cif_inline(node)
        node = conv['cif']

    if not isinstance(node,CifData):
        raise NotImplementedError("Exporter does not know how to "
                                  "export {}".format(type(node)))

    # Reduction of the symmetry

    if reduce_symmetry:
        conv = None
        if store:
            _,conv = make_inline(convert_and_refine_inline)(node=node)
        else:
            conv = convert_and_refine_inline(node)
        node = conv['cif']

    # Addition of the metadata

    conv = None
    args = ParameterData(dict=kwargs)
    if store:
        function_args = { 'what': what, 'args': args }
        if node != what:
            function_args['node'] = node
        if parameters is not None:
            function_args['parameters'] = parameters
        _,conv = make_inline(add_metadata_inline)(**function_args)
    else:
        conv = add_metadata_inline(what,node,parameters,args)
    node = conv['cif']

    return node

def deposit(what,type,author_name=None,author_email=None,url=None,
            title=None,username=None,password=None,user_email=None,
            **kwargs):
    """
    Launches a JobCalculation to deposit data node to \*COD-type database.
    """
    if not what:
        raise ValueError("Node to be deposited is not supplied")
    if not type:
        raise ValueError("Deposition type is not supplied. Should be "
                         "one of the following: 'published', "
                         "'prepublication' or 'personal'")
    if not username:
        raise ValueError("Depositor username is not supplied")
    if not password:
        raise ValueError("Depositor password is not supplied")
    if not user_email:
        raise ValueError("Depositor email is not supplied")

    if type == 'published':
        pass
    elif type in ['prepublication','personal']:
        if not author_name:
            raise ValueError("Author name is not supplied")
        if not author_email:
            raise ValueError("Author email is not supplied")
        if not title:
            raise ValueError("Publication title is not supplied")
    else:
        raise ValueError("Unknown deposition type '{}' -- should be "
                         "one of the following: 'published', "
                         "'prepublication' or 'personal'".format(type))

    kwargs['additional_tags'] = {}
    if title:
        kwargs['additional_tags']['_publ_section_title'] = title
    if author_name:
        kwargs['additional_tags']['_publ_author_name'] = author_name

    cif = export_cifnode(what,store=True,**kwargs)

    from aiida.orm.code import Code
    from aiida.orm.data.parameter import ParameterData
    from aiida.common.exceptions import NotExistent

    code = Code.get_from_string('cif_cod_deposit') #TODO allow to be changed
    calc = code.new_calc()
    calc.set_resources({'num_machines': 1, 'num_mpiprocs_per_machine': 1})

    parameters = {
        'deposition-type': type,
        'username'       : username,
        'password'       : password,
        'user_email'     : user_email,
    }
    if author_name:
        parameters['author_name'] = author_name
    if author_email:
        parameters['author_email'] = author_email
    if url:
        parameters['url'] = url
    pd = ParameterData(dict=parameters)

    calc.use_cif(cif)
    calc.use_parameters(pd)

    calc.store_all()
    calc.submit()

    return calc

def deposition_cmdline_parameters(parser,expclass="Data"):
    """
    Provides descriptions of command line options, that are used to control
    the process of deposition to TCOD.

    :param parser: an argparse.Parser instance
    :param expclass: name of the exported class to be shown in help string
        for the command line options
    """
    import argparse
    parser.add_argument('--type', '--deposition-type', type=str,
                        choices=['published','prepublication','personal'],
                        help="Type of the deposition.")
    parser.add_argument('-u', '--username', type=str, default=None,
                        dest='username',
                        help="Depositor's username.")
    parser.add_argument('-p', '--password', type=str, default=None,
                        dest='password',
                        help="Depositor's password.")
    parser.add_argument('--user-email', type=str, default=None,
                        help="Depositor's e-mail address.")
    parser.add_argument('--title', type=str, default=None,
                        help="Title of the publication.")
    parser.add_argument('--author-name', type=str, default=None,
                        help="Full name of the publication author.")
    parser.add_argument('--author-email', type=str, default=None,
                        help="E-mail address of the publication author.")
    parser.add_argument('--url', type=str,
                        help="URL of the deposition API.")

def translate_calculation_specific_values(parameters,translator,**kwargs):
    """
    Translates calculation-specific values from ParameterData object to
    appropriate TCOD CIF tags.
    """
    from aiida.tools.dbexporters.tcod_plugins import BaseTcodtranslator
    if not issubclass(translator,BaseTcodtranslator):
        raise ValueError("supplied translator is of class {}, while it "
                         "must be derived from {} class".format(translator.__class__,
                                                                BaseTcodtranslator.__class__))
    translation_map = {
        '_tcod_total_energy'              : 'get_total_energy',
        '_dft_1e_energy'                  : 'get_one_electron_energy',
        '_dft_correlation_energy'         : 'get_exchange_correlation_energy',
        '_dft_ewald_energy'               : 'get_ewald_energy',
        '_dft_hartree_energy'             : 'get_hartree_energy',
        '_dft_fermi_energy'               : 'get_fermi_energy',
        '_dft_cell_valence_electrons'     : 'get_number_of_electrons',
        '_tcod_computation_wallclock_time': 'get_computation_wallclock_time',
    }
    tags = dict()
    for tag,function in translation_map.iteritems():
        value = None
        try:
            value = getattr(translator,function)(parameters,**kwargs)
        except NotImplementedError as e:
            pass
        if value is not None:
            tags[tag] = value

    return tags
