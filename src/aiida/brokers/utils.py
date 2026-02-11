"""Shared utilities for message brokers."""

from __future__ import annotations

import uuid
from functools import partial

import yaml

__all__ = ('YAML_DECODER', 'YAML_ENCODER', 'AiidaYamlLoader')


class AiidaYamlLoader(yaml.FullLoader):
    """Custom YAML loader that can deserialize Python UUIDs.

    Extends FullLoader to handle the !!python/object:uuid.UUID tag that
    yaml.dump produces when serializing UUID objects. This is needed because
    FullLoader (for security reasons) cannot deserialize arbitrary Python objects.

    This loader only adds support for UUIDs, which are commonly used as process
    identifiers in AiiDA and plumpy.
    """

    pass


def _uuid_constructor(loader: yaml.Loader, node: yaml.MappingNode) -> uuid.UUID:
    """Construct a UUID from the YAML python/object representation.

    :param loader: The YAML loader instance
    :param node: The YAML node containing the UUID data
    :return: The reconstructed UUID object
    """
    mapping = loader.construct_mapping(node)
    return uuid.UUID(int=mapping['int'])


# Register the UUID constructor
AiidaYamlLoader.add_constructor('tag:yaml.org,2002:python/object:uuid.UUID', _uuid_constructor)

# Default encoder and decoder for broker messages
YAML_ENCODER = yaml.dump
YAML_DECODER = partial(yaml.load, Loader=AiidaYamlLoader)
