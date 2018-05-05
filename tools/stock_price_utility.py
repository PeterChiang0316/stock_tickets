# -*- coding: utf-8 -*-
import requests, os, re, datetime, collections, math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import xlsxwriter
from bs4 import BeautifulSoup
import time, pickle, sys


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
            
    def is_stock_open(self, day):
    
        '''
        :param day: stock date
        :return: True if stock opens in specified day
        '''
        filename = os.path.join(self.stock_data_folder, 'finance.pickle')
        
        if not os.path.exists(filename):
            self.get_stock_finance(day)
        
        date_list = pickle_load(filename)
        assert min(map(int, date_list.keys())) <= int(day), 'Date too old, can not obtain'
        
        return day in date_list
    
    def get_stock_daily_info(self, date):
    
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
            l = []
        
            for dot in dots:
                # time, deal_price, deal_num, high_price, low_price
                #d = datetime.datetime.utcfromtimestamp(float(dot[0] / 1000)).strftime('%Y\t%m\t%d\t%H\t%M\t')
                d = datetime.datetime.utcfromtimestamp(float(dot[0] / 1000)).strftime('%H%M\t')
                l.append(d + '\t'.join(map(str, dot[1:])))
        
            return l
            
        def json2dic(json):
            return {'open_price': json['RealInfo']['OpenPrice'], 
                    'last_close_price': json['RealInfo']['PrvSalePrice'], 
                    'daily_magnitude': json['RealInfo']['MagnitudeOfPrice'],
                    'daily_amount': json['RealInfo']['Amount'],
                    'low_price': json['RealInfo']['LowPrice'],
                    'high_price': json['RealInfo']['HighPrice'],
                    'data': JSONParser(json, 'DataPrice')
                    }
        
        return json2dic(json)
    
    
    
    def get_next_opening(date, diff=1):
        year, month, day = int(date[:4]), int(date[4:6]), int(date[6:])
    
        next_day = datetime.date(year, month, day) + datetime.timedelta(days=diff)
        year, month, day = next_day.year, next_day.month, next_day.day
        #print year, month, day
    
        while not is_stock_open("%d%0.2d%0.2d" % (year, month, day)):
            #print 'in next day loop'
            current_date = datetime.date(year, month, day)
            yesterday_date = datetime.datetime.today().date() - datetime.timedelta(days=diff)
            assert current_date < yesterday_date, 'Can not use future days'
            next_day = datetime.date(year, month, day) + datetime.timedelta(days=diff)
            year, month, day = next_day.year, next_day.month, next_day.day
            print year, month, day
        return "%d%0.2d%0.2d" % (year, month, day)
    
    def get_stock_finance(self, date):
        
        filename = os.path.join('data', self.stock, 'finance.pickle')

        if os.path.exists(filename):
        
            d = pickle_load(filename)
            
            if date in d:
                return d[date]
            elif max(map(int, d.keys())) < self.stock:
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
            d[element['Date']] = element
        
        pickle_save(filename, d)
        
        assert min(map(int, d.keys())) <= int(date), 'Date too old, can not obtain'
            
        return d[date]
    
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







    

    
###########################################################
# Public Function
###########################################################


def __main__():
    pass
    


__main__()
        