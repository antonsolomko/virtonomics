import math


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
    """Отсортировать контракты по возрастанию заказа"""
    units = self.units(unit_class_kind='warehouse')
    for unit_id in units:
        sale_contracts = self.sale_contracts(unit_id)
        consumers = set(c['consumer_company_id'] for c in sale_contracts)
        if consumers and consumers != {self.company['id']}:
            self.sort_sale_contracts(unit_id)


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
                    #or c['consumer_unit_class_symbol'] == 'shop'
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
