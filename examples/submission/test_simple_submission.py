#!/usr/bin/env python
import sys

from aida.common.utils import load_django
load_django()

from aida.orm import Calculation, Code, Data
from aida.djsite.db.models import Computer

#from aida.common.pluginloader import load_plugin
#ParameterData = load_plugin(Data, 'aida.orm.dataplugins', 'parameter')
from aida.orm.dataplugins.parameter import ParameterData

computername = "bellatrix.epfl.ch"
# A string with the version of this script, used to recreate a code when necessary
current_version = "1.0.0"

def get_or_create_machine():
    import json
    from django.core.exceptions import ObjectDoesNotExist
    from aida.djsite.db.models import Computer

    try:
        computer = Computer.objects.get(hostname=computername)
        print >> sys.stderr, "Using the existing computer {}...".format(computername)
    except ObjectDoesNotExist:
        print >> sys.stderr, "Creating a new computer..."
        computer =Computer.objects.create(
            hostname=computername,
            workdir = "/scratch/{username}/aida",
            transport_type = "ssh",
            scheduler_type = "pbspro",
            transport_params = json.dumps(
            {})
            )
    return computer

def get_or_create_code():
    import tempfile

    useful_codes = Code.query(attributes__key="_local_executable",
                              attributes__tval="sum.py").filter(
                                  attributes__key="version", attributes__tval=current_version)

    if not(useful_codes):
        print >> sys.stderr, "Creating the code..."
        with tempfile.NamedTemporaryFile() as f:
            f.write("""#!/usr/bin/env python
import sys

try:
    print float(sys.argv[0])+float(sys.argv[1])
except KeyError:
    print >> sys.stderr, "Pass two numbers on the command line"
except ValueError:
    print >> sys.stderr, "The values on the command line are not valid numbers"
""")
            f.flush()
            code = Code(local_executable = "sum.py", 
                        input_plugin='simple_plugin.template_replacer')
            code.add_file(f.name, "sum.py")
            code.store()
            code.set_metadata("version", current_version)
        return code
    
    elif len(useful_codes) == 1:
        print >> sys.stderr, "Using the existing code {}...".format(useful_codes[0].uuid)
        return useful_codes[0]
    else:
        raise ValueError("More than one valid code!")
        

#####

computer = get_or_create_machine()
code = get_or_create_code()

#template_data = ParameterData({
#    'input_file_template': "",
#    'input_file_name': "",
#    'stdin' = ["", ""],
#    })

template_data = ParameterData({
    'stdin': ["{add1}", "{add2}"],
    }).store()

parameters = ParameterData({
    'add1': 3.45,
    'add2': 7.89,
    }).store()

calc = Calculation(computer=computer).store()
print "created calculation; calc=Calculation(uuid='{}') # ID={}".format(
    calc.uuid,calc.dbnode.pk)

calc.add_link_from(code)

calc.add_link_from(template_data, label="template")
calc.add_link_from(parameters, label="parameters")

calc.submit()
print "submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
    calc.uuid,calc.dbnode.pk)

