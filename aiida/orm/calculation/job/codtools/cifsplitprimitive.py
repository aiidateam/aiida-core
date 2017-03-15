# -*- coding: utf-8 -*-

from aiida.orm.calculation.job.codtools.ciffilter import CiffilterCalculation



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
