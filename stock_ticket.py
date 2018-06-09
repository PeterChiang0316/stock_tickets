# -*- coding: utf-8 -*-
import time, datetime, collections
from tools.stock_price_utility import Stock
from multiprocessing import Pool, Lock

def magnitude_test(stock):
    
    ship = Stock(stock)
    magnitude = []
    
    for date in ship.iterate_date('20180216'):
        info = ship.get_daily_info(date)
        #print date, info
        magnitude.append((info.highest_price - info.lowest_price) / info.highest_price)
         
    #print 'Stock magnitude > 0.02'
    #print 'Count: %d' % sum(i > 0.02 for i in magnitude)
    #print 'Total: %d' % len(magnitude)
    #print 'percentage: %.2f' % (sum(i > 0.02 for i in magnitude) / float(len(magnitude)))
    return (sum(i > 0.02 for i in magnitude) / float(len(magnitude)))
    
def stock_win_point_test(stock, minutes=5):

    def tick_after_minutes(time, minutes):
        now = datetime.datetime(2018, 5, 25, time/10000, (time/100) % 100, time % 100)
        after = now + datetime.timedelta(minutes=minutes)
        return after
    
    ship = Stock(stock)
    
    info = ship.get_daily_info('20180525', every_transaction=True)
    details = info.data
    
    
    trace = collections.OrderedDict()
    
    for k, v in details.items():
        trace[int(k)] = v
    
    
    for tick, data in trace.items()[:5]:
        print tick
        print tick_after_minutes(tick, minutes)
        #print tick, data.deal, data.buy, data.sell, data.count, data.diff
        
    
if __name__ == '__main__':

    
    stock_win_point_test('2454')    
    
    stock_list = ['2454', '2439', '2330', '2455', '2448', '2377', '3035',\
                  '2456', '2313', '5269', '2383', '1312', '2353', '1707',\
                  '3443', '4906']
                  
    #for s in stock_list:
    #    ship = Stock(s)
    #    ship.update_daily_info('20180608')


            