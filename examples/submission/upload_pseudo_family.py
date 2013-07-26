#!/usr/bin/env python
import optparse
import sys
import os

from aiida.common.utils import load_django
load_django()
from aiida.orm.data.upf import upload_upf_family

#upload_upf_family('pz-rrkjus', 'pslib030-pz-rrkjus', "PSLibrary by Andrea Dal Corso, version 0.3.0; PZ functional, rrkjus")
#upload_upf_family('pbe-rrkjus', 'pslib030-pbe-rrkjus', "PSLibrary by Andrea Dal Corso, version 0.3.0; PBE functional, rrkjus")
#upload_upf_family('pbesol-rrkjus', 'pslib030-pbesol-rrkjus', "PSLibrary by Andrea Dal Corso, version 0.3.0; PBEsol functional, rrkjus")

parser = optparse.OptionParser()
parser.add_option("-f", "--folder", dest="folder",
                  help="Folder containing the UPF files", metavar="FOLDER")
parser.add_option("-n", "--name",
                  dest="name", help="Name of the pseudo family", metavar="NAME")
parser.add_option("-d", "--description",
                  dest="description", help="Name of the pseudo family", metavar="DESCRIPTION")

(options, args) = parser.parse_args()

if options.folder is None:
    print "You have to specify the folder"
    print ""
    parser.print_help()
    sys.exit(1)
if options.name is None:
    print "You have to specify the family name"
    print ""
    parser.print_help()
    sys.exit(1)

if not(os.path.isdir(options.folder)):
    print >> sys.stderr, '{} is not a valid directory'.format(options.folder)
    sys.exit(1)

list_files = sorted([i for i in os.listdir(options.folder) if i.lower().endswith('.upf')])
if not list_files:
    print >> sys.stderr, '{} does not contain any UPF file'.format(options.folder)
    sys.exit(1)

print "The following files are going to be added to the DB:"
for f in list_files:
    print "*", f
print "in a group with name '{}'".format(options.name)

desc = options.description
if desc is None:
    desc = ""

if desc:
    print "and description:"
    print desc
else:
    print "and you did not specify any description."

print "Is this OK? Press [Enter] to continue, or [Ctrl]+C to stop now."
raw_input()

upload_upf_family(options.folder, options.name, desc)

    
