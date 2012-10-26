############################
Developer's Guide For AIDADB
############################

All urls are defined in the urlconf file :mod:`aidadb.urls`.  Most views
are found within :mod:`aidadb.data.views` and :mod:`aidadb.data.simple_views`.
The views within :mod:`aidadb.data.views` use the `ModelAdmin` classes
from :mod:`aidadb.data.myadmin`. These `ModelAdmin` derived classes
are heavily modified, so that we can use Django Admin tables,
javascript interfaces, changelist details, the infrastructure for the
filtered lists, action items, etc.

The html files for many views are found within the `templates`
directory. The directory `templates/admin` and its subdirectory
contain specific html files that are used by the heavily modified
`ModelAdmin` class based methods. The html files `base.html` and
`base_site.html` in `templates` contain the basic site. 

If you want to change the root aida url, change the AIDA_ROOT_URL
variable in `settings.py` in `aidadb` directory. Currently it is set
so that links like http://host/aida/ work.

