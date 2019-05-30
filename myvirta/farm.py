def farm_seasons(self):
    from .const import unit_seasons
    for unit_id, seasons in unit_seasons.items():
        self.farm_season(unit_id, seasons)