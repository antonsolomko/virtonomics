from scipy.optimize import linprog


def supply_equipment(self, unit_id, offer_id, amount, operation):
    """Buy or repair equipment for a given unit.
    
    Arguments:
        unit_id (int): Unit id.
        offer_id (int): Offer id.
        amount (int): Amount of equipment to buy or replace.
        operation (str): 'buy' or 'repair'.
    
    Returns:
        POST request responce.
    """
    
    url = self.domain + '/%s/ajax/unit/supply/equipment' % self.server
    data = {
        'operation': operation,
        'unit': unit_id,
        'offer': offer_id,
        'supplier': offer_id,
        'amount': amount
        }
    result = self.session.post(url, data=data)
    self.refresh(unit_id)
    return result


def buy_equipment(self, unit_id, offer_id, amount):
    """Buy equipment for a given unit.
    
    Arguments:
        unit_id (int): Unit id.
        offer_id (int): Offer id.
        amount (int): Amount of equipment to buy.
    
    Returns:
        POST request responce.
    """
    
    return self.supply_equipment(unit_id, offer_id, amount, 'buy')


def repair_equipment(self, unit_id, offer_id, amount):
    """Repair equipment for a given unit.
    
    Arguments:
        unit_id (int): Unit id.
        offer_id (int): Offer id.
        amount (int): Amount of equipment to replace.
    
    Returns:
        POST request responce.
    """
    
    return self.supply_equipment(unit_id, offer_id, amount, 'repair')


def destroy_equipment(self, unit_id, amount):
    """Destroy equipment for a given unit.
    
    Arguments:
        unit_id (int): Unit id.
        amount (int): Amount of equipment to destroy.
    
    Returns:
        POST request responce.
    """
    
    url = self.domain + '/%s/ajax/unit/supply/equipment' % self.server
    data = {
        'operation': 'terminate',
        'unit': unit_id,
        'amount': amount
        }
    result = self.session.post(url, data=data)
    self.refresh(unit_id)
    return result


def supply_equipment_all(self, offer_id, units, operation):
    """Buy or repair equipment for all given units.
    
    Note:
        If there is no enough equipment to fill all the units passed,
        no equipment will be bought or repaired.
    
    Arguments:
        offer_id (int): Offer id.
        units (list): List of units ids.
        operation (str): 'buy' or 'repair'.
    
    Returns:
        POST request responce.
    
    Todo:
        Add 'destroy' operation.
    """
    
    url = self.domain_ext + 'management_units/equipment/%s' % operation
    data = {'units[%s]'%unit_id: 1 for unit_id in units}
    data['supplyData[offer]'] = offer_id
    data['submitRepair'] = 1
    return self.session.post(url, data=data)


def buy_equipment_all(self, offer_id, units):
    """Buy equipment for all given units.
    
    Note:
        If there is no enough equipment to fill all the units passed,
        no equipment will be bought.
    
    Arguments:
        offer_id (int): Offer id.
        units (list): List of units ids.
    
    Returns:
        POST request responce.
    """
    
    return self.supply_equipment_all(offer_id, units, 'buy')


def repair_equipment_all(self, offer_id, units):
    """Repair equipment for all given units.
    
    Note:
        If there is no enough equipment to fill all the units passed,
        no equipment will be repaired.
    
    Arguments:
        offer_id (int): Offer id.
        units (list): List of units ids.
    
    Returns:
        POST request responce.
    """
    
    return self.supply_equipment_all(offer_id, units, 'repair')


