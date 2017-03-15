# -*- coding: utf-8 -*-

from distutils.version import StrictVersion
from aiida.orm.data.structure import has_pymatgen, get_pymatgen_version


def skip_condition():
    return not (has_pymatgen() and
                StrictVersion(get_pymatgen_version()) == StrictVersion('4.5.3'))