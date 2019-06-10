import math
from .math import sigmoid, log

from .const import (
    REFERENCE_SHOP_ID,  # эталонный магазин, из которого копируем ассортимент
    TARGET_CUSTOMERS,  # целевое количество посетителей
    MIN_MARKET_SHARE,  # минимальная доля рынка
    MAX_MARKET_SHARE,  # максимальная доля рынка
    MAX_MARKET_SHARE_STOCK,  # максимальный запас относительно рынка
    MAX_SALES_ADJUSTMENT,  # максимальных шаг изменения продаж
    MAX_PRICE_ADJUSTMENT,  # максимальных шаг изменения цены
    ELASTICITY,  # эластичность спроса
    SALES_PRICE_FACTOR,  # множитель к распродажной цене для новых товаров
    TARGET_STOCK_RATIO,
    )


def set_shops_advertisement(self, target_customers=None):
    if not target_customers:
        target_customers = TARGET_CUSTOMERS
    for shop_id, shop in self.units(unit_class_kind='shop').items():
        if 'Конкурс Олигархов' in shop['name'] or shop['name'][:2] == '* ':
            continue
        sections = max(1, self.unit_summary(shop_id)['section_count'])
        customers = target_customers // sections
        self.set_advertisement(shop_id, target_customers=customers, 
                               innovation=(shop['name']=='*****'))


def set_shops_innovations(self, refresh=False):
    for shop_id in self.units(name='*****'):
        self.set_innovation(shop_id, 'shop_advertisement', refresh=refresh)
        self.set_innovation(shop_id, 'shop_retail', refresh=refresh)


def distribute_shops_employees(self):
    units = [unit_id for unit_id, unit in self.units(unit_class_kind='shop').items()
             if unit['name'] == '*****' or unit['name'][0] != '*']
    return self.distribute_shop_employees(units, reserve=100)


def set_shop_default_prices(self, shop_id, factor=2):
    trading_hall_prev = self.trading_hall(shop_id)
    self.set_shop_sales_prices(shop_id)
    trading_hall_new = self.trading_hall(shop_id)
    offers = {}
    for product_id in trading_hall_new:
        if trading_hall_prev[product_id]['price'] > 0:
            offers[product_id] = trading_hall_prev[product_id]['price']
            if offers[product_id] < trading_hall_new[product_id]['price']:
                offers[product_id] = trading_hall_new[product_id]['price']
        else:
            offers[product_id] = factor * trading_hall_new[product_id]['price']
    self.set_shop_sale_prices(shop_id, offers)


def set_shops_default_prices(self, factor=2):
    for shop_id in self.units(name='*****'):
        self.set_shop_default_prices(shop_id)


def propagate_contracts(self, reference_shop_id=None):
    print('Copying contracts')
    if not reference_shop_id:
        reference_shop_id = REFERENCE_SHOP_ID
    shops = self.units(name='*****')
    ref_contracts = self.supply_contracts(reference_shop_id)  # вытягиваем из ведущего магазина список контрактов
    for shop_id in shops:
        print(shop_id)
        contracts = self.supply_contracts(shop_id)
        for offer_id in ref_contracts:
            if offer_id not in contracts:
                print('+', offer_id)
                self.create_supply_contract(shop_id, offer_id, max_increase=0)


def _get_retail_terget_volumes(self):
    units = {unit_id: unit 
             for unit_id, unit in self.units(unit_class_kind='warehouse').items()
             if unit['name'][:1] == '!'}
    result = {}
    for unit_id in units:
        url = self.domain_ext + 'unit/view/%s' % unit_id
        page = self.session.tree(url)
        xp = '//tr//img[contains(@src, "/img/products/")]/../..'
        for row in page.xpath(xp):
            name = str(row.xpath('./td[1]/text()')[0])
            purchase = int(row.xpath('./td[8]/text()')[0].replace(' ', ''))
            result[name] = purchase
    return result


