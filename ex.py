import urllib
import urllib2
import datetime
import xml.etree.cElementTree as ElementTree
import re
from pprint import pprint

def identify_peak(ds):
    return ds.index(max(ds))

def roll(lst):
    lst[0], lst[1:] = lst[-1], lst[0:-1]

def dot(l1, l2):
    total = 0
    for i in range(len(l1)):
        total += (l1[i] * l2[i])
    return total

def cross_correlate(d1, d2):
    length1, length2 = len(d1), len(d2)
    paddedlength = length1 + length2 - 1
    padded1, padded2 = [0] * paddedlength, [0] * paddedlength
    for i in range(length1):
        padded1[i] = d1[i]
    for i in range(length1 - 1, length1 + length2 - 1):
        padded2[i] = d2[i - (length1 - 1)]
    roll(padded2)
    correlation = []
    for _ in range(len(padded2)):
        correlation.append(dot(padded1, padded2))
        roll(padded2)
    return correlation

#returns delay in ms of d2 when compared to d1 (d1 and d2 are the dp/dt arrays)
def correlation(d1, d2):
    return identify_peak(cross_correlate(d1, d2))

# Returns a list of dictionaries
# Use if you XML contains multiple elements at the same level
#
class Xml2List(list):
    def __init__(self, aList):
        for element in aList:
            if element:
                # treat like dict
                if len(element) == 1 or element[0].tag != element[1].tag:
                    self.append(Xml2Dict(element))
                # treat like list
                elif element[0].tag == element[1].tag:
                    self.append(Xml2List(element))
            elif element.text:
                text = element.text.strip()
                if text:
                    self.append(text)

# Returns a dictionary
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
                # treat like dict - we assume that if the first two tags
                # in a series are different, then they are all different.
                if len(element) == 1 or element[0].tag != element[1].tag:
                    aDict = Xml2Dict(element)
                # treat like list - we assume that if the first two tags
                # in a series are the same, then the rest are the same.
                else:
                    # here, we put the list in dictionary; the key is the
                    # tag name the list elements all share in common, and
                    # the value is the list itself
                    aDict = {element[0].tag: Xml2List(element)}
                # if the tag has attributes, add those to the dict
                if element.items():
                    aDict.update(dict(element.items()))
                self.update({element.tag: aDict})
            # this assumes that if you've got an attribute in a tag,
            # you won't be having any text. This may or may not be a
            # good idea -- time will tell.
            elif element.items():
                self.update({element.tag: dict(element.items())})
            # finally, if there are no child tags and no attributes, extract
            # the text
            else:
                self.update({element.tag: element.text})


#Given the market_center code, symbol code, start_time, and stop_time in ?? format,
#and interval in ms, return an array of average? bid or offer? for
#every ms.
def get_summarized_trades(market_center, symbol, start_time, stop_time, interval=1):
    url = 'http://ws.nasdaqdod.com/v1/NASDAQAnalytics.asmx/GetSummarizedTrades'
    ms = datetime.timedelta(0,0,interval)
    prices, times = [], []


    # a bunch of code I copied from the nasdaq git example
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
# stringifies a datetime object in the correct format for teh api hopefully
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
    #return correlation(dpdt1, dpdt2)
    #the correlation function is rather inefficient right now and can take a very long time to compute


#Sample Usage
start_time = datetime.datetime(2016, 9, 8, 9, 30, 0, 0)
stop_time = datetime.datetime(2016, 9, 8, 9, 30, 5, 0)
market_center1 = 'P'
market_center2 = 'Q'
symbol1= 'NVDA'
symbol2 = 'GOOG'

calc_latency_two_stocks(symbol1, symbol2, market_center1 , market_center2, start_time, stop_time)