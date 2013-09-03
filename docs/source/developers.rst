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
