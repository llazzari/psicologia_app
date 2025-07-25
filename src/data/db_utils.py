from typing import Any

import duckdb
import logfire

logfire.configure()


def insert_model(
    connection: duckdb.DuckDBPyConnection,
    table: str,
    field_map: dict[str, Any],
) -> None:
    """
    Inserts a Pydantic model into the given DuckDB table using parameterized SQL.
    fields: list of column names (order matters)
    field_map: optional mapping for custom field extraction/flattening
    """
    try:
        values = tuple(field_map.values())
        placeholders = ", ".join(["?"] * len(field_map.keys()))
        sql = f"INSERT OR REPLACE INTO {table} ({', '.join(field_map.keys())}) VALUES ({placeholders})"
        connection.execute(sql, values)
        logfire.info(f"APP-LOGIC: Inserted into {table}: {values}")
    except Exception:
        logfire.error(f"APP-LOGIC: Failed to insert into {table}.", exc_info=True)
        raise
