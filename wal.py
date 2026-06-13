import json
import os


class WAL:
    """
    Simple write-ahead log.
    Before any page write, we append a record: (filename, page_num, data_hex).
    On startup, if a WAL file exists with unflushed records, replay them.
    On clean shutdown, the WAL is cleared.
    """

    def __init__(self, wal_filename="wal.log"):
        self.wal_filename = wal_filename
        self.file = open(wal_filename, 'a')

    def log_write(self, db_filename, page_num, data):
        record = {
            "file": db_filename,
            "page": page_num,
            "data": data.hex()
        }
        self.file.write(json.dumps(record) + "\n")
        self.file.flush()
        os.fsync(self.file.fileno())

    def clear(self):
        self.file.close()
        open(self.wal_filename, 'w').close()  # truncate
        self.file = open(self.wal_filename, 'a')

    def close(self):
        self.file.close()

    @staticmethod
    def replay(wal_filename="wal.log"):
        """
        Read the WAL file and reapply any pending writes directly to
        the database files. Returns the number of records replayed.
        """
        if not os.path.exists(wal_filename):
            return 0

        count = 0
        with open(wal_filename, 'r') as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            db_filename = record["file"]
            page_num = record["page"]
            data = bytes.fromhex(record["data"])

            if not os.path.exists(db_filename):
                open(db_filename, 'wb').close()

            with open(db_filename, 'r+b') as f:
                f.seek(page_num * len(data))
                f.write(data)
            count += 1

        open(wal_filename, 'w').close()
        return count