import requests
import os
from dotenv import load_dotenv
# from all_scripts.decorators import time_decorator
# from all_scripts.my_func import new_paths
import pandas as pd
from datetime import timedelta
import datetime

pd.set_option('display.width', 1500)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
# pd.set_option('display.max_rows', None)

load_dotenv()

oauth_token = str(os.getenv('YANDEX_METRIKA_TOKEN'))
counter_id = '155462'
start_date = '2025-09-01'
end_date = '2025-09-02'

class MetricaSave:
    """Класс для получения и сохранения данных отчетов из Яндекс.Метрики."""
    # oauth_token = str(os.getenv('YANDEX_METRIKA_TOKEN'))
    # counter_id = '155462'
    # start_date = 1
    # end_date = 1

    def get_yandex_metrika_data(self, oauth_token, counter_id, start_date, end_date):
        """Получаем данные из Метрики."""

        url = "https://api-metrika.yandex.net/stat/v1/data"

        headers = {
            "Authorization": f"OAuth {oauth_token}"
        }

        params = {
            "ids": counter_id,
            "metrics": "ym:s:ecommercePurchases,ym:s:ecommerceRevenue",
            "dimensions": "ym:s:date,ym:s:lastsignDirectClickOrder, ym:s:DeviceCategory",
            "date1": start_date,
            "date2": end_date,
            "accuracy": "full",
            "limit": 10000  # убрать в константы
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            data = data['data']

            result = []
            for i in data:
                if '-' in str(i['dimensions'][1]['name']):
                    result.append([i['dimensions'][0]['name'],
                                   i['dimensions'][1]['name'].split('|')[0],
                                   i['dimensions'][2]['name'],
                                   int(i['metrics'][0]),
                                   int(float(i['metrics'][1]))])

            return result

    def main(self):
        data = self.get_yandex_metrika_data(oauth_token,
                                       counter_id,
                                       start_date,
                                       end_date)

        columns = ['Date', 'CampaignName', 'Device', 'transactions', 'revenue']
        df = pd.DataFrame(data, columns=columns)  # Сильно урезанный df из старого файла
        df['sn'] = df.apply(self.add_ps, axis=1)
        df['type'] = df.apply(self.add_type, axis=1)
        df['apptype'] = df.apply(self.add_apptype, axis=1)
        df['geo'] = df.apply(self.geo, axis=1)
        df['Device'] = df['Device'].str.lower()
        df['Device'] = df['Device'].str.replace('smartphones', 'mobile')
        df['Device'] = df['Device'].str.replace('tablets', 'tablet')
        df['Device'] = df['Device'].str.replace('pc', 'desktop')
        df['Devices'] = df.apply(self.desmob, axis=1)
        del df['Device']
        df.rename(columns={'Devices': 'Device'}, inplace=True)

        return df

    def desmob(self, row):
        if row['apptype'] != 'web':
            return 'mobile'
        else:
            return row['Device']
    def geo(self, row):
        geo = row['CampaignName'].split('-')[0]
        return geo

        # print(df.head())
    def add_type(self, row):
        # if 'ios' in row['CampaignName'] or 'android' in row['CampaignName']:
        #     return 'rmp'
        if 'cpm' in row['CampaignName']:
            return 'brandformance'
        elif '-brand' in row['CampaignName']:
            return 'brand'
        else:
            return 'nonbrand'
    def add_ps(self, row):
        if 'srch' in row['CampaignName'] or '-srch-' in row['CampaignName']:
            return 'поиск'
        elif '-all-' in row['CampaignName']:
            return 'все'
        elif '-net-' in row['CampaignName'] or 'network' in row['CampaignName']:
            return 'сеть'
        else:
            return 'nd'
    def add_apptype(self, row):
        if 'ios' in row['CampaignName']:
            return 'ios'
        elif 'android' in row['CampaignName']:
            return 'android'
        else:
            return 'web'

test = MetricaSave()
print(test.main())