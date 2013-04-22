#!/usr/bin/python
from django.core.management import setup_environ
from scalingtest import settings

import logging
import signal
import sys
import traceback
import os
import random
import time


def fixme():

  from scaling.models import DataCalc, Attribute
  from django.db import transaction

  with transaction.commit_on_success():
    for a in Attribute.objects.filter(key = "energy"):
      a.val_num = float(a.val_text)
      a.save()
      #a.val_text = 

def main():

  # Setup Django
  os.environ['DJANGO_SETTINGS_MODULE'] = 'scalingtest.settings'

  # Start and import
  #queryNeo();
  fixme();
  
if __name__ == "__main__":
  main()

