import json
import pandas


def read_shagreen_data(self, df=False):
    def load_data(shagreen_id):
        try:
            with open(f'./olla/shagren{shagreen_id}.json', 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}
        return data
    
    def save_data(data, shagreen_id):
        with open(f'./olla/shagren{shagreen_id}.json', 'w') as file:
            json.dump(data, file)
    
    def read_unit_data(unit_id):
        result = {}
        url = self.domain_ext + 'unit/view/%d' % unit_id
        page = self.session.tree(url)
        xp = '//a[contains(@href,"user/view")]/text()'
        result['user'] = str(page.xpath(xp)[1])
        xp = '//a[contains(@href,"company/view/")]/text()'
        result['company'] = str(page.xpath(xp)[-1])
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
        result['price'] = float(page.xpath(xp)[0].replace(' ', '').replace('$', ''))
        return result
    
    def to_dataframe(data):
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
            result.append(res)
        return pandas.DataFrame(result, index).sort_values('total_revenue', ascending=False)
            
    days_left = self.oligarch_competition_days_left
    if days_left is None:
        return
    
    url = self.domain_ext + 'olla'
    page = self.session.tree(url)
    xp = '//a[contains(.,"Шагрень")]/@href'
    url = page.xpath(xp)[0]
    shagreen_id = int(url.split('/')[-1])
    
    data = load_data(shagreen_id)
    day = 7 - days_left + 1
    
    page = self.session.tree(url)
    xp = '//a[contains(@href, "unit/view/")]/..'
    cells = page.xpath(xp)
    units = []
    for cell in cells:
        total_revenue = float(cell.xpath('./text()')[0].strip().replace(' ', '').replace('$', ''))
        unit_id = int(cell.xpath('./a/@href')[0].split('/')[-1])
        units.append(unit_id)
        if unit_id not in data:
            data[unit_id] = {}
            data[unit_id][day] = {}
            data[unit_id][day]['total_revenue'] = total_revenue
    
    for unit_id in units:
        if unit_id in self.units():
            continue
        unit_data = read_unit_data(unit_id)
        data[unit_id][day] = {**data[unit_id][day], **unit_data}
        revenue = data[unit_id][day]['total_revenue']
        if day-1 in data[unit_id]:
            revenue -= data[unit_id][day]['total_revenue']
        data[unit_id][day]['revenue'] = revenue
        data[unit_id][day]['sold'] = round(revenue / data[unit_id][day]['price'])
        total_sold = data[unit_id][day]['sold']
        if day-1 in data[unit_id]:
            total_sold += data[unit_id][day]['total_sold']
        data[unit_id][day]['total_sold'] = total_sold
    
    save_data(data, shagreen_id)
    
    if df:
        data = to_dataframe(data)
        
    return data