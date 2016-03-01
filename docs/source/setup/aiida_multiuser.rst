.. _aiida_multiuser:

==============================
Using AiiDA in multi-user mode
==============================

.. note:: multi-user mode is still not fully supported, and the way it
  works will change significantly soon. Do not use unless you know what you
  are doing.

.. todo:: To be documented.

   Discuss:

    * Security issues
    * Under which linux user (aiida) to run, and remove the pwd with ``passwd -d aiida``.
    * How to setup each user (aiida@localhost for the daemon user,
      correct email for the others using ``verdi install --only-config``)
    * How to configure a given user (verdi user configure)
    * How to list users (also the --color option, and the meaning of colors)
    * How to setup the daemon user (verdi daemon configureuser)
    * How to start the daemon
    * How to configure the permissions! (all AiiDA in the same group, and
      set the 'chmod -R g+s' flag to all folders and subfolders of the AiiDA repository)
      (comment that by default now we have a flag (harcoded to True) in aiida.common.folders
      to give write permissions to the group both to files and folders
      created using the Folder class.
    
    * Some configuration example::
      
       {u'compress': True,
        u'key_filename': u'/home/aiida/.aiida/sshkeys/KEYFILE',
        u'key_policy': u'RejectPolicy',
        u'load_system_host_keys': True,
        u'port': 22,
        u'proxy_command': u'ssh -i /home/aiida/.aiida/sshkeys/KEYFILE USERNAME@MIDDLECOMPUTER /bin/nc FINALCOMPUTER 22',
        u'timeout': 60,
        u'username': u'xxx'}
    
    * Moreover, on the remote computer do::
 
         ssh-keyscan FINALCOMPUTER

      and append the output to the ``known_hosts`` of the aiida daemon account.
      Do the same also for the MIDDLECOMPUTER if a proxy_command is user.
      
    * 
    
============================
Deploying AiiDA using Apache
============================

.. note:: At this stage, this section is meant for developers only.

.. todo:: To be documented.

Some notes:

* Configure your default site of Apache (check in ``/etc/apache2/sites-enabled``,
  probably it is called ``000-default``).
  
  Add the full ServerName outside of any ``<VirtualHost>`` section::

    ServerName FULLSERVERNAMEHERE

  and inside the VirtualHost that provide access, specifiy the email of the
  server administrator (note that the email will be accessible, e.g. it is
  shown if a ``INTERNAL ERROR 500`` page is shown)::
  
    <VirtualHost *:80>
        ServerAdmin administratoremail@xxx.xx

        # [...]
        
    </VirtualHost>
        
* Login as the user running apache, e.g. ``www-data`` in Ubuntu; use something
  like::
  
    sudo su www-data -s /bin/bash 
    
    and run ``verdi install`` to configure where the DB and the files stay, etc.
    
    Be also sure to check that this apache user belongs to the group that has
    read/write permissions to the AiiDA repository.
    
* If you home directory is set to ``/var/www``, and this is published by Apache,
  double check that nobody can access the .aiida subfolder! By default, during
  ``verdi install`` AiiDA puts inside the folder a .htaccess file to disallow
  access, but this file is not read by some default Apache configurations.
  
  To have Apache honor the ``.htaccess`` file, in the default Apache site
  (probably the same file as above) you need to set the ``AllowOverride all`` 
  flag in the proper VirtualHost and Directory (note that there can be more 
  than one, e.g. if you have both HTTP and HTTPS).
  
  You should have something like::
  
    <VirtualHost *:80>
        ServerAdmin xxx@xxx.xx

        DocumentRoot /var/www
        <Directory /var/www/>
                AllowOverride all
        </Directory>
    </VirtualHost>

  .. note:: Of course, you will typically have other configurations as well, the
    snippet above just shows where the ``AllowOverride all`` line should appear.
  
  Double check if you cannot list/read the files (e.g. connecting to
  ``http://YOURSERVER/.aiida``). 
  
  .. todo:: Allow to have a trick to have only one file in .aiida, containing
    the url where the actual configuration stuff resides (or some other trick
    to physically move the configuration files out of /var/www).
  
* Create a ``/etc/apache2/sites-available/wsgi-aiida`` file,
  with content::

   Alias /static/awi /PATH_TO_AIIDA/aiida.backends.djsite/awi/static/awi/
   Alias /favicon.ico /PATH_TO_AIIDA/aiida.backends.djsite/awi/static/favicon.ico
 
   WSGIScriptAlias / /PATH_TO_AIIDA/aiida.backends.djsite/settings/wsgi.py
   WSGIPassAuthorization On
   WSGIPythonPath /PATH_TO_AIIDA/
 
   <Directory /PATH_TO_AIIDA/aiida.backends.djsite/settings>
   <Files wsgi.py>
   Order deny,allow
   Allow from all
   ## For Apache >= 2.4, replace the two lines above with the one below:
   # Require all granted
   </Files>
   </Directory>
  
 .. note:: Replace everywhere ``PATH_TO_AIIDA`` with the full path to the
   AiiDA source code. Check that the user running the Apache daemon
   can read/access all files in that folder and subfolders.
   
 .. note:: in the ``WSGIPythonPath`` you can also add other folders that should
   be in the Python path (e.g. if you use other libraries that should be
   accessible). The different paths must be separated with ``:``.
   
 .. note:: For Apache >= 2.4, replace the two lines::

     Order deny,allow
     Allow from all

  with::
  
    Require all granted
    
 .. note:: The ``WSGIScriptAlias`` exposes AiiDA under main address of your
   website (``http://SERVER/``).
   
   If you want to serve AiiDA under a subfolder, e.g. ``http://SERVER/aiida``,
   then change the line containing ``WSGIScriptAlias`` with::
   
     WSGIScriptAlias /aiida /PATH_TO_AIIDA/aiida.backends.djsite/settings/wsgi.py
     
   **without any trailing slashes after '/aiida'**.

* Enable the given
  site::

    sudo a2ensite wsgi-aiida
   
  and reload the Apache configuration to load the new site::
  
    sudo /etc/init.d/apache2 reload
      
* A comment on permissions (to be improved):
  the default Django Authorization (used e.g. in the API) does not allow a
  "standard" user to modify data in the DB, but only to read it, therefore
  if you are accessing with a user that is not a superuser, all API calls
  trying to modify the DB will return an HTTP UNAUTHORIZED message.
  
  Temporarily, you can fix this by going in a ``verdi shell``, loading your user
  with something like::
  
    u = models.DbUser.objects.get(email='xxx')
  
  and then upgrading the user to a superuser::
    
    u.is_superuser = True
    u.save()
    
 