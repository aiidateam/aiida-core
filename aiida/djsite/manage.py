#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aiida.djsite.settings.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
