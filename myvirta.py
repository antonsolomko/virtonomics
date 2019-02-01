"""Virtonomics framework.
@author: Anton Solomko
"""

from virtonomics import *
import math


#@for_all_methods(logger)
class MyVirta(Virta):
    eco_factors = [
        'Промышленный и бытовой мусор',
        'Загрязнение автотранспортом',
        'Промышленные стоки',
        'Выбросы электростанций'
        ]
    industrial_cities = ['Борисполь']  # managed differently from other cities
    supported_parties = [
        'Украинская партия',
        'Партия Власти',
        '"Фронт национального освобождения имени Фарабундо Марти"'
        ]
    
    
    def __init__(self, server='olga', **kwargs):
        super().__init__(server, **kwargs)
    
    
    def set_innovation(self, unit_id, innovation_name, **kwargs):
        alternative_names = {
            'agitation': 'Политическая агитация',
            'lab1': 'Электронная библиотека',
            'lab2': 'Сотрудничество с CERN',
            'lab3': 'Производственная практика для ученых',
            'lab_equipment': 'Сверхпроводники',
            'shop_parking': 'Автомобильная парковка',
            'shop_retail': 'Консалтинг мирового лидера ритейла',
            }
        if innovation_name in alternative_names:
            innovation_name = alternative_names[innovation_name]
        return super().set_innovation(unit_id, innovation_name, **kwargs)
    
    
    def farm_seasons(self):
        unit_seasons = {
            7429138: {5: 'Зерно',
                      6: 'Сахар',
                      7: 'Сахар',
                      8: 'Сахар',
                      9: 'Кукуруза',
                      10: 'Кукуруза',
                      11: 'Выращивание помидоров'
                     }
            }
        for unit_id, seasons in unit_seasons.items():
            self.farm_season(unit_id, seasons)
    
    
    def autorepair_equipment(self):
        suppliers = {
            5600270: 'office',
            6715974: ('workshop', 'mill'),
            3329984: ('farm', 'orchard'),
            8393314: 'educational'
            }
        # Find supplier for restaurants
        offers = {i: o for i, o in self.offers(373198).items()
                  if o['price'] <= 2000000 and o['quality'] > 60 and o['free_for_buy'] > 300}
        if offers:
            offer_id = min(offers, key=lambda i: offers[i]['price']/offers[i]['quality'])
            suppliers[offer_id] = 'restaurant'
        
        for offer_id, unit_class in suppliers.items():
            units = [u['id'] for u in self.units(unit_class_kind=unit_class).values()]
            self.repair_equipment_all(offer_id, units)
    
    
    def party_sales(self, unit_ids=None):
        """Open warehouse sales for party members.
        
        Arguments:
            unit_ids (list): Units to handle. If not passed, opens all
                warehouses with names starting with '%'.
        """
        
        # Determine party members companies ids
        url = self.domain_ext + 'company/view/%s/party' % self.company['id']
        page = self.session.tree(url)
        xp = '//input[@name="member[]"]/../..//a[contains(@href,"company/view")]/@href'
        companies = [href.split('/')[-1] for href in page.xpath(xp)]
        for unit_id, unit in self.units(class_name='Склад').items():
            if (not unit_ids and unit['name'][:1] == '%' or unit_id in unit_ids):
                print(unit['name'])
                products = {}
                for contract in self.sale_contracts(unit_id)['data']:
                    products[contract['product_id']] = contract['offer_price']
                data = {product: {'price': price, 
                                  'constraint': 2, 
                                  'company': companies} 
                        for product, price in products.items()}
                self.set_sale_offers(unit_id, data)
    
    
    def agitation(self):
        """Run political agitation for all villas"""
        
        print('\nПолитическая агитация:')
        units = self.units(unit_type_name='Вилла', country_name='Украина')
        for unit in units.values():
            print(unit['name'])
            self.set_innovation(unit['id'], 'agitation')
    
    
    def manage_cities(self):
        print('\nMAYOR')
        cities = [c for c in self.cities.values() 
                  if 'mayor' in c and c['mayor']['mayor_name']==self.user]
        
        for city in cities:
            is_industrial = city['city_name'] in self.industrial_cities
            days_passed = city['mayor']['mayor_elections_counter']
            days_to_election = self.days_to_election(days_passed)
            print('\n%s %d / %d' % (city['city_name'], days_to_election, 
                                    self.days_to_refresh))
            
            # Run ecological projects once necessary and before election
            url = self.domain_ext + 'politics/mayor/%s' % city['id']
            page = self.session.tree(url)
            for eco_factor in self.eco_factors:
                xpath = '//td[.="%s"]/../td[2]/span/text()' % eco_factor
                if days_to_election <= 1 or page.xpath(xpath)[0] != 'в норме':
                    self.city_money_project(city['id'], eco_factor)
                    
            # Continuously run trade union agreement for industrial cities
            if is_industrial:
                self.city_money_project(city['id'], 'trade_union')
                self.city_money_project(city['id'], 'salary_down')
            
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
            
            if days_to_election == 0:
                shops = self.units(city_id=city['id'], unit_class_kind='shop')
                for shop_id in shops:
                    self.set_innovation(shop_id, 'shop_retail')
                    self.set_innovation(shop_id, 'shop_parking')
    
    
    def region_money_projects(self, country_id, project_names):
        """Run several region progects."""
        
        for project_name in project_names:
            self.region_money_project(country_id, project_name)
    
    
    def manage_regions(self):
        print('\nGOVERNOR')
        regions = [c for c in self.regions.values() if 'governor' in c 
                   and c['governor']['governor_name']==self.user]
        for region in regions:
            print('\n' + region['region_name'], self.days_to_refresh)
            url = self.domain_ext + 'politics/governor/%s' % region['id']
            page = self.session.tree(url)
            for eco_factor in self.eco_factors:
                xpath = '//td[.="%s"]/../td[2]/span/text()' % eco_factor
                if page.xpath(xpath)[0] != 'в норме':
                    self.region_money_project(region['id'], eco_factor)
            self.region_money_projects(
                    region['id'], 
                    ('eco90', 'agriculture', 'forest', 'animal', 'air', 'road')
                    )
    
    
    def country_money_projects(self, country_id, project_names):
        """Run several country progects."""
        
        for project_name in project_names:
            self.country_money_project(country_id, project_name)
    
    
    def manage_countries(self):
        print('\nPRESIDENT')
        countries = [c for c in self.countries.values() if 'president' in c 
                     and c['president']['president_name']==self.user]
        for country in countries:
            print('\n' + country['country_name'], self.days_to_refresh)
            if self.days_to_refresh <= 26:
                #self.country_money_project(country['id'], 'education')
                self.country_money_project(country['id'], 'construction')
            self.country_money_projects(
                country['id'], ['sport', 'food', 'ecology', 'transport'])
    
    
    def vote(self, election_id):
        """Vote in a given election"""
        
        url = self.domain_ext + 'politics/elections/%s' % election_id
        page = self.session.tree(url)
        xpath = '//div[@class="title"][.="%s"]/../../../td/input/@value'
        for party_name in self.supported_parties:
            if '"' in party_name:
                xpath = xpath.replace('"',"'")
            elif "'" in party_name:
                xpath = xpath.replace("'",'"')
            members = page.xpath(xpath % party_name)
            if members:
                print(election_id, 'vote for', party_name)
                supported_candidate = members[0]
                break
        else:
            candidates = page.xpath('//input[@name="member"]/@value')
            if len(set(candidates)) == 2:
                print(election_id, 'vote for single candidate')
                supported_candidate = candidates[0]
            else:
                return None
        data = {
            'member': supported_candidate,
            'pr_member': supported_candidate
            }
        return self.session.post(url, data=data)
    
    
    def elections_vote(self, within_days=2):
        """Vote in all elections"""
        
        print('\nELECTIONS')
        for e in self.elections(within_days=within_days):
            self.vote(e)
    
    
    def politics(self):
        self.agitation()
        self.manage_cities()
        self.manage_regions()
        self.manage_countries()
        self.elections_vote()
        self.buy_equipment(6247327, 7970419, 4)
        self.send_yacht_to_regatta(6247327)
    
    
    def sort_sale_contracts(self, unit_id):
        products = {}
        contracts = self.sale_contracts(unit_id)
        sort_key = lambda c: (c['consumer_company_id'] != self.company['id'],
                              c['party_quantity'])
        for contract in sorted(contracts, key=sort_key):
            p = contract['product_id']
            products[p] = products.get(p, []) + [contract['consumer_id']]
        self.reorder_sale_contracts(unit_id, products)
    
    
    def sort_all_sale_contracts(self):
        units = self.units(unit_class_kind='warehouse')
        for unit_id in units:
            sale_contracts = self.sale_contracts(unit_id)
            consumers = set(c['consumer_company_id'] for c in sale_contracts)
            if consumers and consumers != {self.company['id']}:
                self.sort_sale_contracts(unit_id)
    
    
    def resize_warehouses(self):
        for unit_id in self.units(unit_class_kind='warehouse'):
            unit = self.unit_summary(unit_id, refresh=True)
            target_size = int(unit['size'] * unit['filling'] / 90) + 1
            print(unit_id, unit['name'], unit['size'], '->', target_size)
            self.resize_unit(unit_id, size=target_size)
    
    
    def sypply_own_shops(self):
        offers = set(c['offer_id'] for c in self.sale_contracts(7355677))
        for offer_id in offers:
            self.create_supply_contract(7489136, offer_id, max_increase=0)
    
    
    def set_technologies(self):
        types = {
            'animalfarm': 27, 
            'farm': 23, 
            'mill': 30, 
            'mine': 23, 
            'orchard': 23, 
            'sawmill': 30,
            'workshop': 30}
        for unit_id in self.units(unit_class_kind=list(types.keys())):
            unit = self.unit_summary(unit_id)
            level = unit.get('technology_level', 0)
            if level > 0:
                available_levels = self.investigated_technologies.get(
                                       unit['unit_type_id'], [0])
                top_level = types[unit['unit_class_kind']]
                max_level = max(v for v in available_levels if v <= top_level)
                if max_level > level:
                    print(unit['id'], unit['name'], level, max_level)
        pass
    
    
    @staticmethod
    def lab_quality_required(level):
        return 0.0106 * level**2 + 1.4468 * level - 1.6955 + 0.1
    
    
    def manage_research(self):
        print('\nRESEARCH')
        labs = {lab_id: self.unit_summary(lab_id) 
                for lab_id in self.units(unit_class_kind='lab')}
        free_labs = []
        current_research = {}
        for lab_id, lab in labs.items():
            lab = self.unit_summary(lab_id)
            unittype_id = lab['project'].get('unit_type_id', 0)
            level = lab['project'].get('level_developing', 0)
            stage = lab['project'].get('current_step', 0)
            if (stage == 0 or level in 
                    self.investigated_technologies.get(unittype_id, [])):
                free_labs.append(lab_id)
            else:
                if stage == 1 and lab['project']['hepotesis']:
                    stage = 1.5
                elif stage == 3 and not lab['project']['project_unit_id']:
                    stage = 2.5
                
                if unittype_id not in current_research:
                    current_research[unittype_id] = {}
                if level not in current_research[unittype_id]:
                    current_research[unittype_id][level] = {}
                current_research[unittype_id][level][lab_id] = stage
                
                time_left = lab['project']['current_step_time_left']
                if stage == 1 and time_left < 2:
                    print(lab_id, self.unittypes[unittype_id]['name'], '1..2')
                    self.set_innovation(lab_id, 'lab2')
                
                if (stage == 3 and lab['project']['project_unit_loading'] is not None
                        and lab['project']['project_unit_loading'] < 100):
                    print(lab_id, self.unittypes[unittype_id]['name'])
                    print(' ! модификатор скорости испытаний < 100%')
        #return current_research
        
        for unittype_id, levels in current_research.items():
            for level, lab_stages in levels.items():
                if any(stage > 2 for stage in lab_stages.values()):
                    # select single laboratory to carry on research and
                    # filter out redundant labs
                    key = lambda lab_id: (
                             lab_stages[lab_id] <= 2,
                             labs[lab_id]['project']['current_step_time_left'],
                             labs[lab_id]['equipment_count'],
                             labs[lab_id]['equipment_quality']
                             )
                    lab_id = min(lab_stages, key=key)
                    
                    # Mark remaining laboratories as free
                    for l_id in lab_stages:
                        if l_id != lab_id:
                            free_labs.append(l_id)
                    
                    stage = lab_stages[lab_id]
                    levels[level] = {lab_id: stage}

                    if stage == 2.5:
                        # Set experimental unit
                        lab = labs[lab_id]
                        self.set_innovation(lab_id, 'lab3')
                        print(lab['id'], self.unittypes[unittype_id]['name'], 
                              '%s.3' % level)
                        min_size = lab['project'][
                                       'workshop_produce_bound_level_required']
                        exp_unit = self.choose_experimental_unit(
                                       unittype_id, min_size, level-1)
                        if exp_unit:
                            print(' ->', exp_unit['id'], exp_unit['name'])
                            self.set_experemental_unit(lab_id, exp_unit['id'])
                            self.holiday_unset(exp_unit['id'])
                        else:
                            print(' No experimental units available of size',
                                  min_size, 'and technology level', level-1)
                else:
                    num = len(lab_stages)
                    for lab_id, stage in lab_stages.items():
                        if stage == 1.5:
                            # Select hypotesis
                            #self.set_innovation(lab_id, 'lab2')
                            labs[lab_id] = self.unit_summary(lab_id, refresh=1)
                            lab = labs[lab_id]
                            hypoteses = lab['project']['hepotesis']
                            hypotesis = self.choose_hypothesis(hypoteses, num)
                            print(lab['id'], 
                                  self.unittypes[unittype_id]['name'],
                                  '%s.2' % level, '(%d)' % num,
                                  '\n ->', 
                                  '%s%%' % hypotesis['success_probabilities'],
                                  '%.2f days' % hypotesis['expected_time'])
                            self.select_hypotesis(lab_id, hypotesis['id'])
        
        # New research
        new_research = {}
        for unittype_id in self.unittypes(need_technology=True):
            if self.unittypes[unittype_id]['kind'] in ['mine', 'farm', 
                    'orchard', 'fishingbase']:
                continue
            for level in self.researchable_technologies(unittype_id):
                if not current_research.get(unittype_id, {}).get(level, []):
                    if level not in new_research:
                        new_research[level] = []
                    new_research[level].append(unittype_id)
        
        free_labs0 = [lab_id for lab_id in free_labs
                     if labs[lab_id]['city_id'] in (310400, 422041)]

        print(len(free_labs0), 'free laboratories:')
        
        eq_key = lambda i: (labs[i]['equipment_count'],
                            labs[i]['equipment_quality'])
        for i in sorted(free_labs0, key=eq_key):
            print(i, labs[i]['equipment_count'],
                  '%.2f' % labs[i]['equipment_quality'])
        
        for level, unittypes in sorted(new_research.items()):
            if level <= 13: num = 5  # 100
            elif level <= 19: num = 4  # 300
            elif level <= 25: num = 3  # 700
            elif level <= 27: num = 2-1  # 850
            else: num = 1  # 1000
            for unittype_id in unittypes:
                # Choose free laboratory satisfying minimal requirements
                print('+', self.unittypes[unittype_id]['name'], level, 
                      '(%d)' % num)
                num_required = self.lab_employees_required(level)
                qual_required = self.lab_quality_required(level)
                for i in range(num):
                    candidate_labs = [i for i in free_labs0
                        if labs[i]['equipment_count'] >= 10*num_required
                        and labs[i]['equipment_quality'] >= qual_required]
                    #if not candidate_labs:
                    #    candidate_labs = [i for i in free_labs0
                    #        if labs[i]['equipment_count'] >= 10*num_required]
                    if candidate_labs:
                        lab_id = min(candidate_labs, key=eq_key)
                        self.start_research_project(lab_id, unittype_id, level)
                        self.holiday_unset(lab_id)
                        self.set_employees(lab_id, quantity=num_required, 
                                           trigger=2)
                        self.rename_unit(lab_id, 
                                         self.unittypes[unittype_id]['name'])
                        self.set_innovation(lab_id, 'lab1')
                        free_labs0.remove(lab_id)
                        free_labs.remove(lab_id)
                        print(' ->', lab_id,
                              '(%d %.2f)' % (num_required, qual_required))
                    else:
                        print(' -> ???')
        
        print(len(free_labs0), 'free laboratories')
        
        for lab_id in free_labs:
            self.rename_unit(lab_id, '-')
            self.holiday_set(lab_id)
        
        for lab_id in labs:
            self.set_innovation(lab_id, 'lab_equipment')
            
        return current_research
    
    
    ### UNDER DEVELOPMENT ###
    
    def manage_shop(self, shop_id):
        """"""
        
        supply_contracts = self.supply_contracts(shop_id)
        categories = set(c['shop_goods_category_id'] for c in supply_contracts.values())
        products = self.goods(category_id=categories)
        for product_id, product in products.items():
            print(product['name'], end=' ')
            product_contracts = supply_contracts(product_id=product_id)
            offers = self.offers(product_id)(brandname_id=None)
            print(len(offers))
        
    
    def manage_shops(self):
        for shop_id in self.units(unit_class_kind='shop'):
            self.manage_shop(shop_id)
    

    def manage_sale_offers(self, unit_id, delta=0, markup=0.1, target_ratio=10):
        """Manage sale offers.
        
        Note:
            Supported unit kinds (all that have "sale" bookmark): 'animalfarm', 
            'farm', 'fishingbase', 'mill',  'mine', 'orchard', 'sawmill', 
            'warehouse', 'workshop'. Passing units of other kind may cause an 
            error. No check is made.
        
        Arguments:
            unit_id (int): Unit_id.
            delta (float 0..1): For products sold to shops or other companies
                the selling price will be changed by delta, depending on the 
                ratio between stock and orders amount (increased if demand is 
                high, and decreased otherwise). Defaults to 0.
            markup (float): Industrial products for internal use get base 
                markup to their cost price. Defaults to 0.1 (10% markup).
        
        Todo:
            Price change algorithm to be defined.
        """
        
        assert 0 <= delta < 1, 'delta should be in the range 0 <= delta < 1'
        markup_factor = 1 + markup
        sale_offers = self.sale_offers(unit_id)
        sale_contracts = self.sale_contracts(unit_id)
        
        for product_id, offer in sale_offers.items():
            contracts = sale_contracts(product_id=product_id)
            if offer['stock']:
                print(' ', offer['product_name'], end=' ')
                if offer['constraint'] == 0:
                    offer['constraint'] = 3
                if offer['constraint'] in (1,2,5) or any(
                        c['consumer_company_id'] != self.company['id'] 
                        or c['consumer_unit_class_symbol'] == 'shop'
                        for c in contracts):
                    # Adjust price
                    r = target_ratio
                    s = offer['stock']
                    t = sum(c['party_quantity'] for c in contracts)  # total order
                    if t < s:
                        percent = delta * math.sin(
                                  0.5*math.pi * (math.log(1 + r*(r-2)*t/s) / math.log(r-1) - 1)
                                  )
                    else:
                        percent = delta
                    
                    factor = 1 + percent
                    print('%.2f %+.2f%%' % (r*t/s, 100 * percent))
                    offer['price'] *= factor
                    offer['price'] = max(offer['price'], offer['cost'])
                elif offer['cost']:
                        print('x', markup_factor)
                        offer['price'] = markup_factor * offer['cost']
                offer['price'] = round(offer['price'], 2)
            else:
                if offer['constraint'] == 0 and not contracts:
                    offer['constraint'] = 0  # Hide empty offers
        #self.set_sale_offers(unit_id, sale_offers)
        
    
    def manage_sale_offers_all(self, *, unit_class=None, delta=0, markup=0.1):
        print('\nADJUSTING SALE OFFERS')
        if not unit_class:
            unit_class = [
                'animalfarm',
                'farm',
                'fishingbase',
                'mill',
                'mine',
                'orchard',
                'sawmill',
                'warehouse',
                'workshop',
                ]
        ecxeptions = [7424134, 6745609, 6749443]
        units = self.units(unit_class_kind=unit_class)
        for unit_id, unit in units.items():
            print(unit['id'], unit['name'])
            if unit_id in ecxeptions:
                print('  skip')
            else:
                mrkp = 0 if unit['unit_class_kind'] == 'warehouse' else markup
                self.manage_sale_offers(unit_id, delta=delta, markup=mrkp)
    
    
if __name__ == '__main__':
    v = MyVirta('olga')
    #v.manage_research()
    #p = v.manage_shop(7402726)
    v.manage_sale_offers_all(delta=0.05, unit_class='warehouse')