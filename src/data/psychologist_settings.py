import logging

import duckdb

from data.models import PsychologistSettings

log = logging.getLogger("TestLogger")


def create_psychologist_settings_table(connection: duckdb.DuckDBPyConnection) -> None:
    """Creates the 'psychologist_settings' table with the expanded schema."""
    try:
        log.info(
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
        log.info("APP-LOGIC: 'psychologist_settings' table created or already exists.")
    except Exception:
        log.error(
            "APP-LOGIC: Failed to create 'psychologist_settings' table.", exc_info=True
        )
        raise


def insert(
    connection: duckdb.DuckDBPyConnection, psychologist_settings: PsychologistSettings
) -> None:
    try:
        log.info(f"Inserting psychologist settings: {psychologist_settings}")
        connection.execute(
            "INSERT OR REPLACE INTO psychologist_settings VALUES (?, ?, ?, ?, ?, ?, ?)",
            psychologist_settings.model_dump().values(),
        )
        log.info("Inserted psychologist settings.")
    except Exception:
        log.error("Failed to insert psychologist settings.", exc_info=True)
        raise


def get_by_email(
    connection: duckdb.DuckDBPyConnection, email: str
) -> PsychologistSettings:
    try:
        log.info(
            f"APP-LOGIC: Attempting to retrieve psychologist settings for email {email}."
        )
        sql = "SELECT * FROM psychologist_settings WHERE user_email = ?;"
        result = connection.execute(sql, (email,)).fetchone()  # type: ignore

        if result is None:
            log.warning(f"APP-LOGIC: No psychologist settings found for email {email}.")
            raise ValueError(f"No psychologist settings found for email {email}.")

        psychologist_settings = PsychologistSettings(
            **{k: v for k, v in zip(PsychologistSettings.model_fields.keys(), result)}  # type: ignore
        )
        log.info(
            f"APP-LOGIC: Successfully retrieved psychologist settings for email {email}."
        )
        return psychologist_settings
    except Exception:
        log.error(
            f"APP-LOGIC: Failed to retrieve psychologist settings for email {email}.",
            exc_info=True,
        )
        raise
