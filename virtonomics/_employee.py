import math


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


def set_max_employee_level(self, unit_id):
    """Set the maximal employee level, given the total number of employees, 
    the number of employees at the given unitt and top qualification.
    """
    
    bases = {
        'management': 2,
        'it': 2,
        'car': 5,
        'medicine': 25,
        'educational': 3,
        'restaurant': 10,
        'service': 3,
        'trade': 10,
        'mining': 200,
        'manufacture': 100,
        'power': 150,
        'animal': 15,
        'fishing': 25,
        'farming': 40,
        'research': 10
        }
    
    unit = self.unit_summary(unit_id)
    knowledge_area = unit['knowledge_area_kind']
    if knowledge_area not in bases:
        return
    competence = self.knowledge[knowledge_area]
    base = bases[knowledge_area]
    all_staff_base = base * competence * (competence + 3)
    load = unit['all_staff'] / all_staff_base
    if load > 1.2: 
        load = 1.2
    if load < 1 / 1.2: 
        load = 1 / 1.2
    employee_count = unit['employee_count']
    if employee_count > 0:
        employee_level = 1 + math.log(
            base * competence**2 / load**2 / employee_count, 1.4)
        employee_level = int(100 * employee_level) / 100
        print(unit_id, employee_count, employee_level)
        return self.set_employees(unit_id, quantity=employee_count, 
                                  target_level=employee_level, trigger=1,
                                  salary_max=50000)
    else:
        print(unit_id, 'auto')
        return self.set_employees(unit_id, quantity=employee_count, trigger=2,
                                  salary_max=50000)