from typing import Any

import duckdb
import logfire

from data.db_utils import insert_model
from data.models.psychologist_settings_models import PsychologistSettings

logfire.configure()


def create_psychologist_settings_table(connection: duckdb.DuckDBPyConnection) -> None:
    """Creates the 'psychologist_settings' table with the expanded schema."""
    try:
        logfire.info(
            "APP-LOGIC: Attempting to create 'psychologist_settings' table with new schema."
        )
        sql_command = """
        CREATE TABLE IF NOT EXISTS psychologist_settings (
            user_email VARCHAR NOT NULL PRIMARY KEY,
            psychologist_name VARCHAR NOT NULL,
            crp VARCHAR,
            default_session_price INTEGER NOT NULL,
            default_evaluation_price INTEGER NOT NULL,
            default_session_duration INTEGER NOT NULL,
            logo_path VARCHAR
        );
        """
        connection.execute(sql_command)
        logfire.info(
            "APP-LOGIC: 'psychologist_settings' table created or already exists."
        )
    except Exception:
        logfire.error(
            "APP-LOGIC: Failed to create 'psychologist_settings' table.", exc_info=True
        )
        raise


def insert(
    connection: duckdb.DuckDBPyConnection, psychologist_settings: PsychologistSettings
) -> None:
    try:
        insert_model(
            connection,
            "psychologist_settings",
            psychologist_settings.model_dump(),
        )
        logfire.info(
            f"Inserted psychologist settings for {psychologist_settings.user_email}"
        )
    except Exception:
        logfire.error(
            f"Failed to insert psychologist settings for {psychologist_settings.user_email}",
            exc_info=True,
        )
        raise


def _fetch_psychologist_settings_row(
    connection: duckdb.DuckDBPyConnection, email: str
) -> tuple[Any, ...] | None:
    sql = "SELECT * FROM psychologist_settings WHERE user_email = ?;"
    return connection.execute(sql, (email,)).fetchone()  # type: ignore


def get_by_email(
    connection: duckdb.DuckDBPyConnection, email: str
) -> PsychologistSettings:
    try:
        logfire.info(
            f"APP-LOGIC: Attempting to retrieve psychologist settings for email {email}."
        )
        row = _fetch_psychologist_settings_row(connection, email)
        if row is None:
            logfire.warning(
                f"APP-LOGIC: No psychologist settings found for email {email}."
            )
            raise ValueError(f"No psychologist settings found for email {email}.")
        psychologist_settings = PsychologistSettings(
            **{k: v for k, v in zip(PsychologistSettings.model_fields.keys(), row)}  # type: ignore
        )
        logfire.info(
            f"APP-LOGIC: Successfully retrieved psychologist settings for email {email}."
        )
        return psychologist_settings
    except Exception:
        logfire.error(
            f"APP-LOGIC: Failed to retrieve psychologist settings for email {email}.",
            exc_info=True,
        )
        raise
