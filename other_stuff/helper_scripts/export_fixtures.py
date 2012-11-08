import sys, os, os.path

#sys.path.append(os.path.abspath('..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'aida.djsite.settings.settings'

from django.core.serializers import serialize
from aida.djsite.main import models

#model_names = ['CalcStatus', 'CalcType', 'CodeStatus', 'CodeType', 'Code', 'Computer', 'Project'] # a list of the names of the models you want to export
model_names = ['Element']

for model_name in model_names:
    cls = getattr(models, model_name)
    filename = model_name.lower() + ".json"
    file = open(filename, "w")
    file.write(serialize("json", cls.objects.all()))
