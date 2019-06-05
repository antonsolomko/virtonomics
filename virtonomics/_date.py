import datetime

def str_to_date(date_str):
    months = {
        'января': 1,
        'февраля': 2,
        'марта': 3,
        'апреля': 4,
        'мая': 5,
        'июня': 6,
        'июля': 7,
        'августа': 8,
        'сентября': 9,
        'октября': 10,
        'ноября': 11,
        'декабря': 12
        }
    day, month, year, *_ = date_str.split()
    day = int(day)
    month = months[month]
    year = int(year)
    return datetime.date(year, month, day)


def date_to_str(date):
    months = ('', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
              'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря')
    return '%d %s %d' % (date.day, months[date.month], date.year)


def get_server_date(self):
    url = self.domain_ext + 'company/rank/%s/info' % self.company['id']
    xp = '//div[@title="Время на сервере"]/text()'
    date_str = self.session.tree(url).xpath(xp)[0].strip()
    self.server_date = str_to_date(date_str)
    return self.server_date


def get_days_to_refresh(self):
    refresh_date = datetime.date(self.server_date.year, 9, 30)
    if refresh_date < self.server_date:
        refresh_date = refresh_date.replace(year=refresh_date.year + 1)
    days_left = (refresh_date - self.server_date).days
    self.days_to_refresh = days_left // 7
    return self.days_to_refresh


def get_oligarch_competition_days_left(self):
    url = self.domain_ext + 'olla'
    page = self.session.tree(url)
    xp = '//td[contains(.,"Осталось пересчётов: ")]/text()'
    days = page.xpath(xp)
    self.oligarch_competition_days_left = int(
        days[0].split('Осталось пересчётов: ')[1].split('\n')[0]) if days else None
    return self.oligarch_competition_days_left