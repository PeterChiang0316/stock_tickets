import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from tools.stock_price_utility import Stock
from tools.stock_price_utility import get_TWA_stock_price
import datetime, tools, bisect, os


def main():
    def get_last_close(e):
        stock, date = e
        stock_finance = finance_dict[stock]
        left = bisect.bisect_left(stock_finance.keys(), str(date))
        last_finance = stock_finance.values()[left - 1]
        #print str(date), stock_finance.keys()[left - 1]
        return last_finance['ClosePr']
        
    def get_TWA_current_magtitude(e):
        date, time = e
        TWA_finance = tools.stock_price_utility.json_load('data/TWA.json')
        left = bisect.bisect_left(TWA_finance.keys(), str(date))
        last_finance = TWA_finance.values()[left-1]
        last_TWA_close_price = last_finance['close_price']
        
        today_finance = TWA_finance.values()[left]
        today_open_price = today_finance['open_price']
        
        TWA_daily_price = get_TWA_stock_price(str(date))
        time_string = '%04d' % time
        left = bisect.bisect_left(TWA_daily_price.keys(), time_string)
        current_TWA_price = TWA_daily_price.values()[left-1]['deal_price']
        #print time_string, TWA_daily_price.keys()[left-1], current_TWA_price
        return 100 * float(current_TWA_price - last_TWA_close_price) / last_TWA_close_price
        
        
    df_list = [pd.read_csv(os.path.join('build', p)) for p in os.listdir('build')]

    df = df_list[0].append(df_list[1:], ignore_index=True)

    finance_dict = {s: Stock(str(s)).get_stock_finance() for s in df.stock.unique()}
    
    
    df['last_close_price'] = map(get_last_close, zip(df.stock, df.date))
    df['TWA_current_magtitude'] = map(get_TWA_current_magtitude, zip(df.date, df.buy_tick/100))
    
    print df.head()
    
    print len(df[df.buy_price >= df.last_close_price]), len(df), len(df[df.buy_price < df.last_close_price])
    print df[df.buy_price < df.last_close_price]

    print df.groupby('reason').size()
    high_price = {percent*0.5:df[df.buy_price >= df.last_close_price*(1+percent*0.005)].groupby('reason').size() for percent in range(11)}
    print high_price
    
    high_price = {t*0.1:df[df.TWA_current_magtitude > t*0.1].groupby('reason').size() for t in range(6)}
    print high_price

    high_price = df[(df.TWA_current_magtitude > 0.1) & (df.buy_price >= df.last_close_price*(1+0.01))].groupby('reason').size()
    print high_price

if __name__ == '__main__':
    main()

plt.show()