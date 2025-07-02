import calendar
from datetime import date, timedelta


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
