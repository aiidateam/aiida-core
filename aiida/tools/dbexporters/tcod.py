# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################


from aiida.orm import DataFactory
from aiida.orm.calculation.inline import optional_inline

aiida_executable_name = '_aiidasubmit.sh'
inline_executable_name = 'aiidainline.py'

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
        '_tcod_computation_reference_uuid',
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
    ],
    '_dft_atom_basisset': [
        '_atom_type_symbol',
        '_dft_atom_basisset',
        '_dft_atom_basisset_type',
        '_dft_atom_basisset_energy_conv',
        '_dft_atom_basisset_citation_id',
        '_dft_atom_type_valence_configuration',
    ],
    '_tcod_atom_site_resid_force_Cartn_': [
        '_tcod_atom_site_resid_force_Cartn_x',
        '_tcod_atom_site_resid_force_Cartn_y',
        '_tcod_atom_site_resid_force_Cartn_z',
    ],
    '_dft_pseudopotential_': [
        '_dft_pseudopotential_atom_type',
        '_dft_pseudopotential_type',
        '_dft_pseudopotential_type_other_name',
    ],
}

conforming_dictionaries = [
    {
        'name': 'cif_tcod.dic',
        'version': '0.010',
        'url': 'http://www.crystallography.net/tcod/cif/dictionaries/cif_tcod.dic'
    },
    {
        'name': 'cif_dft.dic',
        'version': '0.020',
        'url': 'http://www.crystallography.net/tcod/cif/dictionaries/cif_dft.dic'
    }
]

default_options = {
    'code': 'cif_cod_deposit',
    'dump_aiida_database': True,
    'exclude_external_contents': False,
    'gzip': False,
    'gzip_threshold': 1024,
    'reduce_symmetry': True,
}


def cif_encode_contents(content, gzip=False, gzip_threshold=1024):
    """
    Encodes data for usage in CIF text field in a *best possible* way:
    binary data is encoded using Base64 encoding; text with non-ASCII
    symbols, too long lines or lines starting with semicolons (';')
    is encoded using Quoted-printable encoding.

    :param content: the content to be encoded
    :return content: encoded content
    :return encoding: a string specifying used encoding (None, 'base64',
        'ncr', 'quoted-printable', 'gzip+base64')
    """
    import re
    method = None
    if len(content) == 0:
        # content is empty
        method = None
    elif gzip and len(content) >= gzip_threshold:
        # content is larger than some arbitrary value and should be gzipped
        method = 'gzip+base64'
    elif float(len(re.findall('[^\x09\x0A\x0D\x20-\x7E]', content)))/len(content) > 0.25:
        # contents are assumed to be binary
        method = 'base64'
    elif re.search('^\s*data_',content) is not None or \
         re.search('\n\s*data_',content) is not None:
        # contents have CIF datablock header-like lines, that may be
        # dangerous when parsed with primitive parsers
        method = 'base64'
    elif re.search('.{2048}.',content) is not None:
        # lines are too long
        method = 'quoted-printable'
    elif len(re.findall('[^\x09\x0A\x0D\x20-\x7E]', content)) > 0:
        # contents have non-ASCII symbols
        method = 'quoted-printable'
    elif re.search('^;', content) is not None or re.search('\n;', content) is not None:
        # content has lines starting with semicolon (';')
        method = 'quoted-printable'
    elif re.search('\t', content) is not None:
        # content has TAB symbols, which may be lost during the
        # parsing of TCOD CIF file
        method = 'quoted-printable'
    elif content == '.' or content == '?':
        method = 'quoted-printable'
    else:
        method = None

    if method == 'base64':
        content = encode_textfield_base64(content)
    elif method == 'quoted-printable':
        content = encode_textfield_quoted_printable(content)
    elif method == 'ncr':
        content = encode_textfield_ncr(content)
    elif method == 'gzip+base64':
        content = encode_textfield_gzip_base64(content)

    return content, method


def encode_textfield_base64(content, foldwidth=76):
    """
    Encodes the contents for CIF textfield in Base64 using standard Python
    implementation (``base64.standard_b64encode()``).

    :param content: a string with contents
    :param foldwidth: maximum width of line (default is 76)
    :return: encoded string
    """
    import base64

    content = base64.standard_b64encode(content)
    content = "\n".join(list(content[i:i + foldwidth]
                             for i in range(0, len(content), foldwidth)))
    return content


