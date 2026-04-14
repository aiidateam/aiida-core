"""Shared calcfunctions for tutorial modules 2 and 3."""

import io

import yaml

from aiida import engine, orm


@engine.calcfunction
def prepare_input(parameters: orm.Dict) -> orm.SinglefileData:
    """Convert a Dict of parameters into a SinglefileData YAML file."""
    content = yaml.dump(parameters.get_dict())
    return orm.SinglefileData(io.BytesIO(content.encode()), filename='input.yaml')


@engine.calcfunction
def parse_output(output_file: orm.SinglefileData) -> dict[str, orm.Float]:
    """Extract variance_V and mean_V from a SinglefileData YAML results file."""
    with output_file.open(mode='r') as f:
        data = yaml.safe_load(f)
        return {
            'variance_V': orm.Float(data['variance_V']),
            'mean_V': orm.Float(data['mean_V']),
        }
