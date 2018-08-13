# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

def extract_zip(infile, folder, nodes_export_subfolder="nodes",
                silent=False):
    """
    Extract the nodes to be imported from a zip file.

    :param infile: file path
    :param folder: a SandboxFolder, used to extract the file tree
    :param nodes_export_subfolder: name of the subfolder for AiiDA nodes
    :param silent: suppress debug print
    """
    import os
    import zipfile

    if not silent:
        print "READING DATA AND METADATA..."

    try:
        with zipfile.ZipFile(infile, "r", allowZip64=True) as zip:

            if not zip.namelist():
                raise ValueError("The zip file is empty.")

            zip.extract(path=folder.abspath,
                   member='metadata.json')
            zip.extract(path=folder.abspath,
                   member='data.json')

            if not silent:
                print "EXTRACTING NODE DATA..."

            for membername in zip.namelist():
                # Check that we are only exporting nodes within
                # the subfolder!
                # TODO: better check such that there are no .. in the
                # path; use probably the folder limit checks
                if not membername.startswith(nodes_export_subfolder+os.sep):
                    continue
                zip.extract(path=folder.abspath,
                            member=membername)
    except zipfile.BadZipfile:
        raise ValueError("The input file format for import is not valid (not"
                         " a zip file)")

def extract_tar(infile, folder, nodes_export_subfolder="nodes",
                silent=False):
    """
    Extract the nodes to be imported from a (possibly zipped) tar file.

    :param infile: file path
    :param folder: a SandboxFolder, used to extract the file tree
    :param nodes_export_subfolder: name of the subfolder for AiiDA nodes
    :param silent: suppress debug print
    """
    import os
    import tarfile

    if not silent:
        print "READING DATA AND METADATA..."

    try:
        with tarfile.open(infile, "r:*", format=tarfile.PAX_FORMAT) as tar:

            tar.extract(path=folder.abspath,
                   member=tar.getmember('metadata.json'))
            tar.extract(path=folder.abspath,
                   member=tar.getmember('data.json'))

            if not silent:
                print "EXTRACTING NODE DATA..."

            for member in tar.getmembers():
                if member.isdev():
                    # safety: skip if character device, block device or FIFO
                    print >> sys.stderr, ("WARNING, device found inside the "
                        "import file: {}".format(member.name))
                    continue
                if member.issym() or member.islnk():
                    # safety: in export, I set dereference=True therefore
                    # there should be no symbolic or hard links.
                    print >> sys.stderr, ("WARNING, link found inside the "
                        "import file: {}".format(member.name))
                    continue
                # Check that we are only exporting nodes within
                # the subfolder!
                # TODO: better check such that there are no .. in the
                # path; use probably the folder limit checks
                if not member.name.startswith(nodes_export_subfolder+os.sep):
                    continue
                tar.extract(path=folder.abspath,
                            member=member)
    except tarfile.ReadError:
        raise ValueError("The input file format for import is not valid (1)")

def extract_tree(infile, folder, silent=False):
    """
    Prepare to import nodes from plain file system tree.

    :param infile: path
    :param folder: a SandboxFolder, used to extract the file tree
    :param silent: suppress debug print
    """
    import os

    def add_files(args,path,files):
        folder = args['folder']
        root = args['root']
        for f in files:
            fullpath = os.path.join(path,f)
            relpath = os.path.relpath(fullpath,root)
            if os.path.isdir(fullpath):
                if os.path.dirname(relpath) != '':
                    folder.get_subfolder(os.path.dirname(relpath) +
                                         os.sep, create=True)
            elif not os.path.isfile(fullpath):
                continue
            if os.path.dirname(relpath) != '':
                folder.get_subfolder(os.path.dirname(relpath)+os.sep,
                                     create=True)
            folder.insert_path(os.path.abspath(fullpath),relpath)

    os.path.walk(infile,add_files,{'folder': folder, 'root': infile})

def extract_cif(infile, folder, nodes_export_subfolder="nodes",
                aiida_export_subfolder="aiida", silent=False):
    """
    Extract the nodes to be imported from a TCOD CIF file. TCOD CIFs,
    exported by AiiDA, may contain an importable subset of AiiDA database,
    which can be imported. This function prepares SandboxFolder with files
    required for import.

    :param infile: file path
    :param folder: a SandboxFolder, used to extract the file tree
    :param nodes_export_subfolder: name of the subfolder for AiiDA nodes
    :param aiida_export_subfolder: name of the subfolder for AiiDA data
        inside the TCOD CIF internal file tree
    :param silent: suppress debug print
    """
    import os
    import urllib2
    import CifFile
    from aiida.common.exceptions import ValidationError
    from aiida.common.utils import md5_file, sha1_file
    from aiida.tools.dbexporters.tcod import decode_textfield

    values = CifFile.ReadCif(infile)
    values = values[values.keys()[0]] # taking the first datablock in CIF

    for i in range(0,len(values['_tcod_file_id'])-1):
        name = values['_tcod_file_name'][i]
        if not name.startswith(aiida_export_subfolder+os.sep):
            continue
        dest_path = os.path.relpath(name,aiida_export_subfolder)
        if name.endswith(os.sep):
            if not os.path.exists(folder.get_abs_path(dest_path)):
                folder.get_subfolder(folder.get_abs_path(dest_path),create=True)
            continue
        contents = values['_tcod_file_contents'][i]
        if contents == '?' or contents == '.':
            uri = values['_tcod_file_uri'][i]
            if uri is not None and uri != '?' and uri != '.':
                contents = urllib2.urlopen(uri).read()
        encoding = values['_tcod_file_content_encoding'][i]
        if encoding == '.':
            encoding = None
        contents = decode_textfield(contents,encoding)
        if os.path.dirname(dest_path) != '':
            folder.get_subfolder(os.path.dirname(dest_path)+os.sep,create=True)
        with open(folder.get_abs_path(dest_path),'w') as f:
            f.write(contents)
            f.flush()
        md5  = values['_tcod_file_md5sum'][i]
        if md5 is not None:
            if md5_file(folder.get_abs_path(dest_path)) != md5:
                raise ValidationError("MD5 sum for extracted file '{}' is "
                                      "different from given in the CIF "
                                      "file".format(dest_path))
        sha1 = values['_tcod_file_sha1sum'][i]
        if sha1 is not None:
            if sha1_file(folder.get_abs_path(dest_path)) != sha1:
                raise ValidationError("SHA1 sum for extracted file '{}' is "
                                      "different from given in the CIF "
                                      "file".format(dest_path))