def decode_textfield_base64(content):
    """
    Decodes the contents for CIF textfield from Base64 using standard
    Python implementation (``base64.standard_b64decode()``)

    :param content: a string with contents
    :return: decoded string
    """
    import base64

    return base64.standard_b64decode(content)


def encode_textfield_quoted_printable(content):
    """
    Encodes the contents for CIF textfield in quoted-printable encoding.
    In addition to non-ASCII characters, that are encoded by Python
    function ``quopri.encodestring()``, following characters are encoded:

        * '``;``', if encountered on the beginning of the line;
        * '``\\t``' and '``\\r``';
        * '``.``' and '``?``', if comprise the entire textfield.

    :param content: a string with contents
    :return: encoded string
    """
    import re
    import quopri

    content = quopri.encodestring(content)

    def match2qp(m):
        prefix = ''
        postfix = ''
        if 'prefix' in m.groupdict().keys():
            prefix = m.group('prefix')
        if 'postfix' in m.groupdict().keys():
            postfix = m.group('postfix')
        h = hex(ord(m.group('chr')))[2:].upper()
        if len(h) == 1:
            h = "0{}".format(h)
        return "{}={}{}".format(prefix, h, postfix)

    content = re.sub('^(?P<chr>;)', match2qp, content)
    content = re.sub('(?P<chr>[\t\r])', match2qp, content)
    content = re.sub('(?P<prefix>\n)(?P<chr>;)', match2qp, content)
    content = re.sub('^(?P<chr>[\.\?])$', match2qp, content)
    return content


def decode_textfield_quoted_printable(content):
    """
    Decodes the contents for CIF textfield from quoted-printable encoding.

    :param content: a string with contents
    :return: decoded string
    """
    import quopri

    return quopri.decodestring(content)


def encode_textfield_ncr(content):
    """
    Encodes the contents for CIF textfield in Numeric Character Reference.
    Encoded characters:

        * ``\\x09``, ``\\x0A``, ``\\x0D``, ``\\x20``--``\\x7E``;
        * '``;``', if encountered on the beginning of the line;
        * '``\\t``'
        * '``.``' and '``?``', if comprise the entire textfield.

    :param content: a string with contents
    :return: encoded string
    """
    import re

    def match2ncr(m):
        prefix = ''
        postfix = ''
        if 'prefix' in m.groupdict().keys():
            prefix = m.group('prefix')
        if 'postfix' in m.groupdict().keys():
            postfix = m.group('postfix')
        return prefix + '&#' + str(ord(m.group('chr'))) + ';' + postfix

    content = re.sub('(?P<chr>[&\t])', match2ncr, content)
    content = re.sub('(?P<chr>[^\x09\x0A\x0D\x20-\x7E])', match2ncr, content)
    content = re.sub('^(?P<chr>;)', match2ncr, content)
    content = re.sub('(?P<prefix>\n)(?P<chr>;)', match2ncr, content)
    content = re.sub('^(?P<chr>[\.\?])$', match2ncr, content)
    return content


def decode_textfield_ncr(content):
    """
    Decodes the contents for CIF textfield from Numeric Character Reference.

    :param content: a string with contents
    :return: decoded string
    """
    import re

    def match2str(m):
        return chr(int(m.group(1)))

    return re.sub('&#(\d+);', match2str, content)


def encode_textfield_gzip_base64(content, **kwargs):
    """
    Gzips the given string and encodes it in Base64.

    :param content: a string with contents
    :return: encoded string
    """
    from aiida.common.utils import gzip_string

    return encode_textfield_base64(gzip_string(content), **kwargs)


def decode_textfield_gzip_base64(content):
    """
    Decodes the contents for CIF textfield from Base64 and decompresses
    them with gzip.

    :param content: a string with contents
    :return: decoded string
    """
    from aiida.common.utils import gunzip_string

    return gunzip_string(decode_textfield_base64(content))


