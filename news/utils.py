from datetime import datetime


data = {
    "year": 31536e6,
    "month": 2628e6,
    "day": 864e5,
    "hour": 36e5,
    "minute": 6e4,
}


def get_date_difference(date):
    date_format = "%Y-%m-%d %H:%M:%S"
    now = datetime.now()
    date = datetime.strptime(date, date_format)

    for key in data:
        diff = (now - date).total_seconds() * 1000

        if diff >= data[key]:
            value = int(diff / data[key])
            return f"{value} {key + ('' if value == 1 else 's')} ago"

    return "Just now"
