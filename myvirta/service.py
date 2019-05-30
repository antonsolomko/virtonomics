def manage_restaurants(self, days=3):
    def calculate_new_price(history, max_customers, min_price=0):
        if not history or not max_customers:
            return None
        current_price = history[0]['price']
        current_sold = history[0]['sold']
        if None in [current_price, current_sold]:
            return None
        almost_max_visitors = 0.96 * max_customers
        if current_sold < almost_max_visitors:
            equivalent_price = current_price * current_sold / max_customers
            new_price = (current_price + equivalent_price) / 2
        else:
            consecutive_days_with_max = 0
            for week in history:
                if week['sold'] >= almost_max_visitors:
                    consecutive_days_with_max += 1
                else:
                    break
            new_price = current_price * (1 + consecutive_days_with_max / 100)
        if new_price < 0.95 * current_price:
            new_price = 0.95 * current_price
        if new_price < min_price:
            new_price = min_price
        return round(new_price)
    
    min_price = {
        'restaurant': 7200,
        'educational': 100000,
        'repair': 1000
        }
    
    for unit_id in self.units(unit_class_kind=['restaurant', 'educational', 'repair', 'service_light']):
        print(unit_id)
        unit = self.unit_summary(unit_id)
        if unit['name'][:1] == '*':
            continue
        max_customers = 100 * unit['employee_count'] if unit['unit_class_kind'] == 'repair' else unit['customers']
        new_price = calculate_new_price(self.service_history(unit_id), max_customers,
                                        min_price.get(unit['unit_class_kind'], 0))
        if new_price:
            self.set_service_price(unit_id, new_price)
        
        if unit['unit_class_kind'] in ['restaurant', 'educational', 'repair']:
            contracts = self.supply_contracts(unit_id)
            orders = self.supply_contracts_to_orders(contracts)
            for product_id, product in self.supply_products(unit_id).items():
                per_day = product['per_client'] * max_customers
                fund = max(0, product['stock'] - per_day)
                to_order = max(0, days * per_day - fund)
                if to_order > 1.05 * per_day:
                    to_order = round(1.05 * per_day)
                for contract_id, contract in contracts(product_id=product_id).items():
                    available = contract['free_for_buy']
                    if contract['offer_max_qty'] and contract['offer_max_qty'] < available:
                        available = contract['offer_max_qty']
                    orders[contract_id]['quantity'] = min(to_order, available)
                    to_order -= orders[contract_id]['quantity']
            self.set_supply_contracts(unit_id, orders)