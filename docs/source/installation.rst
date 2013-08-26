====================================
Installation and Deployment of AiiDA
====================================

1. Download the Community python edition of ActiveState Python from
ActiveState_. Choose the appropiate distribution corresponding to your 
architecture.

.. _ActiveState: http://www.activestate.com/activepython/downloads


2. After untaring the distribution, cd to the untared directory,
install ActiveState using :program:`install.sh`.

3. Using pypm install django::

     sudo pypm -g install django

4. Install apache::

     sudo yum install httpd httpd-devel

5. Download and install mod_wsgi by hand from GoogleCode_.

.. _GoogleCode: http://code.google.com/p/modwsgi/

6. Download the AiiDA distribution to /usr/local/www/aiida using svn.

7. Copy the following files::

      $ cp /usr/local/www/aiida/aiidadb/apache/mod_wsgi.conf  /etc/httpd/conf.d/
      $ cp /usr/local/www/aiida/aiidadb/apache/z_aiida_wsgi.conf  /etc/httpd/conf.d/

   and edit them as you see fit.

8. Restart httpd::

      /etc/init.d/httpd restart


Verdi install
+++++++++++++

We need to install some basic packages::

      sudo apt-get install git
      sudo apt-get install ipython
      sudo apt-get install python-pip
      sudo apt-get install python2.7-dev
      sudo apt-get install libsqlite3-dev

Git clone the repository somewhere, using the address provided by Bitbucket.
If this is the first time you use Bitbucket, remember to add the ssh key of your computer on your Bitbucket account.
First of all, you will need to install the requirements. To do this, using pip you can install required dependencies using the command::

      pip install -U -r requirements.txt

in the main folder of aiida. 
This will install the required python packages (refer to the content of the file to know the requirements.

add the following to the .bashrc::

      export PYTHONPATH=THE_PATH_TO_THE_AIIDA_FOLDER:${PYTHONPATH}
      export PATH=THE_PATH_TO_THE_AIIDA_FOLDER/bin:${PATH}

source the .bashrc file, or login in a new window
Note: remember to check that your .bashrc is sourced from your
.profile or .bash_profile script. E.g., my .bash_profile contains::

    if [ -f ~/.bashrc ] 
    then
        . ~/.bashrc
    fi

    if [ -f ~/.profile ]
    then
        . ~/.profile
    fi

Run verdi install to configure aiida (database, repository location, syncdb + migrations). 
If this is you first installation the code will ask to set an admin user ("Would you like to create one now?" prompt).
In this case chose yes and fill accordingly to you preferences.
Make sure that the username matches with your local machine username.

If something fails, you may have misconfigured the database.

To enable bash-completion of the commands, modify the bashrc by adding
the string::
   
   eval "$(verdi completioncommand)"

Remember later to source the .bashrc file or to open a new shell window. 
Alternatively, you can execute by yourself verdi completioncommand and copy the output in the .bashrc.
To try it, run verdi daemon start and verdi daemon stop and connect to the address shown in the output text with your browser.

You can also try if the python setup is OK: go in your home folder or in another folder different from the aiida folder, run python or ipython and try to import a module, e.g.: import aiida. 
If the setup is ok, you shouldn't get any error. 
If you do get an ImportError, check if you correctly set up the PYTHONPATH environment variable in the steps above.

You can also try to run verdi test db to run some tests. 
Note that the DB (and repository folder) used for the tests are different; in particular, the DB is a sqlite3, resident in memory. 
Typing verdi test will run the entire suite of tests.

Further notes
^^^^^^^^^^^^^

* For some reasons, on some machines (often Mac OS X) there is no
  default locale defined, and when you run verdi syncdb for the first
  time it fails (see also this issue of django).  To solve, first
  remove the sqlite database that was created. 
  Then, run in your terminal (or add to your .bashrc) before running
  syncdb for the first time::

     export LANG="en_US.UTF-8"
     export LC_ALL="en_US.UTF-8"

  and then run syncdb again.

* The tests of the transport plugins are done connecting the localhost to localhost. The tests may fail if this operation is not allowed. To add the ssh key, simply install the ssh server on your computer::

     sudo apt-get install openssh-server

  And then add the key to the set of authorized keys::

     ssh-copy-id localhost

  Note: we haven't yet tested what happens in case of firewalls blocks.


Temporarily disabled
^^^^^^^^^^^^^^^^^^^^
Run (in the main folder) verdi migrate to apply south migrations to our djsite.db.models tables.
