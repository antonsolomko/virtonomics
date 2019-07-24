from .jsondecoder import Decoder
from .types import Dict


def supply_contracts(self, unit_id, product_id=None):
    """List of supply contracts for a given unit.
    
    Arguments:
        unit_id (int): Unit id.
        product_id (int): Defaults to None.

    Returns:
        Dict: List of supply contracts.
    """
    
    product_filter = '&product_id=%s'%product_id if product_id else ''
    data = dict(unit_id=unit_id, product_filter=product_filter)
    url = self.api['supply_contracts'].format(**data)
    return Dict(self.session.get(url).json(cls=Decoder))


def supply_products(self, unit_id):
    url = self.domain_ext + 'unit/view/%s/supply' % unit_id
    page = self.session.tree(url)
    row_xp = '//img[@title="Выбрать поставщика"]/ancestor::tr[last()]'
    rows = page.xpath(row_xp)
    base_xp = './/table//td[contains(.,"%s")]/../td[2]/text()'
    xps = {
        'product_id': './/@href[contains(.,"supply/create")]',
        'stock': base_xp % 'Количество',
        'quality': base_xp % 'Качество',
        'cost': base_xp % 'Себестоимость',
        # Not present in some unit types
        'needed': base_xp % 'Требуется',
        'brand': base_xp % 'Бренд',
        'sold': base_xp % 'Продано',
        'per_client': base_xp % 'Расх. на клиента',
        }
    result = {}
    for row in rows:
        res = {}
        for name, xp in xps.items():
            try:
                res[name] = str(row.xpath(xp)[0])
            except IndexError:
                pass
        
        name_xp = './/img[contains(@src,"img/products")]/@alt'
        try:
            res['product_name'] = str(row.xpath(name_xp)[0])
        except:
            name_xp = '//td/@title'
            res['product_name'] = str(row.xpath(name_xp)[0])
            
        res['product_id'] = int(res['product_id'].split('/')[-1])
        res['stock'] = int(res['stock'].replace(' ',''))
        
        try:
            res['quality'] = float(res['quality'])
        except ValueError:
            res['quality'] = None
            
        try:
            res['cost'] = float(res['cost'].replace(' ','').replace('$',''))
        except ValueError:
            res['cost'] = None
            
        if 'needed' in res:
            res['needed'] = int(res['needed'].replace(' ',''))
            
        if 'brand' in res:
            try:
                res['brand'] = float(res['brand'])
            except ValueError:
                res['brand'] = None
                
        if 'sold' in res:
            try:
                res['sold'] = int(res['sold'].replace(' ',''))
            except ValueError:
                res['sold'] = 0
        
        if 'per_client' in res:
            res['per_client'] = int(res['per_client'].replace(' ',''))
        
        result[res['product_id']] = res
        
    return Dict(result)


def create_supply_contract(self, unit_id, offer_id, amount=1, max_price=0, 
                           max_increase=2, min_quality=0, instant=0):
    """Create new supply contract.
    
    Arguments:
        unit_id (int): Ordering unit id.
        offer_id (int): Every market offer has its own unique id,
            different from seller id and product id.
    
    Keyword arguments:
        amount (int): Amount to be ordered. Defaults to 1.
        max_price (float): If supplier price reaches max_price, the 
            contract is automatically broken. If 0, max_increase is used 
            instead to control price changes. Defaults to 0.
        max_increase (int, 0..5): If supplier price growth by mote than
            a given percentage, the contract is automatically broken.
            Can take values:
                0 (never break the contract),
                1 (break the contract if price growth by 5% or more),
                2 (break the contract if price growth by 10% or more), 
                3 (break the contract if price growth by 20% or more), 
                4 (break the contract if price growth by 50% or more), 
                5 (break the contract if price growth by 100% or more).
            Defaults to 2 (10%).
        min_quality (float): If product quality drops below min_quality,
            no purchase is made, although the contract remains valid.
            Defaults to 0 (no constraint).
        instant (bool): One-time purchase flag. If True, the contract
            will be automatically broken next day. Defaults to False.
    
    Returns:
        POST request responce.
    """
    
    url = self.domain + '/%s/ajax/unit/supply/create' % self.server
    data = {
        'offer': offer_id,
        'unit': unit_id,
        'amount': amount,
        'priceConstraint': max_price,
        'priceMarkUp': max_increase,
        'qualityMin': min_quality,
        'constraintPriceType': 'Abs' if max_price else 'Rel',
        'instant': 'true' if instant else ''
        }
    return self.session.post(url, data=data)


