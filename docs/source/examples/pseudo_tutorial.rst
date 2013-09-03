.. _my-ref-to-pseudo-tutorial:

Pseudopotential families tutorial
=================================

As you might have seen in the previous ``PWscf`` tutorial, the procedure of attaching a pseudopotential file to each atomic species could be a bit tedious.
In many situations, you will not produce a different pseudopotential file for every calculation you do. More likely, when you start a project you will stick to a pseudopotential file for as long as possible. 
Moreover, in a high-throughput calculation, you will like to do calculation over several elements keeping the same functional.
That's also part of the reason why there are several projects (like `PSLibrary <http://qe-forge.org/gf/project/pslibrary/frs/>`_ or `GBRV <http://www.physics.rutgers.edu/gbrv/>`_ to name a few), that intend to develop a set of pseudopotentials that covers most of the periodic table for different functionals.

That's why we introduced the pseudopotential families. You can think at them as for a group of pseudopotentials that are useful to pack together.
Let's say for example that I want to create a family of LDA Ultrasoft pseudos.
As the first step, you need to get all the pseudopotential files in a single folder.
(For your convenience, it is useful to use a common name for your files, for example with a structure like 'Element.a-short-description.UPF')
Then, a minimal script to load them consists in the following::

  from aiida.common.utils import load_django
  load_django()
  from aiida.orm.data.upf import upload_upf_family

  upload_upf_family('absolute/path/to/folder', 'family_name', 'a description')

The first three lines consists in loading the needed modules of AiiDA.
The only execution line consists in calling the function upload_upf_family.
It accepts three arguments: first the **Absolute** path to the folder where you put the pseudopotentials, second the family name that you will always use in the future to load these files, lastly you can put a description of what this family is. (Suggestion: in two months you will forget what that family is there for if you don't put a meaningful description!)

And that's it. Now you can attach pseudopotentials to a calculation in a way like this::

  calculation.use_pseudo_from_family('pseudo_family_name')

And AiiDA will match the element with the pseudopotential of that family you just uploaded.

The only catch to let this method work, is that you need to use meaningful names for the atomic species.
If you name an atomic species `X`, it's difficult to guess if you want Carbon rather than Uranium there!
Therefore, you must stick to existing element names. 
(Also, we decided not to support elements heavier than Lawrencium...)

Script to execute
-----------------

Here is a script to upload a pseudopotential family.
Its usage is self-documented, help appears when you run it with the option ``-h``.

::

   #!/usr/bin/env python
   import optparse
   import sys
   import os
   
   from aiida.common.utils import load_django
   load_django()
   from aiida.orm.data.upf import upload_upf_family

   parser = optparse.OptionParser()
   parser.add_option("-f", "--folder", dest="folder",
                     help="Folder containing the UPF files", metavar="FOLDER")
   parser.add_option("-n", "--name",dest="name", 
                     help="Name of the pseudo family", metavar="NAME")
   parser.add_option("-d", "--description", dest="description", 
                     help="Name of the pseudo family", metavar="DESCRIPTION")

   (options, args) = parser.parse_args()

   if options.folder is None:
       print "You have to specify the folder\n"
       parser.print_help()
       sys.exit(1)
   if options.name is None:
       print "You have to specify the family name\n"
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

