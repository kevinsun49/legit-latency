import urllib
import urllib2
import datetime
import xml.etree.cElementTree as ElementTree
import re
from pprint import pprint
import correlate

# Returns a list of dictionaries
# Use if you XML contains multiple elements at the same level
class Xml2List(list):
    def __init__(self, aList):
        for element in aList:
            if element:
                if len(element) == 1 or element[0].tag != element[1].tag:
                    self.append(Xml2Dict(element))
                elif element[0].tag == element[1].tag:
                    self.append(Xml2List(element))
            elif element.text:
                text = element.text.strip()
                if text:
                    self.append(text)

# Returns a properly formatted dictionary
class Xml2Dict(dict):
    '''
    Example usage:
    Given an XML string:
    >>> root = ElementTree.XML(xml_string)
    >>> xmldict = Xml2Dict(root)
    '''
    def __init__(self, parent_element):
        if parent_element.items():
            self.update(dict(parent_element.items()))
        for element in parent_element:
            if element:
                if len(element) == 1 or element[0].tag != element[1].tag:
                    aDict = Xml2Dict(element)
                else:
                    aDict = {element[0].tag: Xml2List(element)}
                if element.items():
                    aDict.update(dict(element.items()))
                self.update({element.tag: aDict})
            elif element.items():
                self.update({element.tag: dict(element.items())})
            else:
                self.update({element.tag: element.text})

#input: market center code, stock ticker symbol, datetime objects (use make_string(date)), and interval in ms
#output: list of prices for each millisecond in input time interval
def get_summarized_trades(market_center, symbol, start_time, stop_time, interval=1):
    url = 'http://ws.nasdaqdod.com/v1/NASDAQAnalytics.asmx/GetSummarizedTrades'
    ms = datetime.timedelta(0,0,interval)
    prices, times = [], []

    #set parameters of the DOD search
    values = {'_Token' : '25D26255F6924F31BD86503A4253BEA0',
          'Symbols' : symbol,
          'StartDateTime' :  make_string(start_time),
          'EndDateTime' : make_string(stop_time),
          'MarketCenters' : market_center,
          'TradePrecision' : 'Second',
          'TradePeriod' : '1'}
    request_parameters = urllib.urlencode(values)
    req = urllib2.Request(url, request_parameters)

    try:
        response = urllib2.urlopen(req)
    except urllib2.HTTPError as e:
        print(e.code)
        print(e.read())

    the_page = response.read()
    the_page = re.sub(' xmlns="[^"]+"', '', the_page, count=1)
    root = ElementTree.XML(the_page)
    data = Xml2List(root)

    #use data to populate a list of times and prices from the search
    tradedata = data[0]['SummarizedTrades']['SummarizedTrade']
    if isinstance(tradedata, Xml2Dict):
        prices.append(tradedata['TWAP'])
        times.append(datetime.datetime.strptime(tradedata['Time'][:-4].replace('/', '-').replace(' ', '-').replace(':', '-') , "%d-%m-%Y-%H-%M-%S"))
    else:
        for trade in tradedata:
            prices.append(trade['TWAP'])
            times.append(datetime.datetime.strptime(trade['Time'][:-4].replace('/', '-').replace(' ', '-').replace(':', '-') , "%d-%m-%Y-%H-%M-%S"))
    extended_prices, temp, last_price = [], times[0], prices[0]
    while temp < times[len(times) - 1]:
        if temp in times:
            extended_prices.append(float(prices[times.index(temp)]))
            last_price = prices[times.index(temp)]
        else:
            last_index = prices.index(last_price)
            extended_prices.append(float(last_price) + (float(prices[last_index + 1]) - float(last_price))/((times[last_index + 1] - times[last_index]).total_seconds() * 1000) * (temp - times[last_index]).total_seconds() * 1000)
        temp = temp + ms
    return extended_prices

# turns a datetime object into a string that matches with the api's parameters
def make_string( date):
    return str(date ).replace('-' ,'/')

# takes array of price points with corresponding time interval and returns
# array of the same length of derivatives with units $/ms
def calc_dpdt(price):
    if len(price) == 0:
        return 0
    elif len(price) == 1:
        return 0
    else:
        return [price[i+1] - price[i] for i in range(len(price) - 1)] + [price[len(price)-1] - price[len(price)-2]]

#return latency between two stocks
def calc_latency_two_stocks(symbol1, symbol2, market1, market2, start_time, stop_time):
    summarized_trade1 = get_summarized_trades(market1, symbol1, start_time, stop_time)
    summarized_trade2 = get_summarized_trades(market2, symbol2, start_time, stop_time)
    dpdt1 = calc_dpdt(summarized_trade1)
    dpdt2 = calc_dpdt(summarized_trade2)
    print 'done'
    #return correlate.correlation(dpdt1, dpdt2)
    #the correlation function is rather inefficient right now and can take a very long time to compute


#set parameters
start_time = datetime.datetime(2016, 9, 8, 9, 30, 0, 0)
stop_time = datetime.datetime(2016, 9, 8, 9, 30, 5, 0)
market_center1 = 'P'
market_center2 = 'Q'
symbol1= 'NVDA'
symbol2 = 'GOOG'

calc_latency_two_stocks(symbol1, symbol2, market_center1 , market_center2, start_time, stop_time)