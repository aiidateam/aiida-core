#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This function, when called, will migrate from the schema version 1.0.0 to
the schema version 1.0.1.

Schema changes: 
Added the JobCalculation subclass of Calculation, and moved all plugins
as subclasses of JobCalculation. Migration will convert all type strings
from 'calculation.Calculation.' to 'calculation.job.JobCalculation.'
and 'calculation.ANYTHINGELSE' to 'calculation.job.ANYTHINGELSE'.
"""

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.3.0"

prefix = 'calculation.'
prefix_len = len(prefix)

def get_new_type_string(oldstring):
    if not oldstring.startswith(prefix):
        raise ValueError("Invalid type string {}".format(oldstring))
    if oldstring == "calculation.Calculation.":
        return "calculation.job.JobCalculation."
    else:
        if oldstring.startswith("calculation.job."):
            # This should not happen! Probably a failed migration?
            # I assume that it is already migrated
            return oldstring
        else:
            return "calculation.job.{}".format(oldstring[prefix_len:])

# define the origin and destination version strings
version_from = "1.0.0"
version_to = "1.0.1"
# Print a message every XX calculations to have the user aware of what's
# going on
print_every = 100
def migrate(process):
    """
    Migrate the DB from v. 1.0.0 to v.1.0.1.
    """
    # Load the DB without performing the version check
    from aiida.djsite.utils import (_load_dbenv_noschemacheck,
                                   get_db_schema_version, set_db_schema_version)
    _load_dbenv_noschemacheck(process=process)

    from django.db import transaction
    from aiida.djsite.db import models
    
    # Check if the starting version is the expected one
    current_version = get_db_schema_version()
    if current_version != version_from:
        raise ValueError("This migration can only be used to migrate from "
                         "version {}, current version is instead {}".format(
                          version_from,current_version))

    # Do everything in a transaction
    with transaction.commit_on_success():
        counter = 0
        old_calcs = models.DbNode.objects.filter(type__startswith='calculation.')
        tot_num = old_calcs.count()
        print "Running migration on {} calculations...".format(tot_num)
        for c in old_calcs:
            new_type = get_new_type_string(c.type)
            c.type = new_type
            c.save()
            counter+=1
            if counter%print_every == 0:
                print "{}/{} done.".format(counter, tot_num)
        set_db_schema_version(version_to)
    print "Migration succeeded on {} calculations!".format(tot_num)
    print "New DB version: {}".format(version_to)

if __name__ == "__main__":
    import sys
    try:
        process = sys.argv[1]
    except IndexError:
        process = None
    
    migrate(process=process)
    
    
