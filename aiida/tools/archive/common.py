# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Shared resources for the archive."""
from html.parser import HTMLParser
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Type
import urllib.parse
import urllib.request

from aiida.orm import AuthInfo, Comment, Computer, Entity, Group, Log, Node, User
from aiida.orm.entities import EntityTypes

# Mapping from entity names to AiiDA classes
entity_type_to_orm: Dict[EntityTypes, Type[Entity]] = {
    EntityTypes.AUTHINFO: AuthInfo,
    EntityTypes.GROUP: Group,
    EntityTypes.COMPUTER: Computer,
    EntityTypes.USER: User,
    EntityTypes.LOG: Log,
    EntityTypes.NODE: Node,
    EntityTypes.COMMENT: Comment,
}


def batch_iter(iterable: Iterable[Any],
               size: int,
               transform: Optional[Callable[[Any], Any]] = None) -> Iterable[Tuple[int, List[Any]]]:
    """Yield an iterable in batches of a set number of items.

    Note, the final yield may be less than this size.

    :param transform: a transform to apply to each item
    :returns: (number of items, list of items)
    """
    transform = transform or (lambda x: x)
    current = []
    length = 0
    for item in iterable:
        current.append(transform(item))
        length += 1
        if length >= size:
            yield length, current
            current = []
            length = 0
    if current:
        yield length, current


class HTMLGetLinksParser(HTMLParser):
    """
    If a filter_extension is passed, only links with extension matching
    the given one will be returned.
    """

    # pylint: disable=abstract-method

    def __init__(self, filter_extension=None):
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
    with urllib.request.urlopen(url) as request:
        parser = HTMLGetLinksParser(filter_extension='aiida')
        parser.feed(request.read().decode('utf8'))

    return_urls = []

    for link in parser.get_links():
        return_urls.append(urllib.parse.urljoin(request.geturl(), link))

    return return_urls
