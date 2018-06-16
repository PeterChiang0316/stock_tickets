# -*- coding: utf-8 -*-
import time, datetime, collections
from tools.stock_price_utility import Stock
from multiprocessing import Pool, Lock
import argparse

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
        return int("%02d%02d%02d" % (after.hour, after.minute, after.second))
        
    def get_element_list(l, attr):
        return [e[attr] for e in l]
        
    def time_diff(t1, t2):
        t1 = datetime.datetime(2018, 5, 25, t1/10000, (t1/100) % 100, t1 % 100)
        t2 = datetime.datetime(2018, 5, 25, t2/10000, (t2/100) % 100, t2 % 100)
        return (t2 - t1).total_seconds()
        
    ship = Stock(stock)
    
    info = ship.get_daily_info('20180525', every_transaction=True)
    details = info.data
    
    trace = collections.OrderedDict()
    
    for k, v in details.items():
        trace[int(k)] = v
    
    tick_begin = trace.keys()[0]
    
    for tick, data in trace.items():
        
        if tick < tick_begin:
            continue
            
        price = data.deal
        target_price = price * 1.015

        next_tick = tick_after_minutes(tick, minutes)
        ticks = collections.OrderedDict()
        
        for interval_tick, interval_data in trace.items():
            if tick <= interval_tick and interval_tick <= next_tick:
                ticks[interval_tick] = interval_data

        max_value = max(get_element_list(ticks.values(), 'deal'))
        if max_value > target_price:
            tick_begin = next_tick
        else:
            continue
        
        #print ticks.items()
        
        buy_price = max_value * 0.99
        
        high_number, low_number = 0, 0
        
        items = ticks.items()
        
        for idx, element in enumerate(items):
        
            interval_tick, interval_data = element
            
            if interval_data.deal >= buy_price:
                break
                
            if interval_data.deal >= interval_data.sell:
                high_number += interval_data.count
            else:
                low_number += interval_data.count    
                
        print time_diff(tick, interval_tick), high_number, low_number, (high_number / (high_number+low_number)), price, max_value, buy_price, items[idx-1][1].deal 
        
        #print tick, , data.buy, data.sell, data.count, data.diff
        
    
if __name__ == '__main__':
    '''
    Algorithm:
        1. Scan through the next N minute, find the max deal price
        2. Get the tick match the max deal price and check if it rise up over the threshold
            if no: continue
            else:
                Find the earliest tick that we can buy and earn 1%
                Calculate the accumalated number since the initial tick
                Then we can know the 
    '''   
    stock_list = ['2454', '2439', '2330', '2455', '2448', '2377', '3035',\
                  '2456', '2313', '5269', '2383', '1312', '2353', '1707',\
                  '3443', '4906']
    
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--update', help='Get today\'s data', action='store_true')    
    args = parser.parse_args()
    
    if args.update:
        for s in stock_list:
            ship = Stock(s)
            ship.update_daily_info()
        exit(0)
    
    for s in stock_list[:]:   
        print s
        stock_win_point_test(s, minutes=5)  
    
    
    
    
    
            