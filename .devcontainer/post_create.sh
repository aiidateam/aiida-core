 #!/bin/bash
 set -e

 # Add test dependencies (not installed in image)
 pip install .[tests,pre-commit]

# add aiida user
/etc/my_init.d/10_create-system-user.sh

# configure aiida
/opt/configure-aiida.sh