###########################
Developer's Guide For AiiDA
###########################

Commits
+++++++

Before committing, **always** run::
  
  verdi developertest
  
to be sure that your modifications did not introduce any new bugs in existing
code. Remember to do it even if you believe your modification to be small - 
the tests run pretty fast!

Tests
+++++

For any new feature that you add/modify, write a test for it! This is extremely
important to have the project last and be as bug-proof as possible.

Remember to make unit tests as atomic as possible, and to document them so that
other developers can understand why you wrote that test, in case it should fail
after some modification.

Remember in best codes actually the `tests are written even before writing the
actual code`_, because this helps in having a clear API. 

.. _tests are written even before writing the actual code: http://it.wikipedia.org/wiki/Test_Driven_Development

Python style
++++++++++++
When writing python code, a more than reasonable guideline is given by
the Google python styleguide
http://google-styleguide.googlecode.com/svn/trunk/pyguide.html.
The documentation should be written consistently in the style of
sphinx.

And more generally, write verbose! Will you remember
after a month why you had to write that check on that line? (Hint: no)
Write comments!

South migrations: quick tutorial
++++++++++++++++++++++++++++++++
When changing the database schema (that should happen rarely, we hope),
we use Django South to manage the migrations.

First migration
---------------

The preliminary setup is not needed, since South is already present
in the ``requirements.py`` file and is already active in the
``aiida.djsite.settings.settings`` module.

To manage migrations, we have to use the original Django ``manage.py`` file,
that is present inside ``aiida/djsite/manage.py``.

For the very first migration,  run::
  
  ./manage.py schemamigration aida.djsite.main --initial

and then immediately apply this migration using a fake migration (since
you already have the database in place)::

  ./manage.py migrate aida.djsite.main 0001 --fake

.. note:: The
   previous command, or more specifically::

     ./manage.py migrate aida.djsite.main 0001 --fake

   has to be run by all people that already had a working database, in 
   order to tell South that we are now at version ``0001`` of the migration
   history, and this did not require any actual change to the database.

   When instead starting the installation from scratch, this step is not
   required because the first migration will create all needed tables.


Creating a schema migration
---------------------------

Addition or removal of fields
.............................

If you just want to add or remove a field, start by modifying the ``models.py``
file. After saving it, run::

   ./manage.py schemamigration aiida.djsite.db --auto

If the fields that you added (or removed) did not provide a default value,
South will ask for one. Provide a value, and then possibly manually modify
the generated ``.py`` file inside ``aiida/aiida/djsite/db/migrations``.

When you are happy with the migration, run::

  ./manage.py migrate aiida.djsite.db 

to bring your database to the most recent version. If you want to move to a specific version, add the version number, e.g. to go to the third migration, use::

  ./manage.py migrate aiida.djsite.db 0003

.. note:: It is very important to do a single commit with the code modifications
  together with the migration, and then immediately inform other users and
  developers that run ``git pull`` to apply the migration. To do this cleanly,
  one has to use the following sequence of commands::
    
    verdi daemon stop
    git pull

    ## ONLY FOR THE VERY FIRST MIGRATION #############
    # cd aiida/djsite
    # ./manage.py migrate aida.djsite.main 0001 --fake
    ##################################################

    verdi syncdb --migrate
    verdi daemon start 

Renaming of a field
...................
If you want to rename a field, as the first step rename the field in the
``models.py`` file. Then, run::

  ./manage.py schemamigration aiida.djsite.db [workflow_fields_rename] --auto

(the part in square brackets is optional, and is the migration title; if you
don't specify it, it will be automatically generated).

If the field that you are renaming did not have default values, South will ask
to provide them. Just provide any valid value (we will remove it later).

Then, edit the file that was generated, using e.g.::

  emacs db/migrations/0003_workflow_fields_rename.py

In the ``forward()`` (and similarly in the ``backward()``) methods, 
you will find a ``db.delete_column(TABLENAME, OLDNAME)`` call for the
old field, and a ``db.add_column(TABLENAME, NEWNAME, other_properties)``
call for the new field. Remove these lines and replace them with the following
command::

  db.rename_column(TABLENAME, OLDNAME, NEWNAME)

in the ``forward()`` method and with::

  db.rename_column(TABLENAME, NEWNAME, OLDNAME)

in the ``backward()`` method (to allow to do a backward migration).

.. note:: use the ``TABLENAME``, ``OLDNAME`` and ``NEWNAME`` from the lines
  automatically generated by South in order to avoid errors.

Data migrations
...............

If you do not want to edit the schema, but just do a data migration (e.g. 
because you want to change the internal way of representing specific data), 
you can do a **data migration**.

Start by creating an empty migration::

  ./manage.py schemamigration aiida.djsite.db TITLEOFTHEMIGRATION --empty

Then, edit the just created migration file inside 
``aiida/aiida/djsite/db/migrations`` and define the ``forward()`` and
``backward()`` functions.

Use the tutorial here: 
http://south.readthedocs.org/en/latest/tutorial/part3.html#data-migrations
to know how it works. 

.. note:: If you are making a data-migration only, without any schema migration,
  add within the migration class a::

    no_dry_run = True

  (or wrap your code in a ``if not db.dry_run:`` block; see for instance
  http://south.aeracode.org/wiki/Tutorial3 for some comments.
  

Finally, apply your modifications as usual::

  ./manage.py migrate aiida.djsite.db 
