#!/usr/bin/env python

# Import requirements specs
from setup_requirements import install_requires, dependency_links, extras_require

# generate basic requirements and dependency links,
with open('../requirements.txt', 'w') as fout:
    
    fout.write('##Requirements\n')    
    for req in install_requires:
        fout.write(req + '\n')    

    fout.write('\n## Dependency links\n')    
    for dep in dependency_links:
        fout.write(dep + '\n')

# generate optional requirements
with open('../optional_requirements.txt', 'w') as fout:
    for k, v in extras_require.iteritems():
        fout.write('##' + k + '\n')
        fout.write('\n'.join(v) + '\n\n')


