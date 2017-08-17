try:
    from FlaskApp.FlaskApp import app
except:
    import sys

    sys.path.append('..')
    from FlaskApp import app
from flask import request, json, make_response
from functools import wraps
import time
import datetime
import os
import pandas as pd
import tushare as ts


##---------------------------------------------------utils--------------------------------
def unix_to_str(unixtime):
    return datetime.datetime.fromtimestamp(int(unixtime)).strftime('%Y-%m-%d')


def time_to_unix(date_list):
    unix_list = []
    for date in date_list:
        timetuple = time.strptime(date, "%Y-%m-%d")
        unix_list.append(int(time.mktime(timetuple)))
    return unix_list

def get_stock_type(stock_code):
    """判断股票ID对应的证券市场
    匹配规则
    ['50', '51', '60', '90', '110'] 为 sh
    ['00', '13', '18', '15', '16', '18', '20', '30', '39', '115'] 为 sz
    ['5', '6', '9'] 开头的为 sh， 其余为 sz
    :param stock_code:股票ID, 若以 'sz', 'sh' 开头直接返回对应类型，否则使用内置规则判断
    :return 'sh' or 'sz'"""
    assert type(stock_code) is str, 'stock code need str type'
    if stock_code.startswith(('SH', 'SZ')):
        return stock_code[:2]
    if stock_code.startswith(('50', '51', '60', '73', '90', '110', '113', '132', '204', '78')):
        return 'SH'
    if stock_code.startswith(('00', '13', '18', '15', '16', '18', '20', '30', '39', '115', '1318')):
        return 'SZ'
    if stock_code.startswith(('5', '6', '9')):
        return 'SH'
    return 'SZ'


def allow_cross_domain(fun):
    @wraps(fun)
    def wrapper_fun(*args, **kwargs):
        rst = make_response(fun(*args, **kwargs))
        rst.headers['Access-Control-Allow-Origin'] = '*'
        rst.headers['Access-Control-Allow-Methods'] = 'PUT,GET,POST,DELETE'
        allow_headers = "Referer,Accept,Origin,User-Agent"
        rst.headers['Access-Control-Allow-Headers'] = allow_headers
        return rst
    return wrapper_fun

## ---------------------------------------------------api---------------------------------
stock_basic = ts.get_stock_basics()

@app.route('/config', methods=['GET'])
@allow_cross_domain
def config():
    config = {'supports_search': True,
              'supports_group_request': False,
              'supported_resolutions': ["1D", "1W", "1M"],
              'supports_marks': False,
              'supports_time': True,
              'supports_timescale_marks': False,
              'exchanges':[{'value':'', 'name':'All Exchanges', 'desc':''},
                           {'value':'SZ', 'name':'SZ', 'desc':'SZ'},
                           {'value':'SH', 'name':'SH', 'desc':'SH'}],
              'symbolsTypes':[{'name':'All types', 'value':''},
                              {'name':'Stock', 'value':'stock'}]}
    return json.dumps(config)


@app.route('/symbols', methods=['GET'])
@allow_cross_domain
def symbols():
    symbol = request.values.get('symbol')
    symbol_return = {'symbol': symbol,
                     'description': stock_basic[stock_basic.index == symbol]['name'][0],
                     'exchange-listed': get_stock_type(symbol),
                     'exchange-traded': get_stock_type(symbol),
                     'minmov': 1,
                     'minmov2': 0,
                     'pricescale': [1, 1, 100],
                     'has-dwm': 'true',
                     'has-intraday': 'true',
                     'has-no-volume': 'false',
                     'type': 'stock',
                     'ticker': '%s%s' % (get_stock_type(symbol),symbol),
                     'timezone': 'Asia/Shanghai',
                     'session-regular': '0900-1500'}
    return json.dumps(symbol_return)


@app.route('/search', methods=['GET'])
@allow_cross_domain
def search_symbols():
    query = request.values.get('query')
    type = request.values.get('type')
    exchange = request.values.get('exchange')
    limit = int(request.values.get('limit'))
    try:
        returndict = {'symbol':query,
                  'full_name': stock_basic[stock_basic.index == query]['name'][0],
                  'description': stock_basic[stock_basic.index == query]['name'][0],
                  'exchange':get_stock_type(query),
                  'ticker':query,
                  'type':'stock'}
        return json.dumps([returndict])
    except:
        return json.dumps([])



@app.route('/history', methods=['GET'])
@allow_cross_domain
def history():
    symbol = request.values.get('symbol')[2:]
    resolution = request.values.get('resolution')
    from_date = request.values.get('from')
    to_date = request.values.get('to')
    if resolution == 'D':
        from_date = unix_to_str(from_date)
        to_date = unix_to_str(to_date)
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        if to_date == today:
            history_df = ts.get_k_data(symbol)
        else:
            history_df = ts.get_k_data(symbol, ktype='D', start=from_date, end=to_date)
        if len(history_df) == 0:
            s = 'no_data'
            try:
                next_his = ts.get_k_data(symbol, ktype='D', start=to_date)['date'].tolist()
                nextTime = time_to_unix(next_his)[0]
            except:
                dtime = datetime.datetime.now()
                nextTime = time.mktime(dtime.timetuple())
            his_dict = {'s': s,
                        'nextTime': nextTime}
            return json.dumps(his_dict)
        else:
            s = 'ok'
            t_list = time_to_unix(history_df['date'].tolist())
            c = history_df['close'].tolist()
            o = history_df['open'].tolist()
            h = history_df['high'].tolist()
            l = history_df['low'].tolist()
            v = history_df['volume'].tolist()
            his_dict = {'s': s,
                        't': t_list,
                        'c': c,
                        'o': o,
                        'h': h,
                        'l': l,
                        'v': v}
            return json.dumps(his_dict)


@app.route('/time', methods=['GET'])
@allow_cross_domain
def get_time():
    dtime = datetime.datetime.now()
    ans_time = time.mktime(dtime.timetuple())
    return str(int(ans_time))
