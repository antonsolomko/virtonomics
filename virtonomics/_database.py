import sqlite3

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def open_database(self):
    self.conn = sqlite3.connect(self.path + self.db_name)
    self.db = self.conn.cursor()
    self.db.row_factory = dict_factory


def initialize_database(self):
    self.db.execute('''
        CREATE TABLE IF NOT EXISTS retail(
            date TEXT,
            unit_id INT,
            product_id INT,
            sold INT,
            purchase INT,
            stock INT,
            quality REAL, 
            brand REAL,
            cost REAL,
            price REAL,
            market_share REAL,
            avg_brand REAL,
            avg_price REAL,
            avg_quality REAL,
            ids TEXT,
            PRIMARY KEY (unit_id, product_id, date)
        )''')
    self.db.execute('''
        CREATE TABLE IF NOT EXISTS tech_offers(
        	unittype_id INT,
            level INT,
        	date TEXT,
        	tender_id INT,
        	tender_day INT,
            olc_days_left INT,
        	company_id INT,
        	price REAL,
        	impact BOOLEAN,
            mean_price REAL,
            share REAL,
        	PRIMARY KEY (unittype_id, level, date, company_id)
        )''')
    self.conn.commit()


def db_insert(self, table_name: str, data: dict):
    """Insert values from data into a table"""
    
    query = 'INSERT OR IGNORE INTO {0} ({1}) VALUES ({2})'.format(
            table_name, ', '.join(data.keys()), ', '.join('?'*len(data)))
    self.db.execute(query, list(data.values()))