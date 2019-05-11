import math
from .jsondecoder import Decoder


def set_advertisement(self, unit_id, *, cost=None, ratio=None, 
                      target_fame=None, target_limit_fame=None, 
                      target_customers=None, max_cost=None, 
                      competence=None, innovation=False, platform=1):
    """Launch an advertising campaign for a given unit.
    
    Notes:
        New fame is defined by two factors: current fame and the ratio of 
        the number of contacts to the city population.
        
        In the game interface the fame (известность) is displayed 
        multiplied by 100 compared to the one used here and by game API.
        To secure users from unintentionally pasing high target fames,
        any fame greater than 7.8 passed to the method is divided by 100.
        
        Effectiveness is not currently controlled, and should be controlled
        manually by passing competence or max_cost. Otherwise, the cost may
        be very high and the compaign not 100% effective.
    
    Arguments:
        unit_id (int): Unit id.
        cost (float): Advertising campaign price. This is the most
            straightforward way to launch an advertising campaign.
            If not passed, ratio, target_fame or target_limit_fame are used
            instead to define the compaign cost.
        ratio (float): ratio of the number of contacts to the city 
            population. Can only be between 0 and 1600. The corresponding 
            cost is computed authomatically. If not passed, target_fame or 
            target_limit_fame are used.
        target_fame (float): Target fame to achieve the next day. The
            corresponding compaign cost is computed given the current fame.
            If the target fame cannot be achieved in one day due to 
            effectiveness or ratio restrictions, the cost will be reduced
            to the maximum 100% effective one. If not passed, 
            target_limit_fame is used to determine the cost.
        target_limit_fame (float): Target limit fame to achieve. If the 
            price of an advertising campaign is fixed, the fame converges
            to some value. The cost is computed so that the limit will be 
            eventually equal to target_limit_fame.
        target_customers (int): Target customers number. target_fame will
            be estimated accordingly.
        max_cost (float): Maximum compaign cost bound.
        competence (int): Top manager's competence in marketing. Used to 
            determine max_cost if max_cost is not passed.
        innovation (bool): Партнёрский договор с рекламным агентством flag.
            Defaults to False.
        platform (int, 1..5): Advertising platform:
            1 - TV (the cheapest per contact),
            2 - radio,
            3 - outdoor advertising,
            4 - printed media,
            5 - the Internet.
            Only used if cost is explicitely passed (defaults to 1), 
            otherwise the cheapest options is choosen.
    
    Returns:
        POST request responce.
    """
    
    # exp and log are base e=2.718281828459045...
    max_fame = 7.8  # no higher fame can be ever achieved
    growth_rate = 9 if innovation else 6
    if not cost:
        if not ratio:
            if target_fame:
                if target_fame > max_fame:
                    target_fame /= 100
                cf = self.unit_summary(unit_id)['fame']  # current fame
                ratio = (math.exp(target_fame) - math.exp(cf - cf**2 / 200)) / growth_rate
            elif target_limit_fame:
                if target_limit_fame > max_fame:
                    target_limit_fame /= 100
                f = target_limit_fame
                ratio = (math.exp(f) - math.exp(f - f**2 / 200)) / growth_rate
            elif target_customers:
                unit = self.unit_summary(unit_id)
                if not unit['customers_count']:
                    return
                cf = unit['fame']  # current fame
                target_fame = cf + math.log(target_customers / unit['customers_count'])
                ratio = (math.exp(target_fame) - math.exp(cf - cf**2 / 200)) / growth_rate
            else:
                ratio = 0
            if ratio > 30:
                ratio = 30 + (ratio - 30)**2
        if ratio > 1600:
            ratio = 1600
            
        if ratio <= 0:
            return self.stop_advertisement(unit_id)
        else:
            unit = self.units.select(id=unit_id)
            city = self.cities.select(city_id=unit['city_id'])
            estimator_url = '%s/%s/ajax/unit/virtasement/%s/fame' % (
                                self.domain, self.server, unit_id)
            for platform in range(1,6):
                data = {'type[]': 2265 - platform}
                estimate = self.session.post(estimator_url, data=data).json(cls=Decoder)
                cost = ratio * estimate['contactCost'] * city['population']
                if cost >= estimate['minCost']:
                    break
    if not competence:
        competence = self.knowledge['advert']
    if not max_cost:
        max_cost = 200000 * competence**1.4
    if max_cost and cost > max_cost:
        cost = max_cost
    print(unit_id, target_fame, target_limit_fame, platform, int(cost/10000)/100)
    url = self.domain_ext + 'unit/view/%s/virtasement' % unit_id
    data = {
        'advertData[type][]': 2265 - platform,
        'advertData[totalCost]': cost,
        'accept': 1
        }
    return self.session.post(url, data=data)


def stop_advertisement(self, unit_id):
    """Stop advertising campaign for a given unit."""
    
    url = self.domain_ext + 'unit/view/%s/virtasement' % unit_id
    data = {'cancel': 1}
    return self.session.post(url, data=data)