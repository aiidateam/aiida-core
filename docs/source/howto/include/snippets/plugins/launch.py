# -*- coding: utf-8 -*-
"""Launch a calculation using the 'diff-tutorial' plugin"""
from pathlib import Path

from aiida import engine, orm
from aiida.common.exceptions import NotExistent

INPUT_DIR = Path(__file__).resolve().parent / 'input_files'

# Create or load code
computer = orm.load_computer('localhost')
try:
    code = orm.load_code('diff@localhost')
except NotExistent:
    # Setting up code via python API (or use "verdi code setup")
    code = orm.InstalledCode(
        label='diff', computer=computer, filepath_executable='/usr/bin/diff', default_calc_job_plugin='diff-tutorial'
    )

# Set up inputs
builder = code.get_builder()
builder.file1 = orm.SinglefileData(file=INPUT_DIR / 'file1.txt')
builder.file2 = orm.SinglefileData(file=INPUT_DIR / 'file2.txt')
builder.metadata.description = 'Test job submission with the aiida_diff_tutorial plugin'

# Run the calculation & parse results
result = engine.run(builder)
computed_diff = result['diff'].get_content()
print(f'Computed diff between files:\n{computed_diff}')
