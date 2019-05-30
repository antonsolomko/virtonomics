def autorepair_equipment(self):
    from .const import EQUIPMENT_SUPPLIERS 
    for offer_id, unit_class in EQUIPMENT_SUPPLIERS.items():
        units = [u['id'] for u in self.units(unit_class_kind=unit_class).values()]
        self.repair_equipment_all(offer_id, units)