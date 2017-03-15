# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import re
import numpy as np
from qeinputparser import (
        QeInputFile,parse_namelists,parse_atomic_positions,
        parse_atomic_species,parse_cell_parameters, RE_FLAGS )
from aiida.orm.data.array.kpoints import KpointsData
from aiida.common.exceptions import ParsingError


from qeinputparser import (
        QeInputFile,parse_namelists,parse_atomic_positions,
        parse_atomic_species,parse_cell_parameters, RE_FLAGS )

class CpInputFile(QeInputFile):
    def __init__(self, pwinput):
        """
        Parse inputs's namelist and cards to create attributes of the info.

        :param pwinput:
            Any one of the following

                * A string of the (existing) absolute path to the pwinput file.
                * A single string containing the pwinput file's text.
                * A list of strings, with the lines of the file as the elements.
                * A file object. (It will be opened, if it isn't already.)

        :raises IOError: if ``pwinput`` is a file and there is a problem reading
            the file.
        :raises TypeError: if ``pwinput`` is a list containing any non-string
            element(s).
        :raises aiida.common.exceptions.ParsingError: if there are issues
            parsing the pwinput.
        """

        super(CpInputFile, self).__init__(pwinput)

        # Parse the namelists.
        self.namelists = parse_namelists(self.input_txt)
        # Parse the ATOMIC_POSITIONS card.
        self.atomic_positions = parse_atomic_positions(self.input_txt)
        # Parse the CELL_PARAMETERS card.
        self.cell_parameters = parse_cell_parameters(self.input_txt)
        # Parse the ATOMIC_SPECIES card.
        self.atomic_species = parse_atomic_species(self.input_txt)
    
