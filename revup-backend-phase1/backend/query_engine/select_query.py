from query_engine.safe import table_expr, where_clause


def build_select(table, columns="*", conditions=None, joins=None, order_by=None,
                 group_by=None, limit=None, for_update=False):
    """columns/joins/order_by/group_by are developer-written strings; user input only enters via conditions/limit."""
    cols = columns if isinstance(columns, str) else ", ".join(columns)
    sql = f"SELECT {cols} FROM {table_expr(table)}"
    for j in joins or []:
        sql += f" {j}"
    where, values = where_clause(conditions)
    sql += where
    if group_by:
        sql += f" GROUP BY {group_by}"
    if order_by:
        sql += f" ORDER BY {order_by}"
    if limit is not None:
        sql += " LIMIT %s"
        values.append(int(limit))
    if for_update:
        sql += " FOR UPDATE"
    return sql, tuple(values)
