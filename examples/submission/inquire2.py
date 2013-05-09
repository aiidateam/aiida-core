#!/usr/bin/env python
import sys
from aida.orm import Calculation
from aida.common.utils import load_django

load_django()

calcs = []
for i in sys.argv[1:]:
  try:
    calcs.append(int(i))
  except ValueError:
    print >> sys.stderr, "Ignoring invalid pk={}".format(i)

for pk in calcs:
  print '#'*20
  print '### CALC pk={}'.format(pk)
  print '#'*20

  c = Calculation.get_subclass_from_pk(pk)
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
          print obj.get_path_list()
          print r"   / BEGIN Content of first file"
          print "\n".join("   | {}".format(l.strip()) for l in open(obj.get_abs_path(obj.get_path_list()[0])).readlines())
          print r"   \ END Content of first file"
      else:
          print ""

  print ""
