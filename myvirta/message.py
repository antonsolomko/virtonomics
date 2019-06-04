def read_messages(self):
    ukr_cities = [city['city_name'] for city in self.cities(country_name='Украина').values()]
    messages = [message_id for message_id, title in self.messages.items()
                if title == 'Поставка продукта прекращена'
                or title == 'Увеличена цена на продукт'
                or title == 'Поставщик ограничил объём поставок'
                or title == 'Товар не отгружен из-за низкого качества'
                or title == 'Товар не получен из-за низкого качества'
                #or 'Внедрение технологии на предприятие' in title
                or 'губернатора' in title and 'Украина' not in title
                or 'главы государства' in title and 'Украина' not in title
                or 'мэра' in title and not any(name in title for name in ukr_cities)
                or 'выбран' in title
                or 'ставки налога на прибыль' in title
                or 'повышение энерготарифов' in title
                or 'Новое достижение' in title
                ]
    self.mark_messages_as(messages)