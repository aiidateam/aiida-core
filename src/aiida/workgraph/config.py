import json
from aiida.manage import get_config
from pathlib import Path
from aiida.orm.nodes.process.calculation.calcfunction import CalcFunctionNode
from aiida.orm.nodes.process.workflow.workfunction import WorkFunctionNode
from aiida.engine import CalcJob, WorkChain

WORKGRAPH_EXTRA_KEY = '_workgraph'
WORKGRAPH_SHORT_EXTRA_KEY = '_workgraph_short'

task_types = {
    CalcFunctionNode: 'CALCFUNCTION',
    WorkFunctionNode: 'WORKFUNCTION',
    CalcJob: 'CALCJOB',
    WorkChain: 'WORKCHAIN',
}


def load_config() -> dict:
    """Load the configuration from the config file."""
    config = get_config()
    config_file_path = Path(config.dirpath) / 'workgraph.json'
    try:
        with config_file_path.open('r') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}
    return config
