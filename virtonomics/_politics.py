import datetime


@classmethod
def days_to_election(cls, days_passed, post='mayor'):
    """Days left to election.
    Takes into account day of the week when elections run.
    
    Arguments:
        days_passed (int): Days passed since election.
        post: 'mayor', 'governor' or 'president'.
    
    Returns:
        int: Days to elections. 0 the day before the election.
    """
    
    days_left = 156 - days_passed
    election_date = cls.today + datetime.timedelta(days=days_left)
    shift = 1 if post=='mayor' else 0 if post=='governor' else 3
    extra_days = 6 - (election_date.weekday() - shift) % 7
    return days_left + extra_days


def city_change_council_tax(self, city_id, increase=True):
    """Change (increase or decrease) council tax for a given city.
    
    Note:
        The council tax only changes if the corresponding function is
        available to a major (depends on approval rating etc.)
        No availability check is done to minimize the number of requests.
    
    Arguments:
        city_id (int): City id.
        increase (bool): Flag. If True, tax will be increased. Decreased
            otherwise. Defaults to True (increase).
    
    Returns:
        POST request responce.
    """
    
    action = 'fee_up' if increase else 'fee_down'
    url = self.domain_ext + 'politics/%s/%s' % (action, city_id)
    self.session.get(url)


def city_money_project(self, city_id, project_name):
    """Run municipal project.
    (Запустить муниципальный проект в городе)
    
    Arguments:
        city_id (int): City id.
        project_name (str): Project name, as appears in the game interface,
            or one of the following short forms:
                'festival'  ('Городской фестиваль')
                'education'  ('Научная конференция')
                'salary_up'  ('Дотации населению')
                'salary_down'  ('Борьба с высокими ценами')
                'construction'  ('Доступное жильё')
                'freeze'  ('Управление трудовыми ресурсами')
                'migration'  ('Миграционная служба')
                'trade_union'  ('Договор с профсоюзами')
                'recycling'  ('Городская программа утилизации мусора')
                'transport'  ('Транспортная развязка')
                'sewage'  ('Очистные сооружения')
                'power'  ('Экологический мониторинг электростанций')
                
    Returns:
        POST request responce.
    """
    
    codes = {
        'Городской фестиваль': 1,
        'Научная конференция': 2,
        'Дотации населению': 3,
        'Борьба с высокими ценами': 4,
        'Доступное жильё': 5,
        'Управление трудовыми ресурсами': 6,
        'Миграционная служба': 10,
        'Договор с профсоюзами': 20,
        'Городская программа утилизации мусора': 12,
        'Транспортная развязка': 13,
        'Очистные сооружения': 14,
        'Экологический мониторинг электростанций': 15
        }
    #Alternative project names
    codes['festival'] = codes['Городской фестиваль']
    codes['education'] = codes['Научная конференция']
    codes['salary_up'] = codes['Дотации населению']
    codes['salary_down'] = codes['Борьба с высокими ценами']
    codes['construction'] = codes['Доступное жильё']
    codes['freeze'] = codes['Управление трудовыми ресурсами']
    codes['migration'] = codes['Миграционная служба']
    codes['trade_union'] = codes['Договор с профсоюзами']
    codes['recycling'] = codes['Городская программа утилизации мусора']
    codes['transport'] = codes['Транспортная развязка']
    codes['sewage'] = codes['Очистные сооружения']
    codes['power'] = codes['Экологический мониторинг электростанций']
    codes['Промышленный и бытовой мусор'] = codes['recycling']
    codes['Загрязнение автотранспортом'] = codes['transport']
    codes['Промышленные стоки'] = codes['sewage']
    codes['Выбросы электростанций'] = codes['power']
    
    url = self.domain_ext + 'politics/money_project/%s/%s' % (
              city_id, codes[project_name])
    return self.session.get(url)


