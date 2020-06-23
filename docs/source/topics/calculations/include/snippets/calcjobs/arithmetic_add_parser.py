# -*- coding: utf-8 -*-
from aiida.common import exceptions
from aiida.orm import Int
from aiida.parsers.parser import Parser


class ArithmeticAddParser(Parser):

    def parse(self, **kwargs):
        """Parse the contents of the output files retrieved in the `FolderData`."""
        try:
            output_folder = self.retrieved
        except exceptions.NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_FOLDER

        try:
            with output_folder.open(self.node.get_option('output_filename'), 'r') as handle:
                result = self.parse_stdout(handle)
        except (OSError, IOError):
            return self.exit_codes.ERROR_READING_OUTPUT_FILE

        if result is None:
            return self.exit_codes.ERROR_INVALID_OUTPUT

        self.out('sum', Int(result))

    @staticmethod
    def parse_stdout(filelike):
        """Parse the sum from the output of the ArithmeticAddcalculation written to standard out

        :param filelike: filelike object containing the output
        :returns: the sum
        """
        try:
            result = int(filelike.read())
        except ValueError:
            result = None

        return result
