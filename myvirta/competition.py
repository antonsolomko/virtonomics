import json
import pandas
import sys
sys.path.append('./virtonomics')
from jsondecoder import Decoder


def load_shagreen_data(self, shagreen_id, day):
    try:
        with open(f'./olla/shagren{shagreen_id}-{day}.json', 'r') as file:
            data = json.load(file, cls=Decoder)
    except FileNotFoundError:
        data = {}
    return data


def save_shagreen_data(data, shagreen_id, day):
    with open(f'./olla/shagren{shagreen_id}-{day}.json', 'w') as file:
        json.dump(data, file)


def summary_to_dataframe(data, day=None):
    if not day:
        day = max(k for d in data.values() for k in d)
    result = []
    index = []
    for unit_id in data:
        if day not in data[unit_id]:
            continue
        res = {}
        index.append(unit_id)
        for k, v in data[unit_id][day].items():
            if k != 'innovations':
                res[k] = v
            else:
                for i in v:
                    res[i] = 1
        if 'total_revenue' in res and 'total_sold' in res:
            res['avg_price'] = res['total_revenue'] / res['total_sold']
        result.append(res)
    df = pandas.DataFrame(result, index)
    if not df.empty:
        df.sort_values('total_revenue', ascending=False, inplace=True)
    return df


def read_shagreen_data(self, save=False):
    def read_unit_data(unit_id):
        result = {}
        url = self.domain_ext + 'unit/view/%d' % unit_id
        page = self.session.tree(url)
        
        if page.xpath('//h1[contains(.,"404")]'):
            return self.load_shagreen_data(shagreen_id, day).get(unit_id, {}).get(day, {})
        
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
            result['price'] = float(price[0].replace(' ', '').replace('$', ''))
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
        return
    
    url = self.domain_ext + 'olla'
    page = self.session.tree(url)
    xp = '//a[contains(.,"Шагрень")]/@href'
    url = page.xpath(xp)[0]
    shagreen_id = int(url.split('/')[-1])
    day = 7 - days_left + 1
    data = self.load_shagreen_data(shagreen_id, day-1)
    
    page = self.session.tree(url)
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
        data[unit_id][day] = {**data[unit_id][day], **unit_data}
        revenue = data[unit_id][day]['total_revenue']
        if day-1 in data[unit_id]:
            revenue -= data[unit_id][day-1]['total_revenue']
        data[unit_id][day]['revenue'] = revenue
        if 'price' in unit_data:
            data[unit_id][day]['sold'] = round(revenue / data[unit_id][day]['price'])
            total_sold = data[unit_id][day]['sold']
            if day-1 in data[unit_id]:
                total_sold += data[unit_id][day-1]['total_sold']
            data[unit_id][day]['total_sold'] = total_sold
    
    if save and data:
        save_shagreen_data(data, shagreen_id, day)
    
    product_history = {}
    for i, d in data.items():
        k = next(iter(d.values())).get('company', i)
        product_history[k] = pandas.DataFrame(d.values(), d.keys())
    
    data_df = summary_to_dataframe(data, day)
        
    return data, data_df, product_history