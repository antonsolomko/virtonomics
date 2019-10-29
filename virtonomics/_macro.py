from .jsondecoder import Decoder
from .types import List, Dict


def produce(self, unittype_id):
    """Production information for a given unit type."""
    
    if not hasattr(self, '__produce'):
        self.__produce = {}
    if unittype_id not in self.__produce:
        url = self.api['produce'].format(unittype_id=unittype_id)
        self.__produce[unittype_id] = self.session.get(url).json(cls=Decoder)
    return self.__produce[unittype_id]


def city_rent(self, city_id):
    """Стоимость аренды в городе
    
    Returns:
        List.
    """
    
    if not hasattr(self, '__city_rent'):
        self.__city_rent = {}
    if city_id not in self.__city_rent:
        url = self.api['city_rent'].format(city_id=city_id)
        self.__city_rent[city_id] = List(self.session.get(url).json(cls=Decoder))
    return self.__city_rent[city_id]


def offers(self, product_id):
    """Open market offers"""
    
    url = self.api['offers'].format(product_id=product_id)
    result = self.session.get(url).json(cls=Decoder)
    return Dict(result.get('data',{}))


def retail_metrics(self, product_id, geo=None, **geo_filters):
    """Retail sales summary for a given product at a given location.
    
    Arguments:
        product_id (int): Retail product id (this.goods attribute contains
            the full list of retail products).
        geo (str or tuple): Location. Can be either a string of the form 
            'country_id[/region_id[/city_id]]', or a tuple 
            (country_id[, region_id[, city_id]]). If not passed or False,
            geo_filters are used instead to determine location.
            Defaults to None.
        geo_filters: Keyword arguments specifying location. 
        
    Returns:
        dict: Various retail metrics.
        None if geo is not passed and city (or region or country) can not 
            be uniquely identified based on geo_filters.
    
    Example:
        # Equivalent forms
        v.retail_metrics(1510, geo='424181/424184/424201')
        v.retail_metrics(1510, geo=(424181,424184,424201))
        v.retail_metrics(1510, city_id=424201)  # slower than the first two
    """
    
    if geo:
        if not isinstance(geo, str):
            geo = '/'.join(map(str, geo))
    else:
        city = self.cities.select(**geo_filters)
        if city:
            geo = '%s/%s/%s' % (city['country_id'], city['region_id'], city['id'])
        else:
            region = self.regions.select(**geo_filters)
            if region:
                geo = '%s/%s' % (region['country_id'], region['id'])
            else:
                country = self.countries.select(**geo_filters)
                if country:
                    geo = str(country['id'])
                else:
                    return None
    url = self.api['retail_metrics'].format(product_id=product_id, geo=geo)
    return self.session.get(url).json(cls=Decoder)


def retail_history(self, product_id, geo=None, **geo_filters):
    """Retail sales history for a given product at a given location.
    
    Arguments:
        product_id (int): Retail product id (self.goods attribute contains
            the full list of retail products).
        geo (str or tuple): Location. Can be either a string of the form 
            'country_id[/region_id[/city_id]]', or a tuple 
            (country_id[, region_id[, city_id]]). If not passed or False,
            geo_filters are used instead to determine location.
            Defaults to None.
        geo_filters: Keyword arguments specifying location. 
        
    Returns:
        dict: Various retail metrics.
        None if geo is not passed and city (or region or country) can not 
            be uniquely identified based on geo_filters.
    
    Example:
        # Equivalent forms
        v.retail_metrics(1510, geo='424181/424184/424201')
        v.retail_metrics(1510, geo=(424181,424184,424201))
        v.retail_metrics(1510, city_id=424201)  # slower than the first two
    """
    
    if geo:
        if not isinstance(geo, str):
            geo = '/'.join(map(str, geo))
    else:
        city = self.cities.select(**geo_filters)
        if city:
            geo = '%s/%s/%s' % (city['country_id'], city['region_id'], city['id'])
        else:
            region = self.regions.select(**geo_filters)
            if region:
                geo = '%s/%s' % (region['country_id'], region['id'])
            else:
                country = self.countries.select(**geo_filters)
                if country:
                    geo = str(country['id'])
                else:
                    return None
    url = self.api['retail_history'].format(product_id=product_id, geo=geo)
    return self.session.get(url).json(cls=Decoder)