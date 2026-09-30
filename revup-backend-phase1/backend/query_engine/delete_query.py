from query_engine.safe import ident, where_clause


def build_delete(table, conditions):
    if not conditions:
        raise ValueError("DELETE requires WHERE conditions")
    where, vals = where_clause(conditions)
    return f"DELETE FROM {ident(table)}{where}", tuple(vals)
