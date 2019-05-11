import datetime


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