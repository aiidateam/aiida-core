#!/usr/bin/env python
"""Quick test of the benchmark feature."""

import subprocess
import sys

def test_benchmark_help():
    """Test that the new flags are recognized."""
    result = subprocess.run(
        [sys.executable, '-m', 'aiida', 'devel', 'check-load-time', '--help'],
        capture_output=True,
        text=True
    )
    
    print("=" * 80)
    print("HELP OUTPUT:")
    print("=" * 80)
    print(result.stdout)
    print("\nSTDERR:")
    print(result.stderr)
    print("\nReturn code:", result.returncode)
    
    # Check if new options are present
    if '--benchmark' in result.stdout:
        print("\n✓ --benchmark flag found!")
    if '--json' in result.stdout:
        print("✓ --json flag found!")
    if '--compare' in result.stdout:
        print("✓ --compare flag found!")

if __name__ == '__main__':
    test_benchmark_help()
