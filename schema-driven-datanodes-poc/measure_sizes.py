# -*- coding: utf-8 -*-
"""Measure on-disk size of the protobuf schema entry and instance value blobs."""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from poc.orm._core.nodes.data.protobuf import encode_schema, encode_values
from poc.orm.nodes.data import FieldSpec, SchemaSpec, TrajectoryData, load_node
from poc.storage import load_profile
from poc.storage.profile import get_profile
from poc.storage.sqlite_temp.schema_store import store_schema

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
    rows = conn.execute('SELECT id, schema_id, length(value_blob) FROM nodes').fetchall()
    for node_id, schema_id, length in rows:
        print(f"nodes[{node_id}].value_blob: {length} B (schema_id={schema_id})")
    total_blobs = schema_col + sum(length for _, _, length in rows)
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
    conn2 = get_profile()
    small = dict(label='water-md', nsteps=1000, tags=['production', 'nvt'])
    ids = [TrajectoryData(**small).store() for _ in range(100)]
    sizes = conn2.execute(
        f'SELECT length(value_blob) FROM nodes WHERE id IN ({",".join("?" * len(ids))})',
        ids,
    ).fetchall()
    print(f"100 identical small instances: {sizes[0][0]} B each (schema blob stored once per version: {schema_col} B)")
    print("=> the schema is O(1) per type+version; each instance pays its own blob and a small int schema_id")
    row_size = conn2.execute('SELECT schema_id FROM nodes LIMIT 1').fetchone()[0]
    print(
        f"   (schema_id={row_size} stores inline as a ~1-2 B varint in the record; "
        'the old design repeated an 18 B text key per row)'
    )

    # round-trip sanity: rebuild one and show it decodes
    rebuilt = load_node(ids[0], TrajectoryData)
    print(f"\nround-trip check: {rebuilt}")

    # file size growth
    conn2.commit()
    print(f"db file after 103 nodes: {tmp.stat().st_size} B")

    # ------------------------------------------------------------------
    # 4. Version pinning and FK enforcement
    # ------------------------------------------------------------------
    section("4. Version pinning & FK enforcement")
    v1_id = TrajectoryData(label='v1-run', nsteps=10).store()

    # publish a v2 of the same schema name: drops 'nsteps' to prove pinning
    v2 = SchemaSpec(
        name='TrajectoryMetadata',
        fields=(FieldSpec('label', 0, validator_name='non_empty', description='Human-readable label'),),
    )
    store_schema(conn2, v2, format_version=2)
    print(f"installed format_version=2 of {v2.name!r}; v1 node id {v1_id} still: {load_node(v1_id, TrajectoryData)}")

    v2_id = TrajectoryData(label='v2-run', nsteps=20).store()
    pinned = conn2.execute(
        'SELECT n.id, s.schema_name, s.format_version FROM nodes n JOIN schemas s ON s.id = n.schema_id ORDER BY n.id'
    ).fetchall()
    by_version = {}
    for node_id, name, version in pinned:
        by_version.setdefault(version, []).append(node_id)
    print("per-node pinned schema version (join over schemas.id):")
    for version, ids in sorted(by_version.items()):
        print(f"  format v{version}: {len(ids)} nodes, e.g. ids {ids[:3]}{'...' if len(ids) > 3 else ''}")
    print(f"  v1 node {v1_id} decodes against v1: {load_node(v1_id, TrajectoryData)}")
    print(f"  v2 node {v2_id} decodes against v2: {load_node(v2_id, TrajectoryData)}")

    try:
        conn2.execute("INSERT INTO nodes(schema_id, value_blob) VALUES (999, x'00')")
        conn2.commit()
        print('WARNING: bogus schema_id was accepted')
    except sqlite3.IntegrityError as exc:
        print(f"FK enforced on insert: {exc}")


if __name__ == "__main__":
    main()
