from setup_requirements import install_requires
import yaml

environment = dict(
    name = 'aiida',
    channels = ['anaconda', 'conda-forge', 'etetoolkit'],
    dependencies = install_requires,
)

with open('environment.yml', 'w') as f:
    yaml.dump(environment, f,
            explicit_start=True,
            default_flow_style=False)
