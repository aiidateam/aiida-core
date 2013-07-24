#!/usr/bin/env python
import sys
from aiida.orm import Calculation
import json

from aiida.common.utils import load_django

def string_shorten(string, length):
  ellipsis = " [...]"
  if length < len(ellipsis):
    raise ValueError("length must be >= {}".format(len(ellipsis)))

  if len(string) <= length:
    return string
  else:
    return string[:length-len(ellipsis)] + ellipsis

load_django()

calcs = []
if not sys.argv[1:]:
  print >> sys.stderr, "pass at least on pk"
  sys.exit(1)
for i in sys.argv[1:]:
  try:
    calcs.append(int(i))
  except ValueError:
    print >> sys.stderr, "Ignoring invalid pk={}".format(i)

for pk in calcs:
  c = Calculation.get_subclass_from_pk(pk)
  print '#'*20
  print '### CALC pk={}'.format(pk), c.__class__.__name__
  print '#'*20

  print "*** INPUTS:"
  for label, obj in c.get_inputs(also_labels=True):
      print '  {} -> {}[{}]'.format(label, type(obj).__name__,obj.pk),
      if type(obj).__name__ == 'RemoteData':
          print obj.get_remote_machine(), obj.get_remote_path()
      else:
          print ""
  print "*** OUTPUTS:"
  for label, obj in c.get_outputs(also_labels=True):
      print '  {} -> {}[{}]'.format(label, type(obj).__name__,obj.pk),
      if type(obj).__name__ == 'RemoteData':
          print obj.get_remote_machine(), obj.get_remote_path()
      elif type(obj).__name__ == 'FolderData':
          #          print list(o for o in dir(obj) if 'list' in o)#.list_folder_content()
          print obj.current_folder.abspath
          files = obj.get_path_list()
          print files
          if 'aiida.out' in files:
            print r"   / BEGIN Last 10 lines of the output file"
            print "\n".join("   | {}".format(l.strip()) for l in open(obj.get_abs_path('aiida.out')).readlines()[-10:])
            print r"   \ END of first file"
          else:
            print r"   / BEGIN Last 10 lines of the output file"
            print "\n".join("   | {}".format(l.strip()) for l in open(obj.get_abs_path(obj.get_path_list()[0])).readlines()[-10:])
            print r"   \ END of first file"
      elif type(obj).__name__ == 'ParameterData':
          print ""
          for k, v in obj.iterattrs():
              print "    {} -> {}".format(k.ljust(10), 
                                          string_shorten(json.dumps(v),50))
      else:
          print ""

  print ""
