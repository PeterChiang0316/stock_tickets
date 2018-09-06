# -*- coding: utf-8 -*-
import requests, os, re, datetime, collections, math, json
import numpy as np
import xlsxwriter
from bs4 import BeautifulSoup
import time, sys
import bisect
import ujson
###########################################################
# Global class
###########################################################

class Container(dict):
    def __init__(self, *args, **kwargs):
        super(Container, self).__init__(*args, **kwargs)
        self.__dict__ = self

class DailyInfo(Container):
    pass

class DetailInfo(Container):
    pass
###########################################################
# Stock class
###########################################################
class Stock:
    
    def __init__(self, stock):
        self.stock = stock
        
        if not os.path.exists('data'):
            print 'Initializing ... Creating data folder'
            os.mkdir('data')
        
        self.stock_data_folder = os.path.join('data', stock)
        if not os.path.exists(self.stock_data_folder):
            print 'Initializing ... Creating stock private data folder'
            os.mkdir(self.stock_data_folder)
        
        self.cache = {}

        pattern = re.compile('trans_\d\d\d\d\d\d\d\d\.json')
        self.trans_list = sorted(filter(pattern.match, os.listdir(self.stock_data_folder)))
        self.trans_list = map(lambda v: v[6:14], self.trans_list)

    def is_stock_open(self, day):
    
        '''
        :param day: stock date
        :return: True if stock opens in specified day
        '''
        return day in self.trans_list
    
    def get_daily_info(self, date, every_transaction=False):
        
        if date in self.cache: return self.cache[date]
        
        # Check date format
        assert len(date) == 8, 'Date format error, should be in yyyymmdd format ex: 20171011 but get %s' % date
        assert int(date[:4]) > 1990, 'Year error'
        assert 1 <= int(date[4:6]) <= 12, 'Month error'
        assert 1 <= int(date[6:]) <= 31, 'Day error'
        #assert self.is_stock_open(date), 'Stock date error % s' % date
        
        folder = os.path.join('data', self.stock)
        
        def transaction_info_parser():
        
            # If we need daily transaction info, search if the data is available
            filename = os.path.join('data', self.stock, 'trans_'+date+'.json')

            if not os.path.exists(filename):
                return None

            d = json_load(filename)
            return collections.OrderedDict((k, DailyInfo(v)) for k, v in d.items())
        
        self.cache[date] = DetailInfo({'data': transaction_info_parser()})
        
        return self.cache[date]
    
    def get_next_opening(self, date):
        pos = bisect.bisect_right(self.trans_list, date)
        return self.trans_list[pos] if pos < len(self.trans_list) else None

    def get_stock_finance(self):
    
        today = datetime.datetime.today().date()
        year, month, day = today.year, today.month, today.day
        today_date = '%d%0.2d%0.2d' % (year, month, day)
        
        filename = os.path.join('data', self.stock, 'finance.json')

        if os.path.exists(filename):
            try:
                # For preventing data error in the existed file
                d = json_load(filename)
                
                # finance.json exists but too old, update it
                if d.keys()[-1] < self.trans_list[-1]:
                    pass
                # Otherwise, return directly in nomal case
                else:
                    return d
            except:
                # [ERROR] something wrong in finance.json, re-download it
                d = collections.OrderedDict()
                   
        else:    
            # For the first
            d = collections.OrderedDict()
        
        print '#####################################################################'
        print '# Start crawler                                                     #'
        print '#####################################################################'
        cmkey, session= get_stock_cmkey()
        data = {
            'action': 'GetTechnicalData',
            'stockId': self.stock,
            'time':'d',
            'range':'1000',
            'cmkey': cmkey
        }
        cookies = session.cookies.get_dict()
        h = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-Encoding': 'gzip, deflate, br',
            'accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-CN;q=0.2',
            'Connection': 'keep-alive',
            'Cookie': 'AspSession=' + cookies['AspSession'] + ';',
            'Host': 'www.cmoney.tw',
            'Referer': 'https://www.cmoney.tw/finance/technicalanalysis.aspx?s=8341',
            'user-ugent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'}
                
        res = session.get('https://www.cmoney.tw/finance/ashx/MainPage.ashx', headers=h, params=data)
        json = res.json()
        
        for element in json:
            if int(element['DealQty']) == 0:
                continue
            if element['Date'] not in d:
                d[element['Date']] = element
        
        json_save(filename, d)
            
        return d
    
    def iterate_date(self, date_start, date_end=datetime.datetime.now().strftime('%Y%m%d')):
        
        if date_end <= date_start:
            return []
        else:
            left = bisect.bisect_left(self.trans_list, date_start)
            right = bisect.bisect_right(self.trans_list, date_end)
            return self.trans_list[left:right]
        

    def iterate_range(self, date, count):
        assert date in self.trans_list
        idx = self.trans_list.index(date)
        return self.trans_list[idx:idx+count]

    def update_daily_info(self, today_date=None):
        
        # Not specified date, use today
        if not today_date:
            today = datetime.datetime.today().date()
            year, month, day = today.year, today.month, today.day
            today_date = '%d%0.2d%0.2d' % (year, month, day)
        
        filename = os.path.join('data', self.stock, 'trans_' + today_date + '.json')
        
        if os.path.exists(filename):
            print 'already download'
        else:
            try:
                json_save(filename, stock_daily_parser(self.stock))
                print '[%s][%s] download success' % (self.stock, today_date)
            except:
                print '[%s][%s] download fail' % (self.stock, today_date)
            
            
