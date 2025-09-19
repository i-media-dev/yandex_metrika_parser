import datetime as dt

from parser.constants import DATE_FORMAT


def get_date_list() -> list[str]:
    """Функция генерирует список дат за указанное количество дней."""
    dates_list = []
    for i in range(4, 0, -1):
        tempday = dt.datetime.now()
        tempday -= dt.timedelta(days=i)
        tempday_str = tempday.strftime(DATE_FORMAT)
        dates_list.append(tempday_str)
    return dates_list
