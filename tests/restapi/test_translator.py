# -*- coding: utf-8 -*-
"""Tests for the `aiida.restapi.translator` module."""
# pylint: disable=invalid-name
from aiida.restapi.translator.nodes.node import NodeTranslator
from aiida.orm import Data


def test_get_all_download_formats():
    """Test the `get_all_download_formats` method."""
    NodeTranslator.get_all_download_formats()


def test_get_all_download_formats_missing_get_export_formats(monkeypatch):
    """Test `get_all_download_formats` does not except if a `Data` class does not implement `get_export_formats`."""
    monkeypatch.delattr(Data, 'get_export_formats')
    NodeTranslator.get_all_download_formats()
