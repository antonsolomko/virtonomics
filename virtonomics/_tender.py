from .types import Dict
from .jsondecoder import Decoder
from datetime import datetime


@property
def tenders(self):
    url = self.api['tender'] + '/browse'
    data = self.session.get(url).json(cls=Decoder)
    result = {}
    for day_data in data:
        for tender in day_data['tenders']:
            print(tender['tender_id'])
            tender['estimated_real_date'] = datetime.strptime(
                day_data['estimated_real_date'], "%Y-%m-%d").date()
            result[tender['tender_id']] = tender
    return result


def tender_register(self, tender_id):
    """Подать заявку на участие в тендере"""
    
    url = self.api['tender'] + '/reg?ajax=1&app=adapter_vrt'
    data = {
        'user_id': self.company['president_user_id'],
        'id': tender_id,
        'token': self.token,
        }
    return self.session.post(url, data=data)


def tender_register_all(self):
    for tender_id in self.tenders:
        self.tender_register(tender_id)