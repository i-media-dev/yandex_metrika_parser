from datetime as dt
import logging

from dotenv import load_dotenv
import pandas as pd
from pathlib import Path
import requests

from parser.logging_config import setup_logging
from parser.constants import (
    CAMPAIGN_CATEGORIES,
    CLIENT_LOGINS,
    DEFAULT_FOLDER,
    DEFAULT_RETURNES,
    PLATFORM_TYPES,
    REPORT_FIELDS,
    REPORT_NAME,
    YANDEX_METRICA_URL,
    METRICA_ID,
    METRICA_LIMIT
)

setup_logging()
load_dotenv()


class MetricaSave:
    """Класс для получения и сохранения данных отчетов из Яндекс.Метрики."""

    def __init__(
        self,
        token: str,
        dates_list: list,
        counter_id: str = METRICA_ID,
        login: list = CLIENT_LOGINS,
        folder_name: str = DEFAULT_FOLDER,
        limit: int = METRICA_LIMIT
    ):
        if not token:
            logging.error('Токен отсутствует или не действителен')
        self.token = token
        self.logins = login
        self.dates_list = dates_list
        self.counter_id = counter_id
        self.folder = folder_name
        self.limit = limit

    def _get_file_path(self, filename: str) -> Path:
        """Защищенный метод. Создает путь к файлу в указанной папке."""
        try:
            file_path = Path(__file__).parent.parent / self.folder
            file_path.mkdir(parents=True, exist_ok=True)
            return file_path / filename
        except Exception as e:
            logging.error(f'Ошибка: {e}')
            raise

    def _get_all_metrika_data(self) -> pd.DataFrame:
        """Получаем данные из Метрики."""
        start_date = self.dates_list[0]
        end_date = self.dates_list[-1]
        url = YANDEX_METRICA_URL
        headers = {
            "Authorization": f"OAuth {self.token}"
        }
        params = {
            "ids": self.counter_id,
            "metrics": "ym:s:ecommercePurchases,ym:s:ecommerceRevenue",
            "dimensions": "ym:s:date,ym:s:lastsignDirectClickOrder, ym:s:DeviceCategory",
            "date1": start_date,
            "date2": end_date,
            "accuracy": "full",
            "limit": self.limit
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == requests.codes.ok:
                data = response.json()

                if not data or 'data' not in data or not data['data']:
                    logging.warning('Нет данных для кампании ')
                    return pd.DataFrame()

                data = data['data']
                result = []

                for i in data:
                    if '-' in str(i['dimensions'][1]['name']):
                        result.append(
                            [
                                i['dimensions'][0]['name'],
                                i['dimensions'][1]['name'].split('|')[0],
                                i['dimensions'][2]['name'],
                                int(i['metrics'][0]),
                                int(float(i['metrics'][1]))
                            ]
                        )
                columns = [
                    'Date',
                    'CampaignName',
                    'Device',
                    'transactions',
                    'revenue'
                ]
                df = pd.DataFrame(result, columns=columns)
                df['sn'] = df.apply(self.add_ps, axis=1)
                df['type'] = df.apply(self.add_type, axis=1)
                df['apptype'] = df.apply(self.add_apptype, axis=1)
                df['geo'] = df.apply(self._get_geo, axis=1)
                df['Device'] = df['Device'].str.lower()
                df['Device'] = df['Device'].str.replace(
                    'smartphones', 'mobile')
                df['Device'] = df['Device'].str.replace('tablets', 'tablet')
                df['Device'] = df['Device'].str.replace('pc', 'desktop')
                df['Devices'] = df.apply(self.desmob, axis=1)
                del df['Device']
                df.rename(columns={'Devices': 'Device'}, inplace=True)
                return df
        except Exception as e:
            logging.error(f'Ошибка: {e}')
            raise

    def _get_filtered_cache_data(self, filename_data: str) -> pd.DataFrame:
        """Метод получает отфильтрованные данные из кэш-файла."""
        temp_cache_path = self._get_file_path(filename_data)
        try:
            old_df = pd.read_csv(
                temp_cache_path,
                sep=';',
                encoding='cp1251',
                header=0
            )
            for dates in self.dates_list:
                old_df = old_df[~old_df['Date'].fillna('').str.contains(
                    fr'{dates}', case=False, na=False
                )]
            return old_df
        except FileNotFoundError:
            logging.warning('Файл кэша не найден. Первый запуск.')
            return pd.DataFrame()
        except pd.errors.EmptyDataError:
            logging.warning('Файл кэша пустой.')
            return pd.DataFrame()
        except Exception as e:
            logging.error(f'Ошибка: {e}')
            raise

    def save_data(self, filename_data: str) -> None:
        """Метод сохраняет новые данные, объединяя с существующими."""
        df_new = self._get_all_metrika_data()
        df_old = self._get_filtered_cache_data(filename_data)
        try:
            temp_cache_path = self._get_file_path(filename_data)
            if df_new.empty:
                logging.warning('Нет новых данных для сохранения')
                return
            if not isinstance(df_old, pd.DataFrame) or df_old.empty:
                df_new.to_csv(
                    temp_cache_path,
                    index=False,
                    header=True,
                    sep=';',
                    encoding='cp1251'
                )
                logging.info(
                    'Новые данные сохранены. Исторические данные отсутствовали'
                )
                return
            for dates in self.dates_list:
                df_old = df_old[~df_old['Date'].fillna('').str.contains(
                    fr'{dates}', case=False, na=False
                )]

            df_old = pd.concat([df_new, df_old])
            df_old.to_csv(
                temp_cache_path,
                index=False,
                header=True,
                sep=';',
                encoding='cp1251'
            )
            logging.info('Данные успешно обновлены')
        except Exception as e:
            logging.error(f'Ошибка во время обновления: {e}')

    # def _get_campaign_category(self, row) -> str:
    #     try:
    #         for tag, value in CAMPAIGN_CATEGORIES.items():
    #             if tag in row['CampaignName']:
    #                 return value
    #         return DEFAULT_RETURNES.get('campaign', '')
    #     except (AttributeError, IndexError, KeyError):
    #         return DEFAULT_RETURNES.get('error', '')

    # def _get_platform_type(self, row) -> str:
    #     try:
    #         for tag, value in PLATFORM_TYPES.items():
    #             if tag in row['CampaignName']:
    #                 return value
    #         return DEFAULT_RETURNES.get('platform', '')
    #     except (AttributeError, IndexError, KeyError):
    #         return DEFAULT_RETURNES.get('error', '')

    # def _get_app_type(self, row) -> str:
    #     try:
    #         for tag, value in APP_TYPES.items():
    #             if tag in row['CampaignName']:
    #                 return value
    #         return DEFAULT_RETURNES.get('app', '')
    #     except (AttributeError, IndexError, KeyError):
    #         return DEFAULT_RETURNES.get('error', '')

    def _get_geo(self, row):
        try:
            geo = row['CampaignName'].split('-')[0]
            return geo
        except (AttributeError, IndexError, KeyError):
            return DEFAULT_RETURNES.get('error', '')

    def desmob(self, row):
        if row['apptype'] != 'web':
            return 'mobile'
        else:
            return row['Device']

    def add_type(self, row):
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
