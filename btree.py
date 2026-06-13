import struct
from storage import PAGE_SIZE

# Node types
LEAF_NODE = 0
INTERNAL_NODE = 1

# Header layout: node_type (1 byte) + num_cells/num_keys (4 bytes)
HEADER_SIZE = 5

MAX_LEAF_CELLS = 3  # small number for easy testing; raise later


class LeafNode:
    def __init__(self, page_data=None):
        if page_data is None:
            self.num_cells = 0
            self.cells = []  # list of (key, value) where key/value are strings
        else:
            self.deserialize(page_data)

    def serialize(self):
        buf = bytearray(PAGE_SIZE)
        buf[0] = LEAF_NODE
        struct.pack_into('<I', buf, 1, len(self.cells))
        offset = HEADER_SIZE
        for key, value in self.cells:
            key_bytes = key.encode('utf-8')
            value_bytes = value.encode('utf-8')
            struct.pack_into('<I', buf, offset, len(key_bytes))
            offset += 4
            buf[offset:offset+len(key_bytes)] = key_bytes
            offset += len(key_bytes)
            struct.pack_into('<I', buf, offset, len(value_bytes))
            offset += 4
            buf[offset:offset+len(value_bytes)] = value_bytes
            offset += len(value_bytes)
        return bytes(buf)

    def deserialize(self, page_data):
        self.num_cells = struct.unpack_from('<I', page_data, 1)[0]
        self.cells = []
        offset = HEADER_SIZE
        for _ in range(self.num_cells):
            key_len = struct.unpack_from('<I', page_data, offset)[0]
            offset += 4
            key = page_data[offset:offset+key_len].decode('utf-8')
            offset += key_len
            value_len = struct.unpack_from('<I', page_data, offset)[0]
            offset += 4
            value = page_data[offset:offset+value_len].decode('utf-8')
            offset += value_len
            self.cells.append((key, value))

    def insert(self, key, value):
        # Update existing key
        for i, (k, v) in enumerate(self.cells):
            if k == key:
                self.cells[i] = (key, value)
                return None  # no split

        # Insert in sorted position
        inserted = False
        for i, (k, v) in enumerate(self.cells):
            if k > key:
                self.cells.insert(i, (key, value))
                inserted = True
                break
        if not inserted:
            self.cells.append((key, value))
        self.num_cells = len(self.cells)

        # Check if we need to split
        if self.num_cells > MAX_LEAF_CELLS:
            return self.split()
        return None  # no split

    def delete(self, key):
        for i, (k, v) in enumerate(self.cells):
            if k == key:
                del self.cells[i]
                self.num_cells = len(self.cells)
                return True
        return False

    def split(self):
        """
        Split this leaf into two leaves.
        Returns (left_node, right_node, split_key) where split_key
        is the first key of right_node — used by the parent to
        decide which child to route to.
        """
        mid = len(self.cells) // 2

        left = LeafNode()
        left.cells = self.cells[:mid]
        left.num_cells = len(left.cells)

        right = LeafNode()
        right.cells = self.cells[mid:]
        right.num_cells = len(right.cells)

        split_key = right.cells[0][0]
        return (left, right, split_key)

    def find(self, key):
        for k, v in self.cells:
            if k == key:
                return v
        return None


class InternalNode:
    """
    An internal node stores keys and child page numbers.
    For N keys, there are N+1 children.
    children[i] holds all keys < keys[i]
    children[N] holds all keys >= keys[N-1]
    """
    def __init__(self, page_data=None):
        if page_data is None:
            self.keys = []          # list of split keys (strings)
            self.children = []      # list of page numbers (ints)
        else:
            self.deserialize(page_data)

    def serialize(self):
        buf = bytearray(PAGE_SIZE)
        buf[0] = INTERNAL_NODE
        struct.pack_into('<I', buf, 1, len(self.keys))
        offset = HEADER_SIZE
        # Write children first (all page numbers)
        for child in self.children:
            struct.pack_into('<I', buf, offset, child)
            offset += 4
        # Then write keys
        for key in self.keys:
            key_bytes = key.encode('utf-8')
            struct.pack_into('<I', buf, offset, len(key_bytes))
            offset += 4
            buf[offset:offset+len(key_bytes)] = key_bytes
            offset += len(key_bytes)
        return bytes(buf)

    def deserialize(self, page_data):
        num_keys = struct.unpack_from('<I', page_data, 1)[0]
        offset = HEADER_SIZE
        self.children = []
        for _ in range(num_keys + 1):
            child = struct.unpack_from('<I', page_data, offset)[0]
            offset += 4
            self.children.append(child)
        self.keys = []
        for _ in range(num_keys):
            key_len = struct.unpack_from('<I', page_data, offset)[0]
            offset += 4
            key = page_data[offset:offset+key_len].decode('utf-8')
            offset += key_len
            self.keys.append(key)

    def find_child_index(self, key):
        """Return index of child page that should contain `key`."""
        for i, k in enumerate(self.keys):
            if key < k:
                return i
        return len(self.children) - 1


def read_node(pager, page_num):
    """Read a page and return either a LeafNode or InternalNode."""
    data = pager.read_page(page_num)
    node_type = data[0]
    if node_type == LEAF_NODE:
        return LeafNode(data)
    else:
        return InternalNode(data)