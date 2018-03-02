#!/usr/bin/env runaiida

import json
import sys

def main():
    from aiida.tools.dbimporters import DbImporterFactory

    database = 'mpds'
    importer_parameters = {}
    query_parameters = {
        'query': {
            'elements': 'Ti',
            'classes': 'binary',
            'props': 'atomic structure',
        },
        'collection': 'structures'
    }

    importer_class = DbImporterFactory(database)
    importer = importer_class(**importer_parameters)

    try:
        query_results = importer.query(**query_parameters)
    except BaseException as exception:
        print(exception)
        sys.exit(1)

    count = 0
    limit = 10
    print len(query_results)
    return

    for entry in query_results:
        cif = entry.get_cif_node()
        cif.store()
        print cif.pk
        count += 1
        if count > limit:
            return


if __name__ == '__main__':
    main()