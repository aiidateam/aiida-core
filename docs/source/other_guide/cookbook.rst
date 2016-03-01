AiiDA cookbook (useful code snippets)
=====================================

This cookbook is intended to be a collection of useful short scripts and
code snippets that may be useful in the everyday usage of AiiDA.
Please read carefully the nodes (if any) before running the scripts!


Deletion of nodes
-----------------

At the moment, we do not support natively the deletion of nodes. This is
mainly because it is very dangerous to delete data, as this is cannot be
undone.

If you really feel the need to delete some code, you can use the
function below.

.. note:: **WARNING!** In order to preserve the provenance, this function
  will delete not only the list of specified nodes,
  but also all the children nodes! So please be sure to double check what
  is going to be deleted before running this function.

Here is the function, pass a list of PKs as parameter to delete those nodes
and all the children nodes::

  def delete_nodes(pks_to_delete):
      """
      Delete a set of nodes. 
      
      :note: The script will also delete
      all children calculations generated from the specified nodes.
      
      :param pks_to_delete: a list of the PKs of the nodes to delete
      """
      from django.db import transaction
      from django.db.models import Q
      from aiida.backends.djsite.db import models
      from aiida.orm import load_node
  
      # Delete also all children of the given calculations
      # Here I get a set of all pks to actually delete, including
      # all children nodes.
      all_pks_to_delete = set(pks_to_delete)
      for pk in pks_to_delete:
          all_pks_to_delete.update(models.DbNode.objects.filter(
              parents__in=pks_to_delete).values_list('pk', flat=True))
  
      print "I am going to delete {} nodes, including ALL THE CHILDREN".format(
          len(all_pks_to_delete))
      print "of the nodes you specified. Do you want to continue? [y/N]"
      answer = raw_input()
      
      if answer.strip().lower() == 'y':
          # Recover the list of folders to delete before actually deleting
          # the nodes.  I will delete the folders only later, so that if
          # there is a problem during the deletion of the nodes in
          # the DB, I don't delete the folders
          folders = [load_node(pk).folder for pk in all_pks_to_delete]
      
          with transaction.atomic():
              # Delete all links pointing to or from a given node
              models.DbLink.objects.filter(
                  Q(input__in=all_pks_to_delete) | 
                  Q(output__in=all_pks_to_delete)).delete()
              # now delete nodes
              models.DbNode.objects.filter(pk__in=all_pks_to_delete).delete()
      
          # If we are here, we managed to delete the entries from the DB.
          # I can now delete the folders
          for f in folders:
              f.erase()
    
