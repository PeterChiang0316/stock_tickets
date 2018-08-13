# -*- coding: utf-8 -*-
import time, datetime, collections, os
from tools.stock_price_utility import Stock
from tools.stock_sim import StockSim
from multiprocessing import Pool, Lock, Queue
import argparse, bisect, tools


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
    def ma5comparema20(d, TWA):
        date_list = TWA.keys()
        right = bisect.bisect_left(date_list, d)
        ma20 = sum(map(lambda k: k['close_price'], TWA.values()[right - 20:right])) / 20
        ma5 = sum(map(lambda k: k['close_price'], TWA.values()[right - 5:right])) / 5
        return ma5 >= ma20

    ship = Stock(s)

    print 'Start test %s' % s

    win_standard_dict = {}
    if not os.path.exists('data/TWA.pickle'):
        tools.stock_price_utility.update_TWA_finance()

    TWA = tools.stock_price_utility.pickle_load('data/TWA.pickle')

    for date in ship.iterate_date('20180525', '20180715'):

        print '[%s] Date: %s' % (s, date)
        info = ship.get_daily_info(date, every_transaction=True)

        transaction = info.data

        if not transaction:
            continue

        win_standards = stock_win_point_test(s, date, transaction, minutes=5, verbose=True)

        win_standard_dict[date] = win_standards

    fn = os.path.join('build', s + '.csv')
    fp = open(fn, 'w')
    header = ['stock', 'date', 'second', 'number', 'inout_ratio', 'main_ratio', 'buy_tick', \
              'result_tick', 'interval', 'reason', 'buy_price', 'sell_price', 'K9', 'D9', 'DIF_MACD','diff']
    fp.write(','.join(header) + '\n')

    for date in ship.iterate_date('20180525', '20180715'):

        if date not in win_standard_dict or not win_standard_dict[date]: continue

        #for other_date in ship.iterate_range(date, 5):
        for win_standard in win_standard_dict[date]:

            money, win_count, lose_count, tie_count, escape_count = 1000000, 0, 0, 0, 0

            for other_date in ship.iterate_date('20180525', '20180715'):

                # Filter the date that not safe
                # reference: https://xstrader.net
                if not ma5comparema20(other_date, TWA): continue

                print '[%s] simulating %s ...' % (s, other_date)

                other_info = ship.get_daily_info(other_date, every_transaction=True)

                other_transaction = other_info.data

                if not other_transaction or other_date == date:
                    print '[SYSTEM]', other_date, date
                    continue

                stock_finance = ship.get_stock_finance()
                left = bisect.bisect_left(stock_finance.keys(), other_date)
                last_finance = stock_finance.values()[left-1]

                # reference: http://www.cmoney.tw/learn/course/technicalanalysisfast/topic/1846
                if last_finance['K9'] >= 80 or last_finance['D9'] >= 80:
                    print '[SYSTEM] K/D value exceed 80'
                    continue

                if abs(last_finance['DIF_MACD']) < 0.5:
                    print '[SYSTEM] DIF_MACD too small'
                    continue

                sim = StockSim(s, other_date, other_transaction, fp, \
                               stock_finance[other_date], last_finance)

                money, wc, lc, tc, ec = sim.execute(money, win_standard, verbose=True)

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

    fp.close()






def init(l, q):
    global lock
    global queue
    lock = l
    queue = q


if __name__ == '__main__':

    stock_list = ['2454', '2439', '2455', '2448', '2377', '3035',
                 '2456', '2313', '5269', '2383', '1312', '2353', '1707',
                 '3443', '4906']
    stock_list += ['2915', '5264', '2311', '2105', '3673', '2542', '3044', '2610', '6116', '1319', '2059', '2356']
    stock_list += ['3017', '2485', '1536', '3376', '2603', '6285', '3665', '1476']
    
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--update', help='Get today\'s data', action='store_true')
    parser.add_argument('-pll', help='Use multiprocessing', action='store_true')
    args = parser.parse_args()

    if args.update:
        for s in stock_list:
            print 'updating ', s
            ship = Stock(s)
            ship.update_daily_info()
        exit(0)

    # Real simulation
    else:

        if not os.path.exists('build'): os.mkdir('build')

        start_time = time.time()

        lock = Lock()
        queue = Queue()

        if args.pll:

            pool = Pool(initializer=init, initargs=(lock, queue))
            res = [pool.apply_async(execute, (s,)) for s in stock_list]
            results = [r.get() for r in res]

        else:

            for s in stock_list:
                execute(s)
        
        f_result = open('train_data.csv', 'w')
        f_result.write('stock,date,second,number,inout_ratio,main_ratio,win,lose,tie,escape,money\n')

        while not queue.empty():
            f_result.write(','.join(queue.get()) + '\n')

        f_result.close()

        end_time = time.time()

        print 'Total time: %.2f' % (end_time - start_time)

