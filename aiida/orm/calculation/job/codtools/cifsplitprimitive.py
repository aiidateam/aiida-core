# -*- coding: utf-8 -*-

from aiida.orm.calculation.job.codtools.ciffilter import CiffilterCalculation

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0.1"
__authors__ = "The AiiDA team."


class CifsplitprimitiveCalculation(CiffilterCalculation):
    """
    Specific input plugin for cif_split_primitive from cod-tools package.
    """

    def _init_internal_params(self):
        super(CifsplitprimitiveCalculation, self)._init_internal_params()

        self._default_parser = 'codtools.cifsplitprimitive'

        self._SPLIT_DIR = 'split'

    def _prepare_for_submission(self, tempfolder, inputdict):
        import os

        calcinfo = super(CifsplitprimitiveCalculation,
                         self)._prepare_for_submission(tempfolder, inputdict)

        split_dir = tempfolder.get_abs_path(self._SPLIT_DIR)
        os.mkdir(split_dir)

        calcinfo.codes_info[0].cmdline_params.extend(['--output-dir', self._SPLIT_DIR])
        calcinfo.retrieve_list.append(self._SPLIT_DIR)
        
        return calcinfo
