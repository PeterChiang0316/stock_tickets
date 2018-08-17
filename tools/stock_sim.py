# -*- coding: utf-8 -*-

import requests, os, re, datetime, collections, math, bisect
import time, sys
import cPickle as pickle

###########################################################
# StockSim class
###########################################################
class StockSim:

    #tax_rate = 1.005
    tax_rate = 1.005
    WIN_STANDARD = 1
    LOSE_STANDARD = 2

    def __init__(self, stock, date, transaction_list, output_file, finance, last_finance):
        self.stock = stock
        self.cache = {}
        self.transaction_list = transaction_list
        self.output_file = output_file
        self.date = date
        self.finance = finance
        self.last_finance = last_finance

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
        self.output_file.write(str(self.last_finance['K9']) + ',')
        self.output_file.write(str(self.last_finance['D9']) + ',')
        self.output_file.write(str(self.last_finance['DIF_MACD']) + ',')
        self.output_file.write(str(diff) + '\n')

    def execute(self, money, win_standard, verbose=True):

        def tick_after_seconds(time, seconds):
            now = datetime.datetime(2018, 5, 25, time / 10000, (time / 100) % 100, time % 100)
            after = now + datetime.timedelta(seconds=seconds)
            return int("%02d%02d%02d" % (after.hour, after.minute, after.second))

        def dbg_print(s):
            if verbose:
                print s

        def standard_test(current_tick, transaction, standard, standard_type):

            buy, sell = 0, 0
            assert standard_type == self.WIN_STANDARD or standard_type == self.LOSE_STANDARD

            seconds, number, sell_buy_rate, main_ratio = win_standard
            
            if sell_buy_rate <= 0.5: sell_buy_rate = 0.5

            interval_start = tick_after_seconds(current_tick, -1 * seconds)

            interval_list = []
            
            keys = transaction.keys()
            left = bisect.bisect_left(keys, interval_start)
            right = bisect.bisect_right(keys, current_tick)
            
            for v in transaction.values()[left:right]:
                if standard_type == self.WIN_STANDARD:
                    # For win_standard
                    if v.deal >= v.sell:
                        sell += v.count
                        interval_list.append(v.count)
                    else:
                        buy += v.count
                else:
                    # For lose_standard
                    if v.deal <= v.buy:
                        buy += v.count
                        interval_list.append(v.count)
                    else:
                        sell += v.count
            
            interval_list = sorted(interval_list[:-1], reverse=True)

            if len(interval_list) <= 3 or (buy + sell) == 0:
                return False

            if sum(interval_list[:3]) / sum(interval_list) >= main_ratio:
                if standard_type == self.WIN_STANDARD:
                    if sell >= number and (sell / (buy + sell)) >= sell_buy_rate :
                        return True
                else:
                    if buy >= number and (buy / (buy + sell)) >= sell_buy_rate:
                        return True
            else:
                return False

        # Simulation result flags and counter
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
                    self.add_record(win_standard, buy_tick, tick, buy_price, data.buy, (data.buy - cost_price) * 1000, 'EXPIRE')
                break

            if is_brought:

                # Valid the result
                win_standard_valid = standard_test(tick, trace, win_standard, self.WIN_STANDARD)
                lose_standard_valid = standard_test(tick, trace, win_standard, self.LOSE_STANDARD)

                if data.buy >= win_price:
                    # When reaching the win_price, check if it still match win_standard
                    # if TRUE: Update the win_price for saving the processing fee
                    if win_standard_valid and win_price < last_day_close_price * 1.05:
                        dbg_print('win and update the target again')
                        escape_tick = tick_after_seconds(tick, 600)
                        win_price, lose_price, escape_price = data.sell * 1.01, data.sell * 0.985, data.sell * self.tax_rate
                    else:
                        dbg_print('win')
                        money += data.buy * 1000
                        is_brought = False
                        count -= 1
                        win_count += 1
                        self.add_record(win_standard, buy_tick, tick, buy_price, data.buy, (data.buy - cost_price) * 1000, 'WIN')

                elif data.buy <= lose_price:
                    dbg_print('lose')
                    money += data.buy * 1000
                    is_brought = False
                    count -= 1
                    lose_count += 1
                    self.add_record(win_standard, buy_tick, tick, buy_price, data.buy, (data.buy - cost_price) * 1000, 'LOSE')

                elif tick >= escape_tick :

                    if win_standard_valid:
                        pass

                    elif (lose_standard_valid and data.buy < cost_price * 0.99 and tick >= tick_after_seconds(escape_tick, 600)) or data.buy >= escape_price:
                    
                        dbg_print('dangerous')
                        money += data.buy * 1000
                        is_brought = False
                        count -= 1
                        
                        # After lose 1%, looking for the early escape point even though we are losing money
                        if lose_standard_valid and data.buy < cost_price * 0.99 and tick >= tick_after_seconds(escape_tick, 600):
                            self.add_record(win_standard, buy_tick, tick, buy_price, data.buy, (data.buy - cost_price) * 1000, 'LOSE_ESCAPE')
                        else:
                            self.add_record(win_standard, buy_tick, tick, buy_price, data.buy, (data.buy - cost_price) * 1000, 'SMART_ESCAPE')

                        escape_count += 1
                else:
                    pass
                    #if lose_standard_valid and data.buy < cost_price * 0.99:
                    #    # Although nothing happened, still looking for lose standard for early warning
                    #    dbg_print('dangerous')
                    #    money += data.buy * 1000
                    #    is_brought = False
                    #    count -= 1
                    #    self.add_record(win_standard, buy_tick, tick, buy_price, data.buy, (data.buy - cost_price) * 1000, 'LOSE_ESCAPE')
                    #    escape_count += 1
            else:

                # Bypass the edge case
                if data.deal < last_day_close_price * 0.95 or data.deal > last_day_close_price * 1.05:
                    continue

                # Do not buy after 12:30 to have time to run
                if tick > 123000:
                    break

                win_standard_valid = standard_test(tick, trace, win_standard, self.WIN_STANDARD)
                lose_standard_valid = standard_test(tick, trace, win_standard, self.LOSE_STANDARD)

                if win_standard_valid and not lose_standard_valid:

                    cost_price = data.sell * self.tax_rate
                    money -= (cost_price * 1000)
                    is_brought = True
                    escape_tick = tick_after_seconds(tick, 600)
                    win_price, lose_price, escape_price = data.sell * 1.01, data.sell * 0.985, cost_price
                    buy_tick, buy_price = tick, data.sell

                    count += 1
                    print '[PASS]'

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
