from query_engine.safe import ident


def build_insert(table, data):
    if not data:
        raise ValueError("INSERT data cannot be empty")
    cols = [ident(c) for c in data]
    return (f"INSERT INTO {ident(table)} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})",
            tuple(data.values()))
