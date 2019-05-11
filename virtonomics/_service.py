def service_history(self, unit_id):
    url = self.domain_ext + 'unit/view/%s/service_history' % unit_id
    page = self.session.tree(url)
    xp = '//*[@id="mainContent"]//tr'
    result = []
    for row in page.xpath(xp)[1:]:
        price = row.xpath('./td[2]//text()')
        if price:
            price = float(price[0].replace(' ', '').replace('$', ''))
        else:
            price = None
        sold = row.xpath('./td[3]/text()')
        if sold:
            sold = int(sold[0].replace(' ', ''))
        else:
            sold = 0
        result.append({'price': price, 'sold': sold})
    return result


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