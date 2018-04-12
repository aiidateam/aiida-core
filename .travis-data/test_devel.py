# python script that runs tests, equivalent to:
# $ verdi -p test_$TEST_AIIDA_BACKEND devel tests
from aiida import load_dbenv
import os

profile = 'test_' + os.environ['TEST_AIIDA_BACKEND']
load_dbenv(profile=profile)

from aiida.cmdline.verdilib import Devel
Devel.run(Devel(), 'tests')
