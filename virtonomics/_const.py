import os, datetime

domain = 'https://virtonomica.ru'
user = os.environ.get('VIRTA_USER')
password = os.environ.get('VIRTA_PASSWORD')
path = os.environ.get('VIRTA_DIR', os.getcwd())
db_name = 'v.db'
state_kinds = ('farm', 'fishingbase', 'mine', 'orchard', 'sawmill', 'villa')
today = (datetime.datetime.today() - datetime.timedelta(hours=1)).date()
api = {
    'cities': 
        'geo/city/browse',
    'city_rent': 
        'geo/city/rent?city_id={city_id}',
    'company': 
        'my/company',
    'company_finance': 
        'company/report/finance/byitem?id={company_id}',
    'countries': 
        'geo/country/browse',
    'goods': 
        'product/goods',
    'industries': 
        'industry/browse',
    'offers': 
        'marketing/report/trade/offers?product_id={product_id}&pagesize=1000000',
    'produce': 
        'unittype/produce?id={unittype_id}',
    'product_categories': 
        'product/categories',
    'products': 
        'product/browse',
    'refresh': 
        'unit/refresh',
    'regions': 
        'geo/region/browse',
    'retail': 
        'marketing/report/retail/metrics?product_id={product_id}&geo={geo}',
    'sale_contracts': 
        'unit/sale/contracts?id={unit_id}{product_filter}&pagesize=1000000',
    'supply_contracts': 
        'unit/supply/contracts?id={unit_id}{product_filter}&pagesize=1000000',
    'technologies': 
        'unittype/technologies',
    'token': 
        'token',
    'unit_forecast': 
        'unit/forecast?id={unit_id}',
    'unit_summary': 
        'unit/summary?id={unit_id}',
    'units': 
        'company/units?id={company_id}&pagesize=1000000',
    'unittypes': 
        'unittype/browse',
    }