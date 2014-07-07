#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = "Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aiida.djsite.settings.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
