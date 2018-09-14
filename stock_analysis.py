import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from tools.stock_price_utility import Stock
from tools.stock_price_utility import update_TWA_finance
import datetime, tools, bisect, os


def main():
    def get_last_close(e):
        stock, date = e
        stock_finance = finance_dict[stock]
        left = bisect.bisect_left(stock_finance.keys(), str(date))
        last_finance = stock_finance.values()[left - 1]
        return last_finance['ClosePr']

    df_list = [pd.read_csv(os.path.join('build', p)) for p in os.listdir('build')]

    df = df_list[0].append(df_list[1:], ignore_index=True)

    finance_dict = {s: Stock(str(s)).get_stock_finance() for s in df.stock.unique()}

    df['last_close_price'] = map(get_last_close, zip(df.stock, df.date))
    print len(df[df.buy_price >= df.last_close_price]), len(df), len(df[df.buy_price < df.last_close_price])
    print df[df.buy_price < df.last_close_price]

    print df.groupby('reason').size()
    high_price = {percent*0.5:df[df.buy_price >= df.last_close_price*(1+percent*0.005)].groupby('reason').size() for percent in range(11)}
    print high_price


if __name__ == '__main__':
    main()

plt.show()