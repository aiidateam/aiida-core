#!/usr/bin/env python
"""Benchmark with realistic workload: 100MB of inhomogeneous files."""

import io
import os
import random
import tempfile
import time
from pathlib import Path

from aiida.repository.backend import GitRepositoryBackend, DiskObjectStoreRepositoryBackend
from disk_objectstore import Container


def generate_realistic_files(target_mb=100):
    """Generate a realistic mix of file sizes totaling ~100MB.

    Distribution mimics real-world repository usage:
    - Many small files (configs, metadata): 1KB-10KB
    - Medium files (scripts, data): 10KB-1MB
    - Few large files (datasets, images): 1MB-10MB
    """
    target_bytes = target_mb * 1024 * 1024
    files = []
    total_bytes = 0

    # Distribution weights (approximate percentage of total size)
    # 20% in small files, 50% in medium files, 30% in large files

    # Small files: 1KB - 10KB (lots of them, but small total size)
    small_target = int(target_bytes * 0.20)
    while total_bytes < small_target:
        size = random.randint(1024, 10 * 1024)  # 1KB - 10KB
        files.append(size)
        total_bytes += size

    # Medium files: 10KB - 1MB (moderate number)
    medium_target = int(target_bytes * 0.50)
    while total_bytes < small_target + medium_target:
        size = random.randint(10 * 1024, 1024 * 1024)  # 10KB - 1MB
        files.append(size)
        total_bytes += size

    # Large files: 1MB - 10MB (few of them)
    while total_bytes < target_bytes:
        remaining = target_bytes - total_bytes
        if remaining < 1024 * 1024:
            # If less than 1MB remaining, just add it
            files.append(remaining)
            total_bytes += remaining
        else:
            max_size = min(10 * 1024 * 1024, remaining)  # 10MB max
            size = random.randint(1024 * 1024, max_size)  # 1MB - 10MB
            files.append(size)
            total_bytes += size

    random.shuffle(files)  # Randomize order
    return files, total_bytes


