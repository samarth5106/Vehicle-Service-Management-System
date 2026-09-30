import re
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal

from config.db_config import DATABASE_NAME
from db.connection import get_connection
from query_engine.insert_query import build_insert
from query_engine.select_query import build_select
from query_engine.update_query import build_update
from query_engine.delete_query import build_delete


class ValidationError(Exception):
    def __init__(self, message, fields=None):
        super().__init__(message)
        self.fields = fields or {}


@contextmanager
def transaction():
    conn = get_connection(DATABASE_NAME)
    cur = conn.cursor(dictionary=True)
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def q_insert(cur, table, data):
    sql, vals = build_insert(table, data); cur.execute(sql, vals); return cur.lastrowid


def q_select(cur, *args, **kwargs):
    sql, vals = build_select(*args, **kwargs); cur.execute(sql, vals); return cur.fetchall()


def q_update(cur, table, data, conditions):
    sql, vals = build_update(table, data, conditions); cur.execute(sql, vals); return cur.rowcount


def q_delete(cur, table, conditions):
    sql, vals = build_delete(table, conditions); cur.execute(sql, vals); return cur.rowcount


def q_one(cur, *args, **kwargs):
    rows = q_select(cur, *args, **kwargs)
    return rows[0] if rows else None


def jsonable(rows):
    """Decimal/date -> JSON-friendly values."""
    out = []
    for r in rows:
        out.append({k: (float(v) if isinstance(v, Decimal) else v.isoformat() if isinstance(v, (date, datetime)) else v)
                    for k, v in r.items()})
    return out


_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clean(data, spec, partial=False):
    """spec: {field: (kind, required)}; returns cleaned dict or raises ValidationError with per-field messages."""
    out, errors = {}, {}
    for field, (kind, required) in spec.items():
        if field not in data:
            if required and not partial:
                errors[field] = "This field is required"
            continue
        v = data[field]
        if isinstance(v, str):
            v = v.strip()
        if v in ("", None):
            if required:
                errors[field] = "This field is required"
            else:
                out[field] = None
            continue
        try:
            if kind == "int":
                v = int(v)
                if v < 0: raise ValueError
            elif kind == "year":
                v = int(v)
                if not 1950 <= v <= date.today().year + 1: raise ValueError
            elif kind == "money":
                v = round(float(v), 2)
                if v < 0: raise ValueError
            elif kind == "date":
                v = date.fromisoformat(str(v)).isoformat()
            elif kind == "phone":
                if not re.fullmatch(r"\+?\d{10,13}", str(v)): raise ValueError
            elif kind == "email":
                if not _EMAIL.fullmatch(v): raise ValueError
            elif kind == "reg":
                v = re.sub(r"\s+", "", str(v)).upper()
        except (ValueError, TypeError):
            errors[field] = {"phone": "Enter a valid 10-digit phone number", "email": "Enter a valid email",
                             "year": "Enter a valid year", "date": "Use YYYY-MM-DD"}.get(kind, "Enter a valid non-negative number")
            continue
        out[field] = v
    if errors:
        raise ValidationError("Please correct the highlighted fields", errors)
    return out
