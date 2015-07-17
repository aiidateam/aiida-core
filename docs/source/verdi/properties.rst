Properties
++++++++++

Properties are configuration options that are stored in the ``config.json`` file 
(within the ``.aiida`` directory). They can be accessed and modified thanks to 
``verdi devel`` commands:

* **delproperty**: delete a given property.

* **describeproperty**: describe the content of a given property.

* **getproperty**: get the value of a given property.

* **listproperties**: list all user defined properties. With ``-a`` option, list
  all of them including those still at the default values.
	
* **setproperty**: set a given property (usage: ``verdi devel setproperty PROPERTYNAME PROPERTYVALUE``).

For instance, modules to be loaded automatically in the ``verdi shell`` can be
added by putting their paths (separated by colons ``:``) in the property
``verdishell.modules``, e.g. by typing something like::

    verdi devel setproperty verdishell.modules aiida.common.exceptions.NotExistent:aiida.orm.autogroup.Autogroup
	
More information can be found in the source code: see
:download:`setup.py<../../../aiida/common/setup.py>`.
