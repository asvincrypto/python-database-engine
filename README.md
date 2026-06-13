
# Python Database Engine

A relational database engine built from scratch in Python, featuring disk backed
storage, a B-tree index, a SQL parser, a query executor, and write-ahead logging
for crash recovery.

## Features

- **Page-based storage**: Data is persisted to disk in fixed-size 4KB pages.
- **B-tree indexing**: Keys are stored in a B-tree with automatic node splitting,
  giving O(log n) lookups and ordered traversal.
- **SQL support**: A hand-written parser supports `CREATE TABLE`, `INSERT`,
  `SELECT` (with `WHERE`), `UPDATE`, and `DELETE`.
- **Write-ahead logging (WAL)**: Every page write is logged before it's applied,
  so the database can recover cleanly from a crash mid-write.
- **Interactive REPL**: A command-line shell for running SQL directly.

## Architecture

```
storage.py        -> Pager: low-level page read/write to disk
btree.py           -> LeafNode / InternalNode: B-tree node serialization & logic
btree_engine.py    -> BTree: ties pages together into a working B-tree
                      (insert, find, update, delete, splits)
wal.py             -> WAL: write-ahead log + crash recovery replay
sql_parser.py      -> Parses SQL strings into structured statements
executor.py        -> Database: maps SQL statements onto B-tree operations,
                      manages table schemas
repl.py            -> Interactive command-line interface
```

### How it works

1. Each table is stored in its own `.db` file as a B-tree of 4KB pages.
2. Rows are stored as `(row_id, JSON-encoded row)` pairs, with `row_id` as the
   B-tree key.
3. Table schemas (column names, next auto-increment ID) are tracked in
   `schema.json`.
4. Before any page is written to a `.db` file, the change is first appended to
   `wal.log`. On startup, any unflushed WAL entries are replayed — this ensures
   the database can recover from a crash that happens mid-write.

## Usage

```bash
python repl.py
```

## Supported SQL

The engine supports the core operations:

- `CREATE TABLE users (id, name, age)` — create a table with the given columns
- `INSERT INTO users VALUES (1, 'Alice', 30)` — add a row
- `SELECT * FROM users` — get all rows
- `SELECT * FROM users WHERE id = 1` — get rows matching a condition
- `UPDATE users SET age = 31 WHERE id = 1` — update matching rows
- `DELETE FROM users WHERE id = 1` — delete matching rows
