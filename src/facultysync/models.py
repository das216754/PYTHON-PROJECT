DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]


class TimeInterval:
    def __init__(
        self, day, start, end, faculty,
        kind="availability"
    ):
        if day not in DAYS:
            raise ValueError(f"Invalid day: {day}")

        if not (0 <= start < end <= 1440):
            raise ValueError("Invalid time interval")

        self.day = day
        self.start = start
        self.end = end
        self.faculty = faculty
        self.kind = kind

    def overlaps(self, start, end):
        return self.start < end and start < self.end


def to_minutes(value):
    try:
        hour, minute = map(int, value.strip().split(":"))
    except (ValueError, AttributeError):
        raise ValueError(
            "Enter time in HH:MM format, e.g. 14:30"
        )

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("Enter a valid time between 00:00 and 23:59")

    return hour * 60 + minute


def format_time(minutes):
    return f"{minutes // 60:02d}:{minutes % 60:02d}"