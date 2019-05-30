def party_sales(self, unit_ids=None):
    """Open warehouse sales for party members.
    
    Arguments:
        unit_ids (list): Units to handle. If not passed, opens all
            warehouses with names starting with '%'.
    """
    
    # Determine party members companies ids
    url = self.domain_ext + 'company/view/%s/party' % self.company['id']
    page = self.session.tree(url)
    xp = '//input[@name="member[]"]/../..//a[contains(@href,"company/view")]/@href'
    companies = [href.split('/')[-1] for href in page.xpath(xp)]
    for unit_id, unit in self.units(unit_type_name='Склад').items():
        if (unit_ids and unit_id in unit_ids 
                or not unit_ids and unit['name'][:1] == '%'):
            print(unit['name'])
            products = {}
            for contract in self.sale_contracts(unit_id):
                products[contract['product_id']] = contract['offer_price']
            data = {product: {'price': price, 
                              'constraint': 2, 
                              'company': companies} 
                    for product, price in products.items()}
            self.set_sale_offers(unit_id, data)
