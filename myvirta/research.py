def set_technologies(self):
    print('UPDATE TECHNOLOGIES')
    types = {
        'animalfarm': 27, 
        'farm': 23, 
        'mill': 30, 
        'mine': 23, 
        'orchard': 23, 
        'sawmill': 30,
        'workshop': 30}
    for unit_id in self.units(unit_class_kind=list(types.keys())):
        unit = self.unit_summary(unit_id, refresh=True)
        level = unit.get('technology_level')
        if level:
            available_levels = self.investigated_technologies.get(
                                   unit['unit_type_id'], [0])
            top_level = types[unit['unit_class_kind']]
            max_level = max(v for v in available_levels if v <= top_level)
            if max_level > level:
                print(unit['id'], unit['name'], level, '->', max_level)
                self.set_technology(unit_id, max_level)


@staticmethod
def lab_quality_required(level):
    return 0.0106 * level**2 + 1.4468 * level - 1.6955 + 0.1


def manage_research(self):
    print('\nRESEARCH')
    labs = {lab_id: self.unit_summary(lab_id) for lab_id in self.units(unit_class_kind='lab')}
    free_labs = []
    current_research = {}
    experimental_units = [unit_id for unit_id, unit in self.units.items() 
                          if 365385 in self.indicators.get(unit_id, {})]
    for lab_id, lab in labs.items():
        lab = self.unit_summary(lab_id)
        unittype_id = lab['project'].get('unit_type_id', 0)
        level = lab['project'].get('level_developing', 0)
        stage = lab['project'].get('current_step', 0)
        if (stage == 0 or level in 
                self.investigated_technologies.get(unittype_id, [])):
            free_labs.append(lab_id)
        else:
            if stage == 1 and lab['project']['hepotesis']:
                stage = 1.5
            elif stage == 3 and not lab['project']['project_unit_id']:
                stage = 2.5
            
            if unittype_id not in current_research:
                current_research[unittype_id] = {}
            if level not in current_research[unittype_id]:
                current_research[unittype_id][level] = {}
            current_research[unittype_id][level][lab_id] = stage
            
            time_left = lab['project']['current_step_time_left']
            if stage == 1 and time_left < 3:
                print(lab_id, self.unittypes[unittype_id]['name'], '1..2')
                self.set_innovation(lab_id, 'lab2', refresh=True)
            elif stage == 3 and time_left < 2:
                self.rename_unit(lab_id, '-'+self.unittypes[unittype_id]['name'])
            
            if (stage == 3 and lab['project']['project_unit_loading'] is not None
                    and lab['project']['project_unit_loading'] < 100):
                print(lab_id, self.unittypes[unittype_id]['name'])
                print(' ! модификатор скорости испытаний < 100%')
    
    for unittype_id, levels in current_research.items():
        for level, lab_stages in levels.items():
            if any(stage > 2 for stage in lab_stages.values()):
                # select single laboratory to carry on research and filter 
                # out redundant labs
                key = lambda lab_id: (
                         lab_stages[lab_id] <= 2,
                         labs[lab_id]['project']['current_step_time_left'],
                         labs[lab_id]['equipment_count'],
                         labs[lab_id]['equipment_quality']
                         )
                lab_id = min(lab_stages, key=key)
                
                # Mark remaining laboratories as free
                for l_id in lab_stages:
                    if l_id != lab_id:
                        free_labs.append(l_id)
                
                stage = lab_stages[lab_id]
                levels[level] = {lab_id: stage}

                if stage == 2.5:
                    # Set experimental unit
                    lab = labs[lab_id]
                    self.set_innovation(lab_id, 'lab3', refresh=True)
                    print(lab['id'], self.unittypes[unittype_id]['name'], 
                          '%s.3' % level)
                    min_size = lab['project'][
                                   'workshop_produce_bound_level_required']
                    exp_unit = self.choose_experimental_unit(
                                   unittype_id, min_size, level-1)
                    if exp_unit:
                        print(' ->', exp_unit['id'], exp_unit['name'])
                        self.set_experemental_unit(lab_id, exp_unit['id'])
                        self.holiday_unset(exp_unit['id'])
                        experimental_units.append(exp_unit['id'])
                    else:
                        print(' No experimental units available of size',
                              min_size, 'and technology level', level-1)
            else:
                num = len(lab_stages)
                for lab_id, stage in lab_stages.items():
                    if stage == 1.5:
                        # Select hypotesis
                        #self.set_innovation(lab_id, 'lab2')
                        labs[lab_id] = self.unit_summary(lab_id, refresh=1)
                        lab = labs[lab_id]
                        hypoteses = lab['project']['hepotesis']
                        hypotesis = self.choose_hypothesis(hypoteses, num)
                        print(lab['id'], 
                              self.unittypes[unittype_id]['name'],
                              '%s.2' % level, '(%d)' % num,
                              '\n ->', 
                              '%s%%' % hypotesis['success_probabilities'],
                              '%.2f days' % hypotesis['expected_time'])
                        self.select_hypotesis(lab_id, hypotesis['id'])
    
    # New research
    new_research = {}
    for unittype_id in self.unittypes(need_technology=True):
        if self.unittypes[unittype_id]['kind'] in ['mine', 'farm', 
                'orchard', 'fishingbase', 'sawmill']:
            continue
        for level in self.researchable_technologies(unittype_id):
            if not current_research.get(unittype_id, {}).get(level, []):
                if level not in new_research:
                    new_research[level] = []
                new_research[level].append(unittype_id)
    
    free_labs0 = [lab_id for lab_id in free_labs
                 if labs[lab_id]['city_id'] == 310400]

    print(len(free_labs0), 'free laboratories:')
    
    eq_key = lambda i: (labs[i]['equipment_count'],
                        labs[i]['equipment_quality'])
    for i in sorted(free_labs0, key=eq_key):
        if labs[i]['equipment_count'] > 0:
            print(i, labs[i]['equipment_count'],
                  '%.2f' % labs[i]['equipment_quality'])
    
    for level, unittypes in sorted(new_research.items()):
        if level <= 13: num = 6  # 100
        elif level <= 19: num = 5  # 300
        elif level <= 25: num = 4  # 700
        elif level <= 27: num = 3  # 850
        elif level <= 31: num = 2  # 1000
        else: num = 1  # 1000
        for unittype_id in unittypes:
            # Choose free laboratory satisfying minimal requirements
            print('+', self.unittypes[unittype_id]['name'], level, 
                  '(%d)' % num)
            num_required = self.lab_employees_required(level)
            qual_required = self.lab_quality_required(level)
            for i in range(num):
                candidate_labs = [i for i in free_labs0
                    if labs[i]['equipment_count'] >= 10*num_required
                    and labs[i]['equipment_quality'] >= qual_required]
                #if not candidate_labs:
                #    candidate_labs = [i for i in free_labs0
                #        if labs[i]['equipment_count'] >= 10*num_required]
                if candidate_labs:
                    lab_id = min(candidate_labs, key=eq_key)
                    self.start_research_project(lab_id, unittype_id, level)
                    self.holiday_unset(lab_id)
                    self.set_employees(lab_id, quantity=num_required, 
                                       trigger=2)
                    self.rename_unit(lab_id, 
                                     self.unittypes[unittype_id]['name'])
                    self.set_innovation(lab_id, 'lab1', refresh=True)
                    free_labs0.remove(lab_id)
                    free_labs.remove(lab_id)
                    print(' ->', lab_id,
                          '(%d %.2f)' % (num_required, qual_required))
                else:
                    print(' -> ???')
    
    print(len(free_labs0), 'free laboratories')
    
    for lab_id in free_labs:
        self.rename_unit(lab_id, '-')
        self.holiday_set(lab_id)
    
    for lab_id in labs:
        self.set_innovation(lab_id, 'lab_equipment')
        
    self.set_technologies()
    
    print('SEND ON HOLIDAY')
    nonexperimental_units = {unit_id: unit for unit_id, unit in self.units.items()
                             if unit['name'][0] == '=' 
                             and unit_id not in experimental_units
                             and not self.unit_summary(unit_id)['on_holiday']}
    for unit_id, unit in nonexperimental_units.items():
        print(unit_id, unit['name'])
        self.holiday_set(unit_id)
        
    return current_research