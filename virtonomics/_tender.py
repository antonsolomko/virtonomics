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
            tender['estimated_real_date'] = datetime.strptime(
                day_data['estimated_real_date'], "%Y-%m-%d").date()
            tender['knowledge_area_kind'] = tender['knowledge']['kind']
            result[tender['tender_id']] = tender
    return Dict(result)


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
    for tender_id, tender in self.tenders.items():
        if tender['league'] == 3 or self.knowledge[tender['knowledge']['kind']] <= 30:
            self.tender_register(tender_id)