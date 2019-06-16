def set_max_employee_level_all(self, kinds=None):
        print('Setting max employees level for %s' % kinds)
        if not kinds:
            kinds = ['educational', 'service_light', 'restaurant', 'repair']
        for unit_id in self.units(unit_class_kind=kinds):
            self.set_max_employee_level(unit_id)