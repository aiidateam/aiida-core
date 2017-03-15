# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.parsers.parser import Parser



class BasenwcParser(Parser):
    def parse_with_retrieved(self, retrieved):
        """
        Receives in input a dictionary of retrieved nodes.
        Does all the logic here.
        """
        from aiida.common.exceptions import InvalidOperation
        import os

        output_path = None
        error_path = None
        try:
            output_path, error_path = self._fetch_output_files(retrieved)
        except InvalidOperation:
            raise
        except IOError as e:
            self.logger.error(e.message)
            return False, ()

        if output_path is None and error_path is None:
            self.logger.error("No output files found")
            return False, ()

        return True, self._get_output_nodes(output_path, error_path)

    def _fetch_output_files(self, retrieved):
        """
        Checks the output folder for standard output and standard error
        files, returns their absolute paths on success.

        :param retrieved: A dictionary of retrieved nodes, as obtained from the
          parser.
        """
        from aiida.common.datastructures import calc_states
        from aiida.common.exceptions import InvalidOperation
        import os

        # check in order not to overwrite anything
        #         state = self._calc.get_state()
        #         if state != calc_states.PARSING:
        #             raise InvalidOperation("Calculation not in {} state"
        #                                    .format(calc_states.PARSING) )

        # Check that the retrieved folder is there
        try:
            out_folder = retrieved[self._calc._get_linkname_retrieved()]
        except KeyError:
            raise IOError("No retrieved folder found")

        list_of_files = out_folder.get_folder_list()

        output_path = None
        error_path = None

        if self._calc._DEFAULT_OUTPUT_FILE in list_of_files:
            output_path = os.path.join(out_folder.get_abs_path('.'),
                                       self._calc._DEFAULT_OUTPUT_FILE)
        if self._calc._DEFAULT_ERROR_FILE in list_of_files:
            error_path = os.path.join(out_folder.get_abs_path('.'),
                                      self._calc._DEFAULT_ERROR_FILE)

        return output_path, error_path
