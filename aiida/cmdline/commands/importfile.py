# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import sys

from aiida.backends.utils import load_dbenv
from aiida.cmdline.baseclass import VerdiCommand



class Import(VerdiCommand):
    """
    Import nodes and group of nodes

    This command allows to import nodes from file, for backup purposes or
    to share data with collaborators.
    """

    def run(self, *args):
        load_dbenv()

        import argparse
        import traceback
        import urllib2

        from aiida.common.folders import SandboxFolder
        from aiida.orm.importexport import get_valid_import_links, import_data_dj, import_data_sqla

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Import data in the DB.')
        parser.add_argument('-w', '--webpage', nargs='+', type=str,
                            dest='webpages', metavar='URL',
                            help="Download all URLs in the given HTTP web "
                                 "page with extension .aiida")
        parser.add_argument(nargs='*', type=str,
                            dest='files', metavar='URL_OR_PATH',
                            help="Import the given files or URLs")

        parsed_args = parser.parse_args(args)

        all_args = [] if parsed_args.files is None else parsed_args.files
        urls = []
        files = []
        for path in all_args:
            if path.startswith('http://') or path.startswith('https://'):
                urls.append(path)
            else:
                files.append(path)

        webpages = [] if parsed_args.webpages is None else parsed_args.webpages

        for webpage in webpages:
            try:
                print "**** Getting links from {}".format(webpage)
                found_urls = get_valid_import_links(webpage)
                print " `-> {} links found.".format(len(found_urls))
                urls += found_urls
            except Exception:
                traceback.print_exc()
                print ""
                print "> There has been an exception during the import of webpage"
                print "> {}".format(webpage)
                answer = raw_input("> Do you want to continue (c) or stop "
                                   "(S, default)? ")
                if answer.lower() == 'c':
                    continue
                else:
                    return

        if not (urls + files):
            print >> sys.stderr, ("Pass at least one file or URL from which "
                                  "you want to import data.")
            sys.exit(1)

        for filename in files:
            try:
                print "**** Importing file {}".format(filename)
                from aiida.backends.settings import BACKEND
                from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA
                if BACKEND == BACKEND_SQLA:
                    import_data_sqla(filename)
                elif BACKEND == BACKEND_DJANGO:
                    import_data_dj(filename)
            except Exception:
                traceback.print_exc()

                print ""
                print "> There has been an exception during the import of file"
                print "> {}".format(filename)
                answer = raw_input("> Do you want to continue (c) or stop "
                                   "(S, default)? ")
                if answer.lower() == 'c':
                    continue
                else:
                    return

        download_file_name = 'importfile.tar.gz'
        for url in urls:
            try:
                print "**** Downloading url {}".format(url)
                response = urllib2.urlopen(url)
                with SandboxFolder() as temp_download_folder:
                    temp_download_folder.create_file_from_filelike(
                        response, download_file_name)

                    print " `-> File downloaded. Importing it..."
                    import_data(temp_download_folder.get_abs_path(
                        download_file_name))
            except Exception:
                traceback.print_exc()

                print ""
                print "> There has been an exception during the import of url"
                print "> {}".format(url)
                answer = raw_input("> Do you want to continue (c) or stop "
                                   "(S, default)? ")
                if answer.lower() == 'c':
                    continue
                else:
                    return

    def complete(self, subargs_idx, subargs):
        return ""
