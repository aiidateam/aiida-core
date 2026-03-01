#!/usr/bin/env python
"""Test script to demonstrate the error message output."""

# Simulate the error message formatting
loaded = 'aiida.orm.fields'
allowed = ('aiida.brokers', 'aiida.cmdline', 'aiida.common', 'aiida.manage', 'aiida.plugins', 'aiida.restapi')
allowed_str = '\n  - '.join(allowed)

error_message = (
    f'potential `verdi` speed problem: `{loaded}` module is imported by the cmdline package.\n'
    f'The `verdi` CLI is optimized for fast startup and should only import from these packages:\n'
    f'  - {allowed_str}\n'
    f"Importing '{loaded}' increases load time significantly.\n"
    f'To fix this, consider moving the import inside a function for lazy loading, '
    f'or restructuring your code to avoid cmdline → orm dependencies.'
)

print("=" * 80)
print("SIMULATED ERROR OUTPUT:")
print("=" * 80)
print(error_message)
print("=" * 80)
