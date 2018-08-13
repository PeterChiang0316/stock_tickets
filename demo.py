import time
from tools.stock_price_utility import Stock
from sklearn import svm
import random

def demo():
    start_time = time.time()
    
    # For querying the stock info
    my_stock = Stock('2454')
    info = my_stock.get_daily_info('20180525')

    # Detail tracsaction status
    # You can use for loop to iterate all the element
    # It will follow the timing ordering
    details = info.data

    print 'date\tdeal\thigh\tlow\tcount\tdiff'
    for minute, data in details.items()[:5]:
        print minute, data.deal, data.sell, data.buy, data.count, data.diff

    date = '20180427'
    info = my_stock.get_stock_finance(date)
    print info['Date'], 'open price', info['OpenPr']

    # Query 3 consecutive daily info
    date = '20180525'
    for _ in range(3):
        date = my_stock.get_next_opening(date)

    # Query iteratively from 20180427 to today
    for date in my_stock.iterate_date('20180801'):
        print date

    end_time = time.time()

    print 'Total time: %.2f' % (end_time - start_time)

if __name__ == '__main__':
    
    demo()