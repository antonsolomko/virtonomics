def sypply_own_shop(self, shop_id, units=None):
    if not units:
        units = [7405776, 6703013, 7355677, 7429787, 7495664, 7515896, 6991290]
    offers = set(c['offer_id'] for u in units for c in self.sale_contracts(u))
    print(offers)
    for offer_id in offers:
        self.create_supply_contract(shop_id, offer_id, max_increase=0)


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