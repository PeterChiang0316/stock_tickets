# -*- coding: utf-8 -*-
import time, datetime, collections
from tools.stock_price_utility import Stock
from tools.stock_sim import StockSim
from multiprocessing import Pool, Lock
import argparse


def magnitude_test(stock):
    ship = Stock(stock)
    magnitude = []

    for date in ship.iterate_date('20180216'):
        info = ship.get_daily_info(date)
        # print date, info
        magnitude.append((info.highest_price - info.lowest_price) / info.highest_price)

    # print 'Stock magnitude > 0.02'
    # print 'Count: %d' % sum(i > 0.02 for i in magnitude)
    # print 'Total: %d' % len(magnitude)
    # print 'percentage: %.2f' % (sum(i > 0.02 for i in magnitude) / float(len(magnitude)))
    return sum(i > 0.02 for i in magnitude / float(len(magnitude)))


def stock_win_point_test(transaction, minutes=5, verbose=True):
    def tick_after_minutes(time, minutes):
        now = datetime.datetime(2018, 5, 25, time / 10000, (time / 100) % 100, time % 100)
        after = now + datetime.timedelta(minutes=minutes)
        return int("%02d%02d%02d" % (after.hour, after.minute, after.second))

    def get_element_list(l, attr):
        return [e[attr] for e in l]

    def time_diff(t1, t2):
        t1 = datetime.datetime(2018, 5, 25, t1 / 10000, (t1 / 100) % 100, t1 % 100)
        t2 = datetime.datetime(2018, 5, 25, t2 / 10000, (t2 / 100) % 100, t2 % 100)
        return (t2 - t1).total_seconds()

    statistics = []

    trace = collections.OrderedDict()

    for k, v in transaction.items():
        trace[int(k)] = v

    if max(trace.keys()) < 130000:
        return []

    tick_begin = trace.keys()[0]

    for tick, data in trace.items():

        if tick < tick_begin:
            continue

        if tick < 91000:
            continue

        if tick > 130000:
            break

        # The price we can buy at that moment
        price = data.sell
        target_price = price * 1.015

        next_tick = tick_after_minutes(tick, minutes)
        ticks = collections.OrderedDict()

        # Gather the tick in the interval
        for interval_tick, interval_data in trace.items():
            if tick < interval_tick <= next_tick:
                ticks[interval_tick] = interval_data

        if not ticks:
            continue

        max_value = max(get_element_list(ticks.values(), 'buy'))

        if max_value < target_price:
            continue

        # Find the tick that we can buy and earn 1%
        buy_price = max_value * 0.99

        high_number, low_number, main = 0, 0, []

        items = ticks.items()

        for idx, element in enumerate(items):

            interval_tick, interval_data = element

            if interval_data.sell >= buy_price:
                break

            if interval_data.deal >= interval_data.sell:
                high_number += interval_data.count
                main.append(interval_data.count)
            else:
                low_number += interval_data.count

        win_element = items[idx - 1]
        win_tick, win_data = win_element
        win_inout_ratio = (100 * high_number / (high_number + low_number))

        if win_inout_ratio < 70:
            #print 'Ratio does not exceed threshold'
            continue
#
        main = sorted(main, reverse=True)
        main_ratio = sum(main[:3]) / sum(main)

        acc = 0
        for i in items:
            acc += i[1].count
            #print str(i), acc

        if verbose:
            print '-------- Report -----------'
            print 'Start point: %d' % tick
            print 'Win point: %d' % win_tick
            print 'Duration: %d s' % time_diff(tick, win_tick)
            print 'Sell/Buy number %d/%d' % (high_number, low_number)
            print 'InOut Ratio %.2f%%' % win_inout_ratio
            print 'Initial price %.2f' % price
            print 'Max sell price %.2f in future %d minutes' % (max_value, minutes)
            print 'Min buy price %.2f' % buy_price
            print 'Actual buy price %.2f' % win_data.sell
            print 'Main ratio %.2f' % main_ratio
            print '---------------------------'

        tick_begin = next_tick
        # print tick, , data.buy, data.sell, data.count, data.diff
        statistics.append((time_diff(tick, win_tick), high_number, win_inout_ratio, main_ratio))

    return statistics


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
    stock_list = ['2454', '2439', '2455', '2448', '2377', '3035',
                  '2456', '2313', '5269', '2383', '1312', '2353', '1707',
                  '3443', '4906']

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--update', help='Get today\'s data', action='store_true')
    args = parser.parse_args()

    if args.update:
        for s in stock_list:
            ship = Stock(s)
            ship.update_daily_info()
        exit(0)

    money = 1000000
    win_count, lose_count = 0, 0
    for s in stock_list[:]:

        ship = Stock(s)

        print 'Start test %s' % s
        for date in ship.iterate_date('20180525'):

            info = ship.get_daily_info(date, every_transaction=True)

            transaction = info.data

            if not transaction:
                continue

            print '[%s] Date: %s' % (s, date)

            win_standard = stock_win_point_test(transaction, minutes=5, verbose=True)

            if win_standard:

                print s, win_standard

                # Try to use the strict one
                win_standard = sorted(win_standard, key=lambda v: (v[1]/v[0]))
                print win_standard

                #if win_standard[-1][0] < 60 or win_standard[-1][0] > 180:
                #    print 'Interval time too short'
                #    continue

                # Percentage
                percent = max(win_standard, key=lambda v: v[2])

                sim = StockSim()
                money, wc, lc = sim.execute(money, transaction, win_standard[-1][0], win_standard[-1][1], percent[2], percent[3], verbose=True)
                win_count += wc
                lose_count += lc
                #print money


        print win_count, lose_count
    print win_count, lose_count, money