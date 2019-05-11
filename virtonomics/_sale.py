from .jsondecoder import Decoder
from .types import List, Dict


def sale_contracts(self, unit_id, product_id=None):
    """List of sale contracts for a given unit
    
    Arguments:
        unit_id (int): Unit id.
        product_id (int): Defaults to None.

    Returns:
        List: List of sale contracts.
    """
    
    product_filter = '&product_id=%s'%product_id if product_id else ''
    data = dict(unit_id=unit_id, product_filter=product_filter)
    url = self.api['sale_contracts'].format(**data)
    return List(self.session.get(url).json(cls=Decoder).get('data', []))


def sale_offers(self, unit_id):
    url = self.domain_ext + 'unit/view/%s/sale' % unit_id
    page = self.session.tree(url)
    row_xp = '//input[contains(@name,"[price]")]/ancestor::tr'
    rows = page.xpath(row_xp)
    if not rows:
        return {}
    
    column_names = [None]
    for th in rows[0].xpath('./../tr/th'):
        th = th.xpath('./text()')
        column_names.append(str(th[0]) if th else None)
    stock_column = column_names.index('На складе')
    
    subtable_xp = './td[%d]/table//td[contains(.,"%s")]/../td[2]/text()'
    xps = {
        'product_name': './td/a[contains(@href,"globalreport/marketing")]/text()',
        'stock': subtable_xp % (stock_column, 'Количество'),
        'quality': subtable_xp % (stock_column, 'Качество'),
        'cost': subtable_xp % (stock_column, 'Себестоимость'),
        'price': './td/input[contains(@name,"[price]")]/@value',
        'max_qty': './td//input[contains(@name,"[max_qty]")]/@value',
        'constraint': './td/select[contains(@name,"[constraint]")]/option[@selected]/@value'
        }
    if 'Выпуск' in column_names:
        produce_column = column_names.index('Выпуск')
        xps['production'] = subtable_xp % (produce_column, 'Количество')
    
    result = {}
    for row in rows:
        res = {name: str(row.xpath(xp)[0]) for name, xp in xps.items()}
        
        product_xp = './td/input[@type="checkbox"]/@value'
        product_str = row.xpath(product_xp)
        if product_str:
            product_str = str(product_str[0])
            res['product_id'] = int(product_str.split('/')[0])
            res['trademark'] = int(product_str.split('/')[-1])
        else:
            product_xp = './td/a[contains(@href,"product_id")]/@href'
            product_str = str(row.xpath(product_xp)[0])
            res['product_id'] = int(product_str.split('product_id=')[-1].split('#')[0])
            res['trademark'] = 0
            
        res['stock'] = res['stock'].replace(' ', '')
        try:
            res['stock'] = float(res['stock'])
        except ValueError:
            res['stock'] = 0
            
        res['cost'] = res['cost'].replace(' ', '').replace('$', '')
        for name in ('quality', 'cost'):
            try:
                res[name] = float(res[name])
            except ValueError:
                res[name] = None
                
        res['price'] = float(res['price'])
        try:
            res['max_qty'] = int(res['max_qty'])
        except ValueError:
            res['max_qty'] = 0
            
        res['constraint'] = int(res['constraint'])
        
        company_xp = './td//select[contains(@name,"[company]")]/option/@value'
        res['company'] = [int(c) for c in row.xpath(company_xp)]
        
        if 'production' in res:
            res['production'] = res['production'].replace(' ', '')
            try:
                res['production'] = float(res['production'])
            except ValueError:
                res['production'] = 0
        
        result[res['product_id']] = res
        
    return Dict(result)(trademark=0)


def set_sale_offers(self, unit_id, offers):
    """Modify sale offers for a given unit.
    
    Arguments:
        unit_id (int): Unit id.
        offers (dict): Sale offers to be modified. Offers should be passed
            as a dictionary with keys corresponding to product ids and
            values specifying offers details. Each value in turn should be
            a dictionary and may contain the following keys:
                price (float): sale price (defaults to 1 if not present);
                max_qty (int): maximal amount to be sold to one consumer
                    (no bound if not present or 0);
                constraint (int, 0..5): may take values
                    0 - don't sale,
                    1 - for everyone,
                    2 - for selected companies only (to be listed),
                    3 - for own company only,
                    5 - for corporation members;
                    Defaults to 3 if not present.
                company (int or list): list of companies, if constraint=2.
    
    Returns:
        POST request responce.
    
    Example:
        from virta import Virta
        v = Virta('olga')
        unit_id = 6079565
        offers = {
            303308: {'price': 331.93, 
                     'constraint': 2,
                     'company': [2138526, 3894443]},
            423160: {'price': 1134.73,
                     'max_qty': 100000,
                     'constraint': 1}
        }
        v.set_sale_offers(unit_id, offers)
    """
    
    url = self.domain_ext + 'unit/view/%s/sale' % unit_id
    data = {}
    for product_id, offer in offers.items():
        name = 'storageData[%s/0][%%s]' % product_id
        data[name%'price'] = offer.get('price', 1)
        data[name%'max_qty'] = offer.get('max_qty', 0)
        data[name%'constraint'] = offer.get('constraint', 3)
        data[name%'company'+'[]'] = offer.get('company', [])
    return self.session.post(url, data=data)


def destroy_sale_contracts(self, unit_id, offer_id, consumers):
    """Destroy sale contract for given consumers.
    
    Arguments:
        unit_id (int): Unit id.
        offer_id (int): Offer id.
        consumers (int or list): Consumers ids. Every contract is uniquely 
        defined by consumer_id that can be found in the list of sale 
        contracts for a given unit.
    
    Returns:
        POST request responce.
    """
    
    url = self.domain_ext + 'unit/view/%s/sale' % unit_id
    data = {
        'consumerContractData[selected][%s][]'%offer_id: consumers,
        'destroy': 1
        }
    return self.session.post(url, data=data)


def reorder_sale_contracts(self, unit_id, products):
    """Reorder sale contracts for a given unit.
    
    Arguments:
        unit_id (int): Unit id.
        products (dict): Dictionary that to every product id assigns an 
            ordered list of consumers ids (can be found in the unit's 
            sale contracts list).
    
    Returns:
        POST request responce.
    
    Example:
        # To move up own orders
        products = {}
        for contract in sorted(
                v.sale_contracts(unit_id),
                key=lambda c: c['consumer_company_id']!=v.company['id']
                ):
            p = contract['product_id']
            products[p] = products.get(p, []) + [contract['consumer_id']]
        v.reorder_sale_contracts(unit_id, products)
    """
    
    url = self.domain_ext + 'unit/view/%s/sale' % unit_id
    data = {'positionData[%s/0][]' % product_id: consumers
            for product_id, consumers in products.items()}
    data['changePosition'] = 1
    return self.session.post(url, data=data)