from .types import Dict
from .jsondecoder import Decoder
from ._date import str_to_date

def __getattr__(self, attrname):
    if attrname == 'session':
        return self.open_session()
        
    elif attrname == 'db' or attrname == 'conn':
        self.open_database()
        return getattr(self, attrname)
    
    elif attrname == 'server_date':
        return self.get_server_date()
    
    elif attrname == 'days_to_refresh':
        return self.get_days_to_refresh()
    
    elif attrname == 'oligarch_competition_days_left':
        return self.get_oligarch_competition_days_left()
        
    elif attrname in ['token', 'cities', 'regions', 'countries', 'product_categories', 
                      'products', 'goods', 'industries', 'unittypes', 'company', 
                      'company_finance']:
        data = {}
        if '{company_id}' in self.api[attrname]:
            data['company_id'] = self.company['id']
        url = self.api[attrname].format(**data)
        setattr(self, attrname, self.session.get(url).json(cls=Decoder))
        if attrname in ['cities', 'regions', 'countries', 'products', 'unittypes', 'goods']:
            setattr(self, attrname, Dict(getattr(self, attrname)))
        return getattr(self, attrname)
    
    elif attrname in ['units', 'indicators']:
        url = self.api['units'].format(company_id=self.company['id'])
        result = self.session.get(url).json(cls=Decoder)
        self.units = Dict(result.get('data', {}))
        self.indicators = result.get('indicators', {})
        return getattr(self, attrname)
    
    elif attrname == 'investigated_technologies':
        self.investigated_technologies = {}
        for unittype_id in self.unittypes(need_technology=True):
            levels = self.technologies(unittype_id)(status=(1,2))
            self.investigated_technologies[unittype_id] = [t['level'] for t in levels]
        return self.investigated_technologies
    
    elif attrname == 'elections':
        url = self.domain_ext + 'politics/news'
        page = self.session.tree(url)
        xp = '//td[contains(.," г.")]/../td/a[contains(@href,"politics/elections")]/../..'
        rows = page.xpath(xp)
        self.elections = Dict()
        for row in rows:
            res = {}
            election_id = int(row.xpath('./td[2]/a/@href')[0].split('/')[-1])
            res['election_id'] = election_id
            res['location_name'] = str(row.xpath('./td[2]/a/text()')[0])
            election_date = str_to_date(row.xpath('./td[3]/text()')[0])
            res['days_to_election'] = (election_date - self.today).days - 1
            self.elections[election_id] = res
        return self.elections
    
    elif attrname in ['qualification', 'knowledge']:
        url = self.domain_ext + 'user/view/%s' % self.company['president_user_id']
        page = self.session.tree(url)
        xp = '//tr/td[1]/img[contains(@src, "/qualification/")]/../..'
        rows = page.xpath(xp)
        res = {}
        for row in rows:
            name = row.xpath('./td[1]/img/@src')[0].split('/')[-1].split('.')[0]
            qual = int(row.xpath('./td[last()]/b/text()')[0])
            res[name] = qual
        setattr(self, attrname, res)
        return getattr(self, attrname)
    
    elif attrname == 'knowledge_areas':
        url = self.api['knowledge']
        result = self.session.get(url).json(cls=Decoder)
        self.knowledge_areas = Dict(result)
        return self.knowledge_areas
        
    raise AttributeError(attrname)