from .jsondecoder import Decoder


def unit_summary(self, unit_id, refresh=False):
    """Detailed information about a given unit, including forecast.
    
    Note:
        For speed reasons, forecast is temporarily unabled.
    
    Arguments:
        unit_id (int): Unit id.
        refresh (bool): If True, refresh unit information first.
            Defaults to False.
    
    Returns:
        Dictionary containing various unit characteristics, including
        the unit and top manager effectiveness forecast.
    """
    
    if not hasattr(self, '__unit_summary'):
        self.__unit_summary = {}
    if refresh or unit_id not in self.__unit_summary:
        if refresh:
            self.refresh(unit_id)
        url_s = self.api['unit_summary'].format(unit_id=unit_id)
        unit_info = self.session.get(url_s).json(cls=Decoder)
        # Forecast
        #url_f = self.api['unit_forecast'].format(unit_id=unit_id)
        #unit_info['forecast'] = self.session.get(url_f).json(cls=Decoder)
        self.__unit_summary[unit_id] = unit_info
    return self.__unit_summary[unit_id]


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


def get_unit_notice(self, unit_id):
    url = self.domain_ext + 'unit/notice/%s' % unit_id
    page = self.session.tree(url)
    xp = '//textarea/text()'
    text = page.xpath(xp)
    if text:
        text = str(page.xpath(xp)[0])
    else:
        text = ''
    return text


def set_unit_notice(self, unit_id, text=''):
    url = self.domain_ext + 'unit/notice/%s' % unit_id
    data = {
        'unitData[text]': text,
        'save': 1
        }
    return self.session.post(url, data=data)


