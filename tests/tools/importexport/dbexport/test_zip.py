# -*- coding: utf-8 -*-
"""Tests for aiida.tools.importexport.dbexport.zip"""
import os
import zipfile

import pytest

from aiida.common import json
from aiida.common.warnings import AiidaWarning
from aiida.tools.importexport.dbexport.zip import ZipFolder


def test_writing_text(temp_dir):
    """Verify writing `str` is possible"""
    zip_file = os.path.join(temp_dir, 'test.zip')
    filename = 'data{}.json'

    data = 'aà'
    bytes_data = data.encode('utf-8')
    json_data = json.dumps(bytes_data)  # Will always return a string

    assert data != bytes_data
    assert isinstance(json_data, str)

    with ZipFolder(zip_file, mode='w') as folder:
        with folder.open(filename.format(0), mode='w') as fhandle:
            fhandle.write(json_data)

        with pytest.warns(AiidaWarning, match='encoding or "b" in mode has no effect for ZipFolder'):
            with folder.open(filename.format(1), mode='wb') as fhandle:
                fhandle.write(json_data)

    zipfile.ZipFile(zip_file, mode='r').extractall(path=temp_dir)

    with open(os.path.join(temp_dir, filename.format(0)), mode='r') as fhandle:
        extracted_data = fhandle.read()

    assert extracted_data == json_data

    with open(os.path.join(temp_dir, filename.format(1)), mode='r') as fhandle:
        extracted_data = fhandle.read()

    assert extracted_data == json_data


def test_writing_utf_bytes(temp_dir):
    """Verify writing `bytes` in UTF-8 is possible"""
    zip_file = os.path.join(temp_dir, 'test.zip')
    filename = 'data{}.json'

    data = 'aà'
    bytes_data = data.encode('utf-8')

    assert data != bytes_data

    with ZipFolder(zip_file, mode='w') as folder:
        with pytest.warns(AiidaWarning, match='encoding or "b" in mode has no effect for ZipFolder'):
            with folder.open(filename.format(0), mode='wb') as fhandle:
                fhandle.write(bytes_data)

        with folder.open(filename.format(1), mode='w') as fhandle:
            fhandle.write(bytes_data)

    zipfile.ZipFile(zip_file, mode='r').extractall(path=temp_dir)

    with open(os.path.join(temp_dir, filename.format(0)), mode='rb') as fhandle:
        extracted_data = fhandle.read()

    assert extracted_data == bytes_data
    assert extracted_data.decode('utf-8') == data

    with open(os.path.join(temp_dir, filename.format(1)), mode='rb') as fhandle:
        extracted_data = fhandle.read()

    assert extracted_data == bytes_data
    assert extracted_data.decode('utf-8') == data


def test_writing_non_utf_bytes(temp_dir):
    """Check ZipFolder can handle `bytes` other than UTF-8"""
    zip_file = os.path.join(temp_dir, 'test.zip')
    filename = 'data.json'

    data = 'aà'
    latin_data = data.encode('latin-1')
    unicode_data = data.encode('utf-8')

    assert latin_data != unicode_data

    with ZipFolder(zip_file, mode='w') as folder:
        with pytest.warns(AiidaWarning, match='encoding or "b" in mode has no effect for ZipFolder'):
            with folder.open(filename, mode='wb', encoding='latin-1') as fhandle:
                fhandle.write(latin_data)

    zipfile.ZipFile(zip_file, mode='r').extractall(path=temp_dir)
    with open(os.path.join(temp_dir, filename), mode='rb') as fhandle:
        extracted_data = fhandle.read()

    assert extracted_data == latin_data
    assert str(extracted_data.decode('latin-1')) == data
