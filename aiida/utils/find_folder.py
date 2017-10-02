#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import itertools
try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

def find_path(root, dir_name):
    path = Path(os.path.abspath(root))
    for p in itertools.chain([path], path.parents):
        directory = p / dir_name
        if directory.is_dir():
            return directory
    raise OSError('No directory found')
