# -*- coding: utf-8 -*-
import os


def import_archive_fixture(filepath):
    """
    Import an archive fixture, which is an AiiDA export archive

    :param filepath: the relative path of the archive file within the fixture directory
    """
    from aiida.orm.importexport import import_data

    filepath_current = os.path.dirname(os.path.realpath(__file__))
    filepath_fixtures = os.path.join(filepath_current, os.pardir, 'fixtures')
    filepath_archive = os.path.join(filepath_fixtures, filepath)

    if not os.path.isfile(filepath_archive):
        raise ValueError('archive {} does not exist in the fixture directory {}'.format(filepath, filepath_fixtures))

    import_data(filepath_archive, silent=True)
