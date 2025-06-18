from datetime import datetime, time, timedelta
from typing import List


def generate_time_slots(
    start_hour: int,
    start_minutes: int,
    end_hour: int,
    end_minutes: int,
    interval_minutes: int,
) -> List[time]:
    """
    Generates a list of time slots for a day.

    Args:
        start_hour (int): The starting hour (e.g., 8 for 8:00 AM).
        end_hour (int): The ending hour (e.g., 19 for 7:00 PM).
        interval_minutes (int): The interval between slots in minutes.

    Returns:
        List[time]: A list of datetime.time objects representing the time slots.
    """
    slots: list[time] = []
    current_time = datetime.strptime(f"{start_hour}:{start_minutes}", "%H:%M")
    end_time = datetime.strptime(f"{end_hour}:{end_minutes}", "%H:%M")

    while current_time < end_time:
        slots.append(current_time.time())
        current_time += timedelta(minutes=interval_minutes)

    return slots


def get_week_days(base_date: datetime.date) -> List[datetime.date]:  # type: ignore
    """
    Gets the dates for the current week (Monday to Friday) based on a given date.

    Args:
        base_date (datetime.date): The date to determine the week from.

    Returns:
        List[datetime.date]: A list of date objects from Monday to Friday of that week.
    """
    # Find the Monday of the current week
    start_of_week: datetime.date = base_date - timedelta(days=base_date.weekday())  # type: ignore

    # Generate dates for Monday to Friday
    return [start_of_week + timedelta(days=i) for i in range(5)]  # type: ignore