def set_technology(self, unit_id, level, max_price=0):
    """Set technology level for a given unit.
    (Внедрить технологию)
    
    Warning:
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


def resize_unit(self, unit_id, size_delta=0, size=None):
    """Change unit size.
    
    Note:
        Attempting to resize a state enterprise will raise an exception.
    
    Arguments:
        unit_id (int): Unit id.
        size_delta (int): Relative size change. Defaults to 0 (no change).
        size (int): Required size. The corresponding relative size change 
            will be computed based on the current unit size.
            Defaults to None (ignored).
    
    Returns:
        POST request responce.
    """
    
    if self.units[unit_id]['unit_class_kind'] in self.state_kinds:
        raise ValueError('State enterprises cannot be resized')
    if size is not None:
        size_delta = size - self.unit_summary(unit_id)['size']
    url = self.domain_ext + 'unit/upgrade/%s' % unit_id
    data = {'upgrade[delta]': size_delta}
    return self.session.post(url, data=data)


def cancel_resize_unit(self, unit_id):
    url = self.domain_ext + 'unit/upgrade/%s/stop' % unit_id
    data = {'accept': 1}
    return self.session.post(url, data=data)


def set_innovation(self, unit_id, innovation_name, action='attach', refresh=False):
    """Attach or detach an innovation for a given unit.
    
    Arguments:
        unit_id (int): Unit id.
        innovation_name (str): Innovation name.
        action: 'attach' or 'remove'. Defaults to 'attach'.
        refresh: if True, the innovation will be removed first.
    
    Returns:
        POST request responce.
    
    Example:
        # Run political agitation at every villa
        for unit in v.units(unit_class_kind='villa').values():
            v.set_innovation(unit['id'], 'Политическая агитация')
    """
    
    if action == 'attach' and refresh:
        self.set_innovation(unit_id, innovation_name, action='remove')
    
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
        'Аптека': (302572, 300144),
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


def remove_innovation(self, unit_id, innovation_name):
    return self.set_innovation(unit_id, innovation_name, action='remove')


def create_unit(self, *args, **kwargs):
    """Create unit.
    
    Order of positional arguments should correspond to order in which they
    appear during the unit creation dialog.
    If named argument city is passed, country and region may be skipped.
    
    Arguments:
        unit_class: класс подразделения
        unit_type: тип подразделения
        country: страна
        region: регион
        city: город
        district: район
        warehouse_product_category: тип хранимой продукции
        produce: специализация
        produce_bound: размер
        techno_level: технология
        custom_name: имя
        name: 
        
    Returns:
        Unit id if unit was created, None otherwise
        
    Example:
        v.create_unit('Ресторан', 'Окраина', 'Кофейня', '500 кв. м', 
                      name='Caffè Roma', city='Рим')
    """
    
    def get_options(page):
        result = {}
        name = None
        rows = page.xpath('//input[@type="radio"]')
        if rows:
            for row in rows:
                if not name:
                    name = str(row.xpath('./@name')[0]).split('[')[-1].split(']')[0]
                value = int(row.xpath('./@value')[0])
                if name == 'unit_type':
                    text = row.xpath('./../label/text()[last()]')
                else:
                    text = row.xpath('./../../td[2]/text()[last()]')
                if not text:
                    text = row.xpath('./../../td[3]/text()[last()]')
                text = str(text[0]).strip()
                result[value] = text
            return name, result
        else:
            name = 'custom_name'
            value = page.xpath('//input[@type="text"]/@value')[0]
            return name, value
    
    if 'city' in kwargs and 'region' not in kwargs or 'country' not in kwargs:
        city = self.cities.select(id=kwargs['city'])
        if not city:
            city = self.cities.select(city_name=kwargs['city'])
        if city:
            kwargs['region'] = city['region_id']
            kwargs['country'] = city['country_id']
        else:
            print('Error: nonexistent city passed')
            return
        
    if 'name' in kwargs and 'custom_name' not in kwargs:
        kwargs['custom_name'] = kwargs['name']
        
    arg_iter = iter(args)
    url = self.domain_ext + 'unit/create/%s?old' % self.company['id']
    name = None
    print('\nCreating unit')
    while 'unit/create/' in url:
        name, options = get_options(self.session.tree(url))
        print(name, end=': ')
        if name in kwargs:
            choice = kwargs[name]
        else:
            try:
                choice = next(arg_iter)
            except StopIteration:
                if name == 'custom_name':
                    choice = options
                else:
                    print('Error: not enough arguments passed')
                    return
        if name != 'custom_name' and choice not in options:
            choice = [k for k, v in options.items() if v == choice]
            if choice:
                choice = choice[0]
            else:
                print('Error: cannot find a proper option')
                return
        print(choice if name=='custom_name' else options[choice])
        data = {
            'unitCreateData[%s]' % name: choice,
            'next': 1 
            }
        url = self.session.post(url, data=data).url
    unit_id = int(url.split('/')[-1])
    print('Unit created:', unit_id)
    return unit_id


def sale_unit(self, unit_id, price=None, factor=1):
    url = self.domain_ext + 'unit/market/sale/%s' % unit_id
    if not price:
        market_price = self.unit_summary(unit_id, refresh=True)['market_price']
        if not market_price:
            page = self.session.tree(url)
            xp = '//input[@name="price"]/@value'
            market_price = page.xpath(xp)
            if market_price:
                market_price = float(page.xpath(xp)[0])
            else:
                return
        price = factor * market_price
    price = int(price)
    print('Sale', unit_id, 'for', price)
    data = {
        'price': price,
        'sale': 1
        }
    return self.session.post(url, data=data)


def cancel_sale_unit(self, unit_id):
    """Отменить продажу предприятия"""
    
    url = self.domain_ext + 'unit/market/cancel_sale/%s' % unit_id
    return self.session.get(url)


def close_unit(self, unit_id):
    """Close unit.
    
    Note:
        Attempting to close a state enterprise will raise an exception.
    
    Arguments:
        unit_id (int): Unit id.
    
    Returns:
        POST request responce.
    """
    
    if self.units[unit_id]['unit_class_kind'] in self.state_kinds:
        raise ValueError('State enterprises cannot be closed')
    url = self.domain_ext + 'unit/close/%s' % unit_id
    data = {'close_unit': 1}
    return self.session.post(url, data=data)