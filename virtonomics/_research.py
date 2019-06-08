@staticmethod
def lab_employees_required(level):
    """Number of employees needed for a given technological level"""
    
    empl = { 2: 5,    3: 10,   4: 10,   5: 15,   6: 15,   7: 15,   8: 30,
             9: 40,  10: 40,  11: 60,  12: 60,  13: 100, 14: 120, 15: 150,
            16: 200, 17: 220, 18: 250, 19: 300, 20: 400, 21: 500, 22: 600,
            23: 700, 24: 700, 25: 700, 26: 850, 27: 850, 28: 1000
           }
    return empl.get(level, 1000) if level > 1 else 0


def start_research_project(self, unit_id, unittype_id, level):
    """Start research project.
    (Начать исследование нового проекта)
    
    Arguments:
        unit_id (int): Laboratory id.
        unittype_id (int): Unit type id.
        level (int): Level to be studied.
    
    Returns:
        POST request responce.
    """
    
    url = self.domain_ext + 'unit/view/%s/project_create' % unit_id
    data = {
        'unit_type': unittype_id, 
        'level': level, 
        'create': 1
        }
    result = self.session.post(url, data=data)
    self.refresh(unit_id)
    return result


def stop_research_project(self, unit_id):
    """Stop research project.
    (Остановить проект)
    
    Arguments:
        unit_id (int): Laboratory id.
    
    Returns:
        POST request responce.
    """
    
    url = self.domain_ext + 'unit/view/%s/project_current_stop' % unit_id
    result = self.session.post(url)
    self.refresh(unit_id)
    return result


def select_hypotesis(self, unit_id, hypotesis_id):
    """Select a hypotesis to study.
    
    Arguments:
        unit_id (int): Unit id.
        hypotesis_id (int): Every hypotesis has a unique id (can be found
            in unit_summary['project']['hepotesis'] list).
    
    Returns:
        POST request responce.
    """
    
    url = self.domain_ext + 'unit/view/%s/investigation' % unit_id
    data = {
        'selectedHypotesis': hypotesis_id,
        'selectIt': 1
        }
    result = self.session.post(url, data=data)
    self.refresh(unit_id)
    return result


def set_experemental_unit(self, lab_id, exp_unit_id):
    """Set experemental unit for a given laboratory.
    
    Arguments:
        lab_id (int): Laboratory id.
        exp_unit_id (int): Experimental unit id.
    
    Returns:
        POST request responce.
    """
    
    url = self.domain_ext + 'unit/view/%s/set_experemental_unit' % lab_id
    data = {'unit': exp_unit_id}
    result = self.session.post(url, data=data)
    self.refresh(lab_id)
    return result
    

@staticmethod
def hypothesis_stydy_expected_time(success_probability, reference_time=1, 
                                   labs_num=1):
    """Expected duration of the 2nd stage of research.
    (Ожидаемое время проработки гипотезы)
    
    Assuming that several laboratories simultaniously start studing the 
    same hypotesis, computes the expected number of days until one of them
    succeeds.
    
    Arguments:
        success_probability (float): Success probability. Either percent
            [1..100] or real value (0..1).
        reference_time (int): Number of days one stage lasts. Defaults to 1
        labs_num (int): Number of laboratories studying the same level.

    Returns:
        Expected number of days needed to complete hypoteses study.
    """
    
    if success_probability >= 1:
        success_probability /= 100
    if success_probability < 0 or success_probability > 1:
        raise ValueError('Probability should be in range 0..100')
        
    expectation = 0
    attempt = 1
    fail_probability = 1
    while success_probability < 1:
        probability = 1 - (1 - success_probability)**labs_num
        expectation += attempt * probability * fail_probability
        fail_probability *= 1 - probability
        attempt += 1
        success_probability += 0.01
    expectation += attempt * fail_probability
    return expectation * reference_time


@classmethod
def choose_hypothesis(cls, hypotheses, labs_num=1):
    """Choose a hypotesis with the shortest expected study time.
    
    Arguments:
        hypotheses (list): List of available hypotheses, as represented in
            unit_summary['project']['hepotesis'] list.
        labs_num (int): Number of laboratories studying the same level.

    Returns:
        dict: The hypotesis from the hypotheses list for which the expected
            study time is the smallest.
    """
    
    expected_time = lambda h: cls.hypothesis_stydy_expected_time(
                                  h['success_probabilities'],
                                  reference_time=h['hypotesis_lengths'],
                                  labs_num=labs_num
                                  )
    hypothesis = min(hypotheses, key=expected_time)
    hypothesis['expected_time'] = expected_time(hypothesis)
    return hypothesis


def choose_experimental_unit(self, unittype_id, min_size=0, tech_level=1):
    """Choose unit of a given type satisfying minimal size and technology
    level requirements.
    
    Arguments:
        unittype_id (int): Unit type_id.
        min_size (int): Minimal size required. Defaults to 0.
        tech_level (int): Minimal technology level required. Defaults to 0.

    Returns:
        dist: Unit of the given type satisfying the restrictions.
            If several units found, the one with the highest productivity.
        None if no units satisfying the restrictions found.
    
    Todo:
        Too specific. Move to MyVirta class?
    """
    
    units = [self.unit_summary(u) for u in self.units(unit_type_id=unittype_id)]
    units = [u for u in units 
             if u['size'] >= min_size and u['technology_level'] >= tech_level]
    if units:
        return max(units, key=lambda u: u['productivity'])
    else:
        return None