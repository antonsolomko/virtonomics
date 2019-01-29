"""Virtonomics framework.
@author: Anton Solomko
"""

import os
import time
import datetime
import sqlite3
import requests
from lxml import html
import json
#from selenium import webdriver
#from selenium.webdriver.common.keys import Keys
#from selenium.common.exceptions import NoSuchElementException
import logging
from functools import wraps

    
TODAY = datetime.datetime.today().date()  # real date, no timezone correction


requests.Session.tree = lambda self,url: html.fromstring(self.get(url).content)

logging.basicConfig(filename='%s.log' % __file__, 
                    format='%(asctime)s  %(message)s',  # %(levelname)-8s
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)

def logger(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        msg = func.__name__ + '( '
        args_present = False
        for arg in args:
            arg = repr(arg)
            if 'object at' not in arg:
                msg += arg + ', '
                args_present = True
        for k, v in kwargs.items():
            msg += str(k) + '=' + repr(v)
            args_present = True
        if args_present:
            msg = msg[:-2]
        msg += ' )'
        logging.info(msg)
        return func(*args, **kwargs)
    return wrapper
            

def for_all_methods(decorator):
    def decorate(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)):
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def str_to_date(date_str):
    months = {
        'января': 1,
        'февраля': 2,
        'марта': 3,
        'апреля': 4,
        'мая': 5,
        'июня': 6,
        'июля': 7,
        'августа': 8,
        'сентября': 9,
        'октября': 10,
        'ноября': 11,
        'декабря': 12
        }
    day, month, year, *_ = date_str.split()
    day = int(day)
    month = months[month]
    year = int(year)
    return datetime.date(year, month, day)

def date_to_str(date):
    months = ('', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
              'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря')
    return '%d %s %d' % (date.day, months[date.month], date.year)


class Dict(dict):
    """Extends built-in dict. Allows to filter dictionaries by attributes."""
    
    def __call__(self, **filters):
        for fk, fv in filters.items():
            if not (isinstance(fv, list) or isinstance(fv, tuple)):
                filters[fk] = [fv]
        return {k: v for k, v in self.items()
                if all(v.get(fk) in fv for fk, fv in filters.items())}
    
    def select(self, **filters):
        result = self(**filters)
        if len(result) == 1:
            return next(iter(result.values()))
        else:
            return None


class List(list):
    """Extends built-in list. Allows to filter lists by attributes."""
    
    def __call__(self, **filters):
        for fk, fv in filters.items():
            if not (isinstance(fv, list) or isinstance(fv, tuple)):
                filters[fk] = [fv]
        return [v for v in self if all(v.get(fk) in fv for fk, fv in filters.items())]
    
    def select(self, **filters):
        result = self(**filters)
        if len(result) == 1:
            return result[0]
        else:
            return None


class Decoder(json.JSONDecoder):
    def decode(self, s):
        result = super().decode(s)
        return self._decode(result)

    def _decode(self, o):
        if isinstance(o, str):
            if o == 't':
                return True
            elif o == 'f':
                return False
            else:
                try:
                    return int(o)
                except ValueError:
                    try:
                        return float(o)
                    except ValueError:
                        return o
        elif isinstance(o, dict):
            result = {}
            for k, v in o.items():
                try:
                    k = int(k)
                except ValueError:
                    pass
                result[k] = self._decode(v)
            return result
        elif isinstance(o, list):
            return [self._decode(v) for v in o]
        else:
            return o
            

