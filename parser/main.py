import os
import datetime as dt

from dotenv import load_dotenv

from parser.utils import get_date_list

load_dotenv()


if __name__ == "__main__":
    load_dotenv()
    oauth_token = str(os.getenv('YANDEX_METRIKA_TOKEN'))
    counter_id = '22004554'

    dates_list = []

    for i in range(4, 0, -1):
        # for i in range(7, 0, -1):
        tempday = dt.datetime.now()
        tempday -= dt.timedelta(days=i)
        tempday = tempday.strftime('%Y-%m-%d')
        dates_list.append(tempday)

    start_date = dates_list[0]
    end_date = dates_list[-1]

    main()
