import time
from tools.stock_price_utility import Stock

def magnitude_test(stock):
    
    ship = Stock('2454')
    magnitude = []
    
    for date in ship.iterate_date('20180101'):
        info = ship.get_daily_info(date)
        magnitude.append((info['highest_price'] - info['lowest_price']) / info['highest_price'])
         
    print 'Stock magnitude > 0.02'
    print 'Count: %d' % sum(i > 0.02 for i in magnitude)
    print 'Total: %d' % len(magnitude)
    print 'percentage: %.2f' % (sum(i > 0.02 for i in magnitude) / float(len(magnitude)))
    
    
if __name__ == '__main__':
    magnitude_test('2454')