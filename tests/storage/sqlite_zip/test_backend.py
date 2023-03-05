# -*- coding: utf-8 -*-
"""Tests for :mod:`aiida.storage.sqlite_zip.backend.SqliteZipBackend`."""
from aiida.storage.sqlite_zip.backend import SqliteZipBackend
from aiida.storage.sqlite_zip.migrator import validate_storage


def test_initialise(tmp_path, aiida_caplog):
    """Test :meth:`aiida.storage.sqlite_zip.backend.SqliteZipBackend.initialise`."""
    filepath_archive = tmp_path / 'archive.zip'
    profile = SqliteZipBackend.create_profile(filepath_archive)
    initialised = SqliteZipBackend.initialise(profile)
    assert initialised

    assert filepath_archive.exists()
    validate_storage(filepath_archive)
    assert any('Initialising a new SqliteZipBackend' in record.message for record in aiida_caplog.records)


def test_initialise_reset_true(tmp_path, aiida_caplog):
    """Test :meth:`aiida.storage.sqlite_zip.backend.SqliteZipBackend.initialise` with ``reset=True``."""
    filepath_archive = tmp_path / 'archive.zip'
    filepath_archive.touch()
    profile = SqliteZipBackend.create_profile(filepath_archive)
    initialised = SqliteZipBackend.initialise(profile, reset=True)
    assert initialised

    assert filepath_archive.exists()
    validate_storage(filepath_archive)
    assert any('Resetting existing SqliteZipBackend' in record.message for record in aiida_caplog.records)


def test_initialise_reset_false(tmp_path, aiida_caplog):
    """Test :meth:`aiida.storage.sqlite_zip.backend.SqliteZipBackend.initialise` with ``reset=True``."""
    filepath_archive = tmp_path / 'archive.zip'

    # Initialise the archive
    profile = SqliteZipBackend.create_profile(filepath_archive)
    initialised = SqliteZipBackend.initialise(profile)
    assert initialised

    # Initialise it again with ``reset=False`
    initialised = SqliteZipBackend.initialise(profile, reset=False)
    assert not initialised

    assert filepath_archive.exists()
    validate_storage(filepath_archive)
    assert any('Migrating existing SqliteZipBackend' in record.message for record in aiida_caplog.records)
