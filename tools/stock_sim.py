# -*- coding: utf-8 -*-

import requests, os, re, datetime, collections, math
import time, pickle, sys


###########################################################
# StockSim class
###########################################################
class StockSim:

    #tax_rate = 1.005
    tax_rate = 1.005

    def __init__(self):
        self.cache = {}

    def execute(self, money, transaction_list, seconds, number, sell_buy_rate, main_ratio, verbose=True):

        def tick_after_seconds(time, seconds):
            now = datetime.datetime(2018, 5, 25, time / 10000, (time / 100) % 100, time % 100)
            after = now + datetime.timedelta(seconds=seconds)
            return int("%02d%02d%02d" % (after.hour, after.minute, after.second))

        def dbg_print(s):
            if verbose:
                print s

        dbg_print ('initial money %.2f' % money)
        dbg_print ('seconds %.2f' % seconds)
        dbg_print ('number %.2f' % number)
        dbg_print ('sell_buy_rate %.2f' % sell_buy_rate)

        is_brought, count = False, 0
        win_count, lose_count = 0, 0

        trace = collections.OrderedDict()
        for k, v in transaction_list.items():
            trace[int(k)] = v

        for tick, data in trace.items():

            # Skip the first chaos 10 minutes
            if tick < 91000:
                continue

            # If there's pending stock, sell it
            if tick > 130000:
                assert count == 0 or count == 1
                if count:
                    dbg_print('execute remain')
                    money += data.buy * 1000
                    count -= 1
                    lose_count += 1
                break

            if is_brought:
                #print tick, data
                # Valid the result
                if data.buy >= win_price:
                    dbg_print('win')
                    money += data.buy * 1000
                    is_brought = False
                    count -= 1
                    win_count += 1
                elif data.buy <= lose_price:
                    dbg_print('lose')
                    money += data.buy * 1000
                    is_brought = False
                    count -= 1
                    lose_count += 1
            else:
                buy, sell = 0, 0

                # last N seconds
                interval_start = tick_after_seconds(tick, -1 * seconds)

                # Calculate the last 10 minutes
                last_10_minutes = tick_after_seconds(tick, -600)

                # Calculate the last 5 minutes
                last_5_minutes = tick_after_seconds(tick, -300)

                sell_list = []

                for k, v in trace.items():
                    if interval_start <= k <= tick:
                        if v.deal >= v.sell:
                            sell += v.count
                            sell_list.append(v.count)
                        else:
                            buy += v.count

                sell_list = sorted(sell_list[:-1], reverse=True)

                if len(sell_list) <= 3:
                    continue

                if sell >= number and (100 * sell / (buy + sell)) >= sell_buy_rate and money > data.sell * 1000:

                    if sum(sell_list[:3]) / sum(sell_list) < main_ratio:
                        print str(tick) + ' skip', sum(sell_list[:3]) / sum(sell_list)
                        continue

                    # Do more check
                    #sm10 = [v for k, v in trace.items() if last_10_minutes <= k < last_5_minutes]
                    #sm5 = [v for k, v in trace.items() if last_5_minutes <= k < tick]

                    def cal_sm(s):
                        return sum(map(lambda v: v.deal * v.count, s)) / sum(map(lambda v: v.count, s))

                    #print cal_sm(sm10)
                    #if cal_sm(sm10) > cal_sm(sm5):
                    #    continue

                    money -= (data.sell * 1000) * self.tax_rate
                    is_brought = True
                    win_price, lose_price = data.sell * 1.01, data.sell * 0.99
                    count += 1
                    print buy, sell, tick, interval_start, money, data.sell, win_price, lose_price, (100 * sell / (buy + sell))

        dbg_print('Final money %.2f' % money)
        assert count == 0, 'count %d' % count
        return money, win_count, lose_count


###########################################################
# Public Function
###########################################################


def __main__():
    pass


if __name__ == '__main__':
    __main__()
