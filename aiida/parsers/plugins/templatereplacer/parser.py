# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Parser for the `TemplatereplacerCalculation` calculation job."""
import os

from aiida.orm import Dict
from aiida.parsers.parser import Parser


class TemplatereplacerParser(Parser):
    """Parser for the `TemplatereplacerCalculation` calculation job."""

    def parse(self, **kwargs):
        """Parse the contents of the output files retrieved in the `FolderData`."""
        output_folder = self.retrieved
        template = self.node.inputs.template.get_dict()

        try:
            output_file = template['output_file_name']
        except KeyError:
            return self.exit_codes.ERROR_NO_OUTPUT_FILE_NAME_DEFINED

        try:
            with output_folder.base.repository.open(output_file, 'r') as handle:
                result = handle.read()
        except (OSError, IOError):
            self.logger.exception(f'unable to parse the output for CalcJobNode<{self.node.pk}>')
            return self.exit_codes.ERROR_READING_OUTPUT_FILE

        output_dict: dict = {'value': result, 'retrieved_temporary_files': []}
        retrieve_temporary_files = template.get('retrieve_temporary_files', None)

        # If the 'retrieve_temporary_files' key was set in the template input node, we expect a temporary directory
        # to have been passed in the keyword arguments under the name `retrieved_temporary_folder`.
        if retrieve_temporary_files is not None:
            try:
                retrieved_temporary_folder = kwargs['retrieved_temporary_folder']
            except KeyError:
                return self.exit_codes.ERROR_NO_TEMPORARY_RETRIEVED_FOLDER

            for retrieved_file in retrieve_temporary_files:

                file_path = os.path.join(retrieved_temporary_folder, retrieved_file)

                if not os.path.isfile(file_path):
                    self.logger.error(
                        'the file {} was not found in the temporary retrieved folder {}'.format(
                            retrieved_file, retrieved_temporary_folder
                        )
                    )
                    return self.exit_codes.ERROR_READING_TEMPORARY_RETRIEVED_FILE

                with open(file_path, 'r', encoding='utf8') as handle:
                    parsed_value = handle.read().strip()

                # We always strip the content of the file from whitespace to simplify testing for expected output
                output_dict['retrieved_temporary_files'].append((retrieved_file, parsed_value))

        label = self.node.process_class.spec().default_output_node  # type: ignore
        self.out(label, Dict(dict=output_dict))

        return
