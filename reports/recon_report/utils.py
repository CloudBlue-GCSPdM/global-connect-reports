from datetime import datetime, timedelta


def convert_to_datetime(param_value):
    if param_value == "" or param_value == "-":
        return "-"

    return datetime.strptime(
        param_value.replace("T", " ").replace("+00:00", ""),
        "%Y-%m-%d %H:%M:%S",
    )


def convert_to_date(param_value):
    if param_value == "" or param_value == "-":
        return "-"

    return datetime.strptime(
        param_value.replace("T", " ").replace("+00:00", ""),
        "%Y-%m-%d",
    )


def today_str():
    return datetime.today().strftime('%Y-%m-%d %H:%M:%S')


def get_first_day_month(date: datetime):
    return datetime(date.year, date.month, 1, 0, 0, 0)


def get_last_day_month(date: datetime):
    m = date.month + 1
    y = date.year
    if m > 12:
        m = 1
        y = y +1
    return datetime(y, m, 1, 0, 0, 0) + timedelta(days=-1)


def get_next_month_anniversary(date: datetime):
    if date.month == 12:
        return datetime(date.year + 1, 1, date.day, 0, 0, 0)
    if date.month == 1 and date.day > 28:
        return datetime(date.year, date.month + 1, 28, 0, 0, 0)
    if date.day > 30 and (date.month == 3 or date.month == 5 or date.month == 8 or date.month == 10):
        return datetime(date.year, date.month + 1, 30, 0, 0, 0)
    return datetime(date.year, date.month + 1, date.day, 0, 0, 0)


def get_next_year_anniversary(date: datetime, years_to_add):
    if date.month == 2 and date.day == 29:
        return datetime(date.year + years_to_add, date.month, 28, 0, 0, 0)
    return datetime(date.year + years_to_add, date.month, date.day, 0, 0, 0)


def get_basic_value(base, value):
    if base and value in base:
        return base[value]
    return '-'


def get_value(base, prop, value):
    if prop in base:
        return get_basic_value(base[prop], value)
    return '-'


class MonthlyBillingItem:
    def __init__(self, item_mpn, item_period, item_display_name, quantity, old_quantity):
        self.Item_mpn = item_mpn
        self.Period = item_period
        self.Item_name = item_display_name
        self.Quantity = quantity
        self.Delta = int(quantity) - int(old_quantity)
