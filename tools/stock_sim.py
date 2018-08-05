# -*- coding: utf-8 -*-

import requests, os, re, datetime, collections, math
import time, sys
import cPickle as pickle

###########################################################
# StockSim class
###########################################################
class StockSim:

    #tax_rate = 1.005
    tax_rate = 1.005

    def __init__(self, transaction_list):
        self.cache = {}
        self.transaction_list = transaction_list

    def execute(self, money, win_standards, verbose=True):

        def tick_after_seconds(time, seconds):
            now = datetime.datetime(2018, 5, 25, time / 10000, (time / 100) % 100, time % 100)
            after = now + datetime.timedelta(seconds=seconds)
            return int("%02d%02d%02d" % (after.hour, after.minute, after.second))

        def dbg_print(s):
            if verbose:
                print s

        is_brought, count = False, 0
        win_count, lose_count = 0, 0

        trace = collections.OrderedDict()
        for k, v in self.transaction_list.items():
            trace[int(k)] = v

        if trace.keys()[-1] <= 130000:
            return money, win_count, lose_count

        start_price = trace.values()[0].deal

        print win_standards

        for tick, data in trace.items():

            # Skip the first chaos 10 minutes
            if tick < 91000:
                continue

            # If there's pending stock, sell it
            if tick > 130000:
                assert count == 0 or count == 1, 'coding bug, count = %d' % count
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

                if data.deal < start_price * 0.98:
                    continue

                if data.deal > start_price * 1.05:
                    continue

                pass_win_standards = True

                for win_standard in win_standards:

                    buy, sell = 0, 0

                    seconds, number, sell_buy_rate, main_ratio = win_standard

                    interval_start = tick_after_seconds(tick, -1 * seconds)

                    sell_list = []

                    for k, v in trace.items():
                        if interval_start <= k <= tick:
                            if v.deal >= v.sell:
                                sell += v.count
                                sell_list.append(v.count)
                            else:
                                buy += v.count

                    sell_list = sorted(sell_list[:-1], reverse=True)

                    if len(sell_list) <= 3 or (buy + sell) == 0:
                        pass_win_standards = False
                        break

                    if sell >= number and (sell / (buy + sell)) >= sell_buy_rate \
                            and money > data.sell * 1000 and sum(sell_list[:3]) / sum(sell_list) >= main_ratio:
                        pass
                    else:
                        pass_win_standards = False
                        break

                if win_standards and pass_win_standards:

                    money -= (data.sell * 1000) * self.tax_rate
                    is_brought = True
                    win_price, lose_price = data.sell * 1.01, data.sell * 0.99
                    count += 1
                    print '[PASS] ', buy, sell, tick, interval_start, money, data.sell, win_price, lose_price, (100 * sell / (buy + sell))

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
