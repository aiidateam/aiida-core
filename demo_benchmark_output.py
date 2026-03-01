#!/usr/bin/env python
"""Demo of what the benchmark output will look like."""

from tabulate import tabulate

print("=" * 80)
print("DEMO: verdi devel check-load-time --benchmark")
print("=" * 80)
print()

# Simulate benchmark output
print("📊 Benchmark Results")
print("Timestamp: 2026-03-01T10:30:45.123456")
print("Total modules loaded: 45")
print("Total size: 1234.56 KB")
print()

# Top 10 modules table
top_modules = [
    ["aiida.orm.nodes", "234.56 KB"],
    ["aiida.engine.processes", "189.23 KB"],
    ["aiida.storage.psql_dos", "156.78 KB"],
    ["aiida.cmdline.commands", "123.45 KB"],
    ["aiida.common.datastructures", "98.76 KB"],
    ["aiida.manage.configuration", "87.65 KB"],
    ["aiida.plugins.entry_point", "76.54 KB"],
    ["aiida.restapi.resources", "65.43 KB"],
    ["aiida.brokers.rabbitmq", "54.32 KB"],
    ["aiida.cmdline.utils", "43.21 KB"],
]

print("Top 10 Largest Modules:")
print(tabulate(top_modules, headers=["Module", "Size"], tablefmt="simple"))
print()
print("✓ Benchmark saved to ~/.aiida/benchmark_history.json")
print()

print("=" * 80)
print("DEMO: verdi devel check-load-time --benchmark --compare last")
print("=" * 80)
print()

print("📊 Benchmark Results")
print("Timestamp: 2026-03-01T10:30:45.123456")
print("Total modules loaded: 45")
print("Total size: 1234.56 KB")
print()

print("Top 10 Largest Modules:")
print(tabulate(top_modules, headers=["Module", "Size"], tablefmt="simple"))
print()

# Comparison table
print("📈 Comparison with baseline (2026-03-01T09:15:30.123456):")
print()

comparison_data = [
    ["Total Modules", "42", "45", "+3"],
    ["Total Size (KB)", "1200.00", "1234.56", "+34.56 KB"]
]

print(tabulate(comparison_data, headers=["Metric", "Baseline", "Current", "Change"], tablefmt="simple"))
print()
print("⚠️  Performance regression detected!")
print()

print("=" * 80)
print("DEMO: verdi devel check-load-time --benchmark --json")
print("=" * 80)
print()

import json

json_output = {
    "timestamp": "2026-03-01T10:30:45.123456",
    "total_modules": 45,
    "total_size_kb": 1234.56,
    "modules": [
        {"module": "aiida.brokers", "size_bytes": 12345, "size_kb": 12.05},
        {"module": "aiida.cmdline", "size_bytes": 234567, "size_kb": 229.07},
        {"module": "aiida.common", "size_bytes": 98765, "size_kb": 96.45},
        {"module": "aiida.engine", "size_bytes": 456789, "size_kb": 446.08},
        {"module": "aiida.manage", "size_bytes": 123456, "size_kb": 120.56},
    ]
}

print(json.dumps(json_output, indent=2))