def decode_textfield(content,method):
    """
    Decodes the contents of encoded CIF textfield.

    :param content: the content to be decoded
    :param method: method, which was used for encoding the contents
        (None, 'base64', 'ncr', 'quoted-printable', 'gzip+base64')
    :return: decoded content
    :raises ValueError: if the encoding method is unknown
    """
    if method == 'base64':
        content = decode_textfield_base64(content)
    elif method == 'quoted-printable':
        content = decode_textfield_quoted_printable(content)
    elif method == 'ncr':
        content = decode_textfield_ncr(content)
    elif method == 'gzip+base64':
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
    :raises MultipleObjectsError: if the node has more than one calculation
        attached.
    """
    from aiida.common.exceptions import MultipleObjectsError
    from aiida.orm.calculation import Calculation
    if len(node.get_inputs(node_type=Calculation)) == 1:
        return node.get_inputs(node_type=Calculation)[0]
    elif len(node.get_inputs(node_type=Calculation)) == 0:
        return None
    else:
        raise MultipleObjectsError("Node {} seems to have more than one "
                                   "parent (immediate) calculation -- "
                                   "exporter does not know which one of "
                                   "them produced the node".format(node))


def _assert_same_parents(a, b):
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
    Create executable Python script for execution of inline script.

    .. note:: the output bash script may not always be correct, since it
        is simply formed from:
        * contents of the file, which contains the original ``\*_inline``
          function;
        * call of the original ``\*_inline`` function with input nodes;
        * storing of the output nodes.
        Execution of generated bash script should result in
        ModificationNotAllowed exception, since the nodes, that are
        created by the ``\*_inline`` function, are already stored.
    """
    input_dict = calc.get_inputs_dict()
    args = ["{}=load_node('{}')".format(x, input_dict[x].uuid)
            for x in input_dict.keys()]
    args_string = ",\n    ".join(sorted(args))
    return """#!/usr/bin/env runaiida
{}

for key, value in {}(
    {}
    )[1].iteritems():
    value.store()
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
    import hashlib
    import os
    calcs_now = []
    for d in calc.get_inputs(node_type=Data):
        for c in d.get_inputs(node_type=Calculation):
            calcs = _collect_calculation_data(c)
            calcs_now.extend(calcs)

    files_in = []
    files_out = []
    this_calc = {
        'uuid' : calc.uuid,
        'files': [],
    }

    if isinstance(calc, JobCalculation):
        retrieved_abspath = calc.get_retrieved_node().get_abs_path()
        files_in  = _collect_files(calc._raw_input_folder.abspath)
        files_out = _collect_files(os.path.join(retrieved_abspath, 'path'))
        this_calc['env'] = calc.get_environment_variables()
        stdout_name = '{}.out'.format(aiida_executable_name)
        while stdout_name in [files_in,files_out]:
            stdout_name = '_{}'.format(stdout_name)
        stderr_name = '{}.err'.format(aiida_executable_name)
        while stderr_name in [files_in,files_out]:
            stderr_name = '_{}'.format(stderr_name)
        files_out.append({
            'name'    : stdout_name,
            'contents': calc.get_scheduler_output(),
            'md5'     : hashlib.md5(calc.get_scheduler_output()).hexdigest(),
            'sha1'    : hashlib.sha1(calc.get_scheduler_output()).hexdigest(),
            'role'    : 'stdout',
            'type'    : 'file',
            })
        files_out.append({
            'name'    : stderr_name,
            'contents': calc.get_scheduler_error(),
            'md5'     : hashlib.md5(calc.get_scheduler_error()).hexdigest(),
            'sha1'    : hashlib.sha1(calc.get_scheduler_error()).hexdigest(),
            'role'    : 'stderr',
            'type'    : 'file',
            })
        this_calc['stdout'] = stdout_name
        this_calc['stderr'] = stderr_name
    else:
        # Calculation is InlineCalculation
        python_script = _inline_to_standalone_script(calc)
        files_in.append({
            'name'    : inline_executable_name,
            'contents': python_script,
            'md5'     : hashlib.md5(python_script).hexdigest(),
            'sha1'    : hashlib.sha1(python_script).hexdigest(),
            'type'    : 'file',
            })
        shell_script = '#!/bin/bash\n\nverdi run {}\n'.format(inline_executable_name)
        files_in.append({
            'name'    : aiida_executable_name,
            'contents': shell_script,
            'md5'     : hashlib.md5(shell_script).hexdigest(),
            'sha1'    : hashlib.sha1(shell_script).hexdigest(),
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
            if 'role' not in f.keys():
                f['role'] = 'output'
            this_calc['files'].append(f)

    calcs_now.append(this_calc)
    return calcs_now


def _collect_files(base, path=''):
    """
    Recursively collects files from the tree, starting at a given path.
    """
    from aiida.common.folders import Folder
    from aiida.common.utils import md5_file,sha1_file
    import os

    def get_filename(file_dict):
        return file_dict['name']

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
        return sorted(files_now,key=get_filename)
    elif path == '.aiida/calcinfo.json':
        files = []
        with open(os.path.join(base,path)) as f:
            files.append({
                'name': path,
                'contents': f.read(),
                'md5': md5_file(os.path.join(base,path)),
                'sha1': sha1_file(os.path.join(base,path)),
                'type': 'file',
                })
        import json
        with open(os.path.join(base,path)) as f:
            calcinfo = json.load(f)
        if 'local_copy_list' in calcinfo:
            for local_copy in calcinfo['local_copy_list']:
                with open(local_copy[0]) as f:
                    files.append({
                        'name': os.path.normpath(local_copy[1]),
                        'contents': f.read(),
                        'md5': md5_file(local_copy[0]),
                        'sha1': sha1_file(local_copy[0]),
                        'type': 'file',
                        })
        return files
    else:
        with open(os.path.join(base,path)) as f:
            return [{
                'name': path,
                'contents': f.read(),
                'md5': md5_file(os.path.join(base,path)),
                'sha1': sha1_file(os.path.join(base,path)),
                'type': 'file',
                }]


def extend_with_cmdline_parameters(parser, expclass="Data"):
    """
    Provides descriptions of command line options, that are used to control
    the process of exporting data to TCOD CIF files.

    :param parser: an argparse.Parser instance
    :param expclass: name of the exported class to be shown in help string
        for the command line options

    .. note:: This method must not set any default values for command line
        options in order not to clash with any other data export plugins.
    """
    parser.add_argument('--reduce-symmetry', action='store_true',
                        default=None,
                        dest='reduce_symmetry',
                        help="Perform symmetry reduction. "
                             "Default option.")
    parser.add_argument('--no-reduce-symmetry',
                        '--dont-reduce-symmetry',
                        default=None,
                        action='store_false',
                        dest='reduce_symmetry',
                        help="Do not perform symmetry reduction.")
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
                        default=None,
                        dest='dump_aiida_database',
                        help="Export AiiDA database to the CIF file. "
                             "Default option.")
    parser.add_argument('--no-dump-aiida-database',
                        '--dont-dump-aiida-database',
                        default=None,
                        action='store_false',
                        dest='dump_aiida_database',
                        help="Do not export AiiDA database to the CIF "
                             "file.")
    parser.add_argument('--exclude-external-contents', action='store_true',
                        default=None,
                        dest='exclude_external_contents',
                        help="Do not save contents for external "
                             "resources if URIs are provided. "
                             "Default option.")
    parser.add_argument('--no-exclude-external-contents',
                        '--dont-exclude-external-contents',
                        default=None,
                        action='store_false',
                        dest='exclude_external_contents',
                        help="Save contents for external resources "
                             "even if URIs are provided.")
    parser.add_argument('--gzip', action='store_true', dest='gzip',
                        default=None,
                        help="Gzip large files.")
    parser.add_argument('--no-gzip', '--dont-gzip', action='store_false',
                        default=None,
                        dest='gzip',
                        help="Do not gzip any files. Default option.")
    parser.add_argument('--gzip-threshold', type=int,
                        default=None,
                        help="Specify the minimum size of exported "
                             "file which should be gzipped. "
                             "Default {}.".format(default_options['gzip_threshold']))


def _collect_tags(node, calc,parameters=None,
                  dump_aiida_database=default_options['dump_aiida_database'],
                  exclude_external_contents=default_options['exclude_external_contents'],
                  gzip=default_options['gzip'],
                  gzip_threshold=default_options['gzip_threshold']):
    """
    Retrieve metadata from attached calculation and pseudopotentials
    and prepare it to be saved in TCOD CIF.
    """
    import os, json
    import aiida
    tags = { '_audit_creation_method': "AiiDA version {}".format(aiida.__version__) }

    # Recording the dictionaries (if any)

    if len(conforming_dictionaries):
        for postfix in ['name', 'version', 'location']:
            key = '_audit_conform_dict_{}'.format(postfix)
            if key not in tags:
                tags[key] = []

    for dictionary in conforming_dictionaries:
        tags['_audit_conform_dict_name'].append(dictionary['name'])
        tags['_audit_conform_dict_version'].append(dictionary['version'])
        tags['_audit_conform_dict_location'].append(dictionary['url'])

    # Collecting metadata from input files:

    calc_data = []
    if calc is not None:
        calc_data = _collect_calculation_data(calc)

    for tag in tcod_loops['_tcod_computation'] + tcod_loops['_tcod_file']:
        tags[tag] = []

    export_files = []

    sn = 1
    for step in calc_data:
        tags['_tcod_computation_step'].append(sn)
        tags['_tcod_computation_command'].append(
            'cd {}; ./{}'.format(sn,aiida_executable_name))
        tags['_tcod_computation_reference_uuid'].append(step['uuid'])
        if 'env' in step:
            tags['_tcod_computation_environment'].append(
                "\n".join(["%s=%s" % (key,step['env'][key]) for key in step['env']]))
        else:
            tags['_tcod_computation_environment'].append('')
        if 'stdout' in step and step['stdout'] is not None:
            tags['_tcod_computation_stdout'].append(step['stdout'])
        else:
            tags['_tcod_computation_stdout'].append('')
        if 'stderr' in step and step['stderr'] is not None:
            tags['_tcod_computation_stderr'].append(step['stderr'])
        else:
            tags['_tcod_computation_stderr'].append('')

        export_files.append( {'name': "{}{}".format(sn, os.sep),
                              'type': 'folder'} )

        for f in step['files']:
            f['name'] = os.path.join(str(sn), f['name'])
        export_files.extend( step['files'] )

        sn = sn + 1

    # Creating importable AiiDA database dump in CIF tags

    if dump_aiida_database and node.is_stored:
        import json
        from aiida.common.exceptions import LicensingException
        from aiida.common.folders import SandboxFolder
        from aiida.orm.importexport import export_tree

        with SandboxFolder() as folder:
            try:
                export_tree([node.dbnode], folder=folder, silent=True,
                            allowed_licenses=['CC0'])
            except LicensingException as e:
                raise LicensingException(e.message + \
                                         ". Only CC0 license is accepted.")

            files = _collect_files(folder.abspath)
            with open(folder.get_abs_path('data.json')) as f:
                data = json.loads(f.read())
            md5_to_url = {}
            if exclude_external_contents:
                for pk in data['node_attributes']:
                    n = data['node_attributes'][pk]
                    if 'md5' in n.keys() and 'source' in n.keys() and \
                      'uri' in n['source'].keys():
                        md5_to_url[n['md5']] = n['source']['uri']

            for f in files:
                f['name'] = os.path.join('aiida',f['name'])
                if f['type'] == 'file' and f['md5'] in md5_to_url.keys():
                    f['uri'] = md5_to_url[f['md5']]

            export_files.extend(files)

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
        for i in range(0, len(layers)):
            tags['_tcod_content_encoding_id'].append(encoding)
            tags['_tcod_content_encoding_layer_id'].append(i+1)
            tags['_tcod_content_encoding_layer_type'].append(layers[i])

    # Describing Brillouin zone (if used)

    if calc is not None:
        from aiida.orm.data.array.kpoints import KpointsData
        kpoints_list = calc.get_inputs(KpointsData)
        # TODO: stop if more than one KpointsData is used?
        if len(kpoints_list) == 1:
            kpoints = kpoints_list[0]
            density, shift = kpoints.get_kpoints_mesh()
            tags['_dft_BZ_integration_grid_X'] = density[0]
            tags['_dft_BZ_integration_grid_Y'] = density[1]
            tags['_dft_BZ_integration_grid_Z'] = density[2]
            tags['_dft_BZ_integration_grid_shift_X'] = shift[0]
            tags['_dft_BZ_integration_grid_shift_Y'] = shift[1]
            tags['_dft_BZ_integration_grid_shift_Z'] = shift[2]

    # Collecting code-specific data

    from aiida.common.pluginloader import BaseFactory, existing_plugins
    from aiida.tools.dbexporters.tcod_plugins import BaseTcodtranslator

    plugin_path = "aiida.tools.dbexporters.tcod_plugins"
    plugins = list()

    if calc is not None:
        for plugin in existing_plugins(BaseTcodtranslator, plugin_path):
            cls = BaseFactory(plugin, BaseTcodtranslator, plugin_path)
            if calc._plugin_type_string.endswith(cls._plugin_type_string + '.'):
                plugins.append(cls)

    from aiida.common.exceptions import MultipleObjectsError

    if len(plugins) > 1:
        raise MultipleObjectsError("more than one plugin found for "
                                   "{}".calc._plugin_type_string)

    if len(plugins) == 1:
        plugin = plugins[0]
        translated_tags = translate_calculation_specific_values(calc,
                                                                plugin)
        tags.update(translated_tags)

    return tags


@optional_inline
def add_metadata_inline(what, node=None, parameters=None, args=None):
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

    .. note:: can be used as inline calculation.
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
    datablock_names = None
    if args:
        kwargs = args.get_dict()
        additional_tags = kwargs.pop('additional_tags',{})
        datablock_names = kwargs.pop('datablock_names',None)

    tags = _collect_tags(what, calc, parameters=parameters, **kwargs)
    loops.update(tcod_loops)

    for datablock in datablocks:
        for k,v in dict(tags.items() + additional_tags.items()).iteritems():
            if not k.startswith('_'):
                raise ValueError("Tag '{}' does not seem to start with "
                                 "an underscode ('_'): all CIF tags must "
                                 "start with underscores".format(k))
            datablock[k] = v

    values = pycifrw_from_cif(datablocks, loops, names=datablock_names)
    cif = CifData(values=values)

    return {'cif': cif}


def export_cif(what, **kwargs):
    """
    Exports given coordinate-containing \*Data node to string of CIF
    format.

    :return: string with contents of CIF file.
    """
    cif = export_cifnode(what, **kwargs)
    return cif._exportstring('cif')[0]


def export_values(what, **kwargs):
    """
    Exports given coordinate-containing \*Data node to PyCIFRW CIF data
    structure.

    :return: CIF data structure.

    .. note:: Requires PyCIFRW.
    """
    cif = export_cifnode(what,**kwargs)
    return cif.values


def export_cifnode(what, parameters=None, trajectory_index=None,
                   store=False,
                   reduce_symmetry=default_options['reduce_symmetry'],
                   **kwargs):
    """
    The main exporter function. Exports given coordinate-containing \*Data
    node to :py:class:`aiida.orm.data.cif.CifData` node, ready to be
    exported to TCOD. All \*Data types, having method ``_get_cif()``, are
    supported in addition to :py:class:`aiida.orm.data.cif.CifData`.

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
    from aiida.common.exceptions import MultipleObjectsError
    from aiida.orm.calculation.inline import make_inline
    CifData        = DataFactory('cif')
    StructureData  = DataFactory('structure')
    TrajectoryData = DataFactory('array.trajectory')
    ParameterData  = DataFactory('parameter')

    calc = _get_calculation(what)

    if parameters is not None:
        if not isinstance(parameters, ParameterData):
            raise ValueError("Supplied parameters are not an "
                             "instance of ParameterData")
    elif calc is not None:
        params = calc.get_outputs(type=ParameterData)
        if len(params) == 1:
            parameters = params[0]
        elif len(params) > 0:
            raise MultipleObjectsError("Calculation {} has more than "
                                       "one ParameterData output, please "
                                       "specify which one to use with "
                                       "an option parameters='' when "
                                       "calling export_cif()".format(calc))

    if parameters is not None:
        _assert_same_parents(what, parameters)

    node = what

    # Convert node to CifData (if required)

    if not isinstance(node, CifData) and getattr(node, '_get_cif'):
        function_args = { 'store': store }
        if trajectory_index is not None:
            function_args['index'] = trajectory_index
        node = node._get_cif(**function_args)

    if not isinstance(node,CifData):
        raise NotImplementedError("Exporter does not know how to "
                                  "export {}".format(type(node)))

    # Reduction of the symmetry

    if reduce_symmetry:
        from aiida.orm.data.cif import refine_inline
        ret_dict = refine_inline(node=node, store=store)
        node = ret_dict['cif']

    # Addition of the metadata

    args = ParameterData(dict=kwargs)
    function_args = { 'what': what, 'args': args, 'store': store }
    if node != what:
        function_args['node'] = node
    if parameters is not None:
        function_args['parameters'] = parameters
    ret_dict = add_metadata_inline(**function_args)

    return ret_dict['cif']