def city_retail_project(self, city_id, category_name):
    categories = {g['product_category_name']: g['product_category_id'] for g in self.goods.values()}
    url = self.domain_ext + 'politics/retail_project/%s/%s' % (city_id, categories[category_name])
    return self.session.get(url)


def city_change_rent(self, city_id, unit_class, rent_up=False):
    """Change rent price.
    
    Note:
        The rent change only happens if the corresponding function is 
        available to a major (depends on approval rating etc.)
        No availability check is done to minimize the number of requests.
    
    Arguments:
        city_id (int): City_id.
        unit_class (str or int): Unit class kind or unit class name, or 
            unit class id. Can take values: 
            'office' ('Офис'), 
            'shop' ('Магазин'),
            'fuel' ('Автозаправочная станция'), 
            'educational' ('Образовательное учреждение'), 
            'service_light' ('Сфера услуг'),
            'restaurant' ('Ресторан'),
            'repair' ('Авторемонтная мастерская'),
            'it' ('IT-центр'),
            'warehouse' ('Склад'),
            'villa' ('Вилла'),
            'network' ('Сеть коммуникационных вышек')
        rent_up (bool): Up/down flag. If True, the rent price will be 
            increased, otherwise decreased.
    
    Returns:
        POST request responce. 
    """
    
    if not isinstance(unit_class, int):
        city_rent = self.city_rent(city_id)
        class_rent = city_rent.select(unit_class_kind=unit_class)
        if not class_rent:
            class_rent = city_rent.select(unit_class_name=unit_class)
        if class_rent:
            unit_class = class_rent['unit_class_id']
        else:
            return
    
    change = 'rent_up' if rent_up else 'rent_down'
    url = self.domain_ext + 'politics/%s/%s/%d' % (
              change, city_id, unit_class)
    self.session.get(url)


def region_money_project(self, region_id, project_name):
    """Run regional project.
    (Запустить региональный проект)
    
    Arguments:
        region_id (int): Region id.
        project_name (str): Project name, as appears in the game interface,
            or one of the following short forms:
                'eco75' ('Экологический стандарт - 75')
                'eco90' ('Экологический стандарт - 90')
                'agriculture' ('Региональная сельхозавиация')
                'fish' ('Рыбнадзор')
                'forest' ('Лесничество')
                'animal' ('Региональная ветеринарная служба')
                'no_luxury' ('Борьба с роскошью')
                'luxury' ('Регаты под патронажем губернатора')
                'air' ('Реконструкция аэропорта')
                'road' ('Ремонт дорог')
                'ecology' ('Экологическая полиция')
                'power' ('Экологический мониторинг электростанций')
                
    Returns:
        POST request responce.
    """
    
    codes = {
        'Экологический стандарт - 75': 1,
        'Экологический стандарт - 90': 2,
        'Региональная сельхозавиация': 4,
        'Рыбнадзор': 6,
        'Лесничество': 7,
        'Региональная ветеринарная служба': 8,
        'Борьба с роскошью': 9,
        'Регаты под патронажем губернатора': 10,
        'Реконструкция аэропорта': 11,
        'Ремонт дорог': 12,
        'Экологическая полиция': 13,
        'Экологический мониторинг электростанций': 14
        }
    #Alternative project names
    codes['eco75'] = codes['Экологический стандарт - 75']
    codes['eco90'] = codes['Экологический стандарт - 90']
    codes['agriculture'] = codes['Региональная сельхозавиация']
    codes['fish'] = codes['Рыбнадзор']
    codes['forest'] = codes['Лесничество']
    codes['animal'] = codes['Региональная ветеринарная служба']
    codes['no_luxury'] = codes['Борьба с роскошью']
    codes['luxury'] = codes['Регаты под патронажем губернатора']
    codes['air'] = codes['Реконструкция аэропорта']
    codes['road'] = codes['Ремонт дорог']
    codes['ecology'] = codes['Экологическая полиция']
    codes['power'] = codes['Экологический мониторинг электростанций']
    codes['Промышленный и бытовой мусор'] = codes['Экологическая полиция']
    codes['Загрязнение автотранспортом'] = codes['Экологическая полиция']
    codes['Промышленные стоки'] = codes['Экологическая полиция']
    codes['Выбросы электростанций'] = codes['Экологический мониторинг электростанций']
    
    url = self.domain_ext + 'politics/money_project/%s/%s' % (
              region_id, codes[project_name])
    self.session.get(url)


