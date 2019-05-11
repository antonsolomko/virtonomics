def set_employees(self, unit_id, quantity=0, salary=0, salary_max=0,
                  target_level=0, trigger=0):
    """Set employees characteristics for a given unit.
    
    Arguments:
        unit_id (int): Unit id.
        quantity (int): Number of emloyees. Defaults to 0.
        salary (float): Salary. Defaults to 0 (leave unchanged).
        salary_max (float): Salaryupper bound. Defaults to 0 (unchanged).
        target_level (float): Target employees qualification. Defaults to 0
            (leave unchanged).
        trigger (0, 1, 2): HR department selector. Values:
            0 - HR department is off (отдел кадров простаивает),
            1 - HR department adapts salary to targer qualification level
                (отдел кадров корректирует зарплату каждый пересчёт),
            2 - HR department adapts salary to technology requirements
                (отдел кадров подстраивается под требования технологии).
            Defaults to 0.
    
    Returns:
        POST request responce.
    """
    
    url = self.domain_ext + 'unit/employees/engage/%s' % unit_id
    data = {
        'unitEmployeesData[quantity]': quantity,
        'unitEmployeesData[salary]': salary,
        'salary_max': salary_max,
        'target_level': target_level,
        'trigger': trigger
        }
    result = self.session.post(url, data=data)
    self.refresh(unit_id)
    return result
    
    
def holiday_set(self, unit_id):
    """Send employees on holiday.
    
    Arguments:
        unit_id (int): Unit id.
    
    Returns:
        POST request responce.
    """
    
    url = self.domain_ext + 'unit/view/%s/holiday_set' % unit_id
    result = self.session.post(url)
    self.refresh(unit_id)
    return result


def holiday_unset(self, unit_id):
    """Return employees from holiday.
    
    Arguments:
        unit_id (int): Unit id.
    
    Returns:
        POST request responce.
    """
    
    url = self.domain_ext + 'unit/view/%s/holiday_unset' % unit_id
    result = self.session.post(url)
    self.refresh(unit_id)
    return result