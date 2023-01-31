# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# Warning: this implementation is used directly in the documentation as a literal-include, which means that if any part
# of this code is changed, the snippets in the file `docs/source/howto/codes.rst` have to be checked for consistency.
# mypy: disable_error_code=arg-type
"""Parser for an `ArithmeticAddCalculation` job."""
from aiida.parsers.parser import Parser


class ArithmeticAddParser(Parser):
    """Parser for an `ArithmeticAddCalculation` job."""

    def parse(self, **kwargs):
        """Parse the contents of the output files stored in the `retrieved` output node."""
        from aiida.orm import Int

        try:
            with self.retrieved.base.repository.open(self.node.get_option('output_filename'), 'r') as handle:
                result = int(handle.read())
        except OSError:
            return self.exit_codes.ERROR_READING_OUTPUT_FILE
        except ValueError:
            return self.exit_codes.ERROR_INVALID_OUTPUT

        self.out('sum', Int(result))

        if result < 0:
            return self.exit_codes.ERROR_NEGATIVE_NUMBER


class SimpleArithmeticAddParser(Parser):
    """Simple parser for an `ArithmeticAddCalculation` job (for demonstration purposes only)."""

    def parse(self, **kwargs):
        """Parse the contents of the output files stored in the `retrieved` output node."""
        from aiida.orm import Int

        output_folder = self.retrieved

        with output_folder.base.repository.open(self.node.get_option('output_filename'), 'r') as handle:
            result = int(handle.read())

        self.out('sum', Int(result))
