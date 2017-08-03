.. _git-cheatsheet:

GIT cheatsheet
==============

Excellent and thorough documentation on how to use GIT can be found online on
the official GIT documentation or by searching on Google. We summarize here
only a set of commands that may be useful.

Interesting online resources
----------------------------

* `Atlassian forking-workflow guide <https://www.atlassian.com/git/tutorials/comparing-workflows/forking-workflow>`_
* `Gitflow model <http://nvie.com/posts/a-successful-git-branching-model/>`_

Set the push default behavior to push only the current branch
-------------------------------------------------------------
The default push behavior may not be what you expect: if a branch you
are not working on changes, you may not be able to push your own
branch, because git tries to check them all. To avoid this, use::

  git config push.default upstream
  
to set the default push.default behaviour to push the current
branch to its upstream branch. Note the actual string to set depends on
the version of git; newer versions allow to use::

  git config push.default simple
  
which is better; see also discussion on `this stackoverflow page <http://stackoverflow.com/questions/948354/default-behavior-of-git-push-without-a-branch-specified>`_.

View commits that would be pushed
---------------------------------
If you want to see which commits would be sent to the remote repository upon a
``git push`` command, you can use (e.g. if you want to compare with the
``origin/develop`` remote branch)::

  git log origin/develop..HEAD
  
to see the logs of the commits, or::

  git diff origin/develop..HEAD
  
to see also the differences among the current ``HEAD`` and the version on 
``origin/develop``.

Switch to another branch
------------------------
You can switch to another branch with::

  git checkout newbranchname
  
and you can see the list of checked-out branches, and the one you are in,
with::

  git branch
  
(or ``git branch -a`` to see also the list of remote branches).

.. _git_associate_local_remote_branch:

Associate a local and remote branch
-----------------------------------

To tell GIT to always push a local branch (checked-out) to a remote branch
called ``remotebranchname``, check out the correct local branch and then
do::

  git push --set-upstream origin remotebranchname

From now on, you will just need to run ``git push``. This will create a new 
entry in ``.git/config`` similar to::

  [branch "localbranchname"]
    remote = origin
    merge = refs/heads/remotebranchname
    
Branch renaming
---------------
To rename a branch `locally`, from ``oldname`` to ``newname``::

  git checkout oldname
  git branch -m oldname newname
  
If you want also to rename it remotely, you have to create a new branch and
then delete the old one. One way to do it, is first editing ``~/.git/config`` 
so that the branch points to the new remote name, changing
``refs/heads/oldname`` to ``refs/heads/newname`` in the correct section::

  [branch "newname"]
    remote = origin
    merge = refs/heads/newname
    
Then, do a::

  git push origin newname
  
to create the new branch, and finally delete the old one with::

  git push origin :oldname
  
(notice the : symbol).
Note that if you are working e.g. on GitHub, there may be a filter to
disallow the deletion of branches (check in the repository settings, and 
then under "Branch management"). Moreover, the "Main branch" (set in the
repository settings, under "Repository details") cannot be deleted. 

Create a new (lightweight) tag
------------------------------
If you want to create a new tag, e.g. for a new version, and you have checked
out the commit that you want to tag, simply run::

  git tag TAGNAME
  
(e.g., ``git tag v0.2.0``). Afterwards, remember to push the tag to the remote
repository (otherwise it will remain only local)::

  git push --tags
  
Create a new branch from a given tag
------------------------------------
This will create a new ``newbranchname`` branch starting from tag ``v0.2.0``::

  git checkout -b newbranchname v0.2.0
  
Then, if you want to push the branch remotely and have git remember
the association::

  git push --set-upstream origin remotebranchname 
   
(for the meaning of --set-upsteam see the section
:ref:`git_associate_local_remote_branch` above).

Disallow a branch deletion, or committing to a branch, on GitHub
----------------------------------------------------------------
You can find these settings in the repository settings of the web interface, and 
then under "Branches".

.. note:: if you commit to a branch (locally) and then discover that you cannot
  push (e.g. you mistakenly committed to the master branch), you can remove
  your last commit using::
    
    git reset --hard HEAD~1
    
  (this removes one commit only, and you should have no local modifications;
  if you do it, be sure to avoid losing your modifications!)
  
Merge from a different repository
---------------------------------
  
It is possible to do a pull request of a forked repository from the GitHub
web interface. However, if one just wants to keep in sync, e.g., the main
AiiDA repository with a fork you are working into without creating a pull
request (e.g., for daily merge of your fork's develop into the main repo's
develop), you can:
  
* commit and pull all your changes in your fork
* from the GitHub web interface, sync your fork with the main repository,
  if needed
* go in a local cloned version of the main repository
* [*only the first time*] add a remote pointing to the new repository, with
  the name you prefer (here: ``myfork``)::
    
    git remote add myfork git@github.com:GITHUBUSER/FORKEDREPO.git
    
* checkout to the correct branch you want to merge into (``git
  checkout develop``)
* do a ``git pull`` (just in case)
* Fetch the correct branch of the other repository (e.g., the develop branch)::
  
    git fetch myfork develop
    
  (this will fetch that branch into a temporary location called ``FETCH_HEAD``).
* Merge the modifications::

    git merge FETCH_HEAD
 
 * Fix any merge conflicts (if any) and commit.
 * Finally, push the merged result into the main repository::
 
     git push
   
   (or, if you did not use the default remote with ``--set-upstream``, specify
   the correct remote branch, e.g. ``git push origin develop``).
   
   

.. note:: If you want to fetch and transfer also tags,
  use instead::

    git fetch -t myfork develop
    git merge FETCH_HEAD
    git push --tags
     
  to get the tags from myfork and then push them in the current repository.
     
     
