# -*- coding: utf-8 -*-
"""
Plugin to create input for scripts from cod-tools package.
This plugin is in the development stage. Andrius Merkys, 2014-10-29
"""
import os
import shutil

from aiida.orm.calculation.job.codtools.ciffilter import CiffilterCalculation
from aiida.orm.data.cif import CifData
from aiida.orm.data.parameter import ParameterData
from aiida.common.datastructures import CalcInfo
from aiida.common.exceptions import InputValidationError
from aiida.common.utils import classproperty

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi"

class CifsplitprimitiveCalculation(CiffilterCalculation):
    """
    Specific input plugin for cif_cell_contents from cod-tools package.
    """

    def _init_internal_params(self):
        super(CifsplitprimitiveCalculation, self)._init_internal_params()

        self._default_parser = 'codtools.cifsplitprimitive'

        self._SPLIT_DIR = 'split'

    def _prepare_for_submission(self,tempfolder,inputdict):
        calcinfo = super(CifsplitprimitiveCalculation,
                         self)._prepare_for_submission(tempfolder,inputdict)

        split_dir = tempfolder.get_abs_path(self._SPLIT_DIR)
        os.mkdir(split_dir)

        calcinfo.cmdline_params.extend([ '--output-dir', self._SPLIT_DIR ])
        calcinfo.retrieve_list.append(self._SPLIT_DIR)

        return calcinfo