#@for_all_methods(logger)
class Virta:
    """Virtonomics framework.
    
    Arguments:
        server (str): Server name (e.g. 'olga', 'vera', etc.).
        user (str): Username (login). If not passed, environment variable
            VIRTA_USER is used.
        password (str): Password. If not passed,  environment variable
            VIRTA_PASSWORD is used.
        path (str): Framework directory path. If not passed, set to environment
            variable VIRTA_PATH. If VIRTA_PATH is not defined, current
            directory is used.

    Attributes:
        api (dict): Some API urls provided by the game developers.
        cities (Dict): List of cities.
        company (dict): Basic company information.
        company_finance (dict): Company finance report.
        connection (sqlite3.Connection): Database connection.
        countries (Dict): List of countries.
        days_to_refresh (int): Number of real days (virtual weeks) left until 
            macroeconomical parameters update. Equals 0 on the day before 
            the update.
        db (sqlite3.Cursor): Database cursor to perform SQL quaries.
        db_name (str): Database name.
        domain (str): Defaults to 'https://virtonomica.ru'
        domain_ext (str): '<domain>/<server>/main/'
        driver: Selenium webdriver instance. (not currently supported)
        goods (Dict): List of retail products.
        indicators (dict): Units indicators (warnings).
        industries (dict): List of inductries.
        investigated_technologies (dict): To every unit type id associates the
            list of investigated levels.
        password (str): User password.
        path (str): Framework directory path.
        product_categories (dict): List of product categories.
        products (Dict): List of products.
        regions (Dict): List of regions.
        server (str): Server name.
        server_date (datetime.date): Current virtual server date.
        session (requests.Session): Requests session. Opens automatically.
        unittypes (Dict): List of unit types.
        units (Dict): List of company units.
        user (str): Username (login).
        webdriver: Selenium webdriver class. Defaults to webdriver.Chrome.
    
    Note:
        Attributes of type Dict and List are callable and can be filtered by 
        any fields. For example,
        v.units(unit_class_kind='farm', country_name=['Куба', 'Дания']) 
        will return all the farms located in the two specified countries.
    """
    
    user = os.environ.get('VIRTA_USER')
    password = os.environ.get('VIRTA_PASSWORD')
    path = os.environ.get('VIRTA_DIR', os.getcwd())
    domain = 'https://virtonomica.ru'
    #webdriver = webdriver.Chrome
    db_name = 'v.db'
    __pagesize = '&pagesize=1000000'
    api = {
        'cities': 'geo/city/browse',
        'company': 'my/company',
        'company_finance': 'company/report/finance/byitem?id={company_id}',
        'countries': 'geo/country/browse',
        'goods': 'product/goods',
        'industries': 'industry/browse',
        'offers': 'marketing/report/trade/offers?product_id={product_id}'+__pagesize,
        'produce': 'unittype/produce?id={unittype_id}',
        'product_categories': 'product/categories',
        'products': 'product/browse',
        'refresh': 'unit/refresh',
        'regions': 'geo/region/browse',
        'retail': 'marketing/report/retail/metrics?product_id={product_id}&geo={geo}',
        'sale_contracts': 'unit/sale/contracts?id={unit_id}{product_filter}'+__pagesize,
        'supply_contracts': 'unit/supply/contracts?id={unit_id}{product_filter}'+__pagesize,
        'technologies': 'unittype/technologies',
        'token': 'token',
        'unit_forecast': 'unit/forecast?id={unit_id}',
        'unit_summary': 'unit/summary?id={unit_id}',
        'units': 'company/units?id={company_id}'+__pagesize,
        'unittypes': 'unittype/browse',
        }
    
    
    def __init__(self, server, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.server = server
        self.domain_ext = self.domain + '/' + self.server + '/main/'
        api_url_prefix = '%s/api/%s/main/' % (self.domain, self.server)
        for key in self.api:
            self.api[key] = api_url_prefix + self.api[key]
        self.__produce = {}
        self.__unit_summary = {}
        self.__technologies = {}
    
    
    def __del__(self):
        self.quit()
    
    
    def open_session(self):
        """Open requests session and login to the game."""
        
        self.session = requests.Session()
        url = '%s/%s/main/user/login' % (self.domain, self.server)
        data = {'userData[login]': self.user, 
                'userData[password]': self.password}
        self.session.post(url, data=data)
        return self.session
    
    '''
    def driver_login(self):
        """Open web browser and ligin to the game."""
        
        self.driver.get(self.domain)
        try:
            login_button = self.driver.find_element_by_class_name('dialog_login_opener')
        except NoSuchElementException:
            return self.driver  # already logged in
        login_button.click()
        login_field = self.driver.find_element_by_name('userData[login]')
        password_field = self.driver.find_elements_by_name('userData[password]')[1]
        login_field.clear()
        login_field.send_keys(self.user)
        password_field.clear()
        password_field.send_keys(self.password)
        password_field.send_keys(Keys.ENTER)
        time.sleep(1)
        return self.driver
    '''
    
    def quit(self):
        """Close any connections if open.
        
        Todo:
            * Does not currently support inheritance.
        """
        
        if 'driver' in self.__dict__:
            self.driver.quit()
        if 'session' in self.__dict__:
            self.session.close()
        if 'conn' in self.__dict__:
            self.conn.close()
    
    
    # API related methods
    
    def __getattr__(self, attrname):
        if attrname == 'session':
            return self.open_session()
            
        #elif attrname == 'driver':
        #    self.driver = self.webdriver()
        #    self.driver_login()
        #    return self.driver
            
        elif attrname == 'db' or attrname == 'conn':
            self.conn = sqlite3.connect(self.path + self.db_name)
            self.db = self.conn.cursor()
            self.db.row_factory = dict_factory
            return getattr(self, attrname)
        
        elif attrname == 'server_date':
            url = self.domain_ext + 'company/rank/%s/info' % self.company['id']
            xp = '//div[@title="Время на сервере"]/text()'
            date_str = self.session.tree(url).xpath(xp)[0].strip()
            self.server_date = str_to_date(date_str)
            return self.server_date
        
        elif attrname == 'days_to_refresh':
            refresh_date = datetime.date(self.server_date.year, 9, 30)
            if refresh_date < self.server_date:
                refresh_date = refresh_date.replace(year=refresh_date.year + 1)
            days_left = (refresh_date - self.server_date).days
            self.days_to_refresh = days_left // 7
            return self.days_to_refresh
            
        elif attrname in ['token', 'cities', 'regions', 'countries', 
                        'product_categories', 'products', 'goods', 
                        'industries', 'unittypes', 'company', 
                        'company_finance']:
            data = {}
            if '{company_id}' in self.api[attrname]:
                data['company_id'] = self.company['id']
            url = self.api[attrname].format(**data)
            setattr(self, attrname, self.session.get(url).json(cls=Decoder))
            if attrname in ['cities', 'regions', 'countries', 'products', 'unittypes']:
                setattr(self, attrname, Dict(getattr(self, attrname)))
            return getattr(self, attrname)
        
        elif attrname in ['units', 'indicators']:
            url = self.api[attrname].format(company_id=self.company['id'])
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
            
        raise AttributeError(attrname)
    
    
    def produce(self, unittype_id):
        """Production information for a given unit type."""
        
        if unittype_id not in self.__produce:
            url = self.api['produce'].format(unittype_id=unittype_id)
            self.__produce[unittype_id] = self.session.get(url).json(cls=Decoder)
        return self.__produce[unittype_id]
    
    
    def unit_summary(self, unit_id, refresh=False):
        """Detailed information about a given unit, including forecast.
        
        Arguments:
            unit_id (int): Unit id.
            refresh (bool): If True, refresh unit information first.
                Defaults to False.
        
        Returns:
            Dictionary containing various unit characteristics, including
            the unit and top manager effectiveness forecast.
        """
        
        if refresh or unit_id not in self.__unit_summary:
            if refresh:
                self.refresh(unit_id)
            url_s = self.api['unit_summary'].format(unit_id=unit_id)
            unit_info = self.session.get(url_s).json(cls=Decoder)
            # Forecast
            url_f = self.api['unit_forecast'].format(unit_id=unit_id)
            unit_info['forecast'] = self.session.get(url_f).json(cls=Decoder)
            self.__unit_summary[unit_id] = unit_info
        return self.__unit_summary[unit_id]
    
    
    def offers(self, product_id):
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
        url = self.api['retail'].format(product_id=product_id, geo=geo)
        return self.session.get(url).json(cls=Decoder)
    
    
    def refresh(self, unit_id):
        """Refresh unit information.
        Needs to be called if unit characteristics have been manually changed,
        in order to get up to date unit summary information.
        
        Arguments:
            unit_id (int): Unit id.
        
        Returns:
            POST request responce.
        """
        
        url = self.api['refresh']
        data = {'id': unit_id, 'token': self.token}
        return self.session.post(url, data=data)
    

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
    
    
    # General purpose unit management methods
    
    def set_technology(self, unit_id, level, max_price=0):
        """Set technology level for a given unit.
        (Внедрить технологию)
        
        Note:
            Some technologies may be very expensive. Be careful when setting 
            max_price to None.
        
        Arguments:
            unit_id (int): Unit id.
            level (int): Technology level to be implemented.
            max_price (float): If not None, technology price will be checked 
                first. If technology price exceeds max_price, no purchase will 
                be made and technology will not be implemented.
                Defaults to 0 (invented and already bought technologies).
        
        Returns:
            POST request responce. None if technology is not available or
            costs more than max_price.
        """
        
        if max_price is not None:
            # Check technology price
            unittype_id = self.units[unit_id]['unit_type_id']
            technology = [t for t in self.technologies(unittype_id) 
                          if t['level']==level]
            if technology:
                technology = technology[0]
            else:
                return None
            status = technology['status']
            price = 0 if status in (1,2,4) else technology['price']
            if price > max_price:
                return None
        url = self.domain_ext + 'unit/view/%s/technology' % unit_id
        data = {'level': level}
        result = self.session.post(url, data=data)
        self.refresh(unit_id)
        return result
    
    
    def rename_unit(self, unit_id, name, international_name=''):
        """Rename unit.
        (Изменить название предприятия)
        
        Arguments:
            unit_id (int): Unit id.
            name (str): New unit name.
            international_name (str): International unit name. Defaults to ''.
        
        Returns:
            POST request responce.
        """
        
        url = self.domain_ext + 'unit/changename/%s' % unit_id
        data = {
            'unitData[name]': name,
            'unitData[international_name]': international_name
            }
        return self.session.post(url, data=data)
    
    
    def set_service_price(self, unit_id, price):
        """Set service price for units like restaurants, power stations etc.
        
        Arguments:
            unit_id (int): Unit id.
            price (float): New price to be set.
        
        Returns:
            POST request responce."""
        
        url = self.domain_ext + 'unit/view/%s' % unit_id
        data = {
            'servicePrice': price, 
            'setprice': 1
        }
        return self.session.post(url, data=data)
    
    
    def create_supply_contract(self, unit_id, offer_id, amount=1, max_price=0, 
                               max_increase=1, min_quality=0, constraint='Rel', 
                               instant=0):
        """Add new supply contract.
        
        Arguments:
            unit_id (int): Ordering unit id.
            offer_id (int): Every market offer has its own unique id,
                different from seller id and product id.
        
        Keyword arguments:
            amount (int): Amount to be ordered. Defaults to 1.
            max_price (float): If supplier price reaches max_price, the 
                contract is automatically broken.
                Valid only if constraint == 'Abs'.
                Defaults to 0 (no constraint).
            max_increase (int, 0..5): If supplier price growth by mote than
                a given percentage, the contract is automatically broken.
                Can take values:
                    0 (never break the contract),
                    1 (break the contract if price growth by 5% or more),
                    2 (break the contract if price growth by 10% or more), 
                    3 (break the contract if price growth by 20% or more), 
                    4 (break the contract if price growth by 50% or more), 
                    5 (break the contract if price growth by 100% or more).
                Valid only if constraint == 'Rel'.
                Defaults to 1 (5% bound).
            min_quality (float): If product quality drops below min_quality,
                no purchase is made, although the contract remains valid.
                Defaults to 0 (no constraint).
            constraint (str): Type of constraint. Can take values 'Abs' for 
                absolute price value or 'Rel' for percetage price change.
                Defaults to 'Rel'.
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
            'constraintPriceType': constraint,
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
                    'constraint' (str): 'Abs' for absolute value or 'Rel' for
                        percetage change (default 'Rel').
                    'max_increase' (int, 0..5): Relative price change 
                        constraint, may take values: 0 (no constraint), 
                        1 (5%), 2 (10%), 3 (20%), 4 (50%), 5 (100%).
                        Defaults to 2 if not present.
                    'max_price' (float): Price constraint (default 0 for 
                        no constraint, if not present).
                    'min_quality': Minimum qualiy (default 0 for no constraint)
        
        Returns:
            POST request responce.
        
        Example:
            from virta import Virta
            v = Virta('olga')
            unit_id = 7358676
            orders = {
                7585670: {'quantity': 1000,
                          'constraint': 'Abs',
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
            data[name%'constraintPriceType'] = order.get('constraint', 'Rel')
            data[name%'price_mark_up'] = order.get('max_increase', 2)
            data[name%'price_constraint_max'] = order.get('max_price', 0)
            data[name%'quality_constraint_min'] = order.get('min_quality', 0)
        return self.session.post(url, data=data)
    
    
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
                        (no bound if not present);
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
    
    
    def set_employees(self, unit_id, quantity=0, salary=0, salary_max=0,
                      target_level=0, trigger=0):
        """Set employees characteristics for a given unit.
        
        Arguments:
            unit_id (int): Unit id.
            quantity (int): Number of emloyees. Defaults to 0.
            salary (float): Salary. Defaults to 0 (leave unchanged).
            salary_max (float): Salaryupper bound. Defaults to 0 (unchanged).
            target_level (float): Target employees qualification. Defaults to 0
                (leave unchanged).
            trigger (0, 1, 2): HR department selector. Values:
                0 - HR department is off (отдел кадров простаивает),
                1 - HR department adapts salary to targer qualification level
                    (отдел кадров корректирует зарплату каждый пересчёт),
                2 - HR department adapts salary to technology requirements
                    (отдел кадров подстраивается под требования технологии).
                Defaults to 0.
        
        Returns:
            POST request responce.
        """
        
        url = self.domain_ext + 'unit/employees/engage/%s' % unit_id
        data = {
            'unitEmployeesData[quantity]': quantity,
            'unitEmployeesData[salary]': salary,
            'salary_max': salary_max,
            'target_level': target_level,
            'trigger': trigger
            }
        result = self.session.post(url, data=data)
        self.refresh(unit_id)
        return result
        
        
    def holiday_set(self, unit_id):
        """Send employees on holiday.
        
        Arguments:
            unit_id (int): Unit id.
        
        Returns:
            POST request responce.
        """
        
        url = self.domain_ext + 'unit/view/%s/holiday_set' % unit_id
        result = self.session.post(url)
        self.refresh(unit_id)
        return result
    
    
    def holiday_unset(self, unit_id):
        """Return employees from holiday.
        
        Arguments:
            unit_id (int): Unit id.
        
        Returns:
            POST request responce.
        """
        
        url = self.domain_ext + 'unit/view/%s/holiday_unset' % unit_id
        result = self.session.post(url)
        self.refresh(unit_id)
        return result
    
    
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
    
    
    def upgrade_equipment(self, unit_id, target_quality, target_amount=None):
        pass
    
    
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
    
    
    def resize_unit(self, unit_id, size_delta=0, size=None):
        """Change unit size.
        
        Arguments:
            unit_id (int): Unit id.
            size_delta (int): Relative size change. Defaults to 0 (no change).
            size (int): Required size. The corresponding relative size change 
                will be computed based on the current unit size.
                Defaults to None (ignored).
        
        Returns:
            POST request responce.
        """
        
        if size is not None:
            size_delta = size - self.unit_summary(unit_id)['size']
        url = self.domain_ext + 'unit/upgrade/%s' % unit_id
        data = {'upgrade[delta]': size_delta}
        return self.session.post(url, data=data)
    
    
    def set_innovation(self, unit_id, innovation_name, action='attach'):
        """Attach or detach an innovation for a given unit.
        
        Arguments:
            unit_id (int): Unit id.
            innovation_name (str): Innovation name.
            action: 'attach' or 'remove'. Defaults to 'attach'.
        
        Returns:
            POST request responce.
        
        Example:
            # Run political agitation at every villa
            for unit in v.units(unit_class_kind='villa').values():
                v.set_innovation(unit['id'], 'Политическая агитация')
        """
        
        artefacts = {
            # Villa
            'Политическая агитация': (1, 368592),
            'Качество производимой в регионе продукции': (2, 111),
            'Центр электронной коммерции': (3, 111),
            'Научный координационный центр': (4, 111),
            'Региональный сервисный центр': (5, 300137),
            # Laboratory
            'Электронная библиотека': (302766, 300141),
            'Сотрудничество с CERN': (302782, 300141),
            'Производственная практика для ученых': (302792, 300141),
            'Сверхпроводники': (300997, 300137),
            # Warehouse
            'Телескопические погрузчики': (302589, 300136),
            'Система бухгалтерского учета': (300821, 300137),
            # Animalfarm
            'Автоматизированная система кормораздачи': (301043, 300138),
            'Загоны для молодняка': (302635, 300136),
            'Селекционная лаборатория': (300941, 300140),
            'Ветеринарная служба': (301030, 300137),
            # Mill
            'Укрепленные жернова': (300958, 300139),
            'Износостойкие подшипники': (301008, 300137),
            # Workshop
            'Система складской маркировки': (302605, 300136),
            'Солнечные батареи': (300804, 300139),
            'Продлённая гарантия': (300990, 300137),
            # Shop
            'Система складской маркировки': (302607, 300136),
            'Автомобильная парковка': (301019, 300143),
            'Партнёрский договор с рекламным агентством': (302661, 300143),
            'Автосалон': (302455, 300144),
            'Бакалейная лавка': (302459, 300144),
            'Продуктовая лавка': (302483, 300144),
            'Бутик одежды': (302485, 300144),
            'Миллион мелочей': (302495, 300144),
            'Все для дома': (302505, 300144),
            'Ювелирный салон': (302526, 300144),
            'Консалтинг мирового лидера ритейла': (302572, 300144),
            'Электронный рай': (302821, 300144),
            'Система бухгалтерского учета': (300821, 300137),
            # Office
            'Креативный отдел': (302645, 300143)
            }
        villa_artefacts = {
            1: {1: 368595, 2: 368596, 4: 368598},
            2: {1: 113,    2: 114   , 4: 116   },
            3: {1: 327819, 2: 336763, 4: 336766},
            4: {1: 336748, 2: 336894, 4: 336900},
            5: {1: 336872, 3: 336874, 4: 336879},
            }
        artefact_id, slot_id = artefacts[innovation_name]
        if artefact_id <= 5:
            size = self.units[unit_id]['size']
            artefact_id = villa_artefacts[artefact_id][size]
        url = (self.domain + 
               '/%s/ajax/unit/artefact/%s?unit_id=%s&artefact_id=%s&slot_id=%s'
               % (self.server, action, unit_id, artefact_id, slot_id))
        return self.session.post(url)
    
    
    def close_unit(self, unit_id):
        """Close unit.
        
        Arguments:
            unit_id (int): Unit id.
        
        Returns:
            POST request responce.
        """
        
        url = self.domain_ext + 'unit/close/%s' % unit_id
        data = {'close_unit': 1}
        return self.session.post(url, data=data)
    
    
    def farm_season(self, unit_id, seasons):
        """Select farm or plantation specialization depending on a season.
        
        Выбрать специализацию земледельческой фермы/плантации в зависимости от
        текущего сезона. Для с/х подразделений, позволяющих выращивать
        несколько культур, позволяет задать специализацию для каждого месяца
        отдельно.
        
        Arguments:
            unit_id (int): Unit id.
            seasons (dict): Dictionary that to a month (1..12) associates 
                specialization name. For example,
                {7: 'Сахар', 8: 'Сахар', 9: 'Сахар', 10: 'Кукуруза'}
            
        Returns:
            POST request responce.
        """
        
        if not seasons or not all(m in range(1,12) for m in seasons):
            raise ValueError('seasons keys should be in range 1..12')
        
        agricultural_specializations = {}
        for unittype_id in (2119, 2420):
            for spec_id, spec in self.produce(unittype_id).items():
                agricultural_specializations[spec['name']] = spec_id
        
        url = self.domain_ext + 'unit/produce_change/%s' % unit_id
        month = (self.server_date + datetime.timedelta(days=7)).month
        while month not in seasons:
            month = month % 12 + 1
        culture = seasons[month]
        spec_id = agricultural_specializations[culture]
        data = {'unitProduceData[produce]': spec_id}
        return self.session.post(url, data=data)
    
    
    # Research related methods
    
    @staticmethod
    def lab_employees_required(level):
        """Number of employees needed for a given technological level"""
        
        empl = { 2: 5,    3: 10,   4: 10,   5: 15,   6: 15,   7: 15,   8: 30,
                 9: 40,  10: 40,  11: 60,  12: 60,  13: 100, 14: 120, 15: 150,
                16: 200, 17: 220, 18: 250, 19: 300, 20: 400, 21: 500, 22: 600,
                23: 700, 24: 700, 25: 700, 26: 850, 27: 850, 28: 1000
               }
        return empl.get(level, 1000) if level > 1 else 0
    
    
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
        max_level = max(t['level'] for t in levels(status=(1,2,4)))
        result = [t['level'] for t in levels
                  if t['level'] <= max_level and t['status'] not in (1,2)]
        result.append(max_level + 1)
        return result


    def start_research_project(self, unit_id, unittype_id, level):
        """Start research project.
        (Начать исследование нового проекта)
        
        Arguments:
            unit_id (int): Laboratory id.
            unittype_id (int): Unit type id.
            level (int): Level to be studied.
        
        Returns:
            POST request responce.
        """
        
        url = self.domain_ext + 'unit/view/%s/project_create' % unit_id
        data = {
            'unit_type': unittype_id, 
            'level': level, 
            'create': 1
            }
        result = self.session.post(url, data=data)
        self.refresh(unit_id)
        return result
    
    
    def stop_research_project(self, unit_id):
        """Stop research project.
        (Остановить проект)
        
        Arguments:
            unit_id (int): Laboratory id.
        
        Returns:
            POST request responce.
        """
        
        url = self.domain_ext + 'unit/view/%s/project_current_stop' % unit_id
        result = self.session.post(url)
        self.refresh(unit_id)
        return result
    
    
    def select_hypotesis(self, unit_id, hypotesis_id):
        """Select a hypotesis to study.
        
        Arguments:
            unit_id (int): Unit id.
            hypotesis_id (int): Every hypotesis has a unique id (can be found
                in unit_summary['project']['hepotesis'] list).
        
        Returns:
            POST request responce.
        """
        
        url = self.domain_ext + 'unit/view/%s/investigation' % unit_id
        data = {
            'selectedHypotesis': hypotesis_id,
            'selectIt': 1
            }
        result = self.session.post(url, data=data)
        self.refresh(unit_id)
        return result
    
    
    def set_experemental_unit(self, lab_id, exp_unit_id):
        """Set experemental unit for a given laboratory.
        
        Arguments:
            lab_id (int): Laboratory id.
            exp_unit_id (int): Experimental unit id.
        
        Returns:
            POST request responce.
        """
        
        url = self.domain_ext + 'unit/view/%s/set_experemental_unit' % lab_id
        data = {'unit': exp_unit_id}
        result = self.session.post(url, data=data)
        self.refresh(lab_id)
        return result
        
    
    @staticmethod
    def hypothesis_stydy_expected_time(success_probability, reference_time=1, 
                                       labs_num=1):
        """Expected duration of the 2nd stage of research.
        (Ожидаемое время проработки гипотезы)
        
        Assuming that several laboratories simultaniously start studing the 
        same hypotesis, computes the expected number of days until one of them
        succeeds.
        
        Arguments:
            success_probability (float): Success probability. Either percent
                (0..100) or real value (0..1).
            reference_time (int): Number of days one stage lasts. Defaults to 1
            labs_num (int): Number of laboratories studying the same level.

        Returns:
            Expected number of days needed to complete hypoteses study.
        """
        
        if success_probability > 1:
            success_probability /= 100
        if success_probability < 0 or success_probability > 1:
            raise ValueError
            
        expectation = 0
        attempt = 1
        fail_probability = 1
        while success_probability < 1:
            probability = 1 - (1 - success_probability)**labs_num
            expectation += attempt * probability * fail_probability
            fail_probability *= 1 - probability
            attempt += 1
            success_probability += 0.01
        expectation += attempt * fail_probability
        return expectation * reference_time
    
    
    @staticmethod
    def choose_hypothesis(hypotheses, labs_num=1):
        """Choose a hypotesis with the shortest expected study time.
        
        Arguments:
            hypotheses (list): List of available hypotheses, as represented in
                unit_summary['project']['hepotesis'] list.
            labs_num (int): Number of laboratories studying the same level.

        Returns:
            dict: The hypotesis from the hypotheses list for which the expected
                study time is the smallest.
        """
        
        expected_time = lambda h: Virta.hypothesis_stydy_expected_time(
                                      h['success_probabilities'],
                                      reference_time=h['hypotesis_lengths'],
                                      labs_num=labs_num
                                      )
        hypothesis = min(hypotheses, key=expected_time)
        hypothesis['expected_time'] = expected_time(hypothesis)
        return hypothesis
    
    
    def choose_experimental_unit(self, unittype_id, min_size=0, tech_level=1):
        """Choose unit of a given type satisfying minimal size and technology
        level requirements.
        
        Arguments:
            unittype_id (int): Unit type_id.
            min_size (int): Minimal size required. Defaults to 0.
            tech_level (int): Minimal technology level required. Defaults to 0.

        Returns:
            dist: Unit of the given type satisfying the restrictions.
                If several units found, the one with the highest productivity.
            None if no units satisfying the restrictions found.
        
        Todo:
            Too specific. Move to MyVirta class?
        """
        
        units = [self.unit_summary(u) for u in self.units(unit_type_id=unittype_id)]
        units = [u for u in units 
                 if u['size'] >= min_size and u['technology_level'] >= tech_level]
        if units:
            return max(units, key=lambda u: u['productivity'])
        else:
            return None
    
    
    # Politics related methods
    
    @staticmethod
    def days_to_election(days_passed, post='mayor'):
        """Days left to election.
        Takes into account day of the week when elections run.
        
        Arguments:
            days_passed (int): Days passed since election.
            post: 'mayor', 'governor' or 'president'.
        
        Returns:
            int: Days to elections. 0 the day before the election.
        """
        
        days_left = 156 - days_passed
        election_date = TODAY + datetime.timedelta(days=days_left)
        shift = 1 if post=='mayor' else 0 if post=='governor' else 3
        extra_days = 6 - (election_date.weekday() - shift) % 7
        return days_left + extra_days
    
    
    def elections(self, within_days=2):
        """List of running elections.
        
        Arguments:
            within_days (int): Elections that take place within the given
                number of days will be returned. Defaults to 2.
        
        Returns:
            list: List of running elections ids.
        """
        
        url = self.domain_ext + 'politics/news'
        page = self.session.tree(url)
        xp = '//td[contains(.,"%s")]/../td/a[contains(@href,"politics/elections")]/@href'
        days = [TODAY + datetime.timedelta(days=d+1) for d in range(within_days)]
        hrefs = sum((page.xpath(xp % date_to_str(d)) for d in days), [])
        return [int(href.split('/')[-1]) for href in hrefs]
    
    
    def city_change_council_tax(self, city_id, increase=True):
        """Change (increase or decrease) council tax for a given city.
        
        Note:
            The council tax only changes if the corresponding function is
            available to a major (depends on approval rating etc.)
            No availability check is done to minimize the number of requests.
        
        Arguments:
            city_id (int): City id.
            increase (bool): Flag. If True, tax will be increased. Decreased
                otherwise. Defaults to True (increase).
        
        Returns:
            POST request responce.
        """
        
        action = 'fee_up' if increase else 'fee_down'
        url = self.domain_ext + 'politics/%s/%s' % (action, city_id)
        self.session.get(url)
    
    
    def city_money_project(self, city_id, project_name):
        """Run municipal project.
        (Запустить муниципальный проект в городе)
        
        Arguments:
            city_id (int): City id.
            project_name (str): Project name, as appears in the game interface,
                or one of the following short forms:
                    'festival'  ('Городской фестиваль')
                    'education'  ('Научная конференция')
                    'salary_up'  ('Дотации населению')
                    'salary_down'  ('Борьба с высокими ценами')
                    'construction'  ('Доступное жильё')
                    'freeze'  ('Управление трудовыми ресурсами')
                    'migration'  ('Миграционная служба')
                    'trade_union'  ('Договор с профсоюзами')
                    'recycling'  ('Городская программа утилизации мусора')
                    'transport'  ('Транспортная развязка')
                    'sewage'  ('Очистные сооружения')
                    'power'  ('Экологический мониторинг электростанций')
                    
        Returns:
            POST request responce.
        """
        
        codes = {
            'Городской фестиваль': 1,
            'Научная конференция': 2,
            'Дотации населению': 3,
            'Борьба с высокими ценами': 4,
            'Доступное жильё': 5,
            'Управление трудовыми ресурсами': 6,
            'Миграционная служба': 10,
            'Договор с профсоюзами': 20,
            'Городская программа утилизации мусора': 12,
            'Транспортная развязка': 13,
            'Очистные сооружения': 14,
            'Экологический мониторинг электростанций': 15
            }
        #Alternative project names
        codes['festival'] = codes['Городской фестиваль']
        codes['education'] = codes['Научная конференция']
        codes['salary_up'] = codes['Дотации населению']
        codes['salary_down'] = codes['Борьба с высокими ценами']
        codes['construction'] = codes['Доступное жильё']
        codes['freeze'] = codes['Управление трудовыми ресурсами']
        codes['migration'] = codes['Миграционная служба']
        codes['trade_union'] = codes['Договор с профсоюзами']
        codes['recycling'] = codes['Городская программа утилизации мусора']
        codes['transport'] = codes['Транспортная развязка']
        codes['sewage'] = codes['Очистные сооружения']
        codes['power'] = codes['Экологический мониторинг электростанций']
        codes['Промышленный и бытовой мусор'] = codes['recycling']
        codes['Загрязнение автотранспортом'] = codes['transport']
        codes['Промышленные стоки'] = codes['sewage']
        codes['Выбросы электростанций'] = codes['power']
        
        url = self.domain_ext + 'politics/money_project/%s/%s' % (
                  city_id, codes[project_name])
        return self.session.get(url)

    
    def city_change_rent(self, city_id, unittype_name, rent_up=False):
        """Change rent price.
        
        Note:
            The rent change only happens if the corresponding function is 
            available to a major (depends on approval rating etc.)
            No availability check is done to minimize the number of requests.
        
        Arguments:
            city_id (int): City_id.
            unittype_name (str): Unit type. Can take values: 
                'office' (or equivalently 'Офис'), 
                'shop' ('Магазин'),
                'gas_station' ('Автозаправочная станция'), 
                'education' ('Образовательное учреждение'), 
                'service' ('Сфера услуг'),
                'restaurant' ('Ресторан'),
                'repair' ('Авторемонтная мастерская'),
                'it' ('IT-центр'),
                'warehouse' ('Склад'),
                'villa' ('Вилла'),
                'communication' ('Сеть коммуникационных вышек')
            rent_up (bool): Up/down flag. If True, the rent price is increased,
                decreased otherwise.
        
        Returns:
            POST request responce. 
        """
        
        codes = {
            'Офис': 1815,
            'Магазин': 1885,
            'Автозаправочная станция': 422789,
            'Образовательное учреждение': 423693,
            'Сфера услуг': 348193,
            'Ресторан': 373182,
            'Авторемонтная мастерская': 422811,
            'IT-центр': 423353,
            'Склад': 2013,
            'Вилла': 100,
            'Сеть коммуникационных вышек': 423768
            }
        #Alternative project names
        codes['office'] = codes['Офис']
        codes['shop'] = codes['Магазин']
        codes['gas_station'] = codes['Автозаправочная станция']
        codes['education'] = codes['Образовательное учреждение']
        codes['service'] = codes['Сфера услуг']
        codes['restaurant'] = codes['Ресторан']
        codes['repair'] = codes['Авторемонтная мастерская']
        codes['it'] = codes['IT-центр']
        codes['warehouse'] = codes['Склад']
        codes['villa'] = codes['Вилла']
        codes['communication'] = codes['Сеть коммуникационных вышек']

        change = 'rent_up' if rent_up else 'rent_down'
        url = self.domain_ext + 'politics/%s/%s/%d' % (
                  change, city_id, codes[unittype_name])
        self.session.get(url)
    
    
    def region_money_project(self, region_id, project_name):
        """Run regional project.
        (Запустить региональный проект)
        
        Arguments:
            region_id (int): Region id.
            project_name (str): Project name, as appears in the game interface,
                or one of the following short forms:
                    'eco75' ('Экологический стандарт - 75')
                    'eco90' ('Экологический стандарт - 90')
                    'agriculture' ('Региональная сельхозавиация')
                    'fish' ('Рыбнадзор')
                    'forest' ('Лесничество')
                    'animal' ('Региональная ветеринарная служба')
                    'no_luxury' ('Борьба с роскошью')
                    'luxury' ('Регаты под патронажем губернатора')
                    'air' ('Реконструкция аэропорта')
                    'road' ('Ремонт дорог')
                    'ecology' ('Экологическая полиция')
                    'power' ('Экологический мониторинг электростанций')
                    
        Returns:
            POST request responce.
        """
        
        codes = {
            'Экологический стандарт - 75': 1,
            'Экологический стандарт - 90': 2,
            'Региональная сельхозавиация': 4,
            'Рыбнадзор': 6,
            'Лесничество': 7,
            'Региональная ветеринарная служба': 8,
            'Борьба с роскошью': 9,
            'Регаты под патронажем губернатора': 10,
            'Реконструкция аэропорта': 11,
            'Ремонт дорог': 12,
            'Экологическая полиция': 13,
            'Экологический мониторинг электростанций': 14
            }
        #Alternative project names
        codes['eco75'] = codes['Экологический стандарт - 75']
        codes['eco90'] = codes['Экологический стандарт - 90']
        codes['agriculture'] = codes['Региональная сельхозавиация']
        codes['fish'] = codes['Рыбнадзор']
        codes['forest'] = codes['Лесничество']
        codes['animal'] = codes['Региональная ветеринарная служба']
        codes['no_luxury'] = codes['Борьба с роскошью']
        codes['luxury'] = codes['Регаты под патронажем губернатора']
        codes['air'] = codes['Реконструкция аэропорта']
        codes['road'] = codes['Ремонт дорог']
        codes['ecology'] = codes['Экологическая полиция']
        codes['power'] = codes['Экологический мониторинг электростанций']
        codes['Промышленный и бытовой мусор'] = codes['Экологическая полиция']
        codes['Загрязнение автотранспортом'] = codes['Экологическая полиция']
        codes['Промышленные стоки'] = codes['Экологическая полиция']
        codes['Выбросы электростанций'] = codes['Экологический мониторинг электростанций']
        
        url = self.domain_ext + 'politics/money_project/%s/%s' % (
                  region_id, codes[project_name])
        self.session.get(url)
    
    
    def country_money_project(self, country_id, project_name):
        """Run country project.
        (Законы страны)
        
        Arguments:
            country_id (int): Country id.
            project_name (str): Project name, as appears in the game interface,
                or one of the following short forms:
                    'education' ('Закон об образовании')
                    'construction' ('Закон о жилищном строительстве')
                    'trade' ('Закон о государственной поддержке розничных
                              рынков')
                    'sport' ('Постановление о развитии физкультуры и спорта')
                    'food' ('Закон об общественном питании')
                    'no_tender' ('Мораторий на проведение в стране регулярных 
                                  тендеров')
                    'ecology' ('Закон о национальной экологической службе')
                    'trademark' ('Закон о торговых марках')
                    'transport' ('Закон о национальной транспортной службе')
                    
        Returns:
            POST request responce.
        """
        
        codes = {
            'Закон об образовании': 1,
            'Закон о жилищном строительстве': 2,
            'Закон о государственной поддержке розничных рынков': 3,
            'Постановление о развитии физкультуры и спорта': 4,
            'Закон об общественном питании': 5,
            'Мораторий на проведение в стране регулярных тендеров': 6,
            'Закон о национальной экологической службе': 8,
            'Закон о торговых марках': 9,
            'Закон о национальной транспортной службе': 10,
            }
        #Alternative project names
        codes['education'] = codes['Закон об образовании']
        codes['construction'] = codes['Закон о жилищном строительстве']
        codes['trade'] = codes['Закон о государственной поддержке розничных рынков']
        codes['sport'] = codes['Постановление о развитии физкультуры и спорта']
        codes['food'] = codes['Закон об общественном питании']
        codes['no_tender'] = codes['Мораторий на проведение в стране регулярных тендеров']
        codes['ecology'] = codes['Закон о национальной экологической службе']
        codes['trademark'] = codes['Закон о торговых марках']
        codes['transport'] = codes['Закон о национальной транспортной службе']

        url = self.domain_ext + 'politics/money_project/%s/%s' % (
                  country_id, codes[project_name])
        self.session.get(url)
    
    
    def send_yacht_to_regatta(self, unit_id):
        """Send yacht to the world regatta.
        (Отправить яхту на мировую регату)
        
        Arguments:
            unit_id (int): Villa id.
        
        Returns:
            POST request responce.
        """
        
        url = self.domain_ext + 'unit/view/%s' % unit_id
        data = {'picnic_btn': 1}
        return self.session.post(url, data=data)
        

if __name__ == '__main__':
    v = Virta('olga')