import json
from datetime import datetime, timezone

import pandas as pd
import requests
from django.db import models

from datasource.models.datasource import Datasource


class Bocc(Datasource):
    """
    Data from the Banking on Climate Change report published by the Rainforest Action Network
    """

    @classmethod
    def load_and_create(cls, bankreg):
        df = pd.read_csv(URIs.BOCC.value)

        for i, row in df.iterrows():
            bank = BOCC(
                bankreg=bankreg,
                name=row['Bank'],
                country=row['Country'],
                europe=row['Europe'],
                asia=row['Asia'],
                north_america=row['North America'],
                canada=row['Canada'],
                uk=row['UK'],
                australia=row['Australia'],
                percent_assets=row['Cum % of Assets Loaned since 2016'],
                assets_2020=row['2020 Assets (Billions)'],
                coal_score=row['Policy - Total Coal (0/80)'],
                og_score=row['Policy - Total O&G (0/120)'],
                total_financing=row[
                    [
                        'FFF - total rank',
                        'FFF - European Rank',
                        'FFF - Asian Rank',
                        'FFF - North American Rank',
                        'FFF - Canadian Rank',
                        'FFF - UK Rank',
                        'FFF - 2016',
                        'FFF - 2017',
                        'FFF - 2018',
                        'FFF - 2019',
                        'FFF - 2020',
                        'FFF - 2016-2020',
                        'FFF - Compared To 2016',
                    ]
                ],
                arctic_og_financing=row[
                    [
                        'AOG - Rank',
                        'AOG - European Rank',
                        'AOG - Asian Rank',
                        'AOG - North American Rank',
                        'AOG - Canadian Rank',
                        'AOG - UK Rank',
                        'AOG - 2016',
                        'AOG - 2017',
                        'AOG - 2018',
                        'AOG - 2019',
                        'AOG - 2020',
                        'AOG - Total',
                        'AOG - Compared To 2016',
                    ]
                ],
                coal_mining_financing=row[
                    [
                        'CM - Rank',
                        'CM - European Rank',
                        'CM - Asian Rank',
                        'CM - North American Rank',
                        'CM - Canadian Rank',
                        'CM - UK Rank',
                        'CM - 2016',
                        'CM - 2017',
                        'CM - 2018',
                        'CM - 2019',
                        'CM - 2020',
                        'CM - Total',
                        'CM - Compared To 2016',
                    ]
                ],
                coal_power_financing=row[
                    [
                        'CP - Rank',
                        'CP - European Rank',
                        'CP - Asian Rank',
                        'CP - North American Rank',
                        'CP - Canadian Rank',
                        'CP - UK Rank',
                        'CP - 2016',
                        'CP - 2017',
                        'CP - 2018',
                        'CP - 2019',
                        'CP - 2020',
                        'CP - Total',
                        'CP - Compared To 2016',
                    ]
                ],
                expansion_financing=row[
                    [
                        'FFE - Rank',
                        'FFE - European Rank',
                        'FFE - Asian Rank',
                        'FFE - North American Rank',
                        'FFE - Canadian Rank',
                        'FFE - UK Rank',
                        'FFE - 2016',
                        'FFE - 2017',
                        'FFE - 2018',
                        'FFE - 2019',
                        'FFE - 2020',
                        'FFE - Total',
                        'FFE - Compared To 2016',
                    ]
                ],
                fracking_financing=row[
                    [
                        'FOG - Rank',
                        'FOG - European Rank',
                        'FOG - Asian Rank',
                        'FOG - North American Rank',
                        'FOG - Canadian Rank',
                        'FOG - UK Rank',
                        'FOG - 2016',
                        'FOG - 2017',
                        'FOG - 2018',
                        'FOG - 2019',
                        'FOG - 2020',
                        'FOG - Total',
                        'FOG - Compared To 2016',
                    ]
                ],
                lng_financing=row[
                    [
                        'LNG - Rank',
                        'LNG - European Rank',
                        'LNG - Asian Rank',
                        'LNG - North American Rank',
                        'LNG - Canadian Rank',
                        'LNG - UK Rank',
                        'LNG - 2016',
                        'LNG - 2017',
                        'LNG - 2018',
                        'LNG - 2019',
                        'LNG - 2020',
                        'LNG - Total',
                        'LNG - Compared To 2016',
                    ]
                ],
                offshore_financing=row[
                    [
                        'OOG - Rank',
                        'OOG - European Rank',
                        'OOG - Asian Rank',
                        'OOG - North American Rank',
                        'OOG - Canadian Rank',
                        'OOG - UK Rank',
                        'OOG - 2016',
                        'OOG - 2017',
                        'OOG - 2018',
                        'OOG - 2019',
                        'OOG - 2020',
                        'OOG - Total',
                        'OOG - Compared To 2016',
                    ]
                ],
                tar_sands_financing=row[
                    [
                        'TS - Rank',
                        'TS - European Rank',
                        'TS - Asian Rank',
                        'TS - North American Rank',
                        'TS - Canadian Rank',
                        'TS - UK Rank',
                        'TS - 2016',
                        'TS - 2017',
                        'TS - 2018',
                        'TS - 2019',
                        'TS - 2020',
                        'TS - Total',
                        'TS - Compared To 2016',
                    ]
                ],
            )

            bankreg.create_or_update_bank(source=bank)

    @classmethod
    def _generate_tag(cls, bt_tag, increment=0, existing_tags=None):
        og_tag = bt_tag

        # memoize existing tags for faster recursion
        if not existing_tags:
            existing_tags = {x.tag for x in cls.objects.all()}

        if increment < 1:
            bt_tag = "banktrack_" + og_tag
        else:
            bt_tag = "banktrack_" + og_tag + "_" + str(increment).zfill(2)

        if bt_tag not in existing_tags:
            return bt_tag
        else:
            return cls._generate_tag(og_tag, increment=increment + 1, existing_tags=existing_tags)
