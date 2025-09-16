import requests
import os
from dotenv import load_dotenv
# from all_scripts.decorators import time_decorator
# from all_scripts.my_func import new_paths
import pandas as pd
from datetime import timedelta
import datetime



def get_yandex_metrika_data(oauth_token, counter_id, start_date, end_date):
    """Получаем данные из метрики."""

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


def add_ps(row):
    if 'srch' in row['CampaignName'] or '-srch-' in row['CampaignName']:
        return 'поиск'
    elif '-all-' in row['CampaignName']:
        return 'все'
    elif '-net-' in row['CampaignName'] or 'network' in row['CampaignName']:
        return 'сеть'
    else:
        return 'nd'


def add_type(row):
    # if 'ios' in row['CampaignName'] or 'android' in row['CampaignName']:
    #     return 'rmp'
    if 'cpm' in row['CampaignName']:
        return 'brandformance'
    elif '-brand' in row['CampaignName']:
        return 'brand'
    else:
        return 'nonbrand'


def add_apptype(row):
    if 'ios' in row['CampaignName']:
        return 'ios'
    elif 'android' in row['CampaignName']:
        return 'android'
    else:
        return 'web'


def geo(row):
    geo = row['CampaignName'].split('-')[0]
    return geo


def filtr_data():
    print('[ + ]\tclean metrika.csv')
    p = os.path.join(new_paths('data'), 'metrica.csv').replace(
        '/all_scripts', '')
    # print(p)
    old_df = pd.read_csv(p, sep=';', encoding='cp1251', header=0)
    for dates in dates_list:
        old_df = old_df[~old_df['Date'].fillna('').str.contains(
            fr'{dates}', case=False, na=False)]
    return old_df


def save_df(df_new, old_df):
    # def save_df(df_new):
    p = os.path.join(new_paths('data'), 'metrica.csv').replace(
        '/all_scripts', '')
    for dates in dates_list:
        old_df = old_df[~old_df['Date'].fillna('').str.contains(
            fr'{dates}', case=False, na=False)]

    print('[ + ]\tsave mertika.csv')

    old_df = pd.concat([df_new, old_df])
    old_df.to_csv(p, index=False, header=True, sep=';', encoding='cp1251')
    # df_new.to_csv(p, index=False, header=True, sep=';', encoding='cp1251')


def desmob(row):
    if row['apptype'] != 'web':
        return 'mobile'
    else:
        return row['Device']


@time_decorator
def main():
    print('[ + ]\tstart stat YAM\n')
    data = get_yandex_metrika_data(oauth_token,
                                   counter_id,
                                   start_date,
                                   end_date)

    columns = ['Date', 'CampaignName', 'Device', 'transactions', 'revenue']
    df = pd.DataFrame(data, columns=columns)
    df['sn'] = df.apply(add_ps, axis=1)
    df['type'] = df.apply(add_type, axis=1)
    df['apptype'] = df.apply(add_apptype, axis=1)
    df['geo'] = df.apply(geo, axis=1)
    df['Device'] = df['Device'].str.lower()
    df['Device'] = df['Device'].str.replace('smartphones', 'mobile')
    df['Device'] = df['Device'].str.replace('tablets', 'tablet')
    df['Device'] = df['Device'].str.replace('pc', 'desktop')
    df['Devices'] = df.apply(desmob, axis=1)
    del df['Device']
    df.rename(columns={'Devices': 'Device'}, inplace=True)

    # df['Device'] = df['Device'].apply(
    #     lambda x: 'mobile' if str(x) != 'web' else x)
    old_df = filtr_data()
    save_df(df, old_df)
    # save_df(df)

    # print(df.head())
    print('[ + ]\tfinish stat YAM')


if __name__ == "__main__":
    load_dotenv()
    oauth_token = str(os.getenv('METRIKA_TOKEN'))
    counter_id = '22004554'

    dates_list = []

    for i in range(4, 0, -1):
        # for i in range(7, 0, -1):
        tempday = datetime.datetime.now()
        tempday -= timedelta(days=i)
        tempday = tempday.strftime('%Y-%m-%d')
        dates_list.append(tempday)

    start_date = dates_list[0]
    end_date = dates_list[-1]

    main()