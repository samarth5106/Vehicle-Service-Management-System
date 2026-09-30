from query_engine.safe import ident, where_clause


def build_update(table, data, conditions):
    if not data:
        raise ValueError("UPDATE data cannot be empty")
    if not conditions:
        raise ValueError("UPDATE requires WHERE conditions")
    sets = ", ".join(f"{ident(c)} = %s" for c in data)
    where, wvals = where_clause(conditions)
    return f"UPDATE {ident(table)} SET {sets}{where}", tuple(list(data.values()) + wvals)
