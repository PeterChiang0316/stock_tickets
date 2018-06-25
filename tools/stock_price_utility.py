# -*- coding: utf-8 -*-
import requests, os, re, datetime, collections, math
import numpy as np
import xlsxwriter
from bs4 import BeautifulSoup
import time, pickle, sys

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
            
    def is_stock_open(self, day):
    
        '''
        :param day: stock date
        :return: True if stock opens in specified day
        '''
        filename = os.path.join(self.stock_data_folder, 'finance.pickle')
        
        if 'date_list_cache' in self.cache:
            date_list = self.cache['date_list_cache']
        else:
            self.get_stock_finance(day)
            date_list = pickle_load(filename)
            self.cache['date_list_cache'] = date_list
            
        assert min(map(int, date_list.keys())) <= int(day), 'Date too old, can not obtain'
        
        return day in date_list
    
    def get_daily_info(self, date, every_transaction=False):
    
        # Check date format
        assert len(date) == 8, 'Date format error, should be in yyyymmdd format ex: 20171011'
        assert int(date[:4]) > 1990, 'Year error'
        assert 1 <= int(date[4:6]) <= 12, 'Month error'
        assert 1 <= int(date[6:]) <= 31, 'Day error'
        assert self.is_stock_open(date), 'Stock date error % s' % date
        
        folder = os.path.join('data', self.stock)
        
        

        filename = os.path.join('data', self.stock, date+'.pickle')
    
        if os.path.exists(filename):
            json = pickle_load(filename)
            
        else:
            # Get CK for stock price
            ck, session = get_stock_ck()
            cookies = session.cookies.get_dict()
        
            h = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-CN;q=0.2',
                'Connection': 'keep-alive',
                'Cookie': 'AspSession=' + cookies['AspSession'] + ';',
                'Host': 'www.cmoney.tw',
                'Referer': 'https://www.cmoney.tw/notice/chart/stockchart.aspx?action=r&id=1101&date=20171011',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest'}
        
            data = {
                'action': 'r',
                'id': self.stock,
                'date': date,
                'ck': ck,
            }
        
            url = 'http://www.cmoney.tw/notice/chart/stock-chart-service.ashx'
            res = session.get(url, headers=h, params=data)
        
            assert res.status_code == 200
        
            # store to cache
            json = res.json()
            pickle_save(filename, json)
            
        def JSONParser(d, key):
            dots = d[key]
            l = collections.OrderedDict()
            for dot in dots:
                # time, deal_price, deal_num, high_price, low_price
                #d = datetime.datetime.utcfromtimestamp(float(dot[0] / 1000)).strftime('%Y\t%m\t%d\t%H\t%M\t')
                d = datetime.datetime.utcfromtimestamp(float(dot[0] / 1000)).strftime('%H%M\t')
                
                l[d] = DailyInfo({
                    'deal_price': float(dot[1]),
                    'count'     : float(dot[2]),
                    'high_price': float(dot[3]),
                    'low_price' : float(dot[4])
                })
        
            return l
        
        def transaction_info_parser():
        
            # If we need daily transction info, search if the data is availiable
            filename = os.path.join('data', self.stock, 'trans_'+date+'.pickle')

            if not os.path.exists(filename):
                return None

            d = pickle_load(filename)
            return collections.OrderedDict((k, DailyInfo(v)) for k, v in d.items())    
            
        def json2dic(json):
            return DetailInfo({'open_price': json['RealInfo']['OpenPrice'], 
                    'last_close_price': json['RealInfo']['PrvSalePrice'], 
                    'daily_magnitude': json['RealInfo']['MagnitudeOfPrice'],
                    'daily_amount': json['RealInfo']['Amount'],
                    'lowest_price': json['RealInfo']['LowPrice'],
                    'highest_price': json['RealInfo']['HighPrice'],
                    'data': JSONParser(json, 'DataPrice') if not every_transaction else transaction_info_parser()
                    })
        
        return json2dic(json)
    
    
    
    def get_next_opening(self, date, diff=1):
        year, month, day = int(date[:4]), int(date[4:6]), int(date[6:])
    
        next_day = datetime.date(year, month, day) + datetime.timedelta(days=diff)
        year, month, day = next_day.year, next_day.month, next_day.day
        #print year, month, day
    
        while not self.is_stock_open("%d%0.2d%0.2d" % (year, month, day)):
            #print 'in next day loop'
            current_date = datetime.date(year, month, day)
            yesterday_date = datetime.datetime.today().date() - datetime.timedelta(days=1)
            #assert current_date < yesterday_date, 'Can not use future days'
            next_day = datetime.date(year, month, day) + datetime.timedelta(days=diff)
            year, month, day = next_day.year, next_day.month, next_day.day
            #print year, month, day
        return "%d%0.2d%0.2d" % (year, month, day)
    
    def get_stock_finance(self, date):
        
        filename = os.path.join('data', self.stock, 'finance.pickle')

        if os.path.exists(filename):
        
            d = pickle_load(filename)
            
            if date in d:
                return d[date]
            elif max(map(int, d.keys())) < date:
                pass
            else:
                assert date in d, 'The stock %s is not open at %s' % (self.stock, date)
                    
        else:    
        
            d = collections.OrderedDict()
            
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
            d[element['Date']] = element
        
        pickle_save(filename, d)
        self.cache['date_list_cache'] = d
        
        assert min(map(int, d.keys())) <= int(date), 'Date too old, can not obtain'
            
        return d[date] if date in d else None
    
    def iterate_date(self, date_start, date_end=datetime.datetime.now().strftime('%Y%m%d')):
        date_start = date_start if self.is_stock_open(date_start) else self.get_next_opening(date_start)
        date_end = date_end if self.is_stock_open(date_end) else self.get_next_opening(date_end, diff=-1)
        assert date_start < date_end, 'should not iterate through future'
        
        while date_start < date_end:
            yield date_start
            date_start = self.get_next_opening(date_start)
        yield date_end
        
    def update_daily_info(self, today_date=None):
    
        # Not specified date, use today
        if not today_date:
            today = datetime.datetime.today().date()
            year, month, day = today.year, today.month, today.day
            today_date = '%d%0.2d%0.2d' % (year, month, day)
            print 'Today is %s' % today_date
        
        filename = os.path.join('data', self.stock, 'trans_' + today_date + '.pickle')
        
        if os.path.exists(filename):
            print 'already download'
        else:
            pickle_save(filename, stock_daily_parser(self.stock))
            
