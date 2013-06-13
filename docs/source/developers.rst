##########################
Developer's Guide For AiiDA
##########################

DJsite
++++

All urls are defined in the urlconf file :mod:`aiida.djsite.main.urls`.  Most views
are found within :mod:`aiida.djsite.main.data.views` and :mod:`aiida.djsite.main.data.simple_views`.
The views within :mod:`aiida.djsite.main.data.views` use the `ModelAdmin` classes
from :mod:`aiida.djsite.main.data.myadmin`. These `ModelAdmin` derived classes
are heavily modified, so that we can use Django Admin tables,
javascript interfaces, changelist details, the infrastructure for the
filtered lists, action items, etc.

The html files for many views are found within the `templates`
directory. The directory `templates/admin` and its subdirectory
contain specific html files that are used by the heavily modified
`ModelAdmin` class based methods. The html files `base.html` and
`base_site.html` in `templates` contain the basic site. 

If you want to change the root aiida url, change the AiiDA_ROOT_URL
variable in `settings.py` in `aiida.djsite.settings` directory. Currently it is set
so that links like http://host/aiida/ work.

Python style
+++++++
When writing python code, a more than reasonable guideline is given by
the Google python styleguide
http://google-styleguide.googlecode.com/svn/trunk/pyguide.html.
The documentation should be written consistently in the style of
sphinx.

And more generally, write verbose! Will you remember
after a month why you had to write that check on that line? (Hint: no)
Write comments!
