import re


class ParsedStatement:
    def __init__(self, kind, **kwargs):
        self.kind = kind  # 'CREATE', 'INSERT', 'SELECT', 'UPDATE', 'DELETE'
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f"<{self.kind} {self.__dict__}>"


def parse(sql):
    sql = sql.strip().rstrip(';')

    # CREATE TABLE name (col1, col2, col3)
    m = re.match(r'CREATE TABLE (\w+)\s*\((.+)\)', sql, re.IGNORECASE)
    if m:
        table = m.group(1)
        columns = [c.strip() for c in m.group(2).split(',')]
        return ParsedStatement('CREATE', table=table, columns=columns)

    # INSERT INTO name VALUES (val1, val2, val3)
    m = re.match(r'INSERT INTO (\w+)\s*VALUES\s*\((.+)\)', sql, re.IGNORECASE)
    if m:
        table = m.group(1)
        raw_values = [v.strip().strip("'\"") for v in m.group(2).split(',')]
        return ParsedStatement('INSERT', table=table, values=raw_values)

    # UPDATE name SET col = val WHERE col = val
    m = re.match(r'UPDATE (\w+)\s+SET\s+(\w+)\s*=\s*(.+?)\s+WHERE\s+(\w+)\s*=\s*(.+)', sql, re.IGNORECASE)
    if m:
        table = m.group(1)
        set_col = m.group(2)
        set_val = m.group(3).strip().strip("'\"")
        where_col = m.group(4)
        where_val = m.group(5).strip().strip("'\"")
        return ParsedStatement('UPDATE', table=table, set_col=set_col, set_val=set_val,
                                where_col=where_col, where_val=where_val)

    # DELETE FROM name WHERE col = val
    m = re.match(r'DELETE FROM (\w+)\s+WHERE\s+(\w+)\s*=\s*(.+)', sql, re.IGNORECASE)
    if m:
        table = m.group(1)
        where_col = m.group(2)
        where_val = m.group(3).strip().strip("'\"")
        return ParsedStatement('DELETE', table=table, where_col=where_col, where_val=where_val)

    # SELECT * FROM name [WHERE col = val]
    m = re.match(r'SELECT \* FROM (\w+)(?:\s+WHERE\s+(\w+)\s*=\s*(.+))?', sql, re.IGNORECASE)
    if m:
        table = m.group(1)
        where_col = m.group(2)
        where_val = m.group(3)
        if where_val:
            where_val = where_val.strip().strip("'\"")
        return ParsedStatement('SELECT', table=table, where_col=where_col, where_val=where_val)

    raise ValueError(f"Could not parse SQL: {sql}")