def generate_file_content(size):
    """Generate semi-random file content of given size."""
    # Use a mix of patterns to simulate real data
    # Not purely random (compressible) but not all zeros either
    if size < 1024:
        return os.urandom(size)

    # For larger files, use a repeating pattern with some randomness
    pattern_size = min(1024, size)
    pattern = os.urandom(pattern_size)
    full_content = pattern * (size // pattern_size)
    remainder = size % pattern_size
    if remainder:
        full_content += pattern[:remainder]

    return full_content


def benchmark_backend(backend_name, backend, file_sizes):
    """Benchmark a backend with the given file sizes."""
    print(f"\n{'='*70}")
    print(f"Benchmarking: {backend_name}")
    print(f"Total files: {len(file_sizes):,}")
    print(f"Total size: {sum(file_sizes) / (1024*1024):.2f} MB")
    print(f"{'='*70}")

    # Categorize files
    small_files = [s for s in file_sizes if s < 10 * 1024]
    medium_files = [s for s in file_sizes if 10 * 1024 <= s < 1024 * 1024]
    large_files = [s for s in file_sizes if s >= 1024 * 1024]

    print(f"\nFile distribution:")
    print(f"  Small (<10KB): {len(small_files):,} files, {sum(small_files)/(1024*1024):.2f} MB")
    print(f"  Medium (10KB-1MB): {len(medium_files):,} files, {sum(medium_files)/(1024*1024):.2f} MB")
    print(f"  Large (>1MB): {len(large_files):,} files, {sum(large_files)/(1024*1024):.2f} MB")

    # === WRITE BENCHMARK ===
    print(f"\n📝 Writing {len(file_sizes):,} files...")
    keys = []
    write_start = time.time()

    for i, size in enumerate(file_sizes):
        if i % 500 == 0 and i > 0:
            elapsed = time.time() - write_start
            progress = (sum(file_sizes[:i]) / sum(file_sizes)) * 100
            rate = sum(file_sizes[:i]) / (1024 * 1024) / elapsed
            print(f"  Progress: {i:,}/{len(file_sizes):,} files ({progress:.1f}%) - {rate:.2f} MB/s")

        content = generate_file_content(size)
        handle = io.BytesIO(content)
        key = backend.put_object_from_filelike(handle)
        keys.append(key)

    write_elapsed = time.time() - write_start
    write_throughput = sum(file_sizes) / (1024 * 1024) / write_elapsed

    print(f"\n  ✓ Write complete:")
    print(f"    Total time: {write_elapsed:.2f} seconds")
    print(f"    Throughput: {write_throughput:.2f} MB/s")
    print(f"    Avg time per file: {write_elapsed / len(file_sizes) * 1000:.2f} ms")

    # === READ BENCHMARK ===
    print(f"\n📖 Reading all {len(keys):,} files...")
    read_start = time.time()

    for i, key in enumerate(keys):
        if i % 500 == 0 and i > 0:
            elapsed = time.time() - read_start
            progress = (i / len(keys)) * 100
            rate = sum(file_sizes[:i]) / (1024 * 1024) / elapsed
            print(f"  Progress: {i:,}/{len(keys):,} files ({progress:.1f}%) - {rate:.2f} MB/s")

        with backend.open(key) as stream:
            _ = stream.read()

    read_elapsed = time.time() - read_start
    read_throughput = sum(file_sizes) / (1024 * 1024) / read_elapsed

    print(f"\n  ✓ Read complete:")
    print(f"    Total time: {read_elapsed:.2f} seconds")
    print(f"    Throughput: {read_throughput:.2f} MB/s")
    print(f"    Avg time per file: {read_elapsed / len(keys) * 1000:.2f} ms")

    # === HAS_OBJECTS BENCHMARK ===
    print(f"\n🔍 Checking existence of all {len(keys):,} files...")
    has_start = time.time()
    batch_size = 100

    for i in range(0, len(keys), batch_size):
        batch = keys[i:i+batch_size]
        backend.has_objects(batch)

    has_elapsed = time.time() - has_start

    print(f"\n  ✓ Check complete:")
    print(f"    Total time: {has_elapsed:.2f} seconds")
    print(f"    Checks per second: {len(keys) / has_elapsed:.2f}")

    # === LIST_OBJECTS BENCHMARK ===
    print(f"\n📋 Listing all objects...")
    list_start = time.time()
    listed_keys = list(backend.list_objects())
    list_elapsed = time.time() - list_start

    print(f"\n  ✓ List complete:")
    print(f"    Total time: {list_elapsed:.2f} seconds")
    print(f"    Objects found: {len(listed_keys):,}")

    # === RANDOM READ BENCHMARK (50 random files) ===
    print(f"\n🎲 Random read test (50 random files)...")
    random_keys = random.sample(keys, min(50, len(keys)))
    random_read_start = time.time()

    for key in random_keys:
        with backend.open(key) as stream:
            _ = stream.read()

    random_read_elapsed = time.time() - random_read_start

    print(f"\n  ✓ Random read complete:")
    print(f"    Total time: {random_read_elapsed:.2f} seconds")
    print(f"    Avg time per file: {random_read_elapsed / len(random_keys) * 1000:.2f} ms")

    # === DELETE BENCHMARK ===
    # Delete a subset of objects to measure deletion performance
    delete_count = min(100, len(keys) // 4)  # Delete 25% or 100 objects, whichever is smaller
    print(f"\n🗑️  Deleting {delete_count} objects...")
    keys_to_delete = random.sample(keys, delete_count)

    delete_start = time.time()
    backend.delete_objects(keys_to_delete)
    delete_elapsed = time.time() - delete_start

    print(f"\n  ✓ Delete complete:")
    print(f"    Total time: {delete_elapsed:.2f} seconds")
    print(f"    Objects deleted: {delete_count:,}")
    print(f"    Avg time per object: {delete_elapsed / delete_count * 1000:.2f} ms")
    print(f"    Deletion rate: {delete_count / delete_elapsed:.2f} objects/second")

    # Verify objects were actually deleted
    objects_after_delete = list(backend.list_objects())
    print(f"    Objects remaining: {len(objects_after_delete):,} (started with {len(keys):,})")

    # === STORAGE INFO ===
    print(f"\n📊 Repository Info:")
    info = backend.get_info()
    for key, value in info.items():
        print(f"  {key}: {value}")

    return {
        'write_time': write_elapsed,
        'write_throughput': write_throughput,
        'read_time': read_elapsed,
        'read_throughput': read_throughput,
        'has_time': has_elapsed,
        'list_time': list_elapsed,
        'random_read_time': random_read_elapsed,
        'delete_time': delete_elapsed,
        'delete_count': delete_count,
        'delete_rate': delete_count / delete_elapsed,
        'num_files': len(keys),
        'total_size_mb': sum(file_sizes) / (1024 * 1024)
    }


def print_comparison(git_results, dos_results):
    """Print comparison summary."""
    print(f"\n{'='*70}")
    print(f"PERFORMANCE COMPARISON SUMMARY")
    print(f"{'='*70}")

    print(f"\n📊 Overall Statistics:")
    print(f"  Files: {git_results['num_files']:,}")
    print(f"  Total size: {git_results['total_size_mb']:.2f} MB")

    print(f"\n📝 Write Performance:")
    git_write_throughput = git_results['write_throughput']
    dos_write_throughput = dos_results['write_throughput']
    if dos_write_throughput > git_write_throughput:
        speedup = dos_write_throughput / git_write_throughput
        comparison = "🔴 DOS faster"
    else:
        speedup = git_write_throughput / dos_write_throughput
        comparison = "🟢 Git faster"

    print(f"  Git: {git_results['write_time']:.2f}s ({git_write_throughput:.2f} MB/s)")
    print(f"  DOS: {dos_results['write_time']:.2f}s ({dos_write_throughput:.2f} MB/s)")
    print(f"  Winner: {comparison} ({speedup:.2f}x)")

    print(f"\n📖 Read Performance:")
    git_read_throughput = git_results['read_throughput']
    dos_read_throughput = dos_results['read_throughput']
    if git_read_throughput > dos_read_throughput:
        speedup = git_read_throughput / dos_read_throughput
        comparison = "🟢 Git faster"
    else:
        speedup = dos_read_throughput / git_read_throughput
        comparison = "🔴 DOS faster"

    print(f"  Git: {git_results['read_time']:.2f}s ({git_read_throughput:.2f} MB/s)")
    print(f"  DOS: {dos_results['read_time']:.2f}s ({dos_read_throughput:.2f} MB/s)")
    print(f"  Winner: {comparison} ({speedup:.2f}x)")

    print(f"\n🔍 has_objects Performance:")
    if git_results['has_time'] < dos_results['has_time']:
        speedup = dos_results['has_time'] / git_results['has_time']
        comparison = "🟢 Git faster"
    else:
        speedup = git_results['has_time'] / dos_results['has_time']
        comparison = "🔴 DOS faster"

    print(f"  Git: {git_results['has_time']:.2f}s")
    print(f"  DOS: {dos_results['has_time']:.2f}s")
    print(f"  Winner: {comparison} ({speedup:.2f}x)")

    print(f"\n📋 list_objects Performance:")
    if git_results['list_time'] < dos_results['list_time']:
        speedup = dos_results['list_time'] / git_results['list_time']
        comparison = "🟢 Git faster"
    else:
        speedup = git_results['list_time'] / dos_results['list_time']
        comparison = "🔴 DOS faster"

    print(f"  Git: {git_results['list_time']:.2f}s")
    print(f"  DOS: {dos_results['list_time']:.2f}s")
    print(f"  Winner: {comparison} ({speedup:.2f}x)")

    print(f"\n🎲 Random Read Performance (50 files):")
    if git_results['random_read_time'] < dos_results['random_read_time']:
        speedup = dos_results['random_read_time'] / git_results['random_read_time']
        comparison = "🟢 Git faster"
    else:
        speedup = git_results['random_read_time'] / dos_results['random_read_time']
        comparison = "🔴 DOS faster"

    print(f"  Git: {git_results['random_read_time']:.2f}s")
    print(f"  DOS: {dos_results['random_read_time']:.2f}s")
    print(f"  Winner: {comparison} ({speedup:.2f}x)")

    print(f"\n🗑️  Delete Performance ({git_results['delete_count']} objects):")
    if git_results['delete_time'] < dos_results['delete_time']:
        speedup = dos_results['delete_time'] / git_results['delete_time']
        comparison = "🟢 Git faster"
    else:
        speedup = git_results['delete_time'] / dos_results['delete_time']
        comparison = "🔴 DOS faster"

    print(f"  Git: {git_results['delete_time']:.2f}s ({git_results['delete_rate']:.2f} obj/s)")
    print(f"  DOS: {dos_results['delete_time']:.2f}s ({dos_results['delete_rate']:.2f} obj/s)")
    print(f"  Winner: {comparison} ({speedup:.2f}x)")


def main():
    """Main benchmark runner."""
    print("="*70)
    print("REALISTIC WORKLOAD BENCHMARK: 100MB of Inhomogeneous Files")
    print("="*70)

    print("\nGenerating realistic file size distribution...")
    file_sizes, total_bytes = generate_realistic_files(target_mb=100)

    print(f"Generated {len(file_sizes):,} files totaling {total_bytes / (1024*1024):.2f} MB")

    # Create temporary directories
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Initialize Git backend
        print("\nInitializing Git backend...")
        git_path = tmppath / 'git_repo'
        git_backend = GitRepositoryBackend(git_path)
        git_backend.initialise()

        # Initialize DiskObjectStore backend
        print("Initializing DiskObjectStore backend...")
        dos_path = tmppath / 'dos_container'
        dos_container = Container(str(dos_path))
        dos_container.init_container()
        dos_backend = DiskObjectStoreRepositoryBackend(container=dos_container)

        # Run benchmarks
        git_results = benchmark_backend("GitRepositoryBackend", git_backend, file_sizes)
        dos_results = benchmark_backend("DiskObjectStoreRepositoryBackend", dos_backend, file_sizes)

        # Print comparison
        print_comparison(git_results, dos_results)

        print(f"\n{'='*70}")
        print("Benchmark complete!")
        print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
