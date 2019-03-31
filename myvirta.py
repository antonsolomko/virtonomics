"""Virtonomics framework.
@author: Anton Solomko
"""

from virtonomics import *
import math
import random


def sigmoid(x, slope=1, bound=1):
    return  1 + bound * (2 / (1 + math.exp(-2 * slope * (x-1) / bound)) - 1) if bound>0 else 0


def delay(func):
    def wrapper(*args, **kwargs):
        secs = random.uniform(0.0, 0.2)
        print('.', end='')
        time.sleep(secs)
        return func(*args, **kwargs)
    return wrapper


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
        self.session.get = delay(self.session.get)
        self.session.post = delay(self.session.post)
    
    
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
    
    
    def farm_seasons(self):
        unit_seasons = {
            7429138: {5: 'Зерно',
                      6: 'Сахар',
                      7: 'Сахар',
                      8: 'Сахар',
                      9: 'Кукуруза',
                      10: 'Кукуруза',
                      11: 'Помидоры',
                     },
            7549945: {8: 'Апельсины',
                      9: 'Апельсины',
                      10: 'Оливки',
                      11: 'Оливки',
                     },
            }
        for unit_id, seasons in unit_seasons.items():
            self.farm_season(unit_id, seasons)
    
    
    def autorepair_equipment(self):
        suppliers = {
            8415404: 'office',
            6715974: ('workshop', 'mill'),
            3329984: ('farm', 'orchard'),
            8393314: 'educational',
            4974307: 'lab',
            8197411: 'restaurant',
            }
        '''
        # Find supplier for restaurants
        offers = {i: o for i, o in self.offers(373198).items()
                  if o['price'] <= 2000000 and o['quality'] > 60 and o['free_for_buy'] > 300}
        if offers:
            offer_id = min(offers, key=lambda i: offers[i]['price']/offers[i]['quality'])
            suppliers[offer_id] = 'restaurant'
        
        # Find supplier for laboratories
        offers = {i: o for i, o in self.offers(1528).items()
                  if o['price'] <= 1000000 and o['quality'] > 60 and o['free_for_buy'] > 300}
        if offers:
            offer_id = min(offers, key=lambda i: offers[i]['price']/offers[i]['quality'])
            suppliers[offer_id] = 'lab'
        '''
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
            print('%s %d / %d' % (city['city_name'], days_to_election, 
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
            print(region['region_name'], self.days_to_refresh)
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
            print(country['country_name'], self.days_to_refresh)
            if self.days_to_refresh < 25:
                self.country_money_project(country['id'], 'education')
                self.country_money_project(country['id'], 'construction')
            self.country_money_projects(
                country['id'], ['sport', 'food', 'ecology', 'transport'])
    
    
    def vote(self, election_id):
        """Vote at a given election"""
        
        url = self.domain_ext + 'politics/elections/%s' % election_id
        page = self.session.tree(url)
        xp = '//div[@class="title"][.=%s]/../../../td/input/@value'
        for party_name in self.supported_parties:
            if '"' in party_name:
                party_name = "'" + party_name + "'"
            else:
                party_name = '"' + party_name + '"'
            members = page.xpath(xp % party_name)
            if members:
                print('  vote for', party_name)
                supported_candidate = members[0]
                break
        else:
            candidates = page.xpath('//input[@name="member"]/@value')
            if not candidates:
                candidates = page.xpath('//input[@name="pr_member"]/@value')
            if len(set(candidates)) == 2:
                print('  vote for the only candidate')
                supported_candidate = candidates[0]
            else:
                return None
        data = {
            'member': supported_candidate,
            'pr_member': supported_candidate
            }
        return self.session.post(url, data=data)
    
    
    def elections_vote(self):
        """Vote in all elections"""
        
        print('\nELECTIONS')
        for election_id, election in self.elections(days_to_election=(0,1,2,3)).items():
            print(election_id, election['location_name'])
            self.vote(election_id)
    
    
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
                              c['country_name'] != 'Украина',
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
    
    
    def sypply_own_shop(self, shop_id, units=None):
        if not units:
            units = [7405776, 6703013, 7355677, 7429787, 7495664, 7515896, 6991290]
        offers = set(c['offer_id'] for u in units for c in self.sale_contracts(u))
        print(offers)
        for offer_id in offers:
            self.create_supply_contract(shop_id, offer_id, max_increase=0)
    
    
    def set_technologies(self):
        print('UPDATE TECHNOLOGIES')
        types = {
            'animalfarm': 27, 
            'farm': 23, 
            'mill': 30, 
            'mine': 23, 
            'orchard': 23, 
            'sawmill': 30,
            'workshop': 30}
        for unit_id in self.units(unit_class_kind=list(types.keys())):
            unit = self.unit_summary(unit_id, refresh=True)
            level = unit.get('technology_level')
            if level:
                available_levels = self.investigated_technologies.get(
                                       unit['unit_type_id'], [0])
                top_level = types[unit['unit_class_kind']]
                max_level = max(v for v in available_levels if v <= top_level)
                if max_level > level:
                    print(unit['id'], unit['name'], level, '->', max_level)
                    self.set_technology(unit_id, max_level)
    
    
    @staticmethod
    def lab_quality_required(level):
        return 0.0106 * level**2 + 1.4468 * level - 1.6955 + 0.1
    
    
    def manage_research(self):
        print('\nRESEARCH')
        labs = {lab_id: self.unit_summary(lab_id) for lab_id in self.units(unit_class_kind='lab')}
        free_labs = []
        current_research = {}
        experimental_units = [unit_id for unit_id, unit in self.units.items() 
                              if 365385 in self.indicators.get(unit_id, {})]
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
                if stage == 1 and time_left < 3:
                    print(lab_id, self.unittypes[unittype_id]['name'], '1..2')
                    self.set_innovation(lab_id, 'lab2')
                elif stage == 3 and time_left < 2:
                    self.rename_unit(lab_id, '-'+self.unittypes[unittype_id]['name'])
                
                if (stage == 3 and lab['project']['project_unit_loading'] is not None
                        and lab['project']['project_unit_loading'] < 100):
                    print(lab_id, self.unittypes[unittype_id]['name'])
                    print(' ! модификатор скорости испытаний < 100%')
        
        for unittype_id, levels in current_research.items():
            for level, lab_stages in levels.items():
                if any(stage > 2 for stage in lab_stages.values()):
                    # select single laboratory to carry on research and filter 
                    # out redundant labs
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
                            experimental_units.append(exp_unit['id'])
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
                    'orchard', 'fishingbase', 'sawmill']:
                continue
            for level in self.researchable_technologies(unittype_id):
                if not current_research.get(unittype_id, {}).get(level, []):
                    if level not in new_research:
                        new_research[level] = []
                    new_research[level].append(unittype_id)
        
        free_labs0 = [lab_id for lab_id in free_labs
                     if labs[lab_id]['city_id'] == 310400]

        print(len(free_labs0), 'free laboratories:')
        
        eq_key = lambda i: (labs[i]['equipment_count'],
                            labs[i]['equipment_quality'])
        for i in sorted(free_labs0, key=eq_key):
            if labs[i]['equipment_count'] > 0:
                print(i, labs[i]['equipment_count'],
                      '%.2f' % labs[i]['equipment_quality'])
        
        for level, unittypes in sorted(new_research.items()):
            if level <= 13: num = 6  # 100
            elif level <= 19: num = 5  # 300
            elif level <= 25: num = 4  # 700
            elif level <= 27: num = 3  # 850
            else: num = 2  # 1000
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
            
        self.set_technologies()
        
        print('SEND ON HOLIDAY')
        nonexperimental_units = {unit_id: unit for unit_id, unit in self.units.items()
                                 if unit['name'][0] == '=' 
                                 and unit_id not in experimental_units
                                 and not self.unit_summary(unit_id)['on_holiday']}
        for unit_id, unit in nonexperimental_units.items():
            print(unit_id, unit['name'])
            self.holiday_set(unit_id)
            
        return current_research
    

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
                    print('%+.2f%%' % (100 * percent))
                    offer['price'] *= factor
                    if percent > 0:
                        offer['price'] -= 0.01
                    offer['price'] = max(offer['price'], offer['cost'])
                elif offer['cost']:
                        print('x', markup_factor)
                        offer['price'] = markup_factor * offer['cost']
                offer['price'] = round(offer['price'], 2)
            else:
                if offer['constraint'] in (0,3) and not contracts:
                    offer['constraint'] = 0  # Hide empty offers
                    offer['price'] = 0
        self.set_sale_offers(unit_id, sale_offers)
        
    
    def manage_sale_offers_all(self, unit_class=None, delta=0, markup=0.1,
                               exception_flag='[M]'):
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
        units = self.units(unit_class_kind=unit_class)
        for unit_id, unit in units.items():
            print(unit['id'], unit['name'])
            if exception_flag and exception_flag in unit['name']:
                print('  skip')
            else:
                mrkp = 0 if unit['unit_class_kind'] == 'warehouse' else markup
                self.manage_sale_offers(unit_id, delta=delta, markup=mrkp)
    
    
    def manage_supply_orders(self, unit_id, days=3, limit_ratio=1.05):
        products = self.supply_products(unit_id)
        contracts = self.supply_contracts(unit_id)
        orders = {}
        sort_key = lambda c: (-c['quality'], 
                              c['offer_price'] + c['offer_price'] + c['offer_transport_cost'])
        for product_id, product in products.items():
            fund = max(0, product['stock'] - product['needed'])
            amount_to_order = max(0, days * product['needed'] - fund)
            amount_to_order = min(amount_to_order, int(limit_ratio * product['needed']))
            for contract in sorted(contracts(product_id=product_id).values(), key=sort_key):
                order = {}
                available = contract['free_for_buy']
                if contract['offer_max_qty'] and contract['offer_max_qty'] < available:
                    available = contract['offer_max_qty']
                if contract['supplier_is_seaport'] or available >= amount_to_order:
                    order['quantity'] = amount_to_order
                else:
                    order['quantity'] = available
                amount_to_order -= order['quantity']
                if contract['supplier_company_id'] == self.company['id']:
                    order['max_price'] = 0
                    order['max_increase'] = 0
                else:
                    order['max_price'] = contract['price_constraint_max']
                    order['max_increase'] = contract['price_constraint']
                order['min_quality'] = contract['quality_constraint_min']
                orders[contract['offer_id']] = order
                
        self.set_supply_contracts(unit_id, orders)
        return products, contracts, orders
    
    
    def manage_supply_orders_all(self, unit_class=None):
        print('\nSUPPLY')
        if not unit_class:
            unit_class = ['animalfarm', 'mill', 'workshop']
        units = self.units(unit_class_kind=unit_class)
        for unit_id, unit in units.items():
            print(unit['id'], unit['name'])
            self.manage_supply_orders(unit_id)
    
    
    def read_messages(self):
        ukr_cities = [city['city_name'] for city in self.cities(country_name='Украина').values()]
        messages = [message_id for message_id, title in self.messages.items()
                    if title == 'Поставка продукта прекращена'
                    or title == 'Увеличена цена на продукт'
                    or title == 'Поставщик ограничил объём поставок'
                    or title == 'Товар не отгружен из-за низкого качества'
                    or title == 'Товар не получен из-за низкого качества'
                    #or 'Внедрение технологии на предприятие' in title
                    or 'губернатора' in title and 'Украина' not in title
                    or 'выбран' in title
                    or 'ставки налога на прибыль' in title
                    or 'повышение энерготарифов' in title
                    or 'мэра' in title and not any(name in title for name in ukr_cities)
                    ]
        self.mark_messages_as(messages)
    
    
    ### UNDER DEVELOPMENT ###
    
    def manage_shop0(self, shop_id, days=3):
        def compute_price(position):
            def exp(percent, p0=1.5, p1=3, p2=6):
                #exp(0)=p0, #exp(0.5)=p1, #exp(1)=p2
                a = (p1-p0)**2 / (p0+p2-2*p1)
                b = ((p2-p1)/(p1-p0))**2
                return a*( b**percent - 1 ) + p0
            if not position['stock']:
                return None
            if not position['sold'] and position['stock'] > position['purchase']:
                target_price = position['cost']
            else:
                target_price = position['cost'] * exp(position['market_share'])
                avg_price = position['avg_price'] * position['quality'] / position['avg_quality']
                target_price = max(avg_price, target_price)
            if position['price']:
                new_price = (position['price'] + target_price) / 2
                max_increase = 1.05 + position['market_share'] / 5
                new_price = min(new_price, max_increase * position['price'])
                new_price = max(new_price, 0.9 * position['price'])
            else:
                new_price = target_price
            new_price = max(new_price, 1.05 * position['cost'])
            return round(new_price, 2)
        
        def compute_order(position=None, days=days):
            result = {
                'amount': 1, 
                'max_price': 100000,
                'min_quality': 0,
                'min_brand': 0
                }
            if position:
                if not position['stock']:
                    result['amount'] = max(1, position['sold'])
                    result['max_price'] = position['avg_price']
                else:
                    if position['stock'] == position['purchase']:
                        forecast = max(position['sold'], position['stock'])
                    else:
                        forecast = position['sold']
                    fund = max(0, position['stock'] - forecast)
                    if not position['sold']:
                        days = 1
                    result['amount'] = max(0, forecast * days - fund)
                    if position['market_share']:
                        market_size = position['sold'] / position['market_share']
                        result['amount'] = min(result['amount'], market_size)
                    result['max_price'] = position['price'] / 1.2
                    result['min_quality'] = position['quality'] / 1.2
                    result['min_brand'] = position['brand'] / 2
            result['amount'] = int(result['amount'])
            return result
        
        def distribute_orders(to_order, contracts):
            result = {}
            for contract in contracts.values():
                order = {}
                order['quantity'] = 0
                if contract['supplier_company_id'] == self.company['id']:
                    order['max_price'] = 0
                    order['max_increase'] = 0
                else:
                    order['max_price'] = contract['price_constraint_max']
                    order['max_increase'] = contract['price_constraint']
                order['min_quality'] = contract['quality_constraint_min']
                result[contract['offer_id']] = order
            return result
        
        supply_products = self.supply_products(shop_id)
        supply_contracts = self.supply_contracts(shop_id)
        
        categories = set(c['shop_goods_category_id'] for c in supply_contracts.values())  # departments
        products = self.goods(category_id=categories)
        
        sale_offers = {}  # New trading hall prices
        to_order = {}
        
        # New prices
        for product_id, position in self.trading_hall(shop_id).items():
            new_price = compute_price(position)
            if new_price:
                sale_offers[position['ids']] = (position['price'], new_price)
            to_order[product_id] = compute_order(position)
        
        # Orders
        orders = {}
        for product_id, product in supply_products.items():
            if product_id not in to_order:
                to_order[product_id] = compute_order()
            to_order[product_id]['product_name'] = product['product_name']  # debug
            product_contracts = supply_contracts(product_id=product_id)
            for offer_id, order in distribute_orders(to_order[product_id], product_contracts).items():
                orders[offer_id] = order
            
        # New contracts
            
        #self.set_shop_sale_prices(shop_id, sale_offers)
        #self.set_supply_contracts(shop_id, orders)
        
        return trading_hall, supply_products, supply_contracts, sale_offers, orders, to_order
        
    
    def manage_shops0(self):
        black_list = []
        global_offers = {}
        for product_id in self.goods:
            product_offers = self.offers(product_id)(brandname_id=None, max_qty=None)
            global_offers[product_id] = {}
            count = 0
            sort_key = lambda o: product_offers[o]['price'] / product_offers[o]['quality']**2
            for i, offer_id in enumerate(sorted(product_offers, key=sort_key)):
                if count >= 5:
                    break
                elif product_offers[offer_id]['company_name'] not in black_list:
                    global_offers[product_id][offer_id] = product_offers[offer_id]
                    count += 1
        return global_offers
        for shop_id, shop in self.units(unit_class_kind='shop').items():
            print(shop['name'])
            self.manage_shop(shop_id)
    
    
    def set_shops_advertisement(self, target_customers=700000):
        for shop_id in self.units(name='*****'):
            self.set_advertisement(shop_id, target_customers=target_customers, 
                                   competence=175, innovation=True)
    
    
    def set_shops_innovations(self):
        for shop_id in self.units(name='*****'):
            self.set_innovation(shop_id, 'shop_advertisement')
            self.set_innovation(shop_id, 'shop_retail')
    
    
    def distribute_shop_employees(self):
        units = [unit_id for unit_id, unit in self.units(unit_class_kind='shop').items()
                 if unit['name'] == '*****' or unit['name'][0] != '*']
        return super().distribute_shop_employees(units, competence=156, reserve=100)
    
    
    def set_shop_default_prices(self, shop_id, factor=2):
        trading_hall_prev = self.trading_hall(shop_id)
        self.set_shop_sales_prices(shop_id)
        trading_hall_new = self.trading_hall(shop_id)
        offers = {}
        for product_id in trading_hall_new:
            if trading_hall_prev[product_id]['price'] > 0:
                offers[product_id] = trading_hall_prev[product_id]['price']
                if offers[product_id] < trading_hall_new[product_id]['price']:
                    offers[product_id] = trading_hall_new[product_id]['price']
            else:
                offers[product_id] = factor * trading_hall_new[product_id]['price']
        self.set_shop_sale_prices(shop_id, offers)
    
    
    def set_shops_default_prices(self, factor=2):
        for shop_id in self.units(name='*****'):
            self.set_shop_default_prices(shop_id)
    
    
    def propagate_contracts(self, reference_shop=7559926):
        print('Copying contracts')
        shops = self.units(name='*****')
        ref_contracts = self.supply_contracts(reference_shop)  # вытягиваем из ведущего магазина список контрактов
        for shop_id in shops:
            print(shop_id)
            contracts = self.supply_contracts(shop_id)
            for offer_id in ref_contracts:
                if offer_id not in contracts:
                    print('+', offer_id)
                    self.create_supply_contract(shop_id, offer_id, max_increase=0)
    
    
    def manage_shops(self):
        min_market_share = 0.01  # минимальная доля рынка
        max_market_share = 0.4  # максимальная доля рынка
        max_adjustment = 0.02  # максимальных шаг изменения закупок
        elasticity = 10  # 20
        sales_price_factor = 2  # множитель к распродажной цене для новых товаров
        ref_shop_id = 7559926  # ведущий магазин
        
        shops = self.units(name='*****')
        cities = self.cities(city_id=[shop['city_id'] for shop in shops.values()])  # города, в которых маги
        # Вытягиваем из ведущего магазина список товаров, которыми торгуем
        products = {p['product_id']: p for p in self.supply_contracts(ref_shop_id).values()}
        
        print('Reading shops info')
        # Считываем инфу из всех торговых залов (из БД, если уже считывали)
        trading_halls = {shop_id: self.trading_hall(shop_id, cache=True) for shop_id in shops}
        
        clearance_count = {product_id: [] for product_id in products}
        for shop_id in shops:
            for product_id, trade in trading_halls[shop_id].items():
                clearance_count[product_id].append(trade['stock'] == trade['purchase'] and trade['sold'] > 0)
        clearance_rate = {product_id: sum(count) / max(1, len(count)) 
                          for (product_id, count) in clearance_count.items()}
        
        # Read retail metrics
        print('Reading markets info')
        # Считаем объемы ранков
        markets = {}
        for product_id in products:
            markets[product_id] = {}
            for shop_id, shop in shops.items():
                trade = trading_halls[shop_id][product_id]
                if trade['market_share'] > 0:
                    # Быстро оцениваем объем рынка исходя из доли и продаж
                    markets[product_id][shop['city_id']] = trade['sold'] / trade['market_share']
                else:
                    # Иначе читаем напрямую из розничного отчета по городу
                    print('!', end='')
                    city = cities[shop['city_id']]
                    geo = city['country_id'], city['region_id'], city['city_id']
                    markets[product_id][shop['city_id']] = self.retail_metrics(
                        product_id, geo)['local_market_size']
            # Считаем суммврный объем всех рынков для каждого товару
            markets[product_id]['total_market_size'] = sum(markets[product_id].values())
        
        # Distribute sales
        print('Distributing sales')
        # Распределяем товары между магами
        target_sales = {}
        for product_id, product in products.items():
            if not product['quantity_at_supplier_storage']:
                # Если на складе нет товара
                target_sales[product_id] = {shop_id: 0 for shop_id in shops}
                continue
                
            # Compute mean price for a given product
            # Считаем среднюю цену сбыта
            total_sold = sum(trading_halls[shop_id][product_id]['sold'] for shop_id in shops)
            if total_sold > 0:
                # средняя цена
                mean_price = sum(trading_halls[shop_id][product_id]['price']
                                 * trading_halls[shop_id][product_id]['sold']
                                 for shop_id in shops) / total_sold
                # стандартное отклоние цены от средней
                std_dev = (sum((trading_halls[shop_id][product_id]['price'] - mean_price) ** 2
                               * trading_halls[shop_id][product_id]['sold']
                               for shop_id in shops) / total_sold) ** 0.5
                # наклон сигмоиды
                adjustment_rate =  max_adjustment * mean_price / std_dev
            else:
                mean_price = None
                adjustment_rate = max_adjustment  # наклон сигмоиды
            
            # Считаем, сколько товара хотим сбывать в каждом магазине
            target = {}
            for shop_id, shop in shops.items():
                trade = trading_halls[shop_id][product_id]
                market_size = markets[product_id][shop['city_id']]
                if trade['sold']:
                    # Отталкиваемся от продаж, если таковые были
                    target_sale = trade['sold']
                    if trade['stock'] == trade['purchase']:
                        # Если распродали весь товар, увеличить долю на 5%
                        target_sale *= 1.05
                    elif mean_price:
                        # Если имеем точное значение спроса, корректируем пропорционально
                        # отклонению цены от средней
                        target_sale *= sigmoid(trade['price'] / mean_price, 
                                               adjustment_rate, max_adjustment)
                else:
                    # По умолчанию, если не было продаж, распределяем пропорционально объемам рынков
                    target_sale = (product['quantity_at_supplier_storage'] 
                                   * market_size
                                   / markets[product_id]['total_market_size'])
                target[shop_id] = (max(1, target_sale),
                                   max(1, min_market_share * market_size),
                                   max(1, max_market_share * market_size)
                                   )
                
            # Найденные объемы не обязательно суммируются в кол-во товара на складе
            # Поэтому распределяем весь имеющийся товар пропорционально
            def total(factor):
                return sum(int(min(max(factor * t, mint), maxt)) 
                           for (t, mint, maxt) in target.values())
            
            target_sales[product_id] = {}
            factor0 = 0
            factor1 = max(maxt / t for (t, mint, maxt) in target.values())
            if total(factor0) >= product['quantity_at_supplier_storage']:
                total_min = total(factor0)
                for shop_id in shops:
                    t, mint, maxt = target[shop_id]
                    target_sale = mint * product['quantity_at_supplier_storage'] / total_min
                    target_sales[product_id][shop_id] = int(target_sale)
            elif total(factor1) <= product['quantity_at_supplier_storage']:
                for shop_id in shops:
                    t, mint, maxt = target[shop_id]
                    target_sales[product_id][shop_id] = int(maxt)
            else:
                total_sales0 = total(factor0)
                total_sales1 = total(factor1)
                while total_sales0 < total_sales1:
                    factor = (factor0 + factor1) / 2
                    if factor == factor0 or factor == factor1:
                        break
                    if total(factor) < product['quantity_at_supplier_storage']:
                        factor0 = factor
                        total_sales0 = total(factor0)
                    else:
                        factor1 = factor
                        total_sales1 = total(factor1)
                error0 = abs(total(factor0) - product['quantity_at_supplier_storage'])
                error1 = abs(total(factor1) - product['quantity_at_supplier_storage'])
                factor = factor0 if error0 <= error1 else factor1
                for shop_id, shop in shops.items():
                    t, mint, maxt = target[shop_id]
                    target_sale = min(max(factor * t, mint), maxt)
                    target_sales[product_id][shop_id] = int(target_sale)
        
        print('Managing shops')
        # Корректируем магазины
        for shop_id, shop in shops.items():
            print(shop_id)
            # Update orders
            # Снабжение
            orders = {}
            for contract in self.supply_contracts(shop_id).values():
                if contract['product_id'] not in products:
                    continue
                # заказываем сколько распределили
                orders[contract['offer_id']] = {
                    'quantity': target_sales[contract['product_id']][shop_id], 
                    'max_increase': 0
                    }
            self.set_supply_contracts(shop_id, orders)
            
            # Update prices
            # Сбрасываем цены в ноль
            offers = {t['ids']: 0 for t in trading_halls[shop_id].values()}
            self.set_shop_sale_prices(shop_id, offers)
            # Устанавливаем распродажные цены
            self.set_shop_sales_prices(shop_id)
            # Считываем торговый зал
            trading_hall_sales = self.trading_hall(shop_id, cache=False)
            offers = {}
            for product_id, trade in trading_halls[shop_id].items():
                # на случай, если уже вывезли часть товара
                trade['current_stock'] = trading_hall_sales[product_id]['stock']  
                if product_id not in products:
                    new_price = trade['price']  # возвращаем старую цену
                elif trade['price'] > 0:
                    new_price = trade['price']
                    if trade['sold'] > 0:
                        if trade['stock'] == trade['purchase']:
                            # если продан весь товар, повышаем цену
                            new_price *= 1 + max_adjustment * (1 + 9*clearance_rate[product_id])
                        else:
                            # иначе, корректируем под требуемый объем продаж
                            new_price *= sigmoid(trade['sold'] / target_sales[product_id][shop_id],
                                                 1 / elasticity, max_adjustment)
                    # Следим, чтобы цена не опускалась ниже распродажной
                    if new_price < trading_hall_sales[product_id]['price']:
                        new_price = trading_hall_sales[product_id]['price']
                else:
                    # Цена по умолчанию для новых продуктов
                    new_price = sales_price_factor * trading_hall_sales[product_id]['price']
                offers[trade['ids']] = round(new_price, 2)
            self.set_shop_sale_prices(shop_id, offers)
            
            # Move surpluses back to warehouse
            #Вывозим излишки товара обратно на склад
            for product_id, trade in trading_halls[shop_id].items():
                if product_id not in products:
                    continue
                market_size = markets[product_id][shop['city_id']]
                # оставляем двухдневный запас или максимальную долю рынка
                need = min(2 * target_sales[product_id][shop_id], max_market_share * market_size)
                # лишнее вывозим
                if trade['current_stock'] > need:
                    self.product_move_to_warehouse(
                        shop_id, product_id, products[product_id]['supplier_id'], 
                        trade['current_stock'] - need)
                    
    
if __name__ == '__main__':
    v = MyVirta('olga')
    #v.set_shops_default_prices()
    #v.propagate_contracts()
    #v.manage_shops()
    #v.set_shops_advertisement()
    #v.set_shops_innovations()
    #v.distribute_shop_employees()
    #v.read_messages()
    #v.manage_research()
    #trading_hall, supply_products, supply_contracts, offers, orders, to_order = v.manage_shop(7355541)