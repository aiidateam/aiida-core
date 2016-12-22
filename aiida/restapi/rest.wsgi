import sys
import os

AIIDA_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path = [AIIDA_DIR] + sys.path

from aiida.restapi.api import app as application
