Directly querying in Django
+++++++++++++++++++++++++++
If you know how AiiDA stores the data internally in the database, you can 
directly use Django to query the database (or even use directly SQL commands,
if you really feel the urge to do so). Documentation on how queries work
in Django can be found on the `official Django documentation <https://docs.djangoproject.com/en/1.7/topics/db/queries/>`_. The models can be found in 
:py:mod:`aiida.backends.djsite.db.models` and is directly accessible as ``models``
in the ``verdi shell`` via ``verdi run``.
