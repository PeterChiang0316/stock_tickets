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

    def __init__(self, stock, date, transaction_list, output_file, finance):
        self.stock = stock
        self.cache = {}
        self.transaction_list = transaction_list
        self.output_file = output_file
        self.date = date
        self.finance = finance

    def add_record(self, win_standard, buy_tick, result_tick, buy_price, sell_price, diff, reason):

        def time_diff(t1, t2):
            t1 = datetime.datetime(2018, 5, 25, t1 / 10000, (t1 / 100) % 100, t1 % 100)
            t2 = datetime.datetime(2018, 5, 25, t2 / 10000, (t2 / 100) % 100, t2 % 100)
            return (t2 - t1).total_seconds()

        # stock,date,second,number,inout_ratio,main_ratio,buy_tick,result_tick,interval,reason,buy_price,sell_price,diff
        self.output_file.write(self.stock + ',')
        self.output_file.write(self.date + ',')
        self.output_file.write(','.join(map(str,win_standard)) + ',')
        self.output_file.write(str(buy_tick) + ',')
        self.output_file.write(str(result_tick) + ',')
        self.output_file.write(str(time_diff(buy_tick, result_tick)) + ',')
        self.output_file.write(reason + ',')
        self.output_file.write(str(buy_price)+ ',')
        self.output_file.write(str(sell_price)+ ',')
        self.output_file.write(str(diff) + '\n')

    def execute(self, money, win_standard, verbose=True):

        def tick_after_seconds(time, seconds):
            now = datetime.datetime(2018, 5, 25, time / 10000, (time / 100) % 100, time % 100)
            after = now + datetime.timedelta(seconds=seconds)
            return int("%02d%02d%02d" % (after.hour, after.minute, after.second))

        def dbg_print(s):
            if verbose:
                print s

        is_brought, count = False, 0
        win_count, lose_count, tie_count, escape_count = 0, 0, 0, 0

        trace = collections.OrderedDict()
        for k, v in self.transaction_list.items():
            trace[int(k)] = v

        # There might be some data lost in simulation data, just skip it
        if trace.keys()[-1] <= 130000:
            return money, win_count, lose_count, tie_count, escape_count

        last_day_close_price = self.finance['ClosePr'] - self.finance['PriceDifference']

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
                    tie_count += 1
                    self.add_record(win_standard, buy_tick, tick, buy_price, data.buy, (data.buy - escape_price) * 1000, 'EXPIRE')
                break

            if is_brought:

                # Valid the result
                if data.buy >= win_price:
                    dbg_print('win')
                    money += data.buy * 1000
                    is_brought = False
                    count -= 1
                    win_count += 1
                    self.add_record(win_standard, buy_tick, tick, buy_price, data.buy, (data.buy - escape_price) * 1000, 'WIN')
                elif data.buy <= lose_price:
                    dbg_print('lose')
                    money += data.buy * 1000
                    is_brought = False
                    count -= 1
                    lose_count += 1
                    self.add_record(win_standard, buy_tick, tick, buy_price, data.buy, (data.buy - escape_price) * 1000, 'LOSE')
                elif tick >= escape_tick and data.buy >= escape_price:
                    dbg_print('escape')
                    money += data.buy * 1000
                    is_brought = False
                    count -= 1
                    escape_count += 1
                    self.add_record(win_standard, buy_tick, tick, buy_price, data.buy, (data.buy - escape_price) * 1000, 'ESCAPE')
            else:

                # Bypass the edge case
                if data.deal < last_day_close_price * 0.95 or data.deal > last_day_close_price * 1.05:
                    continue

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
                    continue

                if sell >= number and (sell / (buy + sell)) >= sell_buy_rate \
                        and money > data.sell * 1000 and sum(sell_list[:3]) / sum(sell_list) >= main_ratio:
                    pass
                else:
                    continue

                money -= (data.sell * 1000) * self.tax_rate
                # If not win in 5 minutes, just escape
                is_brought, escape_tick = True, tick_after_seconds(tick, 300)
                win_price, lose_price, escape_price = data.sell * 1.01, data.sell * 0.99, data.sell * self.tax_rate
                buy_tick, buy_price = tick, data.sell
                count += 1
                print '[PASS] ', buy, sell, tick, interval_start, money, data.sell, win_price, lose_price, (100 * sell / (buy + sell))

        dbg_print('Final money %.2f' % money)
        assert count == 0, 'count %d' % count
        print money, win_count, lose_count, tie_count, escape_count
        return money, win_count, lose_count, tie_count, escape_count


###########################################################
# Public Function
###########################################################


def __main__():
    pass


if __name__ == '__main__':
    __main__()
