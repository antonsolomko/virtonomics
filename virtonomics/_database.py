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
    self.conn.commit()