###########################################################
# Private Function
###########################################################
def json_save(filename, data):
    '''
    :param filename: json filename
    :param data: the dictionary that store date
    :return: None
    '''
    with open(filename, 'w') as fjson:
        json.dump(data, fjson, ensure_ascii=False, sort_keys=True, indent=4)

def json_load(filename):
    '''
    :param filename: the json filename
    :return: the dictionary that store date
    '''
    if not os.path.exists(filename):
        return None
    with open(filename) as f:
        d = ujson.decode(f.read())
        d = collections.OrderedDict(sorted(d.items(), key=lambda k:k[0]))
    return d
    
def xlsWriter(filename, work_list):
    working_book = xlsxwriter.Workbook(filename + ".xlsx".encode('utf-8'))

    for sheet_info in work_list:
        print sheet_info
        sh_name, l = sheet_info
        print 'working on ' + sh_name.encode('utf-8')
        sheet = working_book.add_worksheet(sh_name)
        for i, line in enumerate(l):
            for j, col in enumerate(line):
                sheet.write(i, j, col)
    working_book.close()
    print filename + '.xlsx done'    
    

def get_stock_ck():
    # Prepare header file
    h = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-CN;q=0.2',
        'Connection': 'keep-alive',
        'Cookie': 'AspSession=zy11cs3wrqatq4henntinwpi; __asc=f192f05015e1a2dd01ff253ba0a; __auc=f192f05015e1a2dd01ff253ba0a; _gat_real=1; _gat_UA-30929682-4=1; _ga=GA1.2.1793962014.1465548991; _gid=GA1.2.2115739754.1503677764; _gat_UA-30929682-1=1',
        'Host': 'www.cmoney.tw',
        'Referer': 'https://www.cmoney.tw/finance/technicalanalysis.aspx?s=2330',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'}

    # Browse the webpage once to get the CK value
    url = 'http://www.cmoney.tw/notice/chart/stockchart.aspx?action=r&id=1101&date=20171010'

    # Real get
    session = requests.Session()
    res = session.get(url)

    # Get the content
    content = res.text.encode('utf8')

    # Parse ck from content
    for line in content.split('\n'):
        m = re.match('\s*?var\s*ck\s*=\s*"(.*?)";', line)
        if m:
            ck = m.group(1)

    # Report
    # print 'ck: ' + ck

    return ck, session