def upgrade_equipment(self, unit_id, offers, target_quality=None, 
                      target_amount=None, *, max_price=None, 
                      target_quality_max=None, exact_amount=False,
                      destroy=True, act=False):
    """UNDER DEVELOPMENT
    
    Upgrade unit equipment to achieve given target quality and amount.
    Finds the cheapest mix of available and installed equipment.
    
    Note:
        Current orders are computed using standard simplex method and then
        rounded. This may lead to some inaccuracy in the result, especially
        for small amonts of equipment. Thus it is recommended to allow some
        margin for target quality to compensate possible inaccuracy.
        
        Beware that currently the game API only provides offers open to 
        everyone, and does not include corporate or private ones.
    
    Todo:
        Implement a proper integer linear programming algorithm to get a
        precise result.
    
    Arguments:
        unit_id (int): Target unit id.
        offers (list): List of offers to choose from. Each value should be 
            a dictionary containing the keys: 'id' (offer id), 'total_cost'
            (or 'price'), 'quality', 'free_for_buy'.
            If 'total_cost' is not present or eluals 0, 'price' is used 
            instead (although the resulting cost may be higher due to the 
            transportation cost and customs duties).
        target_quality (float): Target equipment quality. Defaults to None
            (the quality required by technological level).
        target_amount (int or 'max'): Target equipment amount. If 
            target_amount = 'max', the maximum amount will be installed.
            Defaults to None (remain the amount installed already).
        max_price (float): Maximum average price per equipment piece to be
            ordered. Defaults to None (no constraint).
        target_quality_max (float): Resulting quality upper bound.
            Defaults to None (no restriction).
        exact_amount (bool): If True, the exact equipment amount specified
            in target_amount will be installed. Otherwise, the resulting
            amount may be bigger than target_amount. Defaults to False.
        destroy (bool): Allow destroying equipment already
            installed. Defaults to True.
    
    Returns:
        bool: True if optimal solution satisfying the restrictions found, 
            False otherwise.
    """
    
    unit = self.unit_summary(unit_id, refresh=True)
    equipment_count = unit['equipment_count']
    equipment_max = unit['equipment_max']
    equipment_quality = unit['equipment_quality']
    
    destroy_cost = 1  # needs to be positive to prevent unnecessary destroy
    
    if isinstance(offers, dict):
        offers_list = []
        for offer_id, offer in offers.items():
            offer['id'] = offer_id
            if offer['free_for_buy'] > equipment_max:
                offer['free_for_buy'] = equipment_max
            offers_list.append(offer)
        offers = offers_list
        
    print(len(offers), 'offers')
    
    if target_quality is None:
        target_quality = unit['equipment_quality_required']
    
    if target_amount is None:
        target_amount = equipment_count
    elif target_amount == 'max':
        target_amount = equipment_max
    
    bounds = [(0, equipment_count if destroy else 0)]
    bounds += [(0, o['free_for_buy']) for o in offers]
    
    # Target functional to minimize
    c = [destroy_cost] 
    c += [o['total_cost'] if 'total_cost' in o and o['total_cost'] else o['price']
          for o in offers]
    
    A_ub = [[equipment_quality - target_quality] 
            + [target_quality - o['quality'] for o in offers]]
    b_ub = [(equipment_quality - target_quality) * equipment_count]
        
    if target_quality_max:
        A_ub += [[target_quality_max - equipment_quality]
                 + [o['quality'] - target_quality_max for o in offers]]
        b_ub += [(target_quality_max - equipment_quality) * equipment_count]
    
    if exact_amount:
        A_eq = [[-1] + [1]*len(offers)]
        b_eq = [target_amount - equipment_count]
    else:
        A_eq, b_eq = None, None
        A_ub += [[1] + [-1]*len(offers)]
        b_ub += [equipment_count - target_amount]
        
    A_ub += [[-1] + [1]*len(offers)]
    b_ub += [equipment_max - equipment_count]
    
    if max_price:
        A_ub += [[0] + [o['price'] - max_price for o in offers]]
        b_ub += [0]
    
    simplex = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds,
                      options={'tol':10**-9})
    
    if not simplex.success:
        return simplex
    
    to_order = sum(int(a + 0.5) for a in simplex.x[1:] if a > 0)
    
    amount_to_destroy = int(simplex.x[0] + 0.5)
    if equipment_count - amount_to_destroy + to_order < target_amount:
        amount_to_destroy = equipment_count + to_order - target_amount
    if act:
        self.destroy_equipment(unit_id, amount_to_destroy)
    print('Destroy', amount_to_destroy)
    print('To order', to_order)
    total = equipment_count - amount_to_destroy
    quality = equipment_quality * total
    cost = 0
    for offer, amount in zip(offers, simplex.x[1:]):
        if amount > 0:
            amount = int(amount + 0.5)
            if act:
                self.buy_equipment(unit_id, offer['id'], amount)
            total += amount
            quality += offer['quality'] * amount
            cost += offer['price'] * amount
            print('', amount, 'q:%.2f' % offer['quality'], 'p:%.2f' % offer['price'])
    print('Total', total)
    print('Quality %.2f' % (quality / max(1,total)))
    print('Price %.2f' % (cost / max(1,to_order)))
    print('Cost %.0f' % cost)
    
    return True