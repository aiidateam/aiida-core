# -*- coding: utf-8 -*-
"""Measure on-disk size of the protobuf schema entry and instance value blobs."""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from poc.orm._core.nodes.data.protobuf import encode_schema, encode_values
from poc.orm.nodes.data import TrajectoryData, load_node
from poc.storage import load_profile
from poc.storage.profile import get_profile

SCHEMA = TrajectoryData.schema_spec


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Raw protobuf blob sizes (in-memory)
    # ------------------------------------------------------------------
    section("1. Raw protobuf blob sizes (bytes)")
    schema_blob = encode_schema(SCHEMA)
    print(f"schema blob (TrajectoryMetadata, {len(SCHEMA.fields)} fields): {len(schema_blob)} B")

    samples = {
        "small  (label='water-md', nsteps=1000, tags=2)": dict(label='water-md', nsteps=1000, tags=['production', 'nvt']),
        "no-tags (label='water-md', nsteps=1000)": dict(label='water-md', nsteps=1000),
        "long   (label='x'*200, nsteps=999999, tags=10)": dict(
            label='x' * 200, nsteps=999999, tags=[f'tag-{i:02d}' for i in range(10)]
        ),
    }
    payloads = {}
    for name, values in samples.items():
        blob = encode_values(SCHEMA, values)
        payloads[name] = blob
        print(f"instance blob {name}: {len(blob)} B")

    # field-name overhead: the value blob repeats each field name as a string key
    import json
    print("\nfor reference, the same payloads as JSON:")
    for name, values in samples.items():
        print(f"  {name}: {len(json.dumps(values, sort_keys=True).encode())} B (protobuf: {len(payloads[name])} B)")

    # ------------------------------------------------------------------
    # 2. SQLite accounting for one schema row + N node rows
    # ------------------------------------------------------------------
    section("2. SQLite on-disk footprint")
    tmp = Path(tempfile.mkdtemp()) / "poc.sqlite"
    conn = load_profile(str(tmp))

    # trigger schema install + store a few nodes through the public API
    node_ids = []
    for values in samples.values():
        node = TrajectoryData(**values)
        node_ids.append(node.store())

    page_size = conn.execute('PRAGMA page_size').fetchone()[0]
    db_bytes = tmp.stat().st_size
    print(f"page_size              : {page_size} B")
    print(f"database file          : {db_bytes} B ({db_bytes / page_size:.0f} pages)")

    # logical payload bytes stored in the BLOB columns
    schema_col = conn.execute('SELECT length(protobuf_blob) FROM schemas').fetchone()[0]
    schema_name_col = conn.execute('SELECT length(schema_name) FROM schemas').fetchone()[0]
    print(f"schemas.protobuf_blob  : {schema_col} B (+ {schema_name_col} B schema_name key)")
    rows = conn.execute('SELECT id, length(value_blob) FROM nodes').fetchall()
    for node_id, length in rows:
        print(f"nodes[{node_id}].value_blob: {length} B")
    total_blobs = schema_col + sum(length for _, length in rows)
    print(f"sum of all blob columns: {total_blobs} B")

    # per-row/page accounting with dbstat (available in most SQLite builds)
    try:
        conn.execute('CREATE VIRTUAL TABLE IF NOT EXISTS dbstat USING dbstat')
        stats = conn.execute(
            'SELECT name, COUNT(*) n_pages, SUM(pgsize) page_bytes '
            'FROM dbstat GROUP BY name'
        ).fetchall()
        print("\npage bytes per b-tree (dbstat):")
        for tbl, n_pages, page_bytes in stats:
            print(f"  {tbl:28s}: {page_bytes:>6} B in {n_pages:>2} pages")
        conn.execute('DROP TABLE IF EXISTS dbstat')
    except sqlite3.OperationalError as exc:
        print(f"\ndbstat unavailable: {exc}")

    # ------------------------------------------------------------------
    # 3. Scaling: cost per additional node
    # ------------------------------------------------------------------
    section("3. Marginal cost per stored instance")
    before = rows[0][1]
    conn2 = get_profile()
    small = dict(label='water-md', nsteps=1000, tags=['production', 'nvt'])
    ids = [TrajectoryData(**small).store() for _ in range(100)]
    sizes = conn2.execute(
        f'SELECT length(value_blob) FROM nodes WHERE id IN ({",".join("?" * len(ids))})',
        ids,
    ).fetchall()
    print(f"100 identical small instances: {sizes[0][0]} B each (schema blob stored once: {schema_col} B)")
    print("=> the schema is O(1) per type; each instance pays its own blob + a repeated 'TrajectoryMetadata' key")
    key_len = conn2.execute('SELECT length(schema_name) FROM nodes LIMIT 1').fetchone()[0]
    print(f"   (plus {key_len} B nodes.schema_name text per row in this PoC schema)")

    # round-trip sanity: rebuild one and show it decodes
    rebuilt = load_node(ids[0], TrajectoryData)
    print(f"\nround-trip check: {rebuilt}")

    # file size growth
    conn2.commit()
    print(f"db file after 103 nodes: {tmp.stat().st_size} B")


if __name__ == "__main__":
    main()
