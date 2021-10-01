# -*- coding: utf-8 -*-
"""Abstract utility class that helps to import calculation jobs completed outside of AiiDA."""
from abc import abstractmethod
from typing import Dict, Union

from aiida.orm import Node, RemoteData

__all__ = ('CalcJobImporter',)


class CalcJobImporter:

    @staticmethod
    @abstractmethod
    def parse_remote_data(remote_data: RemoteData, **kwargs) -> Dict[str, Union[Node, Dict]]:
        """Parse the input nodes from the files in the provided ``RemoteData``.

        :param remote_data: the remote data node containing the raw input files.
        :param kwargs: additional keyword arguments to control the parsing process.
        :returns: a dictionary with the parsed inputs nodes that match the input spec of the associated ``CalcJob``.
        """