def destroy_supply_contract(self, unit_id, offer_ids):
    """Destroy supply contract.
    
    Arguments:
        unit_id (int): Unit id.
        offer_ids (int or list): Either single offer id, or a list of 
            offer ids.
    
    Returns:
        POST request responce.
    """
    
    url = self.domain_ext + 'unit/view/%s/supply' % unit_id
    data = {
        'contractDestroy': 1,
        'supplyContractData[selected][]': offer_ids
        }
    return self.session.post(url, data=data)


def set_supply_contracts(self, unit_id, orders):
    """Modify existing supply contracts for a given unit.
    Orders are indexed by offer id that can be found in the list of supply
    contracts for a given unit.
    
    Arguments:
        unit_id (int): Unit id.
        orders (dict): Orders details should be passed as a dictionary with
            keys corresponding to offer ids, and values specifying orders
            details. Each value should be in turn a dictionary and may 
            contain the following keys:
                'quantity' (int): Amount to order (defaults to 0 if not 
                    present).
                'max_price' (float): Price constraint (default 0 for 
                    no constraint, if not present). If 0, relative
                    constraint (max_increase) is used instead.
                'max_increase' (int, 0..5): Relative price change 
                    constraint, may take values: 0 (no constraint), 
                    1 (5%), 2 (10%), 3 (20%), 4 (50%), 5 (100%).
                    Defaults to 2 if not present.
                'min_quality': Minimum qualiy (default 0 for no constraint)
    
    Returns:
        POST request responce.
    
    Example:
        from virta import Virta
        v = Virta('olga')
        unit_id = 7358676
        orders = {
            7585670: {'quantity': 1000,
                      'max_price': 150},
            8352860: {'quantity': 10000,
                      'max_increase': 1,
                      'min_quality': 20}
        }
        v.set_supply_contracts(unit_id, orders)
    """
    
    url = self.domain_ext + 'unit/view/%s/supply' % unit_id
    data = {
        'applyChanges': 1, 
        'supplyContractData[selected][]': list(orders.keys())
        }
    for offer_id, order in orders.items():
        name = 'supplyContractData[%%s][%s]' % offer_id
        data[name%'party_quantity'] = order.get('quantity', 0)
        data[name%'price_constraint_max'] = order.get('max_price', 0)
        data[name%'price_mark_up'] = order.get('max_increase', 2)
        if data[name%'price_constraint_max']:
            data[name%'constraintPriceType'] = 'Abs'
        else:
            data[name%'constraintPriceType'] = 'Rel'
        data[name%'quality_constraint_min'] = order.get('min_quality', 0)
    return self.session.post(url, data=data)


def suspend_supply_contracts(self, unit_id):
    """Set quantity to 0 for all supply contracts for a given unit"""
    
    supply_contracts = self.supply_contracts(unit_id)
    orders = self.supply_contracts_to_orders(supply_contracts, quantity=0)
    return self.set_supply_contracts(unit_id, orders)


@staticmethod
def supply_contracts_to_orders(contracts, **kwargs):
    keys = {'quantity': 'dispatch_quantity',
            'max_price': 'price_constraint_max',
            'max_increase': 'price_constraint',
            'min_quality': 'quality_constraint_min'
            }
    return {contract_id: {key: kwargs.get(key, contract[keys[key]]) for key in keys}
            for contract_id, contract in contracts.items()}