import math


def save_technology_sellers_to_db(self, unittype_id: int, level: int,
                                  tender_id: int=None, tender_day: int=None):
    sellers_all = self.technology_sellers_all(unittype_id, level)
    sellers_med = self.technology_sellers_med(unittype_id, level)
    mean_price = sum(sellers_med.values()) / len(sellers_med)
    shares = {company_id: math.exp(-3 * abs(price/mean_price - 0.9))
              for (company_id, price) in sellers_all.items()}
    shares_total = sum(shares.values())
    shares = {company_id: share / shares_total for (company_id, share) in shares}
    for company_id, price in sellers_all.items():
        data = {
            'unittype_id': unittype_id,
            'level': level,
            'date': self.today,
        	'tender_id': tender_id,
        	'tender_day': tender_day,
        	'company_id': company_id,
        	'price': price,
        	'impact': company_id in sellers_med,
            'mean_price': round(mean_price, 2),
            'share': round(mean_price * shares[company_id], 2),
            }
        self.db_insert('tech_offers', data)
    self.conn.commit()


def manage_science_tenders(self):
    def compute_price(sellers, level=2):
        sellers_num = len(sellers)
        total_price = sum(sellers.values())
        if self.company['id'] in sellers:
            sellers_num -= 1
            total_price -= sellers[self.company['id']]
        if sellers_num:
            return 0.9 * total_price / (sellers_num + 0.1)
        else:
            return (level - 1) * 10**8
    
    print('Managing science tenders:')
    for tender_id, tender in self.tenders(knowledge_area_kind='research').items():
        days_left = (tender['estimated_real_date'] - self.today).days
        unittype_id = tender['tender_params'][0]
        duration = tender['tender_type']
        print(tender_id, days_left, '[%d]' % duration)
        for level in range(2, 50):
            self.save_technology_sellers_to_db(unittype_id, level, tender_id,
                                               duration - days_left)
        if days_left <= 0:
            # Снять технологии с продажи
            self.destroy_technology_offers([(unittype_id, level) for level in range(2, 50)])
        elif days_left <= duration + 1:
            # Выставить технологии на продажу
            price_sum = 0
            for tech in self.technologies(unittype_id):
                level = tech['level']
                market_price = tech['price']
                price_sum += market_price
                if price_sum > 2 * 10**9:
                    break
                sellers = self.technology_sellers_med(unittype_id, level)
                price = round(compute_price(sellers, level), 2)
                self.set_technology_offer(unittype_id, level, price)
                print(' ', tech['level'], '(%d)' % len(sellers), market_price, 
                      '->', price)


def manage_tenders(self):
    self.tender_register_all()
    self.manage_science_tenders()