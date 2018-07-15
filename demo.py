import time
from tools.stock_price_utility import Stock
from sklearn import svm
import random

def demo():
    start_time = time.time()
    
    # For querying the stock info
    my_stock = Stock('2454')
    info = my_stock.get_daily_info('20180427')
    
    # Both attribute and hash type access can be used
    # Open price
    print 'open_price', info.open_price
    
    # Last close price
    print 'last close price', info.last_close_price
    
    # Daily magnitude (using dictionary type)
    print 'daily magnitude', info['daily_magnitude']
    
    # Daily total transaction money
    print 'daily amount', info['daily_amount']
    
    # Daily lowest price
    print 'lowest price', info['lowest_price']
    
    # Daily highest price
    print 'highest price', info['highest_price']
    
    # Detail tracsaction status
    # You can use for loop to iterate all the element
    # It will follow the timing ordering
    details = info.data
    
    print 'date\tdeal\thigh\tlow\tcount'
    for minute, data in details.items()[:5]:
        print minute, data.deal_price, data.high_price, data.low_price, data.count
        
    # Query 3 consecutive daily info
    date = '20180427'
    for _ in range(3):
        info = my_stock.get_daily_info(date)
        print date, 'open_price', info['open_price']
        date = my_stock.get_next_opening(date)

    # Query iteratively from 20180427 to today
    for date in my_stock.iterate_date('20180523', '20180605'):
        print date
    
    info = my_stock.get_daily_info('20180525', every_transaction=True)
    details = info.data
    
    for tick, data in details.items()[:5]:
        print tick, data.deal, data.buy, data.sell, data.count, data.diff

    X = [[random.uniform(0, 1), random.uniform(0, 1)] for x in range(10000)]
    y = [(x[0] * x[1]) for x in X]

    clf = svm.SVR()
    clf.fit(X, y)

    print clf.predict([[0.5, 0.7]])

    end_time = time.time()

    print 'Total time: %.2f' % (end_time - start_time)

if __name__ == '__main__':
    
    demo()