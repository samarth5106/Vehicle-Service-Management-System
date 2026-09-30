"""Shared SQL safety helpers. Identifiers are whitelisted by regex, values are always %s parameters."""
import re

_ID = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?$")
_TBL = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\s+[A-Za-z_][A-Za-z0-9_]*)?$")
OPS = {"=", "<>", "<", ">", "<=", ">=", "LIKE", "IN", "NOT IN"}


def ident(value):
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError(f"Unsafe SQL identifier: {value}")
    return value


def table_expr(value):
    if not isinstance(value, str) or not _TBL.fullmatch(value):
        raise ValueError(f"Unsafe SQL table expression: {value}")
    return value


def _one(item):
    if item[0] == "OR":
        parts, vals = zip(*[_one(i) for i in item[1]])
        return "(" + " OR ".join(parts) + ")", [v for vs in vals for v in vs]
    col, op, val = item
    if op not in OPS:
        raise ValueError(f"Unsupported operator: {op}")
    if op in ("IN", "NOT IN"):
        return f"{ident(col)} {op} ({', '.join(['%s'] * len(val))})", list(val)
    return f"{ident(col)} {op} %s", [val]


def where_clause(conditions):
    """conditions: dict {col: value} or list of (col, op, value) / ("OR", [items]). Returns (sql, values)."""
    if not conditions:
        return "", []
    items = [(c, "=", v) for c, v in conditions.items()] if isinstance(conditions, dict) else conditions
    parts, values = [], []
    for item in items:
        sql, vals = _one(item)
        parts.append(sql)
        values += vals
    return " WHERE " + " AND ".join(parts), values