def get_stock_cmkey():
    # Prepare header file
    h = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-CN;q=0.2',
        'Connection': 'keep-alive',
        'Cookie': 'AspSession=zy11cs3wrqatq4henntinwpi; __asc=f192f05015e1a2dd01ff253ba0a; __auc=f192f05015e1a2dd01ff253ba0a; _gat_real=1; _gat_UA-30929682-4=1; _ga=GA1.2.1793962014.1465548991; _gid=GA1.2.2115739754.1503677764; _gat_UA-30929682-1=1',
        'Host': 'www.cmoney.tw',
        'Referer': 'https://www.cmoney.tw/finance/technicalanalysis.aspx?s=2330',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'}

    # Browse the webpage once to get the cmkey value
    url = 'https://www.cmoney.tw/finance/technicalanalysis.aspx?s=8341'

    # Real get
    session = requests.Session()
    res = session.get(url)

    # Get the content
    content = res.text.encode('utf8')

    #f = open('tmp/cmkey.html', 'w')
    #f.write(content)
    #f.close()
    
    # Parse cmkey from content
    for line in content.split('\n'):
        m = re.match('.*?\/finance\/technicalanalysis.aspx.*?cmkey=\'(.*?)\'', line)
        if m:
            cmkey = m.group(1)
            
    # Report
    #print 'cmkey: ' + cmkey

    return cmkey, session

def stock_daily_parser(stock):
        
    s = requests.Session()
    data = {'is_check': '1'}
    res = s.post('http://pchome.megatime.com.tw/stock/sto0/ock3/sid%s.html' % stock, data=data)
    res.encoding = 'utf-8'
    content = res.text.encode('utf-8')
    
    content = re.sub(r'<font.*?>', '', content)
    content = re.sub(r'</font.*?>', '', content)
    soup = BeautifulSoup(content, 'html.parser')
        
    d = {}
    
    
    for row in soup.select('table#tb_chart > tr')[1:-1]:
        
        time, buy, sell, deal, diff, count, acc = [td.text for td in row.find_all('td')]
        time = '%06s' % time.replace(':', '')
        
        if sell == '--':
            sell = buy
        if buy == '--':
            buy = sell

        print buy, sell, deal, diff, count
        d[time] = {'buy': float(buy), \
                'sell': float(sell),\
                'deal': float(deal),\
                'diff': float(diff),\
                'count': float(count)}
        
    return collections.OrderedDict(sorted(d.items(), key=lambda k: k))



def update_TWA_finance():

    today = datetime.datetime.today().date()
    year, month, day = today.year, today.month, today.day
    today_date = '%d%0.2d%0.2d' % (year, month, day)
    
    if os.path.exists('data/TWA.json'):
        d = json_load('data/TWA.json')
        if d.keys()[-1] < today_date:
            print '[SYSTEM] Updating TWA finance...'
        else:
            return
    else:
        d = collections.OrderedDict()
        
    ck, session = get_stock_ck()
    h = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-CN;q=0.2',
        'Connection': 'keep-alive',
        'Cookie': 'AspSession='+session.cookies['AspSession']+'; __asc=f192f05015e1a2dd01ff253ba0a; __auc=f192f05015e1a2dd01ff253ba0a; _gat_real=1; _gat_UA-30929682-4=1; _ga=GA1.2.1793962014.1465548991; _gid=GA1.2.2115739754.1503677764; _gat_UA-30929682-1=1',
        'Host': 'www.cmoney.tw',
        'Referer': 'https://www.cmoney.tw/notice/chart/stockchart.aspx?action=d&id=TWA00&scaleSize=1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'}

    data = {
        'action': 'd',
        'count': '1000',
        'id': 'TWA00',
        'ck': ck,
        '_': '1533974045257'
    }
    res = session.get('https://www.cmoney.tw/notice/chart/stock-chart-service.ashx', headers=h, params=data)
    
    for element in res.json()['DataLine']:
        date, open_price, high_price, low_price, close_price, tmp, diff, rate, tmp2, money = element
        date_string = datetime.datetime.fromtimestamp(date/1000.0).strftime('%Y%m%d')
        if date_string not in d:
            d[date_string] = {
                'open_price': open_price,
                'high_price': high_price,
                'close_price': close_price,
                'diff': diff,
                'rate': rate,
                'money': money * 1000
            }
    json_save('data/TWA.json', d)

###########################################################
# Public Function
###########################################################


def __main__():
    pass
    


__main__()
        