def deposit(what, type, author_name=None, author_email=None, url=None,
            title=None, username=None, password=False, user_email=None,
            code_label=default_options['code'], computer_name=None,
            replace=None, message=None, **kwargs):
    """
    Launches a
    :py:class:`aiida.orm.implementation.general.calculation.job.AbstractJobCalculation`
    to deposit data node to \*COD-type database.

    :return: launched :py:class:`aiida.orm.implementation.general.calculation.job.AbstractJobCalculation`
        instance.
    :raises ValueError: if any of the required parameters are not given.
    """
    from aiida.common.setup import get_property

    parameters = {}

    if not what:
        raise ValueError("Node to be deposited is not supplied")
    if not type:
        raise ValueError("Deposition type is not supplied. Should be "
                         "one of the following: 'published', "
                         "'prepublication' or 'personal'")
    if not username:
        username = get_property('tcod.depositor_username')
        if not username:
            raise ValueError("Depositor username is not supplied")
    if not password:
        parameters['password'] = get_property('tcod.depositor_password')
        if not parameters['password']:
            raise ValueError("Depositor password is not supplied")
    if not user_email:
        user_email = get_property('tcod.depositor_email')
        if not user_email:
            raise ValueError("Depositor email is not supplied")

    parameters['deposition-type'] = type
    parameters['username'] = username
    parameters['user_email'] = user_email

    if type == 'published':
        pass
    elif type in ['prepublication','personal']:
        if not author_name:
            author_name = get_property('tcod.depositor_author_name')
            if not author_name:
                raise ValueError("Author name is not supplied")
        if not author_email:
            author_email = get_property('tcod.depositor_author_email')
            if not author_email:
                raise ValueError("Author email is not supplied")
        if not title:
            raise ValueError("Publication title is not supplied")
    else:
        raise ValueError("Unknown deposition type '{}' -- should be "
                         "one of the following: 'published', "
                         "'prepublication' or 'personal'".format(type))

    if replace:
        if str(int(replace)) != replace or int(replace) < 10000000 \
            or int(replace) > 99999999:
            raise ValueError("ID of the replaced structure ({}) does not "
                             "seem to be valid TCOD ID: must be in "
                             "range [10000000,99999999]".format(replace))
    elif message:
        raise ValueError("Message is given while the structure is not "
                         "redeposited -- log message is relevant to "
                         "redeposition only")

    kwargs['additional_tags'] = {}
    if title:
        kwargs['additional_tags']['_publ_section_title'] = title
    if author_name:
        kwargs['additional_tags']['_publ_author_name'] = author_name
    if replace:
        kwargs['additional_tags']['_tcod_database_code'] = replace
        kwargs['datablock_names'] = [replace]

    cif = export_cifnode(what, store=True, **kwargs)

    from aiida.orm.code import Code
    from aiida.orm.computer import Computer
    from aiida.orm.data.parameter import ParameterData
    from aiida.common.exceptions import NotExistent

    code = Code.get_from_string(code_label)
    computer = None
    if computer_name:
        computer = Computer.get(computer_name)
    calc = code.new_calc(computer=computer)
    calc.set_resources({'num_machines': 1, 'num_mpiprocs_per_machine': 1})

    if password:
        import getpass
        parameters['password'] = getpass.getpass("Password: ")
    if author_name:
        parameters['author_name'] = author_name
    if author_email:
        parameters['author_email'] = author_email
    if url:
        parameters['url'] = url
    if replace:
        parameters['replace'] = True
    if message:
        parameters['log-message'] = str(message)
    pd = ParameterData(dict=parameters)

    calc.use_cif(cif)
    calc.use_parameters(pd)

    calc.store_all()
    calc.submit()

    return calc