def manage_shops(self, reference_shop_id=None):
    if not reference_shop_id:
        reference_shop_id = REFERENCE_SHOP_ID
    shops = self.units(name='*****')
    # Вытягиваем из ведущего магазина список товаров, которыми торгуем
    products = {p['product_id']: p 
                for p in self.supply_contracts(reference_shop_id).values()
                if p['quantity_at_supplier_storage']}
    
    print('Reading shops info')
    # Считываем инфу из всех торговых залов (из БД, если уже считывали)
    trading_halls = {shop_id: self.trading_hall(shop_id, cache=True) for shop_id in shops}
    # Считаем, сколько товаров суммарно отгружать
    # Если на складе слишком много товара, отгружаем среднее 
    # между имеющимся количеством и вчерашний отгрузкой
    # чтобы амортизировать колебания
    for product_id, product in products.items():
        purchase = sum(trading_hall[product_id]['purchase'] for trading_hall in trading_halls.values())
        if product['quantity_at_supplier_storage'] > purchase > 0:
            products[product_id]['quantity_to_distribute'] = (purchase + product['quantity_at_supplier_storage']) / 2
        else:
            products[product_id]['quantity_to_distribute'] = product['quantity_at_supplier_storage']
    
    # считаем долю магазинов, в которых сбыли весь товар
    # чем выше данное отношение, тем больше поднимаем цену
    clearance_count = {product_id: [] for product_id in products}
    for shop_id in shops:
        for product_id, trade in trading_halls[shop_id].items():
            clearance_count[product_id].append(trade['stock'] == trade['purchase'] and trade['sold'] > 0)
    clearance_rate = {product_id: sum(count) / max(1, len(count)) 
                      for (product_id, count) in clearance_count.items()}
    
    # Read retail metrics
    print('Reading markets info')
    # Считаем объемы рынков
    markets = {}
    for product_id in products:
        markets[product_id] = {}
        for shop_id, shop in shops.items():
            trade = trading_halls[shop_id][product_id]
            if trade['market_share'] > 0:
                # Быстро оцениваем объем рынка исходя из доли и продаж
                markets[product_id][shop['city_id']] = trade['sold'] / trade['market_share']
            else:
                # Иначе читаем напрямую из розничного отчета по городу
                print('!', end='')
                city = self.cities[shop['city_id']]
                geo = city['country_id'], city['region_id'], city['city_id']
                markets[product_id][shop['city_id']] = self.retail_metrics(
                    product_id, geo)['local_market_size']
        # Считаем суммврный объем всех рынков для каждого товару
        markets[product_id]['total_market_size'] = sum(markets[product_id].values())
    
    # Distribute sales
    print('Distributing sales')
    # Распределяем товары между магами
    target_sales = {}
    for product_id, product in products.items():
        # Compute mean price for a given product
        # Считаем среднюю цену сбыта
        total_sold = sum(trading_halls[shop_id][product_id]['sold'] for shop_id in shops)
        if total_sold > 0:
            # средняя цена
            mean_price = sum(trading_halls[shop_id][product_id]['price']
                             * trading_halls[shop_id][product_id]['sold']
                             for shop_id in shops) / total_sold
            log_mean_price = math.log(mean_price)
            # стандартное отклоние цены от средней
            std_dev = (sum((log(trading_halls[shop_id][product_id]['price'], log_mean_price) - log_mean_price) ** 2
                           * trading_halls[shop_id][product_id]['sold']
                           for shop_id in shops) / total_sold) ** 0.5
            # наклон сигмоиды
            adjustment_rate =  MAX_SALES_ADJUSTMENT / (2**0.5 * std_dev)  # 2**0.5 is crucial here!
        else:
            mean_price = None
            adjustment_rate = MAX_SALES_ADJUSTMENT  # наклон сигмоиды
        #print(adjustment_rate)
        
        # Считаем, сколько товара хотим сбывать в каждом магазине
        target = {}
        for shop_id, shop in shops.items():
            trade = trading_halls[shop_id][product_id]
            market_size = markets[product_id][shop['city_id']]
            if trade['sold']:
                # Отталкиваемся от продаж, если таковые были
                target_sale = trade['sold']
                if trade['stock'] > trade['purchase'] and mean_price:
                    # Если имеем точное значение спроса, корректируем 
                    # пропорционально отклонению цены от средней
                    target_sale *= sigmoid(log(trade['price'], log_mean_price) - log_mean_price + 1, 
                                           adjustment_rate, MAX_SALES_ADJUSTMENT)
            else:
                # По умолчанию, если не было продаж, распределяем пропорционально объемам рынков
                target_sale = (product['quantity_to_distribute'] 
                               * market_size
                               / markets[product_id]['total_market_size'])
            target[shop_id] = (max(1, target_sale),
                               max(1, MIN_MARKET_SHARE * market_size),
                               max(1, MAX_MARKET_SHARE * market_size)
                               )  # цель, нижняя и верхняя граница
            
        # Найденные объемы не обязательно суммируются в кол-во товара на складе
        # Поэтому распределяем весь имеющийся товар пропорционально
        
        # Методом деления отрезка пополам ищем множитель, для которого
        # суммарное стабжение совпадает с требуемым
        def total(factor):
            return sum(int(min(max(factor * t, mint), maxt)) 
                       for (t, mint, maxt) in target.values())
        
        target_sales[product_id] = {}
        factor0 = 0
        factor1 = max(maxt / t for (t, mint, maxt) in target.values())
        if total(factor0) >= product['quantity_to_distribute']:
            total_min = total(factor0)
            for shop_id in shops:
                t, mint, maxt = target[shop_id]
                target_sale = mint * product['quantity_to_distribute'] / total_min
                target_sales[product_id][shop_id] = int(target_sale)
        elif total(factor1) <= product['quantity_to_distribute']:
            for shop_id in shops:
                t, mint, maxt = target[shop_id]
                target_sales[product_id][shop_id] = int(maxt)
        else:
            total_sales0 = total(factor0)
            total_sales1 = total(factor1)
            while total_sales0 < total_sales1:
                factor = (factor0 + factor1) / 2
                if factor == factor0 or factor == factor1:
                    break
                if total(factor) < product['quantity_to_distribute']:
                    factor0 = factor
                    total_sales0 = total(factor0)
                else:
                    factor1 = factor
                    total_sales1 = total(factor1)
            error0 = abs(total(factor0) - product['quantity_to_distribute'])
            error1 = abs(total(factor1) - product['quantity_to_distribute'])
            factor = factor0 if error0 <= error1 else factor1
            for shop_id, shop in shops.items():
                t, mint, maxt = target[shop_id]
                target_sale = min(max(factor * t, mint), maxt)
                target_sales[product_id][shop_id] = int(target_sale)
    
    print('Managing shops')
    # Корректируем магазины
    for shop_id, shop in shops.items():
        print(shop_id)
        # Update orders
        # Снабжение
        orders = {}
        for contract in self.supply_contracts(shop_id).values():
            if contract['product_id'] not in products:
                continue
            # заказываем сколько распределили
            orders[contract['offer_id']] = {
                'quantity': target_sales[contract['product_id']][shop_id], 
                'max_increase': 0
                }
        self.set_supply_contracts(shop_id, orders)
        
        # Update prices
        # Сбрасываем цены в ноль
        offers = {t['ids']: 0 for t in trading_halls[shop_id].values()}
        self.set_shop_sale_prices(shop_id, offers)
        # Устанавливаем распродажные цены
        self.set_shop_sales_prices(shop_id)
        # Считываем торговый зал
        trading_hall_sales = self.trading_hall(shop_id, cache=False)
        offers = {}
        for product_id, trade in trading_halls[shop_id].items():
            # на случай, если уже вывезли часть товара, сохраняем текущее значение
            trade['current_stock'] = trading_hall_sales[product_id]['stock']  
            if product_id not in products:
                new_price = trade['price']  # просто возвращаем старую цену
            elif trade['price'] > 0:
                new_price = trade['price']
                target = min(target_sales[product_id][shop_id], 
                             trade['current_stock'] * TARGET_STOCK_RATIO)
                if trade['stock'] == trade['purchase'] and target > 0:
                    # если продан весь товар, повышаем цену
                    clearance_factor = 0.4 + 9.6 * clearance_rate[product_id]**1.5
                    stock_ratio = trade['sold'] / target
                    stock_factor = 2 * math.atan(20 * (stock_ratio - 1)) / math.pi + 1
                    total_inc = MAX_PRICE_ADJUSTMENT * stock_factor * clearance_factor
                    new_price *= 1 + total_inc
                elif target > 0:
                    # корректируем под требуемый объем продаж
                    discount_factor = 1 if trade['sold'] > 0 else 2
                    # снижаем цену быстрее, если ничего не продано
                    new_price *= sigmoid(trade['sold'] / target, 1 / ELASTICITY, 
                                         discount_factor * MAX_PRICE_ADJUSTMENT)
                # Следим, чтобы цена не опускалась ниже распродажной
                if new_price < trading_hall_sales[product_id]['price']:
                    new_price = trading_hall_sales[product_id]['price']
            else:
                # Цена по умолчанию для новых продуктов
                new_price = SALES_PRICE_FACTOR * trading_hall_sales[product_id]['price']
            offers[trade['ids']] = round(new_price, 2)
        self.set_shop_sale_prices(shop_id, offers)
        
        # Move surpluses back to warehouse
        #Вывозим излишки товара обратно на склад
        for product_id, trade in trading_halls[shop_id].items():
            if product_id not in products:
                continue
            market_size = markets[product_id][shop['city_id']]
            # оставляем двухдневный запас или максимальную долю рынка 
            #(немного больше максимальной доли рынка, чтобы избежать частых опустошений)
            if trade['sold'] > 0:
                # сглаживаем между днями
                need = target_sales[product_id][shop_id] + trade['sold']
            else:
                need = 2 * target_sales[product_id][shop_id]
            need = min(need, MAX_MARKET_SHARE_STOCK * market_size)
            # лишнее вывозим
            if trade['current_stock'] > need:
                self.product_move_to_warehouse(
                    shop_id, product_id, products[product_id]['supplier_id'], 
                    trade['current_stock'] - need)