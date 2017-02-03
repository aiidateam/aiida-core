#!/usr/bin/env python
import sys, os

# Import requirements specs
from setup_requirements import install_requires, dependency_links, extras_require

parent_directory = os.path.join(os.path.split(os.path.abspath(__file__))[0],os.pardir)
requirement_file = os.path.join(parent_directory, 'requirements.txt')
optional_requirement_file = os.path.join(parent_directory, 'optional_requirements.txt')

# generate basic requirements and dependency links,
with open(requirement_file, 'w') as fout:
    
    fout.write('##Requirements\n')    
    for req in install_requires:
        fout.write(req + '\n')    

    fout.write('\n## Dependency links\n')    
    for dep in dependency_links:
        fout.write(dep + '\n')

# generate optional requirements
with open(optional_requirement_file, 'w') as fout:
    for k, v in extras_require.iteritems():
        fout.write('##' + k + '\n')
        fout.write('\n'.join(v) + '\n\n')


