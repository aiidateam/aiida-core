# Schema-driven data nodes PoC

This is a **self-contained** proof of concept for **AiiDA data nodes only**.
It mirrors the repository hierarchy loosely enough to discuss where code could live in `aiida-core`,
without trying to model the whole ORM.

It demonstrates this protobuf-only design for data nodes:

- define `TrajectoryMetadata` beside `TrajectoryData` in `orm/nodes/data/trajectory.py`
- store a **versioned protobuf schema blob** in SQLite
- load that schema blob back into Python
- validate a `TrajectoryData(...)` instance during `.store()` against the restored schema
- delete the Python object and reconstruct it with `load_node(...)`

It does **not** store pickled Python or Pydantic objects.

## Why this PoC exists

From the discussion:

- `pickle` is fast but unsafe for untrusted or long-lived persisted data.
- `msgpack`, `CBOR`, `orjson`, and `protobuf` are safer because they decode data, not behavior.
- For long-lived, versioned binary state, `protobuf` is attractive because versioning is part of the design.
- `protobuf` lets the persisted schema blob stay declarative and versioned.

So this PoC explores a protobuf-only path:

- **protobuf** for persisted schema blobs
- **SQLite** as the durable store
- **Python validation code** selected from trusted validator identifiers

## Why not pickle?

Because pickled data can execute arbitrary Python reconstruction behavior on load.
That is fine for trusted, ephemeral internal caches, but a bad default for canonical persisted state.

## Why protobuf instead of msgpack/orjson here?

- `msgpack` and `orjson` are both viable safe formats for data.
- But this experiment needs **versioned schema blobs**.
- `protobuf` has a stronger built-in compatibility story than `msgpack`.
- `orjson` is excellent for JSON boundaries, but this PoC is about compact, versioned internal binary state.

## Why no Pydantic in this version?

Because this version is meant to test the opposite choice from the earlier prototype:

- keep the persisted state declarative and versioned with protobuf
- validate with trusted Python functions chosen by identifier
- construct the final Python object directly

That keeps the hot path free of runtime Pydantic model building.

## Round trip for data nodes

```text
     schema declaration in Python
                |
                v
        SchemaSpec dataclass
                |
                v
     protobuf SchemaEnvelope bytes
                |
                v
          SQLite BLOB column
                |
                v
        load blob from SQLite
                |
                v
     protobuf parse -> SchemaSpec
                |
                v
 validate payload dict/list/scalars against schema
                |
                v
     construct Python TrajectoryData
```

## Layout

```text
schema-driven-datanodes-poc/
├── __main__.py
├── README.md
└── poc/
    ├── __init__.py
    ├── orm/
    │   ├── __init__.py
    │   ├── _core/
    │   │   ├── __init__.py
    │   │   └── nodes/
    │   │       ├── __init__.py
    │   │       ├── node.py
    │   │       └── data/
    │   │           ├── __init__.py
    │   │           ├── node.py
    │   │           ├── schema.py
    │   │           └── protobuf.py
    │   └── nodes/
    │       ├── __init__.py
    │       └── data/
    │           ├── __init__.py
    │           ├── data.py
    │           └── trajectory.py
    └── storage/
        ├── __init__.py
        └── sqlite_temp/
            ├── __init__.py
            └── schema_store.py
```

## Run

```console
python -m poc
```

## Notes on scope

This layout is intentionally for **AiiDA data nodes only**.
It does not try to model process nodes, links, repositories, or the full ORM hierarchy.

The example runner uses only the public `aiida.orm.nodes.data` API for the round trip.
`__main__` keeps the profile setup and demo flow in helper functions separate from `main()`.
A singleton backend is activated with `aiida.storage.load_profile(database_url)` and then used implicitly by the ORM.
Schema installation is automatic on first data-node use.
The user-facing flow is:

```python
load_profile(':memory:')
node = TrajectoryData(label='water-md', nsteps=1000, tags=['production', 'nvt'])
node_id = node.store()
del node
rebuilt = load_node(node_id, TrajectoryData)
```
