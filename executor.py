import json
import os
from btree_engine import BTree
from sql_parser import parse

SCHEMA_FILE = "schema.json"


class Database:
    def __init__(self):
        if os.path.exists(SCHEMA_FILE):
            with open(SCHEMA_FILE) as f:
                self.schema = json.load(f)
        else:
            self.schema = {}  # table_name -> {"columns": [...], "next_id": int}

        self.trees = {}  # table_name -> BTree instance

    def _save_schema(self):
        with open(SCHEMA_FILE, 'w') as f:
            json.dump(self.schema, f)

    def _get_tree(self, table):
        if table not in self.trees:
            self.trees[table] = BTree(f"{table}.db")
        return self.trees[table]

    def execute(self, sql):
        stmt = parse(sql)

        if stmt.kind == 'CREATE':
            self.schema[stmt.table] = {"columns": stmt.columns, "next_id": 1}
            self._save_schema()
            self._get_tree(stmt.table)  # create the file
            return f"Table '{stmt.table}' created."

        elif stmt.kind == 'INSERT':
            table_info = self.schema[stmt.table]
            columns = table_info["columns"]
            row_id = table_info["next_id"]

            row = dict(zip(columns, stmt.values))
            tree = self._get_tree(stmt.table)
            tree.insert(str(row_id), json.dumps(row))

            table_info["next_id"] += 1
            self._save_schema()
            return f"1 row inserted into '{stmt.table}'."

        elif stmt.kind == 'SELECT':
            tree = self._get_tree(stmt.table)
            results = []

            if stmt.where_col == 'id' and stmt.where_val is not None:
                # Direct lookup by row id (the B-tree key)
                value = tree.find(stmt.where_val)
                if value:
                    results.append(json.loads(value))
            else:
                # Full scan: walk all leaves
                results = self._full_scan(tree, stmt.where_col, stmt.where_val)

            return results

        elif stmt.kind == 'UPDATE':
            tree = self._get_tree(stmt.table)
            matching_keys = self._collect_matching_keys(tree, stmt.where_col, stmt.where_val)

            count = 0
            for row_id in matching_keys:
                value = tree.find(row_id)
                row = json.loads(value)
                row[stmt.set_col] = stmt.set_val
                tree.update(row_id, json.dumps(row))
                count += 1
            return f"{count} row(s) updated."

        elif stmt.kind == 'DELETE':
            tree = self._get_tree(stmt.table)
            matching_keys = self._collect_matching_keys(tree, stmt.where_col, stmt.where_val)

            count = 0
            for row_id in matching_keys:
                if tree.delete(row_id):
                    count += 1
            return f"{count} row(s) deleted."

    def _full_scan(self, tree, where_col, where_val):
        """Walk every leaf node in the tree and collect matching rows."""
        results = []
        self._scan_node(tree.pager, tree.root_page, results, where_col, where_val)
        return results

    def _scan_node(self, pager, page_num, results, where_col, where_val):
        from btree import read_node, LeafNode
        node = read_node(pager, page_num)
        if isinstance(node, LeafNode):
            for key, value in node.cells:
                row = json.loads(value)
                if where_col is None or str(row.get(where_col)) == str(where_val):
                    results.append(row)
        else:
            for child_page in node.children:
                self._scan_node(pager, child_page, results, where_col, where_val)

    def _collect_matching_keys(self, tree, where_col, where_val):
        """Like _scan_node but returns row IDs (keys) instead of row data."""
        from btree import read_node, LeafNode
        matching_keys = []

        def scan(page_num):
            node = read_node(tree.pager, page_num)
            if isinstance(node, LeafNode):
                for key, value in node.cells:
                    row = json.loads(value)
                    if where_col is None or str(row.get(where_col)) == str(where_val):
                        matching_keys.append(key)
            else:
                for child_page in node.children:
                    scan(child_page)

        scan(tree.root_page)
        return matching_keys

    def close(self):
        for tree in self.trees.values():
            tree.close()