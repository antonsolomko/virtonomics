def resize_warehouses(self):
    for unit_id in self.units(unit_class_kind='warehouse'):
        unit = self.unit_summary(unit_id, refresh=True)
        target_size = int(unit['size'] * unit['filling'] / 90) + 1
        print(unit_id, unit['name'], unit['size'], '->', target_size)
        self.resize_unit(unit_id, size=target_size)