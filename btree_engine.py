from storage import Pager, PAGE_SIZE
from btree import LeafNode, InternalNode, read_node, LEAF_NODE, INTERNAL_NODE


class BTree:
    def __init__(self, filename):
        self.pager = Pager(filename)
        if self.pager.num_pages() == 0:
            # Fresh database: create an empty root leaf at page 0
            root = LeafNode()
            self.pager.write_page(0, root.serialize())
            self.root_page = 0
        else:
            self.root_page = 0  # we always keep root at page 0

    def insert(self, key, value):
        result = self._insert(self.root_page, key, value)
        if result is not None:
            # Root split — create a new root (internal node)
            left, right, split_key = result
            left_page = self.pager.num_pages()
            right_page = left_page + 1
            self.pager.write_page(left_page, left.serialize())
            self.pager.write_page(right_page, right.serialize())

            new_root = InternalNode()
            new_root.keys = [split_key]
            new_root.children = [left_page, right_page]
            self.pager.write_page(self.root_page, new_root.serialize())

    def _insert(self, page_num, key, value):
        node = read_node(self.pager, page_num)

        if isinstance(node, LeafNode):
            split = node.insert(key, value)
            if split is None:
                self.pager.write_page(page_num, node.serialize())
                return None
            else:
                # This leaf split — caller (parent) handles it
                return split
        else:
            # Internal node: find correct child and recurse
            child_index = node.find_child_index(key)
            child_page = node.children[child_index]
            result = self._insert(child_page, key, value)

            if result is None:
                return None

            # Child split — insert new key/child into this internal node
            left, right, split_key = result
            left_page = self.pager.num_pages()
            right_page = left_page + 1
            self.pager.write_page(left_page, left.serialize())
            self.pager.write_page(right_page, right.serialize())

            node.keys.insert(child_index, split_key)
            node.children[child_index] = left_page
            node.children[child_index + 1:child_index + 1] = [right_page]

            # For simplicity, this version doesn't split internal nodes further.
            self.pager.write_page(page_num, node.serialize())
            return None

    def find(self, key):
        return self._find(self.root_page, key)

    def _find(self, page_num, key):
        node = read_node(self.pager, page_num)
        if isinstance(node, LeafNode):
            return node.find(key)
        else:
            child_index = node.find_child_index(key)
            return self._find(node.children[child_index], key)

    def delete(self, key):
        """Delete a key. Simplified: only works correctly within a leaf
        directly reachable via root_page traversal (no rebalancing)."""
        return self._delete(self.root_page, key)

    def _delete(self, page_num, key):
        node = read_node(self.pager, page_num)
        if isinstance(node, LeafNode):
            found = node.delete(key)
            if found:
                self.pager.write_page(page_num, node.serialize())
            return found
        else:
            child_index = node.find_child_index(key)
            return self._delete(node.children[child_index], key)

    def update(self, key, value):
        """Update is just replacing the value for an existing key
        (no split needed since no new cell is added)."""
        return self._update(self.root_page, key, value)

    def _update(self, page_num, key, value):
        node = read_node(self.pager, page_num)
        if isinstance(node, LeafNode):
            for i, (k, v) in enumerate(node.cells):
                if k == key:
                    node.cells[i] = (key, value)
                    self.pager.write_page(page_num, node.serialize())
                    return True
            return False
        else:
            child_index = node.find_child_index(key)
            return self._update(node.children[child_index], key, value)

    def close(self):
        self.pager.close()