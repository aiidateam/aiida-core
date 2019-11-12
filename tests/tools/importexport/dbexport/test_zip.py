"""Tests for aiida.tools.importexport.dbexport.zip"""
import os

from aiida.common import json
from aiida.tools.importexport.dbexport.zip import ZipFolder


def test_writing_bytes(temp_dir):
    """Verify exporting a Node with a bytes object in the repo is possible"""
    zip_file = os.path.join(temp_dir, 'test.zip')
    filename = 'data{}.json'

    data = 'aà'
    bytes_data = data.encode('utf-8')
    json_data = json.dumps(bytes_data)  # Will always return a string

    with ZipFolder(zip_file, mode='w') as folder:
        with folder.open(filename.format(0), mode='w') as fhandle:
            fhandle.write(data)

        with folder.open(filename.format(1), mode='wb') as fhandle:
            fhandle.write(bytes_data)

        with folder.open(filename.format(2), mode='w') as fhandle:
            fhandle.write(json_data)

        with folder.open(filename.format(3), mode='wb') as fhandle:
            fhandle.write(data)

        with folder.open(filename.format(4), mode='w') as fhandle:
            fhandle.write(bytes_data)

        with folder.open(filename.format(5), mode='wb') as fhandle:
            fhandle.write(json_data)
