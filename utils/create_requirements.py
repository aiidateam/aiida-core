#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import sys, os

# Import requirements specs
from setup_requirements import install_requires, dependency_links, extras_require

parent_directory = os.path.join(os.path.split(os.path.abspath(__file__))[0],os.pardir)
requirement_file = os.path.join(parent_directory, 'requirements.txt')
optional_requirement_prefix = os.path.join(parent_directory, 'optional_requirements_')

# generate basic requirements and dependency links,
with open(requirement_file, 'w') as fout:
    
    fout.write('##Requirements\n')    
    for req in install_requires:
        fout.write(req + '\n')    

    fout.write('\n## Dependency links\n')    
    for dep in dependency_links:
        fout.write(dep + '\n')

# generate optional requirements
for requirement_class, reqs in extras_require.iteritems():
    with open(optional_requirement_prefix + requirement_class + '.txt', 'w') as fout:
        fout.write('\n'.join(reqs) + '\n\n')


