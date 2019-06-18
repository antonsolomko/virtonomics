from .const import ECO_FACTORS, INDUSTRIAL_CITIES, SUPPORTED_PARTIES, MANAGED_SHOPS_NAMES


def agitation(self):
    """Запустить политическую агитацию на всех виллах"""
    
    print('\nПолитическая агитация:')
    units = self.units(unit_type_name='Вилла', country_name='Украина')
    for unit in units.values():
        print(unit['name'])
        self.set_innovation(unit['id'], 'agitation')


def manage_cities(self):
    """Управление городами"""
    
    print('\nMAYOR')
    cities = [c for c in self.cities.values() 
              if 'mayor' in c and c['mayor']['mayor_name']==self.user]
    
    for city in cities:
        is_industrial = city['city_name'] in INDUSTRIAL_CITIES
        days_passed = city['mayor']['mayor_elections_counter']
        days_to_election = self.days_to_election(days_passed)
        print('%s %d / %d' % (city['city_name'], days_to_election, 
                                self.days_to_refresh))
        
        # Run ecological projects once necessary and before election
        url = self.domain_ext + 'politics/mayor/%s' % city['id']
        page = self.session.tree(url)
        for eco_factor in ECO_FACTORS:
            xpath = '//td[.="%s"]/../td[2]/span/text()' % eco_factor
            if days_to_election <= 1 or page.xpath(xpath)[0] != 'в норме':
                self.city_money_project(city['id'], eco_factor)
                
        # Continuously run trade union agreement for industrial cities
        if is_industrial:
            self.city_money_project(city['id'], 'trade_union')
            self.city_money_project(city['id'], 'salary_down')
            if days_to_election % 26 == 0:
                self.city_money_project(city['id'], 'transport')
        
        # Run city festival before election
        if days_to_election == 0 or days_to_election == 13:
            self.city_money_project(city['id'], 'festival')
        
        if (is_industrial and self.days_to_refresh <= 1
                or days_to_election == 0):
            self.city_money_project(city['id'], 'education')
            
        if days_to_election == 0 or self.days_to_refresh <= 1:
            if not is_industrial:
                self.city_money_project(city['id'], 'salary_up')
            self.city_money_project(city['id'], 'construction')
        
        if days_to_election > 13:
            self.city_change_council_tax(city['id'], increase=True)
        else:
            self.city_change_council_tax(city['id'], increase=False)
        
        self.city_change_rent(city['id'], 'office', rent_up=True)
        self.city_change_rent(city['id'], 'shop', rent_up=False)
        self.city_change_rent(city['id'], 'fuel', rent_up=False)
        self.city_change_rent(city['id'], 'educational', rent_up=False)
        self.city_change_rent(city['id'], 'service_light', rent_up=False)
        self.city_change_rent(city['id'], 'restaurant', rent_up=False)
        self.city_change_rent(city['id'], 'repair', rent_up=False)
        self.city_change_rent(city['id'], 'warehouse', rent_up=not is_industrial)
        self.city_change_rent(city['id'], 'villa', rent_up=True)
        
        if city['population'] > 500000 and days_to_election > 13:
            self.city_retail_project(city['id'], 'Продукты питания')
            self.city_retail_project(city['id'], 'Бакалея')
        
        # Removed
        if False and days_to_election == 0:
            shops = self.units(city_id=city['id'], unit_class_kind='shop')
            for shop_id, shop in shops.items():
                if shop['name'] not in MANAGED_SHOPS_NAMES:
                    self.set_innovation(shop_id, 'shop_retail')
                    self.set_innovation(shop_id, 'shop_parking')


def region_money_projects(self, country_id, project_names):
    """Запустить несколько региональных проектов"""
    
    for project_name in project_names:
        self.region_money_project(country_id, project_name)


def manage_regions(self):
    """Управление регионами"""
    
    print('\nGOVERNOR')
    regions = [c for c in self.regions.values() if 'governor' in c 
               and c['governor']['governor_name']==self.user]
    for region in regions:
        print(region['region_name'], self.days_to_refresh)
        url = self.domain_ext + 'politics/governor/%s' % region['id']
        page = self.session.tree(url)
        for eco_factor in ECO_FACTORS:
            xpath = '//td[.="%s"]/../td[2]/span/text()' % eco_factor
            if page.xpath(xpath)[0] != 'в норме':
                self.region_money_project(region['id'], eco_factor)
        self.region_money_projects(
                region['id'], 
                ('eco90', 'agriculture', 'forest', 'animal', 'air', 'road')
                )


def country_money_projects(self, country_id, project_names):
    """Запустить несколько государственных проектов"""
    
    for project_name in project_names:
        self.country_money_project(country_id, project_name)


def manage_countries(self):
    """Управление странами"""
    
    print('\nPRESIDENT')
    countries = [c for c in self.countries.values() if 'president' in c 
                 and c['president']['president_name']==self.user]
    for country in countries:
        print(country['country_name'], self.days_to_refresh)
        if self.days_to_refresh < 25:
            self.country_money_project(country['id'], 'education')
            self.country_money_project(country['id'], 'construction')
        self.country_money_projects(
            country['id'], ['sport', 'food', 'ecology', 'transport'])


def election_vote(self, election_id):
    """Vote for candidates from supported parties at a given election"""
    
    candidates = self.election_candidates(election_id)
    supported_candidate_id = None
    for party_name in SUPPORTED_PARTIES:
        if party_name in candidates:
            supported_candidate_id = candidates[party_name]
            break
    else:
        if len(set(candidates.values())) == 1:
            supported_candidate_id = next(iter(candidates.values()))
    
    current = candidates.get('current', None)
    for party_name, candidate_id in candidates.items():
        if party_name != 'current':
            print(' ', party_name + (' (действующий)' if candidate_id==current else ''),
                  '+' if candidate_id==supported_candidate_id else '')
    
    if supported_candidate_id:
        self.vote(election_id, supported_candidate_id)


def elections_vote(self):
    """Vote for candidates from supported parties in all elections"""
    
    print('\nELECTIONS')
    for election_id, election in self.elections(days_to_election=(0,1,2,3)).items():
        print(election_id, election['location_name'])
        self.election_vote(election_id)


def politics(self):
    self.agitation()
    self.manage_cities()
    self.manage_regions()
    self.manage_countries()
    self.elections_vote()
    self.buy_equipment(6247327, 7970419, 4)
    self.send_yacht_to_regatta(6247327)