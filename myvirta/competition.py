import json
import pandas
import sys
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

sys.path.append('./virtonomics')
from jsondecoder import Decoder


def load_shagreen_data(shagreen_id, day):
    try:
        with open(f'./olla/shagren{shagreen_id}-{day}.json', 'r') as file:
            return json.load(file, cls=Decoder)
    except FileNotFoundError:
        return {}


def save_shagreen_data(data, shagreen_id, day):
    with open(f'./olla/shagren{shagreen_id}-{day}.json', 'w') as file:
        json.dump(data, file)


def data_by_day(data):
    result = {}
    for unit_id, unit_info in data.items():
        for day, info in unit_info.items():
            if day not in result:
                result[day] = {}
            result[day][unit_id] = info
    return result


def data_to_dataframe(data):
    result = {}
    for day, day_info in data_by_day(data).items():
        if day < 1:
            continue
        res = []
        index = []
        for unit_id, info in day_info.items():
            if unit_id:
                index.append(unit_id)
                r = {}
                for k, v in info.items():
                    if k != 'innovations':
                        r[k] = v
                    else:
                        for i in v:
                            r[i] = 1
                if 'total_revenue' in r and 'total_sold' in r:
                    r['avg_price'] = r['total_revenue'] / r['total_sold']
                res.append(r)
        df = pandas.DataFrame(res, index)
        if not df.empty:
            df.sort_values('total_revenue', ascending=False, inplace=True)
        result[day] = df
    return result


def history_to_dataframe(data):
    history = {}
    for i, d in data.items():
        k = next(iter(d.values())).get('company', i)
        history[k] = pandas.DataFrame(d.values(), d.keys())
    return history


def clean_data(data):
    result = {}
    for u, unit_info in data.items():
        result[u] = {}
        for d, info in unit_info.items():
            if 'price' in info:
                result[u][d] = info
    return result


