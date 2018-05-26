# -*- coding: utf-8 -*-
import time
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
    
    
if __name__ == '__main__':

    #pool = Pool()
    #lock = Lock()
    #with open('data/stock_list.txt') as f:
    #    lines = f.readlines()
    #results, workers = [], []
    #for line in lines:
    #    s = line.strip()
    #    workers.append([s, pool.apply_async(magnitude_test, (s,))])
    #
    #for w in workers:
    #    lock.acquire()
    #    result = w[1].get()
    #    results.append((w[0], result))
    #    print w[0], result
    #    lock.release()
    #    
    #print 'Sorting...'
    #for r in sorted(results, key=lambda k: k[1], reverse=True):
    #    print r[0], r[1]
        
    
    stock_list = ['2454', '2439', '2330', '2455', '2448', '2377', '3035',\
                  '2456', '2313', '5269', '2383', '1312', '2353', '1707',\
                  '3443', '4906']
                  
    for s in stock_list:
        ship = Stock(s)
        ship.update_daily_info(today_date='20180525')


            