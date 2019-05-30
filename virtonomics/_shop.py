import math
from .types import Dict


def trading_hall(self, shop_id, cache=False):
    result = {}
    if cache:
        # Try to extract data from db
        query_result = self.db.execute('SELECT * FROM retail WHERE unit_id=%d AND date="%s"'
                                 % (shop_id, self.today)).fetchall()
        result = {r['product_id']: r for r in query_result}
    if not result:
        url = self.domain_ext + 'unit/view/%s/trading_hall' % shop_id
        page = self.session.tree(url)
        row_xp = '//input[@type="text"]/ancestor::tr'
        rows = page.xpath(row_xp)
        xps = {
            'ids': './td[2]/input/@name',
            'product_id': './td[3]/a/@href',  # trademark?
            'sold': './td[4]/a/text()',
            'purchase': './td[5]/text()',
            'stock': './td[6]/text()',
            'quality': './td[7]/text()',
            'brand': './td[8]/text()',
            'cost': './td[9]/text()',
            'price': './td[10]/input/@value',
            'market_share': './td[11]/text()',
            'avg_price': './td[12]/text()',
            'avg_quality': './td[13]/text()',
            'avg_brand': './td[14]/text()'
            }
        result = {}
        for row in rows:
            res = {name: str(row.xpath(xp)[0]) for name, xp in xps.items()}
            res['ids'] = '{' + res['ids'].split('}')[0].split('{')[-1] + '}'
            res['product_id'] = int(res['product_id'].split('product_id=')[-1].split('&')[0])
            res['sold'] = int(res['sold'].replace(' ', ''))
            res['purchase'] = int(res['purchase'].replace(' ', '').replace('[', '').replace(']', ''))
            res['stock'] = int(res['stock'].replace(' ', ''))
            res['cost'] = res['cost'].replace(' ', '').replace('$', '')
            for name in ('quality', 'brand', 'cost'):
                try:
                    res[name] = float(res[name])
                except ValueError:
                    res[name] = None
            res['price'] = float(res['price'])
            res['market_share'] = float(res['market_share'].replace(' ', '').replace('%', '')) / 100
            res['avg_price'] = float(res['avg_price'].replace(' ', '').replace('$', ''))
            res['avg_quality'] = float(res['avg_quality'])
            res['avg_brand'] = float(res['avg_brand'])
            res['unit_id'] = shop_id
            res['date'] = self.today
            
            result[res['product_id']] = res
            
            if cache:
                query = 'INSERT OR IGNORE INTO retail ({0}) VALUES ({1})'.format(
                        ', '.join(res.keys()), ', '.join('?'*len(res)))
                self.db.execute(query, list(res.values()))
        self.conn.commit()
        
    return Dict(result)


def set_shop_sale_prices(self, shop_id, offers):
    """Set prices at a shop trading hall.
    
    Arguments:
        shop_id (int): Shop id.
        offers (dict): {<offer_ids>: <price>}. Offer ids look like 
            '{58728937,58982206}'.
    
    Returns:
        POST request responce.
    """
    
    url = self.domain_ext + 'unit/view/%s/trading_hall' % shop_id
    data = {'action': 'setprice'}
    for offer_ids, price in offers.items():
        data['productData[price][%s]'%offer_ids] = price
    return self.session.post(url, data=data)


def set_shop_sales_prices(self, shop_id):
    url = self.domain_ext + 'unit/view/%s' % shop_id
    data = {'auto_Price': 'Распродажные цены'}
    return self.session.post(url, data=data)


def distribute_shop_employees(self, units, total_number=None, competence=None, reserve=0):
    base = 10
    load = 1.2
    if not total_number:
        if not competence:
            competence = self.knowledge['trade']
        total_number = load * base * competence * (competence + 3)
    total_number -= reserve
    units = {unit_id: self.unit_summary(unit_id, refresh=True) for unit_id in units}
    employee_required = {unit_id: unit['employee_required']
                         for unit_id, unit in units.items()
                         if not unit.get('on_holiday', True)}
    total_required = sum(employee_required.values())
    if not total_required:
        return
    factor = total_number / total_required
    for unit_id, required_number in employee_required.items():
        employee_number = int(factor * required_number)
        if employee_number > 0:
            employee_level = 1 + math.log(
                base * competence**2 * min(1.2, 1/load)**2 / employee_number, 1.4)
        else:
            employee_level = 0
        employee_level = int(100 * employee_level) / 100
        print(unit_id, employee_number, employee_level)
        self.set_employees(unit_id, quantity=employee_number, salary_max=50000,
                           target_level=employee_level, trigger=1)


def product_move_to_warehouse(self, from_unit_id, product_id, to_unit_id, quantity=0):
    """Вывоз продукции на склад"""
    
    url = self.domain_ext + 'unit/view/%s/product_move_to_warehouse/%s/0' % (
              from_unit_id, product_id)
    data = {
        'qty': quantity,
        'unit': to_unit_id,
        'doit': 1
        }
    return self.session.post(url, data=data)


def product_terminate(self, unit_id, product_ids):
    """Ликвидировать остатки товара"""
    
    url = self.domain_ext + 'unit/view/%s/trading_hall' % unit_id
    data = {'productData[selected][%s]'%idx: 1 for idx in product_ids}
    data['action'] = 'terminate'
    return self.session.post(url, data=data)