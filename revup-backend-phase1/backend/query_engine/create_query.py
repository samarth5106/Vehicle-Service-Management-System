from query_engine.safe import ident


def build_create(table, columns, constraints=None):
    """Build CREATE TABLE from application-owned column/constraint definitions."""
    defs = [f"{ident(c)} {d}" for c, d in columns.items()] + list(constraints or [])
    return f"CREATE TABLE IF NOT EXISTS {ident(table)} (" + ", ".join(defs) + ") ENGINE=InnoDB"
