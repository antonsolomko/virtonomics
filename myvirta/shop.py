import math
from .math import sigmoid, log

from .const import (
    MANAGED_SHOPS_NAMES,  # ('*****',)
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


def set_shop_advertisement(self, shop_id, target_customers=None, innovation=False):
    if not target_customers:
        target_customers = TARGET_CUSTOMERS
    sections = max(1, self.unit_summary(shop_id)['section_count'])
    customers = target_customers // sections
    return self.set_advertisement(shop_id, target_customers=customers, 
                                  innovation=innovation)


def set_shops_advertisement(self, target_customers=None):
    for shop_id, shop in self.units(unit_class_kind='shop').items():
        if 'Конкурс Олигархов' not in shop['name'] and shop['name'][:2] != '* ':
            self.set_shop_advertisement(shop_id, target_customers, 
                                        innovation=shop['name'] in MANAGED_SHOPS_NAMES)


def set_shop_innovations(self, shop_id, advertisement=True, parking=False, retail=True, refresh=False):
    print(shop_id)
    if advertisement:
        print('  advertisement')
        self.set_innovation(shop_id, 'shop_advertisement', refresh=refresh)
    elif parking:
        print('  parking')
        self.set_innovation(shop_id, 'shop_parking', refresh=refresh)
    
    if retail:
        shop = self.unit_summary(shop_id)
        if shop['section_count'] > 1:
            print('  ratail all')
            self.set_innovation(shop_id, 'shop_retail', refresh=refresh)
        elif shop['section_count'] == 1:
            trading_hall = self.trading_hall(shop_id)
            if trading_hall:
                category = self.goods[next(iter(trading_hall))]['product_category_name']
                print('  ' + category)
                self.set_innovation(shop_id, category, refresh=refresh)


def set_shops_innovations(self, refresh=False):
    print('SETTING SHOPS INNOVATIONS:')
    for shop_id, shop in self.units(unit_class_kind='shop').items():
        self.set_shop_innovations(shop_id, 
                                  advertisement=shop['name'] in MANAGED_SHOPS_NAMES, 
                                  retail=shop['name'] in MANAGED_SHOPS_NAMES, 
                                  refresh=refresh)


def distribute_shops_employees(self, reserve=100):
    units = [unit_id for (unit_id, unit) in self.units(unit_class_kind='shop').items()
             if unit['name'] in MANAGED_SHOPS_NAMES or unit['name'][:1] != '*']
    return self.distribute_shop_employees(units, reserve=reserve)


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
    for shop_id in self.units(name=MANAGED_SHOPS_NAMES):
        self.set_shop_default_prices(shop_id)


def propagate_contracts(self, reference_shop_id=None):
    print('Copying contracts')
    if not reference_shop_id:
        reference_shop_id = REFERENCE_SHOP_ID
    shops = self.units(name=MANAGED_SHOPS_NAMES)
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


def manage_shops(self):
    shops = self.units(name=MANAGED_SHOPS_NAMES)
    trades = {}
    products = {}
    for shop_id in shops:
        for contract in self.supply_contracts(shop_id).values():
            product_id = contract['product_id']
            trades[shop_id, product_id] = {}
            if product_id not in products:
                products[product_id] = contract
                contract['total_market_size'] = 0
                contract['shipped'] = 0
        for product_id, trade in self.trading_hall(shop_id, cache=True).items():
            if (shop_id, product_id) not in trades:
                # Обрабатываем только поставляемые товары 
                continue
            trades[shop_id, product_id] = trade
            # Считаем объемы рынков
            if trade['market_share'] > 0:
                # Быстро оцениваем объем рынка исходя из доли и продаж
                trade['market_size'] = trade['sold'] / trade['market_share']
            else:
                # Иначе читаем напрямую из розничного отчета по городу
                city = self.cities[shops[shop_id]['city_id']]
                geo = city['country_id'], city['region_id'], city['city_id']
                trade['market_size'] = self.retail_metrics(product_id, geo)['local_market_size']
            products[product_id]['total_market_size'] += trade['market_size']
            products[product_id]['shipped'] += trade['purchase']
            
    # Считаем, сколько товаров суммарно отгружать
    for product_id, product in products.items():
        quantity = product['quantity_at_supplier_storage']
        if quantity > product['shipped'] > 0:
            # Если на складе слишком много товара, отгружаем среднее между имеющимся 
            # количеством и вчерашний отгрузкой чтобы амортизировать колебания
            product['quantity_to_distribute'] = (product['shipped'] + quantity) // 2
        else:
            product['quantity_to_distribute'] = quantity
    
    # Считаем долю магазинов, в которых сбыли весь товар
    # чем выше данное отношение, тем больше поднимаем цену
    clearance_count = {product_id: [] for product_id in products}
    for (_, product_id), trade in trades.items():
        clearance_count[product_id].append(
                trade['stock'] == trade['purchase'] and trade['sold'] > 0)
    for product_id, product in products.items():
        count = clearance_count[product_id]
        product['clearance_rate'] = sum(count) / max(1, len(count))
    
    # Distribute sales
    print('Distributing sales')
    # Распределяем товары между магазинами
    for product_id, product in products.items():
        p_trades = {s: t for ((s, p), t) in trades.items() if p == product_id}
        # Считаем среднюю цену сбыта
        total_sold = sum(t['sold'] for t in p_trades.values())
        if total_sold > 0:
            # средняя цена
            mean_price = sum(t['price'] * t['sold'] for t in p_trades.values()) / total_sold
            log_mean_price = math.log(mean_price)
            # стандартное отклоние цены от средней
            std_dev = (sum(t['sold'] * (log(t['price'], log_mean_price) - log_mean_price)**2
                           for t in p_trades.values()) / total_sold
                      ) ** 0.5
            # наклон сигмоиды
            adjustment_rate =  MAX_SALES_ADJUSTMENT / (2**0.5 * std_dev)  # 2**0.5 is crucial here!
        else:
            mean_price = None
            adjustment_rate = MAX_SALES_ADJUSTMENT  # наклон сигмоиды
        
        # Считаем, сколько товара хотим сбывать в каждом магазине
        target = {}
        for shop_id, trade in p_trades.items():
            if trade['sold']:
                # Отталкиваемся от продаж, если таковые были
                target_sale = trade['sold']
                if trade['stock'] > trade['purchase'] and mean_price:
                    # Если имеем точное значение спроса, корректируем 
                    # пропорционально отклонению цены от средней
                    target_sale *= sigmoid(log(trade['price'], log_mean_price) - log_mean_price + 1, 
                                           adjustment_rate, MAX_SALES_ADJUSTMENT)
                elif trade['stock'] == trade['purchase']:
                    # Если распродали весь товар, амортизируем колебания
                    target_sale = (target_sale + trade['stock']) // 2
            else:
                if trade['stock'] == trade['purchase'] > 0:
                    target_sale = trade['purchase']
                else:
                    # По умолчанию, если не было продаж, распределяем пропорционально объемам рынков
                    target_sale = (product['quantity_to_distribute'] * trade['market_size'] / product['total_market_size'])
            target[shop_id] = (max(1, target_sale),
                               max(1, MIN_MARKET_SHARE * trade['market_size']),
                               max(1, MAX_MARKET_SHARE * trade['market_size'])
                               )  # цель, нижняя и верхняя граница
            
        # Найденные объемы не обязательно суммируются в кол-во товара на складе
        # Поэтому распределяем весь имеющийся товар пропорционально
        
        # Методом деления отрезка пополам ищем множитель, для которого
        # суммарное стабжение совпадает с требуемым
        def total(factor):
            return sum(int(min(max(factor * t, mint), maxt)) 
                       for (t, mint, maxt) in target.values())
        
        factor0 = 0
        factor1 = max(maxt / t for (t, mint, maxt) in target.values())
        if total(factor0) >= product['quantity_to_distribute']:
            total_min = total(factor0)
            for shop_id, trade in p_trades.items():
                t, mint, maxt = target[shop_id]
                target_sale = mint * product['quantity_to_distribute'] / total_min
                trade['target_sale'] = int(target_sale)
        elif total(factor1) <= product['quantity_to_distribute']:
            for shop_id, trade in p_trades.items():
                t, mint, maxt = target[shop_id]
                trade['target_sale'] = int(maxt)
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
            for shop_id, trade in p_trades.items():
                t, mint, maxt = target[shop_id]
                target_sale = min(max(factor * t, mint), maxt)
                trade['target_sale'] = int(target_sale)
    
    print('Managing shops')
    # Корректируем магазины
    for shop_id in shops:
        print(shop_id)
        s_trades = {p: t for ((s, p), t) in trades.items() if s == shop_id}
        
        # Снабжение
        orders = {}
        for product_id, trade in s_trades.items():
            orders[products[product_id]['offer_id']] = {
                'quantity': trade['target_sale'], 
                'max_increase': 0
                }
        self.set_supply_contracts(shop_id, orders)
        
        # Выставляем новые цены
        # Сбрасываем цены в ноль, чтобы узнать распродажные цены
        offers = {t['ids']: 0 for t in s_trades.values()}
        self.set_shop_sale_prices(shop_id, offers)
        # Устанавливаем распродажные цены
        self.set_shop_sales_prices(shop_id)
        # Считываем торговый зал
        trading_hall_sales = self.trading_hall(shop_id, cache=False)
        offers = {}
        for product_id, trade in s_trades.items():
            product = products[product_id]
            # на случай, если уже вывезли часть товара, сохраняем текущее значение
            trade['current_stock'] = trading_hall_sales[product_id]['stock']
            trade['sale_price'] = trading_hall_sales[product_id]['price']
            if trade['price'] > 0:
                new_price = trade['price']
                target = min(trade['target_sale'], trade['current_stock'] * TARGET_STOCK_RATIO)
                if target > 0:
                    if trade['stock'] == trade['purchase'] and trade['sold'] > 0:
                        # если распродан весь товар, повышаем цену
                        clearance_factor = 0.4 + 9.6 * product['clearance_rate']**1.5
                        if target < trade['sold']:
                            stock_factor = 1 + 2/math.pi * math.atan(math.pi/2 * (trade['sold'] / target - 1) / ELASTICITY)
                        else:
                            stock_factor = 1
                        total_inc = MAX_PRICE_ADJUSTMENT * stock_factor * clearance_factor
                        new_price *= 1 + total_inc
                    elif trade['stock'] > trade['purchase']:
                        if trade['sold'] == 0:
                            # снижаем цену быстрее, если ничего не продано
                            discount_factor = 2
                        else:
                            discount_factor = 1
                        # корректируем под требуемый объем продаж
                        new_price *= sigmoid(trade['sold'] / target, 1 / ELASTICITY, 
                                             discount_factor * MAX_PRICE_ADJUSTMENT)
                # Следим, чтобы цена не опускалась ниже распродажной
                if new_price < trade['sale_price']:
                    new_price = trade['sale_price']
            else:  # trade['price'] == 0
                # Цена по умолчанию для новых продуктов
                new_price = SALES_PRICE_FACTOR * trade['sale_price']
            offers[trade['ids']] = round(new_price, 2)
        self.set_shop_sale_prices(shop_id, offers)
        
        # Вывозим излишки товара обратно на склад
        for product_id, trade in s_trades.items():
            # Оставляем двухдневный запас или максимальную долю рынка 
            # (немного больше, чтобы избежать частых распродаж)
            if trade['sold'] > 0:
                # сглаживаем между днями
                need = trade['target_sale'] + trade['sold']
            else:
                need = 2 * trade['target_sale']
            need = min(need, MAX_MARKET_SHARE_STOCK * trade['market_size'])
            # лишнее вывозим
            if trade['current_stock'] > need:
                self.product_move_to_warehouse(shop_id, product_id, 
                                               products[product_id]['supplier_id'], 
                                               trade['current_stock'] - need)


def split_shop(self, shop_id, categories=None):
    if not categories:
        categories = ['Продукты питания']
    # только контракты на вывозимые товары
    supply_contracts = self.supply_contracts(shop_id)(shop_goods_category_name=categories)
    if not supply_contracts:
        print('No department(s) %s' % categories)
        return
    shop = self.unit_summary(shop_id)
    if shop['section_count'] <= 1:
        print('One or no department, nothing to split')
        return
    # Город, район, размер и имя копируем из старого магазина
    new_shop_id = self.create_unit('Магазин', shop['district_name'], '100 кв. м', 
                                   shop['name'], city=shop['city_id'])
    self.resize_unit(new_shop_id, size=shop['size'])
    self.set_advertisement(new_shop_id, target_fame=shop['fame'])
    warehouses = {}  # склады для вывоза продукции
    for contract in supply_contracts.values():
        # копируем контракты в новый магазин
        self.create_supply_contract(new_shop_id, contract['offer_id'], 
                                    amount=contract['party_quantity'], max_increase=0)
        # Запоминаем, куда вывозить продукцию из старого магазина
        warehouses[contract['product_id']] = contract['supplier_id']
    # Разорвать контракты в старом магазине
    self.destroy_supply_contract(shop_id, list(supply_contracts.keys()))
    goods = list(self.goods(product_category_name=categories).keys())  # id всех товаров вывозимых категорий
    trading_hall = self.trading_hall(shop_id)(product_id=goods)  # отделы торгового зала, которые перевощим
    # Вывоз продукции на склад
    for product_id, trade in trading_hall.items():
        if product_id in warehouses:
            self.product_move_to_warehouse(shop_id, product_id, warehouses[product_id], trade['stock'])
    # Ликвидировать остатки товара
    ids = [trade['ids'] for trade in trading_hall.values()]
    self.product_terminate(shop_id, ids)
    # Копируем цены
    new_trading_hall = self.trading_hall(new_shop_id)
    offers = {t['ids']: trading_hall[p]['price'] for (p, t) in new_trading_hall.items()}
    self.set_shop_sale_prices(new_shop_id, offers)
    # Refresh shops info
    self.unit_summary(shop_id, refresh=True)
    self.unit_summary(new_shop_id, refresh=True)
    # Инновации
    self.set_shop_innovations(shop_id, refresh=True)
    self.set_shop_innovations(new_shop_id)
    # Меньше отделделов - больше посетителей
    self.set_shop_advertisement(shop_id, innovation=True)
    return new_shop_id