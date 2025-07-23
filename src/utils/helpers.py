import calendar
import pathlib
from datetime import date, timedelta

import pypdf


def get_week_days(base_date: date) -> list[date]:
    """
    Gets the dates for the current week (Monday to Sunday) based on a given date.

    Args:
        base_date (datetime.date): The date to determine the week from.

    Returns:
        List[date]: A list of date objects from Monday to Friday of that week.
    """
    # Finds the Monday of the current week
    start_of_week: date = base_date - timedelta(days=base_date.weekday())

    return [start_of_week, start_of_week + timedelta(days=7)]


def get_last_day_of_month(year: int, month: int) -> date:
    """
    Returns the last day of the specified month and year as a datetime object.
    """
    # monthrange returns a tuple: (weekday of first day, number of days in month)
    _, num_days = calendar.monthrange(year, month)
    last_day = date(year, month, num_days)
    return last_day


def read_text(file_path: pathlib.Path) -> str:
    return file_path.read_text()


def read_pdf(file_path: pathlib.Path) -> str:
    with file_path.open("rb") as f:
        reader = pypdf.PdfReader(f)
        text: str = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text


def read_file(file_path: pathlib.Path) -> str:
    """
    Reads a file based on its extension and returns its content.
    """
    if file_path.suffix == ".pdf":
        return read_pdf(file_path)
    elif file_path.suffix == ".md":
        return read_text(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")
