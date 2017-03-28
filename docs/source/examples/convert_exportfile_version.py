#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################



old_start = "aiida.djsite"
new_start = "aiida.backends.djsite"
old_version = "0.1"
new_version = "0.2"


def upgrade_data_metadata(data, metadata):
    """
    Replace (in place for efficiency) both data and metadata with the new
    format introduced in AiiDA 0.6.0.
    """
    
    def get_new_string(old_str):
        if old_str.startswith(old_start):
            return "{}{}".format(new_start, old_str[len(old_start):])
        else:
            return old_str

    def replace_requires(data):
        if isinstance(data, dict):
            new_data = {}
            for k, v in data.iteritems():
                if k == 'requires' and v.startswith(old_start):
                    new_data[k] = get_new_string(v)
                else:
                    new_data[k] = replace_requires(v)
            return new_data
        else:
            return data

    if metadata['export_version'] != old_version:
        raise ValueError(
            "Can only convert starting from version {}, "
            "file version is instead {}.".format(old_version,
                                                 metadata['export_version']))

    field = 'export_data' 
    for k in list(data[field]):
        if k.startswith(old_start):
            new_k = get_new_string(k)
            data[field][new_k] = data[field][k]
            del data[field][k]

    for field in ['unique_identifiers', 'all_fields_info']: 
        for k in list(metadata[field].keys()):
            if k.startswith(old_start):
                new_k = get_new_string(k)
                metadata[field][new_k] = metadata[field][k]
                del metadata[field][k]

    field = 'all_fields_info'
    metadata[field] = replace_requires(metadata[field])

    metadata['export_version'] = new_version
    metadata['conversion_info'] = (
        metadata.get('conversion_info', []) +
        ["Converted from version {} to {} with external script.".format(
            old_version, new_version)])
    
if __name__ == "__main__":
    import json
    import os, sys
    import tarfile, zipfile

    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()
    
    from aiida.common.folders import SandboxFolder
    from aiida.orm.importexport import extract_tree, extract_zip, extract_tar

    silent = False
    
    try:
        in_path = sys.argv[1]
        out_path = sys.argv[2]
    except IndexError:
        print >> sys.stderr, ("Pass the input file (old version) "
                              "to convert and the new file to create")
        sys.exit(1)

    if os.path.exists(out_path):
        print >> sys.stderr, "The output file already exists!"
        sys.exit(2)
    
    with SandboxFolder() as folder:
        if os.path.isdir(in_path):
            extract_tree(in_path,folder,silent=silent)
        else:
            if tarfile.is_tarfile(in_path):
                extract_tar(in_path,folder,silent=silent)
            elif zipfile.is_zipfile(in_path):
                extract_zip(in_path,folder,silent=silent)
            else:
                raise ValueError("Unable to detect the input file format, it "
                                 "is neither a (possibly compressed) tar "
                                 "file, nor a zip file.")
        try:
            with open(folder.get_abs_path('metadata.json')) as f:
                metadata = json.load(f)

            with open(folder.get_abs_path('data.json')) as f:
                data = json.load(f)
        except IOError as e:
            raise ValueError("Unable to find the file {} in the import "
                             "file or folder".format(e.filename))
            
        # In-place update
        upgrade_data_metadata(data, metadata)

        with open(folder.get_abs_path('metadata.json'),'w') as f:
            json.dump(metadata,f)
        with open(folder.get_abs_path('data.json'),'w') as f:
            json.dump(data, f)

        with zipfile.ZipFile(out_path, mode='w',
                             compression=zipfile.ZIP_DEFLATED) as outzip:
            src = folder.abspath
            for dirpath, dirnames, filenames in os.walk(src):
                relpath = os.path.relpath(dirpath, src)
                for fn in dirnames + filenames:
                    real_src = os.path.join(dirpath,fn)
                    real_dest = os.path.join(relpath,fn)
                    outzip.write(real_src, real_dest)

    print "File {} created at version {}.".format(out_path, new_version)