def region_country_up(self, region_id):
    url = self.domain_ext + 'politics/manage'
    data = {
        'region_id': region_id,
        'command': 'country_up'
    }
    self.session.post(url, data=data)


def country_money_project(self, country_id, project_name):
    """Run country project.
    (Законы страны)
    
    Arguments:
        country_id (int): Country id.
        project_name (str): Project name, as appears in the game interface,
            or one of the following short forms:
                'education' ('Закон об образовании')
                'construction' ('Закон о жилищном строительстве')
                'trade' ('Закон о государственной поддержке розничных
                          рынков')
                'sport' ('Постановление о развитии физкультуры и спорта')
                'food' ('Закон об общественном питании')
                'no_tender' ('Мораторий на проведение в стране регулярных 
                              тендеров')
                'ecology' ('Закон о национальной экологической службе')
                'trademark' ('Закон о торговых марках')
                'transport' ('Закон о национальной транспортной службе')
                
    Returns:
        POST request responce.
    """
    
    codes = {
        'Закон об образовании': 1,
        'Закон о жилищном строительстве': 2,
        'Закон о государственной поддержке розничных рынков': 3,
        'Постановление о развитии физкультуры и спорта': 4,
        'Закон об общественном питании': 5,
        'Мораторий на проведение в стране регулярных тендеров': 6,
        'Закон о национальной экологической службе': 8,
        'Закон о торговых марках': 9,
        'Закон о национальной транспортной службе': 10,
        }
    #Alternative project names
    codes['education'] = codes['Закон об образовании']
    codes['construction'] = codes['Закон о жилищном строительстве']
    codes['trade'] = codes['Закон о государственной поддержке розничных рынков']
    codes['sport'] = codes['Постановление о развитии физкультуры и спорта']
    codes['food'] = codes['Закон об общественном питании']
    codes['no_tender'] = codes['Мораторий на проведение в стране регулярных тендеров']
    codes['ecology'] = codes['Закон о национальной экологической службе']
    codes['trademark'] = codes['Закон о торговых марках']
    codes['transport'] = codes['Закон о национальной транспортной службе']

    url = self.domain_ext + 'politics/money_project/%s/%s' % (
              country_id, codes[project_name])
    self.session.get(url)


def election_candidates(self, election_id):
    url = self.domain_ext + 'politics/elections/%s' % election_id
    page = self.session.tree(url)
    rows = page.xpath('//input[@type="radio" and @name="member" and @value!=0]/../..')
    if not rows:
        rows = page.xpath('//input[@type="radio" and @name="pr_member" and @value!=0]/../..')
    result = {}
    for row in rows:
        candidate_id = int(row.xpath('.//input[@type="radio"]/@value')[0])
        party = row.xpath('.//div[@class="title"]/text()')
        if party:
            party = str(party[0])
        else:
            party = 'current'
        result[party] = candidate_id
    return result


def vote(self, election_id, candidate_id):
    url = self.domain_ext + 'politics/elections/%s' % election_id
    data = {
        'member': candidate_id,
        'pr_member': candidate_id
        }
    return self.session.post(url, data=data)


def send_yacht_to_regatta(self, unit_id):
    """Send yacht to the world regatta.
    (Отправить яхту на мировую регату)
    
    Arguments:
        unit_id (int): Villa id.
    
    Returns:
        POST request responce.
    """
    
    url = self.domain_ext + 'unit/view/%s' % unit_id
    data = {'picnic_btn': 1}
    return self.session.post(url, data=data)