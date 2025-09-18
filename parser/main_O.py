import os

from dotenv import load_dotenv

from parser.decorators import time_of_script
from parser.yam_news_O import MetricaSave
from parser.utils import get_date_list

load_dotenv()

@time_of_script
def main():
    """Основная логика скрипта."""
    oauth_token = str(os.getenv('YANDEX_METRIKA_TOKEN'))
    counter_id = METRIKA_ID
    date_list = get_date_list()
    saver = MetricaSave(token, date_list)
    saver.save_data()