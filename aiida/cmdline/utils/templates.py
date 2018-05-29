from jinja2 import Environment, PackageLoader

env = Environment(
    loader=PackageLoader('aiida', 'cmdline/templates')
)