def read_shagreen_data(self, save=False):
    def read_unit_data(unit_id):
        result = {}
        url = self.domain_ext + 'unit/view/%d' % unit_id
        page = self.session.tree(url)
        
        if page.xpath('//h1[contains(.,"404")]'):
            return None
        
        xp = '//img[contains(@src,"artefact")]/@title'
        innovations = page.xpath(xp)
        result['innovations'] = list(map(str, innovations))
        xp = '//td[.="%s"]/../td[2]/text()'
        fields = [
            ('district', 'Расположение магазина', str),
            ('size', 'Торговая площадь', int),
            ('departments', 'Количество отделов', int),
            ('fame', 'Известность', float),
            ('visitors', 'Количество посетителей', str),
            ('service', 'Уровень сервиса', str),
        ]
        for key, name, typ in fields:
            values = page.xpath(xp % name)
            if values:
                value = values[0]
                if typ != str:
                    value = value.replace(' ', '')
                if key == 'size':
                    value = value.replace('м', '')
                if key == 'district':
                    value = value.replace(',', '').strip()
                result[key] = typ(value)
        xp = '//img[@alt="Шагрень"]/../../td[5]/text()'
        price = page.xpath(xp)
        if price:
            price = price[0].replace(' ', '').replace('$', '')
            if price != 'неизв.':
                result['price'] = float(price)
        return result
    
    def read_self_unit_data(unit_id):
        result = {}
        unit_summary = self.unit_summary(unit_id)
        result['company'] = self.company['name']
        result['district'] = unit_summary['district_name']
        result['size'] = unit_summary['square']
        result['departments'] = unit_summary['section_count']
        result['fame'] = round(unit_summary['fame'] * 100, 2)
        result['visitors'] = unit_summary['customers_count']
        url = self.domain_ext + 'unit/view/%d' % unit_id
        page = self.session.tree(url)
        xp = '//img[contains(@src,"pub/artefact")]/@title'
        innovations = page.xpath(xp)
        result['innovations'] = list(map(str, innovations))
        url = self.domain_ext + 'unit/view/%d/product_history/423040/' % unit_id
        page = self.session.tree(url)
        xp = '//tr/td[4]/text()'
        result['price'] = float(page.xpath(xp)[0])
        return result
    
    
    days_left = self.oligarch_competition_days_left
    if days_left is None:
        return None
    day = 7 - days_left + 1
    shagreen_id = self.shagreen_id
    today_data = load_shagreen_data(shagreen_id, day)
    if today_data:
        data = today_data
    else:
        data = load_shagreen_data(shagreen_id, day-1)
        
        if 0 not in data:
            data[0] = {}
            
        url = self.domain_ext + 'olla/%d' % shagreen_id
        page = self.session.tree(url)
        xp = ('//div[@id="mainContent"]//img[contains(@src,"flags")]' +
              '/following-sibling::b/text()')
        city_name = page.xpath(xp)[0]
        local_market_info = self.retail_history(423040, city_name=city_name)[-1]
        data[0][day] = local_market_info
        
        xp = '//a[contains(@href, "unit/view/")]/..'
        cells = page.xpath(xp)
        units = []
        for cell in cells:
            total_revenue = float(cell.xpath('./text()')[0].strip().replace(' ', '').replace('$', ''))
            unit_id = int(cell.xpath('./a/@href')[0].split('/')[-1])
            units.append(unit_id)
            user = str(cell.xpath('./../td[2]//a/text()')[0])
            company = cell.xpath('./../td[3]//a/text()')
            if unit_id not in data:
                data[unit_id] = {}
            if day not in data[unit_id]:
                data[unit_id][day] = {}
                data[unit_id][day]['total_revenue'] = total_revenue
                data[unit_id][day]['user'] = user
                if company:
                    data[unit_id][day]['company'] = str(company[0])
        
        for unit_id in units:
            print(unit_id)
            if unit_id in self.units():
                unit_data = read_self_unit_data(unit_id)
            else:
                unit_data = read_unit_data(unit_id)
                if not unit_data:
                    unit_data = today_data.get(unit_id, {}).get(day, {})
            data[unit_id][day] = {**data[unit_id][day], **unit_data}
            revenue = data[unit_id][day]['total_revenue']
            if day-1 in data[unit_id]:
                revenue -= data[unit_id][day-1]['total_revenue']
            data[unit_id][day]['revenue'] = revenue
            if 'price' in unit_data:
                data[unit_id][day]['sold'] = round(revenue / data[unit_id][day]['price'])
                total_sold = data[unit_id][day]['sold']
                if day-1 in data[unit_id] and 'total_sold' in data[unit_id][day-1]:
                    total_sold += data[unit_id][day-1]['total_sold']
                data[unit_id][day]['total_sold'] = total_sold
        
        if save and data:
            save_shagreen_data(data, shagreen_id, day)
        
    return data


def compute_elasticity(data, unit_id):
    coords = [(d['price'], d['sold']) for u, d in data.items()
              if abs(d['fame'] - data[unit_id]['fame']) < 20
                 and abs(d['price']/data[unit_id]['price'] - 1) < 0.16]
    X0 = np.array([c[0] for c in coords]).reshape([-1,1]) - data[unit_id]['price']
    Y0 = np.array([c[1] for c in coords]).reshape([-1,1]) - data[unit_id]['sold']
    plt.scatter(X0, Y0, color='red')
    X, Y = X0, Y0
    coefs = []
    while len(X) > 1:
        W = np.sqrt(np.abs(X.flatten()))
        reg = LinearRegression(fit_intercept=False).fit(X, Y, sample_weight=W)
        coefs.append(float(reg.coef_))
        Y_pred = reg.predict(X)
        plt.plot(X0, reg.predict(X0), alpha=0.05, color='grey')
        i = np.argmax(np.abs(Y - Y_pred))
        X = np.delete(X, i).reshape([-1,1])
        Y = np.delete(Y, i).reshape([-1,1])
    coefs = np.array(coefs)
    mean = np.mean(coefs)
    std = np.std(coefs)
    coef = np.mean(coefs[abs(coefs - mean) < std])
    plt.plot(X0, X0 * coef, color='blue')
    plt.show()
    print(coef)
    intercept = data[unit_id]['sold'] - coef * data[unit_id]['price']
    return coef, intercept