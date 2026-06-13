import os

PAGE_SIZE = 4096

class Pager:
    def __init__(self, filename):
        self.filename = filename
        # Open file in read/write binary mode, create if it doesn't exist
        if not os.path.exists(filename):
            open(filename, 'wb').close()
        self.file = open(filename, 'r+b')

    def read_page(self, page_num):
        self.file.seek(page_num * PAGE_SIZE)
        data = self.file.read(PAGE_SIZE)
        if len(data) < PAGE_SIZE:
            # Page doesn't exist yet, return empty page
            data = data + b'\x00' * (PAGE_SIZE - len(data))
        return data

    def write_page(self, page_num, data):
        if len(data) != PAGE_SIZE:
            raise ValueError(f"Page data must be exactly {PAGE_SIZE} bytes")
        self.file.seek(page_num * PAGE_SIZE)
        self.file.write(data)
        self.file.flush()

    def num_pages(self):
        self.file.seek(0, os.SEEK_END)
        size = self.file.tell()
        return size // PAGE_SIZE

    def close(self):
        self.file.close()