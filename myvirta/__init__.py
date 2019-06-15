"""Virtonomics framework.
@author: Anton Solomko
"""

from virtonomics import Virta
from .delay import delay


class MyVirta(Virta):
    from .farm import farm_seasons
    from .equipment import autorepair_equipment
    from .party import party_sales
    from .politics import (
        agitation,
        manage_cities,
        region_money_projects,
        manage_regions,
        country_money_projects,
        manage_countries,
        election_vote,
        elections_vote,
        politics,
        )
    from .sale import (
        sort_sale_contracts,
        sort_all_sale_contracts,
        manage_sale_offers,
        manage_sale_offers_all,
        )
    from .supply import (
        sypply_own_shop,
        manage_supply_orders,
        manage_supply_orders_all,
        )
    from .warehouse import resize_warehouses
    from .research import (
        set_technologies,
        lab_quality_required,
        manage_research,
        )
    from .message import read_messages
    from .shop import (
        set_shop_advertisement,
        set_shops_advertisement,
        set_shops_innovations,
        distribute_shops_employees,
        set_shop_default_prices,
        set_shops_default_prices,
        propagate_contracts,
        _get_retail_terget_volumes,
        manage_shops,
        split_shop,
        )
    from .service import manage_restaurants
    from .employee import set_max_employee_level_all
    from .report import generate_retail_reports
    from .tender import (
        save_technology_sellers_to_db,
        manage_science_tenders,
        manage_tenders,
        )
    
    def __init__(self, server='olga', **kwargs):
        super().__init__(server, **kwargs)
        self.session.get = delay(self.session.get)
        self.session.post = delay(self.session.post)
    
    def __getattr__(self, attrname):
        if attrname == 'retail_target_volumes':
            self.retail_target_volumes = self._get_retail_terget_volumes()
            return self.retail_target_volumes
        return super().__getattr__(attrname)
    
    def set_innovation(self, unit_id, innovation_name, **kwargs):
        alternative_names = {
            'agitation': 'Политическая агитация',
            'lab1': 'Электронная библиотека',
            'lab2': 'Сотрудничество с CERN',
            'lab3': 'Производственная практика для ученых',
            'lab_equipment': 'Сверхпроводники',
            'shop_advertisement': 'Партнёрский договор с рекламным агентством',
            'shop_parking': 'Автомобильная парковка',
            'shop_retail': 'Консалтинг мирового лидера ритейла',
            }
        if innovation_name in alternative_names:
            innovation_name = alternative_names[innovation_name]
        return super().set_innovation(unit_id, innovation_name, **kwargs)