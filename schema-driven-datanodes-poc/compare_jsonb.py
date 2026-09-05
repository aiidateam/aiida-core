# -*- coding: utf-8 -*-
"""Compare on-disk size of protobuf value_blob vs JSON text vs JSONB (SQLite 3.45+),
with and without zstd compression at the application layer.

For identical node payloads we measure:
  1. logical bytes stored per row
  2. on-disk footprint via dbstat (content bytes vs allocated page bytes)
for six encodings: pb / json / jsonb and each of those zstd-compressed.
"""
from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

import zstandard as zstd

from poc.orm._core.nodes.data.protobuf import encode_values
from poc.orm.nodes.data import TrajectoryData

SCHEMA = TrajectoryData.schema_spec
COMPRESSOR = zstd.ZstdCompressor(level=3)

# the exact dict Data.store() persists (validated, defaults filled in)
SMALL = dict(label='water-md', nsteps=1000, tags=['production', 'nvt'], code='cp2k')
LONG = dict(label='x' * 200, nsteps=999999, tags=[f'tag-{i:02d}' for i in range(10)], code='cp2k')
BIG = dict(label='run-42', nsteps=1_000_000, tags=[f'trajectory-frame-{i:05d}' for i in range(2000)], code='cp2k')

N_ROWS_SMALL = 10_000
N_ROWS_BIG = 300


def json_text(values: dict) -> str:
    return json.dumps(values, sort_keys=True, separators=(',', ':'))


def jsonb_bytes(conn: sqlite3.Connection, values: dict) -> bytes:
    return conn.execute('SELECT jsonb(?)', (json_text(values),)).fetchone()[0]


# encodings: kind -> (ddl column decl, value expression for INSERT, bytes-for-length)
ENCODINGS = {
    # raw variants: value stored as-is
    'pb':      ('value_blob BLOB',          'value_blob'),
    'json':    ('value_json TEXT',          'value_json'),
    'jsonb':   ('value_jsonb BLOB',         'value_jsonb'),
    # zstd-compressed variants
    'pb+zstd': ('value_blob BLOB',          'value_blob'),
    'json+zstd': ('value_json TEXT',        'value_json'),
    'jsonb+zstd': ('value_jsonb BLOB',      'value_jsonb'),
}
# which raw encoding each zstd variant compresses
RAW_OF = {'pb+zstd': 'pb', 'json+zstd': 'json', 'jsonb+zstd': 'jsonb'}


def encode_raw(conn: sqlite3.Connection, kind: str, values: dict) -> bytes:
    if kind == 'pb':
        return encode_values(SCHEMA, values)
    if kind == 'json':
        return json_text(values).encode()
    return jsonb_bytes(conn, values)  # jsonb


def build(conn: sqlite3.Connection, kind: str) -> None:
    """Create a single-table db for one encoding; return the store column name."""
    ddl = ENCODINGS[kind][0]
    conn.execute(f'CREATE TABLE t (id INTEGER PRIMARY KEY, schema_name TEXT, {ddl} NOT NULL)')


def store_rows(conn: sqlite3.Connection, kind: str, values: dict, n: int) -> None:
    raw = encode_raw(conn, kind, values)
    if kind in RAW_OF:
        raw = COMPRESSOR.compress(raw)
    col = ENCODINGS[kind][1]
    if kind == 'json':
        conn.executemany(
            f"INSERT INTO t(schema_name, {col}) VALUES ('TrajectoryMetadata', ?)",
            [(raw.decode(),)] * n)
    else:
        conn.executemany(
            f"INSERT INTO t(schema_name, {col}) VALUES ('TrajectoryMetadata', ?)",
            [(raw,)] * n)


def size_sql(kind: str) -> str:
    return f'SELECT length({ENCODINGS[kind][1]}) FROM t'


def logical(conn: sqlite3.Connection, tag: str, values: dict) -> None:
    """One row per encoding, report raw and compressed logical sizes."""
    sizes = {}
    for kind in ENCODINGS:
        build(conn, kind)
        store_rows(conn, kind, values, 1)
        sizes[kind] = conn.execute(size_sql(kind)).fetchone()[0]
        conn.execute('DROP TABLE t')
    print(f'  {tag:6s} raw:  pb={sizes["pb"]:>5d} B  json={sizes["json"]:>5d} B  jsonb={sizes["jsonb"]:>5d} B')
    print(f'         zstd: pb={sizes["pb+zstd"]:>5d} B  json={sizes["json+zstd"]:>5d} B  '
          f'jsonb={sizes["jsonb+zstd"]:>5d} B')


def on_disk(tmp: Path, tag: str, values: dict, n: int) -> None:
    """One db file per encoding; report file size + dbstat content/allocated bytes."""
    print(f'\nOn-disk footprint: {n:,} identical {tag} rows per encoding (page_size=4096)')
    print(f'{"encoding":<10}{"file B":>10}{"pages":>6}{"alloc B":>11}{"content B":>11}  '
          f'{"alloc/row":>9}{"content/row":>12}')
    for kind in ENCODINGS:
        path = tmp / f'{tag}-{kind}.sqlite'
        conn = sqlite3.connect(path)
        build(conn, kind)
        store_rows(conn, kind, values, n)
        conn.execute('CREATE VIRTUAL TABLE dbstat USING dbstat')
        st = path.stat().st_size
        pages, pgsize, payload = conn.execute(
            'SELECT COUNT(*), SUM(pgsize), SUM(payload) FROM dbstat WHERE name = ?', ('t',)).fetchone()
        print(f'{kind:<10}{st:>10,}{pages:>6,}{pgsize:>11,}{payload:>11,}  '
              f'{pgsize / n:>9.2f}{payload / n:>12.2f}')
        conn.close()


def main() -> None:
    tmp = Path(tempfile.mkdtemp())

    print('Logical bytes for one stored row (schema: TrajectoryMetadata, 4 fields)')
    for tag, values in (('small', SMALL), ('long', LONG), ('big node', BIG)):
        conn = sqlite3.connect(':memory:')
        logical(conn, tag, values)
        conn.close()

    on_disk(tmp, 'small', SMALL, N_ROWS_SMALL)
    on_disk(tmp, 'big', BIG, N_ROWS_BIG)


if __name__ == '__main__':
    main()