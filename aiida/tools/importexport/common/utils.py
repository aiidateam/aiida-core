# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""" Utility functions for import/export of AiiDA entities """
# pylint: disable=too-many-branches,too-many-return-statements,too-many-nested-blocks,too-many-locals
from html.parser import HTMLParser
import urllib.request
import urllib.parse

from aiida.tools.importexport.common.config import (
    NODE_ENTITY_NAME, GROUP_ENTITY_NAME, COMPUTER_ENTITY_NAME, USER_ENTITY_NAME, LOG_ENTITY_NAME, COMMENT_ENTITY_NAME
)


def schema_to_entity_names(class_string):
    """
    Mapping from classes path to entity names (used by the SQLA import/export)
    This could have been written much simpler if it is only for SQLA but there
    is an attempt the SQLA import/export code to be used for Django too.
    """
    if class_string is None:
        return None

    if class_string in ('aiida.backends.djsite.db.models.DbNode', 'aiida.backends.sqlalchemy.models.node.DbNode'):
        return NODE_ENTITY_NAME

    if class_string in ('aiida.backends.djsite.db.models.DbGroup', 'aiida.backends.sqlalchemy.models.group.DbGroup'):
        return GROUP_ENTITY_NAME

    if class_string in (
        'aiida.backends.djsite.db.models.DbComputer', 'aiida.backends.sqlalchemy.models.computer.DbComputer'
    ):
        return COMPUTER_ENTITY_NAME

    if class_string in ('aiida.backends.djsite.db.models.DbUser', 'aiida.backends.sqlalchemy.models.user.DbUser'):
        return USER_ENTITY_NAME

    if class_string in ('aiida.backends.djsite.db.models.DbLog', 'aiida.backends.sqlalchemy.models.log.DbLog'):
        return LOG_ENTITY_NAME

    if class_string in (
        'aiida.backends.djsite.db.models.DbComment', 'aiida.backends.sqlalchemy.models.comment.DbComment'
    ):
        return COMMENT_ENTITY_NAME


class HTMLGetLinksParser(HTMLParser):
    """
    If a filter_extension is passed, only links with extension matching
    the given one will be returned.
    """

    # pylint: disable=abstract-method

    def __init__(self, filter_extension=None):  # pylint: disable=super-on-old-class
        self.filter_extension = filter_extension
        self.links = []
        super().__init__()

    def handle_starttag(self, tag, attrs):
        """
        Store the urls encountered, if they match the request.
        """
        if tag == 'a':
            for key, value in attrs:
                if key == 'href':
                    if (self.filter_extension is None or value.endswith(f'.{self.filter_extension}')):
                        self.links.append(value)

    def get_links(self):
        """
        Return the links that were found during the parsing phase.
        """
        return self.links


def get_valid_import_links(url):
    """
    Open the given URL, parse the HTML and return a list of valid links where
    the link file has a .aiida extension.
    """
    request = urllib.request.urlopen(url)
    parser = HTMLGetLinksParser(filter_extension='aiida')
    parser.feed(request.read().decode('utf8'))

    return_urls = []

    for link in parser.get_links():
        return_urls.append(urllib.parse.urljoin(request.geturl(), link))

    return return_urls


def export_shard_uuid(uuid):
    """Sharding of the UUID for the import/export

    :param uuid: UUID to be sharded (v4)
    :type uuid: str

    :return: Sharded UUID as a subfolder path
    :rtype: str
    """
    import os

    return os.path.join(uuid[:2], uuid[2:4], uuid[4:])
