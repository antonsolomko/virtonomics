from .types import List
from .jsondecoder import Decoder


def technologies(self, unittype_id):
    """Technology market overview for a given unit type.
    
    Arguments:
        unittype_id (int): Unit type id.

    Returns:
        List: Known or investigated technologies summary by levels.
        Technology status codes:
            0 - not invented, known
            1 - invented (own invention)
            2 - invented (own invention) and offered for sale
            3 - not invented, not known
            4 - bought, not invented
            5 - current research
    
    Note:
        Result is a List object and thus can be filtered by arbitrary
        attributes.
        
    Example:
        # List of the levels available to the company for free
        # (algeady investigated or bought)
        v.technologies(unittype_id)(status=(1,2,4))
        
        # Record for a particular level
        v.technologies(2071).select(level=15)
    """
    
    if unittype_id not in self.__technologies:
        url = self.api['technologies']
        data = {'company_id': self.company['id'], 'id': unittype_id}
        result = self.session.post(url, data=data).json(cls=Decoder)
        self.__technologies[unittype_id] = List(result)
    return self.__technologies[unittype_id]


def researchable_technologies(self, unittype_id):
    """List of technology levels that can be studied.
    
    Arguments:
        unittype_id (int): Unit type id.

    Returns:
        list: Levels available for investigation.
    """
    
    levels = self.technologies(unittype_id)
    max_level = max((t['level'] for t in levels(status=(1,2,4))), default=1)
    result = [t['level'] for t in levels
              if t['level'] <= max_level and t['status'] not in (1,2)]
    result.append(max_level + 1)
    return result


def set_technology_offer(self, unittype_id: int, level: int, price: float):
    """Выставить технологию на продажу"""
    
    url = (self.domain_ext 
           + 'management_action/%s/investigations/technology_offer_create/%s/%s'
           % (self.company['id'], level, unittype_id))
    data = {'price': price}
    return self.session.post(url, data=data)


def destroy_technology_offers(self, offers: list):
    """Снять технологии с продажи
    
    Arguments:
        offers (list): List of offers to be destroyed. Each element can be 
            either offer id, or a pair (unittype_id, level). In the latter case
            'technology_offers' method is used to substitute actual offers ids.

    Returns:
        POST request responce.
    """
    
    all_offers = self.technology_offers()
    offers = [all_offers[k] if k in all_offers else k 
              for k in offers if k in all_offers or k in all_offers.values()]
    url = self.domain_ext + 'management_action/%s/investigations/technology_offers_destroy' % self.company['id']
    data = {'techs[]': offers}
    return self.session.post(url, data=data)


def technology_offers(self, refresh: bool=False) -> dict:
    """Список выставленных на продажу технологий.
    
    Each technology offer has a unique id. The method is used to map pairs
    (unittype_id, level) to offer ids.
    
    Arguments:
        refresh (bool): If True or the method is called first time, data is 
            read from web page. Otherwise previously extracted data is returned
    
    Returns:
        Dictionary of the form (unittype_id, level) -> offer_id.
    """
    
    if refresh or not hasattr(self, '__technology_offers'):
        url = self.domain_ext + 'management_action/%s/investigations/technologies' % self.company['id']
        page = self.session.tree(url)
        xp = '//input[@type="checkbox" and @name="techs[]"]/..'
        self.__technology_offers = {}
        for cell in page.xpath(xp):
            offer_id = int(cell.xpath('./input/@value')[0])
            href = cell.xpath('./a/@href')[0].split('/')
            unittype_id = int(href[-1])
            level = int(href[-2])
            self.__technology_offers[(unittype_id, level)] = offer_id
    return self.__technology_offers


def technology_sellers_info(self, unittype_id: int, level: int) -> dict:
    """Предложения всех компаний.
    
    Arguments:
        unittype_id (int)
        level (int)
    
    Returns:
        Dictionary company_id -> price
    """
    
    url = (self.domain_ext 
          + 'management_action/%s/investigations/technology_sellers_info/%s/%s' 
          % (self.company['id'], level, unittype_id))
    page = self.session.tree(url)
    xp = '//td/a[contains(@href,"/company/view/")]/../..'
    result = {}
    for row in page.xpath(xp):
        company_id = int(row.xpath('.//a/@href')[0].split('/')[-1])
        price = float(row.xpath('./td[2]/text()')[0].replace(' ', '').replace('$', ''))
        result[company_id] = price
    return result