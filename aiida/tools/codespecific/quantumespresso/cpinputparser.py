import re
import numpy as np
from qeinputparser import (
        QeInputFile,parse_namelists,parse_atomic_positions,
        parse_atomic_species,parse_cell_parameters, RE_FLAGS )
from aiida.orm.data.array.kpoints import KpointsData
from aiida.common.exceptions import ParsingError



class CpInputFile(QeInputFile):
    pass
    
