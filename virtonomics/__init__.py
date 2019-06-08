import requests
from lxml import html

# Little extension of Session interface for code conciseness.
# self.session.tree(url) will return the page tree structure,
# in which we can locate elements by xpath
requests.Session.tree = lambda self, url: html.fromstring(self.get(url).content)


class Virta:
    """Virtonomics framework.
    
    Arguments:
        server (str): Server name (e.g. 'olga', 'vera', etc.).
        user (str): Username (login). If not passed, environment variable
            VIRTA_USER is used.
        password (str): Password. If not passed,  environment variable
            VIRTA_PASSWORD is used.
        path (str): Framework directory path. If not passed, set to environment
            variable VIRTA_PATH. If VIRTA_PATH is not defined, current
            directory is used.

    Attributes:
        api (dict): Some API urls provided by the game developers.
        cities (Dict): List of cities.
        company (dict): Basic company information.
        company_finance (dict): Company finance report.
        conn (sqlite3.Connection): Database connection.
        countries (Dict): List of countries.
        days_to_refresh (int): Number of real days (virtual weeks) left until 
            macroeconomical parameters update. Equals 0 on the day before 
            the update.
        db (sqlite3.Cursor): Database cursor to perform SQL quaries.
        db_name (str): Database name.
        domain (str): Defaults to 'https://virtonomica.ru'
        domain_ext (str): '<domain>/<server>/main/'
        driver: Selenium webdriver instance. (not currently supported)
        elections (Dict): List of running elections.
        goods (Dict): List of retail products.
        indicators (dict): Units indicators (warnings).
        industries (dict): List of inductries.
        investigated_technologies (dict): To every unit type id associates the
            list of investigated levels.
        knowledge (dict): Top manager qualification.
        knowledge_areas (Dict): Knowledge areas.
        oligarch_competition_days_left (int): Days left to the and on oligarch
            competition.
        password (str): User password.
        path (str): Framework directory path.
        product_categories (dict): List of product categories.
        products (Dict): List of products.
        qualification (dict): Top manager qualification.
        regions (Dict): List of regions.
        server (str): Server name.
        server_date (datetime.date): Current virtual server date.
        session (requests.Session): Requests session. Opens automatically.
        state_kinds (tuple): State enterprises kinds.
        tenders (Dict): List of tenders. (not currently supported)
        unittypes (Dict): List of unit types.
        units (Dict): List of company units.
        user (str): Username (login).
        webdriver: Selenium webdriver class. Defaults to webdriver.Chrome.
            (not currently supported)
    
    Note:
        Attributes of type Dict and List are callable and can be filtered by 
        any fields. For example,
        v.units(unit_class_kind='farm', country_name=['Куба', 'Дания']) 
        will return all the farms located in the two specified countries.
    """
    
    from ._const import domain, user, password, path, db_name, api, state_kinds, today
    from ._init import __init__
    from ._del import __del__, quit
    from ._attributes import __getattr__
    from ._session import open_session  # 
    from ._database import (
        open_database,  # 
        initialize_database,  # 
        db_insert,  # 
        )
    from ._date import (
        get_server_date,  # 
        get_days_to_refresh,  # 
        get_oligarch_competition_days_left,  # 
        )
    from ._message import (
        messages,  # 
        mark_messages_as,  # 
        )
    from ._macro import (
        produce,  # 
        city_rent,  # 
        retail_metrics,  # 
        offers,  # 
        )
    from ._unit import (
        unit_summary,  # 
        refresh,  # 
        rename_unit,  # 
        get_unit_notice,  # 
        set_unit_notice,  # 
        set_technology,  # 
        resize_unit,  # 
        cancel_resize_unit,  # 
        set_innovation,  # 
        remove_innovation,  # 
        create_unit,  # 
        sale_unit,  # 
        cancel_sale_unit,  # 
        close_unit,  # 
        )
    from ._equipment import (
        supply_equipment,  # 
        buy_equipment,  # 
        repair_equipment,  # 
        destroy_equipment,  # 
        supply_equipment_all,  # 
        buy_equipment_all,  # 
        repair_equipment_all,  # 
        upgrade_equipment,  # 
        )
    from ._employee import (
        set_employees,  # 
        holiday_set,  # 
        holiday_unset,  # 
        set_max_employee_level,  #
        )
    from ._supply import (
        supply_contracts,  # 
        supply_products,  # 
        create_supply_contract,  # 
        destroy_supply_contract,  # 
        set_supply_contracts,  # 
        supply_contracts_to_orders,  # 
        )
    from ._sale import (
        sale_contracts,  # 
        sale_offers,  # 
        set_sale_offers,  # 
        destroy_sale_contracts,  # 
        reorder_sale_contracts,  # 
        )
    from ._shop import (
        trading_hall,  # 
        set_shop_sale_prices,  # 
        set_shop_sales_prices,  # 
        distribute_shop_employees,  # 
        product_move_to_warehouse,  # 
        product_terminate,  # 
        )
    from ._service import (
        service_history,  # 
        set_service_price,  # 
        )
    from ._advertisement import (
        set_advertisement,  # 
        stop_advertisement,  # 
        )
    from ._technology import (
        technologies,  # 
        researchable_technologies,  # 
        set_technology_offer,  # 
        destroy_technology_offers,  # 
        technology_offers,  # 
        technology_sellers_all,  # 
        technology_sellers_med,  # 
        )
    from ._research import (
        lab_employees_required,  # 
        start_research_project,  # 
        stop_research_project,  # 
        select_hypotesis,  # 
        set_experemental_unit,  # 
        hypothesis_stydy_expected_time,  # 
        choose_hypothesis,  # 
        choose_experimental_unit,  # 
        )
    from ._politics import (
        days_to_election,  # 
        city_change_council_tax,  # 
        city_money_project,  # 
        city_change_rent,  # 
        region_money_project,  # 
        country_money_project,  # 
        election_candidates,  # список кандидатов на выборах
        vote,  # проголосовать на выборах за указанного кандидата
        send_yacht_to_regatta,  # отправить яхту на регану
        )
    from ._farm import farm_season  # 
    from ._tender import (
        tenders,  # 
        tender_register,  # 
        tender_register_all,  # 
        )