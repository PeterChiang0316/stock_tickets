# -*- coding: utf-8 -*-
import time, datetime, collections
from tools.stock_price_utility import Stock
from tools.stock_sim import StockSim
from multiprocessing import Pool, Lock, Queue
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


def stock_win_point_test(s, d, transaction, minutes=5, verbose=True):
    def tick_after_minutes(t, m):
        now = datetime.datetime(2018, 5, 25, t / 10000, (t / 100) % 100, t % 100)
        after = now + datetime.timedelta(minutes=m)
        return int("%02d%02d%02d" % (after.hour, after.minute, after.second))

    def time_diff(t1, t2):
        t1 = datetime.datetime(2018, 5, 25, t1 / 10000, (t1 / 100) % 100, t1 % 100)
        t2 = datetime.datetime(2018, 5, 25, t2 / 10000, (t2 / 100) % 100, t2 % 100)
        return (t2 - t1).total_seconds()

    statistics = []

    trace = collections.OrderedDict()

    for k, v in transaction.items():
        trace[int(k)] = v

    # For work around some data lost error
    if max(trace.keys()) < 130000:
        return []

    tick_begin = trace.keys()[0]

    for tick, data in trace.items():

        # Once we buy the tickets, skip the
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

        max_value = max(ticks.values(), key=lambda v: v['buy'])['buy']

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
        win_inout_ratio = (high_number / (high_number + low_number))

        # if win_inout_ratio < 70:
        # print 'Ratio does not exceed threshold'
        #    continue

        main = sorted(main, reverse=True)
        main_ratio = sum(main[:3]) / sum(main)

        acc = 0
        for i in items:
            acc += i[1].count
            # print str(i), acc

        if verbose:
            print '-------- Report %s %s -----------' % (s, d)
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
        statistics.append([time_diff(tick, win_tick), high_number, win_inout_ratio, main_ratio])

    return statistics


def execute(s):
    ship = Stock(s)

    print 'Start test %s' % s

    win_standard_dict = {}

    for date in ship.iterate_date('20180525', '20180715'):
        print '[%s] Date: %s' % (s, date)
        info = ship.get_daily_info(date, every_transaction=True)

        transaction = info.data

        if not transaction:
            continue

        win_standards = stock_win_point_test(s, date, transaction, minutes=5, verbose=True)

        win_standard_dict[date] = win_standards

    for date in ship.iterate_date('20180525', '20180715'):

        if date not in win_standard_dict or not win_standard_dict[date]: continue

        #for other_date in ship.iterate_range(date, 5):
        for win_standard in win_standard_dict[date]:

            money, win_count, lose_count, tie_count, escape_count = 1000000, 0, 0, 0, 0

            for other_date in ship.iterate_date('20180525', '20180715'):

                print '[%s] simulating %s ...' % (s, other_date)

                other_info = ship.get_daily_info(other_date, every_transaction=True)

                other_transaction = other_info.data

                if not other_transaction or other_date == date:
                    continue

                sim = StockSim(other_transaction)

                money, wc, lc, tc, ec = sim.execute(money, [win_standard], verbose=True)

                win_count += wc
                lose_count += lc
                tie_count += tc
                escape_count += ec

            # Filter the non-reliable statistic
            # if lose_count + win_count < 20:
            #     continue
            if lose_count+win_count+tie_count+escape_count == 0:
                break

            result = map(str, [s, date] + win_standard + [win_count, lose_count, tie_count, escape_count, money])

            queue.put(result)






def init(l, q):
    global lock
    global queue
    lock = l
    queue = q


if __name__ == '__main__':

    stock_list = ['2454', '2439', '2455', '2448', '2377', '3035',
                 '2456', '2313', '5269', '2383', '1312', '2353', '1707',
                 '3443', '4906']

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--update', help='Get today\'s data', action='store_true')
    args = parser.parse_args()

    if args.update:
        for s in stock_list:
            print 'updating ', s
            ship = Stock(s)
            ship.update_daily_info()
        exit(0)

    # Real simulation
    else:

        start_time = time.time()

        lock = Lock()
        queue = Queue()

        pool = Pool(4, initializer=init, initargs=(lock, queue))

        res = [pool.apply_async(execute, (s,)) for s in stock_list]
        results = [r.get() for r in res]

        f_result = open('train_data.csv', 'w')

        #f_result.write('stock,date,num_standard,win,lose,money\n')
        f_result.write('stock,date,second,number,inout_ratio,main_ratio,win,lose,tie,escape,money\n')

        while not queue.empty():
            f_result.write(','.join(queue.get()) + '\n')

        f_result.close()

        end_time = time.time()

        print 'Total time: %.2f' % (end_time - start_time)

        # print win_count, lose_count
    # print win_count, lose_count, money