def deposition_cmdline_parameters(parser, expclass="Data"):
    """
    Provides descriptions of command line options, that are used to control
    the process of deposition to TCOD.

    :param parser: an argparse.Parser instance
    :param expclass: name of the exported class to be shown in help string
        for the command line options

    .. note:: This method must not set any default values for command line
        options in order not to clash with any other data deposition plugins.
    """
    parser.add_argument('--type', '--deposition-type', type=str,
                        choices=['published','prepublication','personal'],
                        help="Type of the deposition.")
    parser.add_argument('-u', '--username', type=str, default=None,
                        dest='username',
                        help="Depositor's username.")
    parser.add_argument('-p', '--password', action='store_true',
                        dest='password', default=None,
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
    parser.add_argument('--code', type=str, dest='code_label',
                        default=None,
                        help="Label of the code to be used for the "
                             "deposition. Default: cif_cod_deposit.")
    parser.add_argument('--computer', type=str, dest='computer_name',
                        help="Name of the computer to be used for "
                             "deposition. Default computer is used if "
                             "not specified.")
    parser.add_argument('--replace', type=str, dest='replace',
                        help="ID of the structure to be redeposited "
                             "(replaced), if any.")
    parser.add_argument('-m', '--message', type=str, dest='message',
                        help="Description of the change (relevant for "
                             "redepositions only.")


def translate_calculation_specific_values(calc, translator, **kwargs):
    """
    Translates calculation-specific values from
    :py:class:`aiida.orm.implementation.general.calculation.job.AbstractJobCalculation` subclass to
    appropriate TCOD CIF tags.

    :param calc: an instance of
        :py:class:`aiida.orm.implementation.general.calculation.job.AbstractJobCalculation` subclass.
    :param translator: class, derived from
        :py:class:`aiida.tools.dbexporters.tcod_plugins.BaseTcodtranslator`.
    :raises ValueError: if **translator** is not derived from proper class.
    """
    from aiida.tools.dbexporters.tcod_plugins import BaseTcodtranslator
    if not issubclass(translator, BaseTcodtranslator):
        raise ValueError("supplied translator is of class {}, while it "
                         "must be derived from {} class".format(translator.__class__,
                                                                BaseTcodtranslator.__class__))
    translation_map = {
        '_tcod_software_package': 'get_software_package',
        '_tcod_software_package_version': 'get_software_package_version',
        '_tcod_software_package_compilation_date': 'get_software_package_compilation_timestamp',
        '_tcod_software_executable_path': 'get_software_executable_path',

        '_tcod_total_energy': 'get_total_energy',
        '_dft_1e_energy': 'get_one_electron_energy',
        '_dft_correlation_energy': 'get_exchange_correlation_energy',
        '_dft_ewald_energy': 'get_ewald_energy',
        '_dft_hartree_energy': 'get_hartree_energy',
        '_dft_fermi_energy': 'get_fermi_energy',

        '_dft_cell_valence_electrons': 'get_number_of_electrons',
        '_tcod_computation_wallclock_time': 'get_computation_wallclock_time',
        '_atom_type_symbol': 'get_atom_type_symbol',
        '_dft_atom_type_valence_configuration': 'get_atom_type_valence_configuration',
        '_dft_atom_basisset': 'get_atom_type_basisset',

        '_dft_BZ_integration_smearing_method': 'get_integration_smearing_method',
        '_dft_BZ_integration_smearing_method_other': 'get_integration_smearing_method_other',
        '_dft_BZ_integration_MP_order': 'get_integration_Methfessel_Paxton_order',

        '_dft_BZ_integration_grid_X': 'get_BZ_integration_grid_X',
        '_dft_BZ_integration_grid_Y': 'get_BZ_integration_grid_Y',
        '_dft_BZ_integration_grid_Z': 'get_BZ_integration_grid_Z',

        '_dft_BZ_integration_grid_shift_X': 'get_BZ_integration_grid_shift_X',
        '_dft_BZ_integration_grid_shift_Y': 'get_BZ_integration_grid_shift_Y',
        '_dft_BZ_integration_grid_shift_Z': 'get_BZ_integration_grid_shift_Z',

        '_dft_kinetic_energy_cutoff_wavefunctions': 'get_kinetic_energy_cutoff_wavefunctions',
        '_dft_kinetic_energy_cutoff_charge_density': 'get_kinetic_energy_cutoff_charge_density',
        '_dft_kinetic_energy_cutoff_EEX': 'get_kinetic_energy_cutoff_EEX',

        '_dft_pseudopotential_atom_type': 'get_pseudopotential_atom_type',
        '_dft_pseudopotential_type': 'get_pseudopotential_type',
        '_dft_pseudopotential_type_other_name': 'get_pseudopotential_type_other_name',

        ## Residual forces are no longer produced, as they should
        ## be in the same CIF loop with coordinates -- to be
        ## implemented later, since it's not yet clear how.
        # '_tcod_atom_site_resid_force_Cartn_x': 'get_atom_site_residual_force_Cartesian_x',
        # '_tcod_atom_site_resid_force_Cartn_y': 'get_atom_site_residual_force_Cartesian_y',
        # '_tcod_atom_site_resid_force_Cartn_z': 'get_atom_site_residual_force_Cartesian_z',
    }
    tags = dict()
    for tag, function in translation_map.iteritems():
        value = None
        try:
            value = getattr(translator, function)(calc, **kwargs)
        except NotImplementedError as e:
            pass
        if value is not None:
            if isinstance(value,list):
                for i in range(0,len(value)):
                    if value[i] is None:
                        value[i] = '?'
            tags[tag] = value

    return tags
