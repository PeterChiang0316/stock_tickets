import time
from tools.stock_price_utility import Stock

start_time = time.time()

# For querying the stock info
my_stock = Stock('2454')
info = my_stock.get_stock_daily_info('20180427')

# Open price
print 'open_price', info['open_price']

# Last close price
print 'last close price', info['last_close_price']

# Daily magnitude
print 'daily magnitude', info['daily_magnitude']

# Daily total transaction money
print 'daily amount', info['daily_amount']

# Daily lowest price
print 'lowest price', info['lowest_price']

# Daily highest price
print 'highest price', info['highest_price']

# Detail tracsaction status
# You can use for loop to iterate all the element
# It will follow the timing ordering
details = info['data']

print 'date\tdeal\thigh\tlow\tcount'
for minute, data in details.items()[:5]:
    print minute, data['deal_price'], data['high_price'], data['low_price'], data['count']
    
# For querying 3 consecutive daily info
date = '20180427'
for _ in range(3):
    info = my_stock.get_stock_daily_info(date)
    print date, 'open_price', info['open_price']
    date = my_stock.get_next_opening(date)
    
end_time = time.time()

print 'Totol time: %.2f' % (end_time - start_time)