MANAGED_SHOPS_NAMES = ('*****', '****')
TARGET_CUSTOMERS = 1620000
REFERENCE_SHOP_ID = 7559926
MIN_MARKET_SHARE = 0.005  # минимальная доля рынка
MAX_MARKET_SHARE = 0.4  # максимальная доля рынка
MAX_MARKET_SHARE_STOCK = 0.8  # максимальный запас относительно рынка
MAX_SALES_ADJUSTMENT = 0.1  # максимальных шаг изменения продаж
MAX_PRICE_ADJUSTMENT = 0.02  # максимальных шаг изменения цены
ELASTICITY = 40  # эластичность спроса
SALES_PRICE_FACTOR = 2  # множитель к распродажной цене для новых товаров 
TARGET_STOCK_RATIO = 0.8  # 

ECO_FACTORS = (
    'Промышленный и бытовой мусор',
    'Загрязнение автотранспортом',
    'Промышленные стоки',
    'Выбросы электростанций'
    )

INDUSTRIAL_CITIES = ['Борисполь',]  # managed differently from other cities

SUPPORTED_PARTIES = [
    'Украинская партия',
    'Партия Власти',
    #'"Фронт национального освобождения имени Фарабундо Марти"',
    ]

unit_seasons = {
    7429138: {5: 'Зерно',
              6: 'Сахар',
              7: 'Сахар',
              8: 'Сахар',
              9: 'Кукуруза',
              10: 'Кукуруза',
              11: 'Помидоры',
             },
    7549945: {8: 'Апельсины',
              9: 'Апельсины',
              10: 'Оливки',
              11: 'Оливки',
             },
    }

EQUIPMENT_SUPPLIERS = {
    8415404: 'office',
    6715974: ('workshop', 'mill'),
    3329984: ('farm', 'orchard'),
    8395882: 'educational',
    4974307: 'lab',
    8197411: 'restaurant',
    8535772: 'repair',
    8206859: 'medicine',
    }

MAX_TECHNOLOGIES = {
    'animalfarm': 30, 
    'farm': 25, 
    'mill': 32, 
    'mine': 23, 
    'orchard': 25, 
    'sawmill': 32,
    'workshop': 32,
    'power': 22,
    }

TENDER_ACTIVE_PLAYERS = [5526168, 6451449][:1]