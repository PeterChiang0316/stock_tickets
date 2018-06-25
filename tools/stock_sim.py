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

    def execute(self, money, transaction_list, seconds, number, sell_buy_rate, debug=True):

        def tick_after_seconds(time, seconds):
            now = datetime.datetime(2018, 5, 25, time / 10000, (time / 100) % 100, time % 100)
            after = now + datetime.timedelta(seconds=seconds)
            return int("%02d%02d%02d" % (after.hour, after.minute, after.second))

        def dbg_print(s):
            if debug:
                print str(s)

        print 'initial money ', money
        is_brought, count = False, 0

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
                break

            if is_brought:
                #print tick, data
                # Valid the result
                if data.buy >= win_price:
                    dbg_print('win')
                    money += data.buy * 1000
                    is_brought = False
                    count -= 1
                elif data.buy <= lose_price:
                    dbg_print('lose')
                    money += data.buy * 1000
                    is_brought = False
                    count -= 1
            else:
                buy, sell = 0, 0

                # last N seconds
                interval_start = tick_after_seconds(tick, -1 * seconds)

                for k, v in trace.items():
                    if interval_start <= k <= tick:
                        if v.deal >= v.sell:
                            sell += v.count
                        else:
                            buy += v.count

                if sell >= number and (100 * sell / (buy + sell)) >= sell_buy_rate and money > data.sell * 1000:
                    money -= (data.sell * 1000) * self.tax_rate
                    is_brought = True
                    win_price, lose_price = data.sell * 1.01, data.sell * 0.98
                    count += 1
                    print buy, sell, tick, interval_start, money, data.sell, win_price, lose_price, (100 * sell / (buy + sell))

        dbg_print(money)
        assert count == 0
        return money


###########################################################
# Public Function
###########################################################


def __main__():
    pass


if __name__ == '__main__':
    __main__()
