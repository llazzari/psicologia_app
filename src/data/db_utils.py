from typing import Any, Callable, Optional, Sequence

import duckdb
import logfire
from pydantic import BaseModel

logfire.configure()


def flatten_model(
    model: BaseModel, field_map: Optional[dict[str, Callable[[BaseModel], Any]]] = None
) -> dict[str, Any]:
    """
    Flattens a (possibly nested) Pydantic model into a dict for DB insertion.
    field_map: Optional mapping of field names to callables for custom extraction.
    """
    if field_map:
        return {k: v(model) for k, v in field_map.items()}
    return model.model_dump()


def insert_model(
    connection: duckdb.DuckDBPyConnection,
    table: str,
    model: BaseModel,
    fields: Sequence[str],
    field_map: Optional[dict[str, Callable[[BaseModel], Any]]] = None,
) -> None:
    """
    Inserts a Pydantic model into the given DuckDB table using parameterized SQL.
    fields: list of column names (order matters)
    field_map: optional mapping for custom field extraction/flattening
    """
    try:
        values_dict = flatten_model(model, field_map)
        values = tuple(values_dict.get(f) for f in fields)
        placeholders = ", ".join(["?"] * len(fields))
        sql = f"INSERT OR REPLACE INTO {table} ({', '.join(fields)}) VALUES ({placeholders})"
        connection.execute(sql, values)
        logfire.info(f"APP-LOGIC: Inserted into {table}: {values_dict}")
    except Exception:
        logfire.error(f"APP-LOGIC: Failed to insert into {table}.", exc_info=True)
        raise
