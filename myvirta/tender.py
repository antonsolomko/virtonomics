import math


def save_technology_sellers_to_db(self, unittype_id: int, level: int,
                                  tender_id: int=None, tender_day: int=None):
    sellers_all = self.technology_sellers_all(unittype_id, level)
    if not sellers_all:
        return
    sellers_med = self.technology_sellers_med(unittype_id, level)
    mean_price = sum(sellers_med.values()) / len(sellers_med)
    shares = {company_id: math.exp(-3 * abs(price/mean_price - 0.9))
              for (company_id, price) in sellers_all.items()}
    shares_total = sum(shares.values())
    shares = {company_id: share / shares_total for (company_id, share) in shares.items()}
    for company_id, price in sellers_all.items():
        data = {
            'unittype_id': unittype_id,
            'level': level,
            'date': self.today,
        	'tender_id': tender_id,
        	'tender_day': tender_day,
            'olc_days_left': self.oligarch_competition_days_left,
        	'company_id': company_id,
        	'price': price,
        	'impact': company_id in sellers_med,
            'mean_price': round(mean_price, 2),
            'share': round(mean_price * shares[company_id], 2),
            }
        self.db_insert('tech_offers', data)
    self.conn.commit()


def manage_science_tenders(self):
    def compute_price(sellers, level=2, active_players=None):
        if not active_players:
            active_players = []
        if self.company['id'] not in active_players:
            active_players.append(self.company['id'])
        if sellers:
            sellers_num = len(sellers)
            price_sum = sum(sellers.values())
        else:
            sellers_num = 1
            price_sum = (level - 1) * 10**8
        for company_id in active_players:
            if company_id in sellers:
                sellers_num -= 1
                price_sum -= sellers[company_id]
        if not sellers_num:
            sellers_num = 1
            price_sum = sum(sellers.values()) / len(sellers)
        return 0.9 * price_sum / (sellers_num + 0.1 * len(active_players))
    
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
                active_players = [5526168, 6451449] if days_left <= duration else []
                price = round(compute_price(sellers, level, active_players), 2)
                self.set_technology_offer(unittype_id, level, price)
                print(' %d:' % tech['level'], market_price, '(%d)' % len(sellers), 
                      '->', price)


def manage_tenders(self):
    self.tender_register_all()
    self.manage_science_tenders()