###########################################################
# Private Function
###########################################################
def pickle_save(filename, data):
    '''
    :param filename: pickle filename
    :param data: the dictionary that store date
    :return: None
    '''
    with open(filename, 'wb') as f:
        pickle.dump(data, f)

def pickle_load(filename):
    '''
    :param filename: the pickle filename
    :return: the dictionary that store date
    '''
    if not os.path.exists(filename):
        return None
    
    with open(filename, 'rb') as f:
        data = pickle.load(f)
        
    return data
    
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
    #with open('tmp.html') as f:
    #    content = f.read()
    
    content = re.sub(r'<font.*?>', '', content)
    content = re.sub(r'</font.*?>', '', content)
    soup = BeautifulSoup(content, 'html.parser')
        
    d = {}
    
    
    for row in soup.select('table#tb_chart > tr')[1:-1]:
        
        time, buy, sell, deal, diff, count, acc = [td.text for td in row.find_all('td')]
        time = '%06s' % time.replace(':', '')
        
        if sell == '--':
            sell = buy
            
        d[time] = {'buy': float(buy), \
                'sell': float(sell),\
                'deal': float(deal),\
                'diff': float(diff),\
                'count': float(count)}
        
    return collections.OrderedDict(sorted(d.items(), key=lambda k: k))






    

    
###########################################################
# Public Function
###########################################################


def __main__():
    pass
    


__main__()
        