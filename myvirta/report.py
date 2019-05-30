import matplotlib.pyplot as plt


def generate_retail_reports(self):
    data = {}
    for rec in self.db.execute('SELECT * FROM product_date_report').fetchall():
        if rec['name'] not in data:
            data[rec['name']] = {'date': [], 'price': [], 'sold': [], 'revenue': []}
        data[rec['name']]['date'].append(rec['date'])
        data[rec['name']]['price'].append(rec['price'])
        data[rec['name']]['sold'].append(rec['sold'])
        data[rec['name']]['revenue'].append(rec['revenue']/10**9)
    
    for product in data:
        date = data[product]['date']
        price = data[product]['price']
        quantity = data[product]['sold']
        revenue = data[product]['revenue']
        
        fig, ax1 = plt.subplots(figsize=(20,10))
        color = 'tab:orange'
        ax1.set_title(product)
        ax1.set_ylabel('Revenue, $1B', color=color)
        ax1.set_xticklabels(date, rotation=90)
        ax1.fill_between(date, 0, revenue, color=color, alpha=0.5)
        ax1.set_ylim(ymin=0)
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.set_title(product)
        
        ax3 = ax1.twinx()
        color = 'tab:blue'
        ax3.set_ylabel('Price, $', color=color)
        ax3.plot(date, price, color=color, linewidth=3)
        ax3.set_ylim(ymin=0)
        ax3.tick_params(axis='y', labelcolor=color)
        
        ax2 = ax1.twinx()
        color = 'tab:red'
        ax2.set_ylabel('Sold', color=color)
        ax2.plot(date, quantity, color=color, linewidth=3)
        target = self.retail_target_volumes.get(product, 0)
        ax2.plot(date, [target]*len(date), color=color, linestyle=':', linewidth=2)
        plt.text(0, target*1.01, 'Target sales: {:,}'.format(target).replace(',', ' '), color=color)
        ax2.set_ylim(ymin=0)
        ax2.axes.get_yaxis().set_visible(False)
        
        plt.savefig(self.path + 'graph/%s.png' % product)