import stock_ticket
from tools.stock_price_utility import Stock
import pandas as pd
import bisect
import numpy as np

if __name__ == '__main__':

    s = '2456'
    ship = Stock(s)
    
    win_standard_dict = {}
    sim_start_date = '20180525'
    sim_end_date = '20180815'
    
    df = pd.DataFrame(columns=('s', 'date', 'last_date', 'K9', 'D9', 'RSI10', 'RSI5', 'DIF_MACD', 'STD5', 'STD10', 'HIT'))
    finance = ship.get_stock_finance()
    
    
    for date in ship.iterate_date(sim_start_date, sim_end_date):

        print '[%s] Date: %s' % (s, date)
        info = ship.get_daily_info(date, every_transaction=True)
    
        transaction = info.data
    
        if not transaction:
            continue
    
        win_standards = stock_ticket.stock_win_point_test(s, date, transaction, minutes=5)
        
        win_standard_dict[date] = win_standards
        
        left = bisect.bisect_left(finance.keys(), date)
        last_date = finance.keys()[left-1]
        last_finance = finance.values()[left-1]
        print last_finance

        last5 = map(lambda v:v['ClosePr'], finance.values()[left-6:left-1])
        std5 = np.std(last5, ddof=1)

        last10 = map(lambda v: v['ClosePr'], finance.values()[left - 11:left - 1])
        std10 = np.std(last10, ddof=1)

        df = df.append(pd.Series({'s':s, 'date':date, 'last_date': last_date,                         \
                                        'K9':last_finance['K9'], 'D9':last_finance['D9'],             \
                                        'RSI10':last_finance['RSI10'], 'RSI5':last_finance['RSI5'],   \
                                        'DIF_MACD':last_finance['DIF_MACD'],
                                        'STD5':std5, 'STD10':std10,
                                        'HIT':len(win_standards)}), ignore_index=True)
    
    df.to_csv('2456_report.csv')