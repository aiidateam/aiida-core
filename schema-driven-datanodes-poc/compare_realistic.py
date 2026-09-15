# -*- coding: utf-8 -*-
"""Size comparison with realistic string content instead of degenerate placeholders.

Labels are natural-language text assembled from a word pool (seeded, so reproducible);
tags are enumeration-style items with a shared prefix and unique suffix (realistic for
frame/sample/batch ids) — some cross-item redundancy, never the same entry everywhere.
"""
from __future__ import annotations

import json
import random
import sqlite3
import zstandard as zstd

from poc.orm._core.nodes.data.protobuf import encode_values
from poc.orm.nodes.data import TrajectoryData
from poc.orm.nodes.data.schema import SchemaSpec

RNG = random.Random(42)
POOL = [
    'cp2k', 'nvt', 'production', 'water', 'box', '300K', 'equilibrated', 'structural',
    'optimization', 'simulation', 'input', 'output', 'temperature', 'pressure',
    'ensemble', 'nanoseconds', 'trajectory', 'density', 'sampling', 'relaxed',
]


def natural_label(target: int) -> str:
    """Join random words until >= target chars, then cut (last word may be truncated)."""
    words: list[str] = []
    while sum(len(w) + 1 for w in words) < target:
        words.append(RNG.choice(POOL))
    return ' '.join(words)[:target]


TRIMMED = SchemaSpec(
    name=TrajectoryData.schema_spec.name,
    fields=tuple(f for f in TrajectoryData.schema_spec.fields if f.name in ('label', 'tags')),
)

C = zstd.ZstdCompressor(level=3)


def main() -> None:
    conn = sqlite3.connect(':memory:')

    labels = {
        'small': 'water-md',
        'medium': natural_label(60),
        'long': natural_label(200),
        'big': 'run-42',
    }
    tags = {
        'small': ['production', 'nvt'],
        'medium': [f'{"".join(RNG.choice(POOL).replace(" " ,"-")[:6])}-{i:02d}' for i in range(3)],
        'long': [f'sample-{i:02d}' for i in range(10)],
        'big': [f'trajectory-frame-{i:05d}' for i in range(2000)],
    }
    payloads = {
        'small': {'label': labels['small'], 'tags': tags['small']},
        'medium': {'label': labels['medium'], 'tags': tags['medium']},
        'long': {'label': labels['long'], 'tags': tags['long']},
        'big': {'label': labels['big'], 'tags': tags['big']},
    }

    print('labels as generated:')
    for k in ('medium', 'long'):
        print(f'  {k:6s} ({len(labels[k])} chars): {labels[k]!r}')
    print(f'  {"tags medium":6s}: {tags["medium"]!r}')

    def jsonb(text: str) -> bytes:
        return conn.execute('SELECT jsonb(?)', (text,)).fetchone()[0]

    print()
    print('| payload type | BLOB protobuf | JSON text | JSONB binary | pb-blob+zstd | json+zstd | jsonb+zstd |')
    print('|---|---|---|---|---|---|---|')
    for name, values in payloads.items():
        pb = encode_values(TRIMMED, values)
        js = json.dumps(values, sort_keys=True, separators=(',', ':')).encode()
        jb = jsonb(js.decode())
        print(f'| {name} (str{len(values["label"])}, list[str, {len(values["tags"])}]) '
              f'| {len(pb)} B | {len(js)} B | {len(jb)} B '
              f'| {len(C.compress(pb))} B | {len(C.compress(js))} B | {len(C.compress(jb))} B |')

    print()
    print('compression ratios (zstd level 3), realistic string content:')
    for name, values in payloads.items():
        pb = encode_values(TRIMMED, values)
        js = json.dumps(values, sort_keys=True, separators=(',', ':')).encode()
        jb = jsonb(js.decode())
        print(f'  {name:6s} pb {len(pb)/len(C.compress(pb)):5.1f}x   '
              f'json {len(js)/len(C.compress(js)):5.1f}x   jsonb {len(jb)/len(C.compress(jb)):5.1f}x')


if __name__ == '__main__':
    main()