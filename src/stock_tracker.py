"""
个股追踪模块
支持A股、港股、美股的行情获取和新闻聚合
"""

import requests
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

class StockTracker:
    """个股追踪器"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 市场类型识别
        self.market_patterns = {
            'sh': r'^6\d{5}$',      # 上证
            'sz': r'^[03]\d{5}$',   # 深证
            'bj': r'^[48]\d{5}$',   # 北交所
            'hk': r'^\d{5}$',       # 港股
            'us': r'^[A-Z]+$',      # 美股
        }
    
    def identify_market(self, symbol: str) -> str:
        """识别股票所属市场"""
        symbol = symbol.upper().strip()
        
        if re.match(r'^6\d{5}$', symbol):
            return 'sh'
        elif re.match(r'^[03]\d{5}$', symbol):
            return 'sz'
        elif re.match(r'^[48]\d{5}$', symbol):
            return 'bj'
        elif re.match(r'^\d{5}$', symbol):
            return 'hk'
        elif re.match(r'^[A-Z]+$', symbol):
            return 'us'
        else:
            return 'unknown'
    
    def get_stock_quote(self, symbol: str) -> Optional[Dict]:
        """获取股票实时行情"""
        market = self.identify_market(symbol)
        
        if market in ['sh', 'sz', 'bj']:
            return self._get_a_stock_quote(symbol, market)
        elif market == 'hk':
            return self._get_hk_stock_quote(symbol)
        elif market == 'us':
            return self._get_us_stock_quote(symbol)
        else:
            return None
    
    def _get_a_stock_quote(self, symbol: str, market: str) -> Optional[Dict]:
        """获取A股行情 - 使用东方财富"""
        try:
            # 东方财富行情接口
            market_code = '1' if market == 'sh' else '0'
            url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={market_code}.{symbol}&fields=f57,f58,f43,f44,f45,f46,f47,f48,f50,f51,f52,f60,f168,f169,f170,f171"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json().get('data', {})
                if data:
                    return {
                        'symbol': symbol,
                        'name': data.get('f58', ''),
                        'market': market,
                        'price': data.get('f43', 0) / 100 if data.get('f43') else 0,
                        'change': data.get('f169', 0) / 100 if data.get('f169') else 0,
                        'change_pct': data.get('f170', 0) / 100 if data.get('f170') else 0,
                        'open': data.get('f46', 0) / 100 if data.get('f46') else 0,
                        'high': data.get('f44', 0) / 100 if data.get('f44') else 0,
                        'low': data.get('f45', 0) / 100 if data.get('f45') else 0,
                        'prev_close': data.get('f60', 0) / 100 if data.get('f60') else 0,
                        'volume': data.get('f47', 0),
                        'amount': data.get('f48', 0),
                        'turnover_rate': data.get('f168', 0) / 100 if data.get('f168') else 0,
                        'pe_ratio': data.get('f50', 0) / 100 if data.get('f50') else 0,
                        'market_cap': data.get('f171', 0),
                        'timestamp': datetime.now().isoformat()
                    }
        except Exception as e:
            print(f"获取A股行情失败: {e}")
        return None
    
    def _get_hk_stock_quote(self, symbol: str) -> Optional[Dict]:
        """获取港股行情"""
        try:
            url = f"https://push2.eastmoney.com/api/qt/stock/get?secid=116.{symbol}&fields=f57,f58,f43,f44,f45,f46,f47,f48,f60,f169,f170"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json().get('data', {})
                if data:
                    return {
                        'symbol': symbol,
                        'name': data.get('f58', ''),
                        'market': 'hk',
                        'price': data.get('f43', 0) / 1000 if data.get('f43') else 0,
                        'change': data.get('f169', 0) / 1000 if data.get('f169') else 0,
                        'change_pct': data.get('f170', 0) / 100 if data.get('f170') else 0,
                        'open': data.get('f46', 0) / 1000 if data.get('f46') else 0,
                        'high': data.get('f44', 0) / 1000 if data.get('f44') else 0,
                        'low': data.get('f45', 0) / 1000 if data.get('f45') else 0,
                        'prev_close': data.get('f60', 0) / 1000 if data.get('f60') else 0,
                        'volume': data.get('f47', 0),
                        'amount': data.get('f48', 0),
                        'currency': 'HKD',
                        'timestamp': datetime.now().isoformat()
                    }
        except Exception as e:
            print(f"获取港股行情失败: {e}")
        return None
    
    def _get_us_stock_quote(self, symbol: str) -> Optional[Dict]:
        """获取美股行情"""
        try:
            # 使用东方财富美股接口
            url = f"https://push2.eastmoney.com/api/qt/stock/get?secid=105.{symbol}&fields=f57,f58,f43,f44,f45,f46,f47,f60,f169,f170"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json().get('data', {})
                if data:
                    return {
                        'symbol': symbol,
                        'name': data.get('f58', ''),
                        'market': 'us',
                        'price': data.get('f43', 0) / 100 if data.get('f43') else 0,
                        'change': data.get('f169', 0) / 100 if data.get('f169') else 0,
                        'change_pct': data.get('f170', 0) / 100 if data.get('f170') else 0,
                        'currency': 'USD',
                        'timestamp': datetime.now().isoformat()
                    }
        except Exception as e:
            print(f"获取美股行情失败: {e}")
        
        # 备用：Yahoo Finance
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                result = data.get('chart', {}).get('result', [{}])[0]
                meta = result.get('meta', {})
                return {
                    'symbol': symbol,
                    'name': meta.get('shortName', symbol),
                    'market': 'us',
                    'price': meta.get('regularMarketPrice', 0),
                    'prev_close': meta.get('chartPreviousClose', 0),
                    'change_pct': ((meta.get('regularMarketPrice', 0) - meta.get('chartPreviousClose', 1)) / meta.get('chartPreviousClose', 1)) * 100,
                    'currency': meta.get('currency', 'USD'),
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Yahoo Finance获取失败: {e}")
        
        return None
    
    def get_stock_news(self, symbol: str, name: str = '', limit: int = 20) -> List[Dict]:
        """获取个股相关新闻"""
        news_list = []
        market = self.identify_market(symbol)
        
        if market in ['sh', 'sz', 'bj']:
            news_list.extend(self._get_eastmoney_stock_news(symbol, limit))
        elif market == 'us':
            news_list.extend(self._get_yahoo_stock_news(symbol, limit))
        
        # 如果有股票名称，搜索相关新闻
        if name:
            news_list.extend(self._search_baidu_news(name, limit // 2))
        
        return news_list[:limit]
    
    def _get_eastmoney_stock_news(self, symbol: str, limit: int = 20) -> List[Dict]:
        """东方财富个股新闻"""
        news_list = []
        try:
            market = self.identify_market(symbol)
            market_code = '1' if market == 'sh' else '0'
            
            url = f"https://np-listapi.eastmoney.com/comm/wap/getListInfo?cb=&type=1&pageSize={limit}&pageIndex=0&code={market_code}.{symbol}"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                text = response.text
                if text.startswith('('):
                    text = text[1:-1]
                data = json.loads(text) if text else {}
                items = data.get('data', {}).get('list', [])
                
                for item in items:
                    title = item.get('title', '')
                    title = re.sub(r'<[^>]+>', '', title)
                    
                    news_list.append({
                        'title': title,
                        'content': item.get('digest', '') or title,
                        'source': '东方财富',
                        'url': item.get('url', ''),
                        'published_at': item.get('showtime', datetime.now().isoformat()),
                        'stock_code': symbol
                    })
        except Exception as e:
            print(f"获取东方财富新闻失败: {e}")
        
        return news_list
    
    def _get_yahoo_stock_news(self, symbol: str, limit: int = 20) -> List[Dict]:
        """Yahoo Finance股票新闻"""
        news_list = []
        try:
            url = f"https://query1.finance.yahoo.com/v1/finance/search?q={symbol}&newsCount={limit}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get('news', [])
                
                for item in items:
                    news_list.append({
                        'title': item.get('title', ''),
                        'content': item.get('title', ''),
                        'source': item.get('publisher', 'Yahoo Finance'),
                        'url': item.get('link', ''),
                        'published_at': datetime.fromtimestamp(item.get('providerPublishTime', 0)).isoformat() if item.get('providerPublishTime') else datetime.now().isoformat(),
                        'stock_code': symbol
                    })
        except Exception as e:
            print(f"获取Yahoo Finance新闻失败: {e}")
        
        return news_list
    
    def _search_baidu_news(self, keyword: str, limit: int = 10) -> List[Dict]:
        """百度新闻搜索"""
        news_list = []
        try:
            url = f"https://www.baidu.com/s?tn=news&rtt=1&bsst=1&cl=2&wd={keyword}"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.select('.result')[:limit]
                
                for item in items:
                    title_elem = item.select_one('h3 a')
                    source_elem = item.select_one('.c-author')
                    
                    if title_elem:
                        news_list.append({
                            'title': title_elem.get_text(strip=True),
                            'content': title_elem.get_text(strip=True),
                            'source': source_elem.get_text(strip=True) if source_elem else '百度新闻',
                            'url': title_elem.get('href', ''),
                            'published_at': datetime.now().isoformat()
                        })
        except Exception as e:
            print(f"百度新闻搜索失败: {e}")
        
        return news_list
    
    def get_company_announcements(self, symbol: str, limit: int = 10) -> List[Dict]:
        """获取公司公告 - 捕捉新产品发布等一手信息"""
        announcements = []
        market = self.identify_market(symbol)
        
        if market not in ['sh', 'sz', 'bj']:
            return announcements
        
        try:
            # 东方财富公告接口
            market_code = 'SH' if market == 'sh' else 'SZ'
            url = f"https://np-anotice-stock.eastmoney.com/api/security/ann?page_index=1&page_size={limit}&ann_type=A&stock_list={market_code}{symbol}"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get('data', {}).get('list', [])
                
                for item in items:
                    # 识别重要公告类型
                    title = item.get('title', '')
                    importance = 'normal'
                    
                    important_keywords = ['新产品', '中标', '签订', '合同', '订单', '增持', 
                                         '回购', '分红', '业绩', '盈利', '亏损', '重组', 
                                         '收购', '出售', '诉讼', '处罚', '立案']
                    for kw in important_keywords:
                        if kw in title:
                            importance = 'high'
                            break
                    
                    announcements.append({
                        'title': title,
                        'source': '公司公告',
                        'category': item.get('columns', [{}])[0].get('column_name', '') if item.get('columns') else '',
                        'url': f"https://data.eastmoney.com/notices/detail/{symbol}/{item.get('art_code', '')}.html",
                        'published_at': item.get('notice_date', ''),
                        'importance': importance,
                        'stock_code': symbol
                    })
        except Exception as e:
            print(f"获取公司公告失败: {e}")
        
        return announcements
    
    def search_stocks(self, keyword: str, limit: int = 10) -> List[Dict]:
        """搜索股票"""
        results = []
        try:
            url = f"https://searchapi.eastmoney.com/api/suggest/get?input={keyword}&type=14&count={limit}"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get('QuotationCodeTable', {}).get('Data', [])
                
                for item in items:
                    market_map = {'1': 'sh', '0': 'sz', '116': 'hk', '105': 'us'}
                    market = market_map.get(str(item.get('MarketId', '')), 'unknown')
                    
                    results.append({
                        'symbol': item.get('Code', ''),
                        'name': item.get('Name', ''),
                        'market': market,
                        'pinyin': item.get('QuoteId', '')
                    })
        except Exception as e:
            print(f"搜索股票失败: {e}")
        
        return results
    
    def get_batch_quotes(self, symbols: List[str]) -> List[Dict]:
        """批量获取行情"""
        quotes = []
        for symbol in symbols:
            quote = self.get_stock_quote(symbol)
            if quote:
                quotes.append(quote)
        return quotes
    
    def get_stock_kline(self, symbol: str, period: str = 'daily', limit: int = 60) -> List[Dict]:
        """获取K线数据
        
        Args:
            symbol: 股票代码
            period: 周期类型 daily/weekly/monthly
            limit: 数据条数
        
        Returns:
            K线数据列表 [{date, open, close, high, low, volume, amount}, ...]
        """
        market = self.identify_market(symbol)
        kline_data = []
        
        # 周期映射
        period_map = {
            'daily': '101',
            'weekly': '102', 
            'monthly': '103'
        }
        klt = period_map.get(period, '101')
        
        if market in ['sh', 'sz', 'bj']:
            kline_data = self._get_a_stock_kline(symbol, market, klt, limit)
        elif market == 'hk':
            kline_data = self._get_hk_stock_kline(symbol, klt, limit)
        elif market == 'us':
            kline_data = self._get_us_stock_kline(symbol, period, limit)
        
        return kline_data
    
    def _get_a_stock_kline(self, symbol: str, market: str, klt: str, limit: int) -> List[Dict]:
        """获取A股K线数据"""
        kline_data = []
        try:
            market_code = '1' if market == 'sh' else '0'
            url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={market_code}.{symbol}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt={klt}&fqt=1&end=20500101&lmt={limit}"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json().get('data', {})
                klines = data.get('klines', [])
                
                for kline in klines:
                    parts = kline.split(',')
                    if len(parts) >= 7:
                        kline_data.append({
                            'date': parts[0],
                            'open': float(parts[1]),
                            'close': float(parts[2]),
                            'high': float(parts[3]),
                            'low': float(parts[4]),
                            'volume': int(float(parts[5])),
                            'amount': float(parts[6]),
                            'change_pct': float(parts[8]) if len(parts) > 8 else 0
                        })
        except Exception as e:
            print(f"获取A股K线失败: {e}")
        
        return kline_data
    
    def _get_hk_stock_kline(self, symbol: str, klt: str, limit: int) -> List[Dict]:
        """获取港股K线数据"""
        kline_data = []
        try:
            url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=116.{symbol}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt={klt}&fqt=1&end=20500101&lmt={limit}"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json().get('data', {})
                klines = data.get('klines', [])
                
                for kline in klines:
                    parts = kline.split(',')
                    if len(parts) >= 7:
                        kline_data.append({
                            'date': parts[0],
                            'open': float(parts[1]),
                            'close': float(parts[2]),
                            'high': float(parts[3]),
                            'low': float(parts[4]),
                            'volume': int(float(parts[5])),
                            'amount': float(parts[6]),
                            'change_pct': float(parts[8]) if len(parts) > 8 else 0
                        })
        except Exception as e:
            print(f"获取港股K线失败: {e}")
        
        return kline_data
    
    def _get_us_stock_kline(self, symbol: str, period: str, limit: int) -> List[Dict]:
        """获取美股K线数据 - 使用Yahoo Finance"""
        kline_data = []
        try:
            interval_map = {'daily': '1d', 'weekly': '1wk', 'monthly': '1mo'}
            interval = interval_map.get(period, '1d')
            
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range=3mo"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                result = data.get('chart', {}).get('result', [{}])[0]
                
                timestamps = result.get('timestamp', [])
                quote = result.get('indicators', {}).get('quote', [{}])[0]
                
                opens = quote.get('open', [])
                closes = quote.get('close', [])
                highs = quote.get('high', [])
                lows = quote.get('low', [])
                volumes = quote.get('volume', [])
                
                for i in range(min(len(timestamps), limit)):
                    if timestamps[i] and closes[i]:
                        kline_data.append({
                            'date': datetime.fromtimestamp(timestamps[i]).strftime('%Y-%m-%d'),
                            'open': round(opens[i] or 0, 2),
                            'close': round(closes[i] or 0, 2),
                            'high': round(highs[i] or 0, 2),
                            'low': round(lows[i] or 0, 2),
                            'volume': int(volumes[i] or 0),
                            'amount': 0,
                            'change_pct': 0
                        })
        except Exception as e:
            print(f"获取美股K线失败: {e}")
        
        return kline_data
    
    def get_stock_detail(self, symbol: str) -> Dict:
        """获取股票详细信息，包括行情、K线、新闻等"""
        quote = self.get_stock_quote(symbol) or {}
        kline = self.get_stock_kline(symbol, 'daily', 30)
        news = self.get_stock_news(symbol, quote.get('name', ''), limit=5)
        
        return {
            'quote': quote,
            'kline': kline,
            'news': news
        }


# 测试
if __name__ == '__main__':
    print("=== 个股追踪测试 ===\n")
    
    tracker = StockTracker()
    
    # 测试搜索
    print("1. 搜索股票...")
    results = tracker.search_stocks("九阳")
    for r in results[:3]:
        print(f"   {r['symbol']} - {r['name']} ({r['market']})")
    
    # 测试A股行情
    print("\n2. 获取A股行情...")
    quote = tracker.get_stock_quote("002242")  # 九阳股份
    if quote:
        print(f"   {quote['name']} ({quote['symbol']})")
        print(f"   价格: {quote['price']} 涨跌幅: {quote['change_pct']}%")
    
    # 测试美股行情
    print("\n3. 获取美股行情...")
    quote = tracker.get_stock_quote("AAPL")
    if quote:
        print(f"   {quote['name']} ({quote['symbol']})")
        print(f"   价格: ${quote['price']}")
    
    # 测试公司公告
    print("\n4. 获取公司公告...")
    announcements = tracker.get_company_announcements("002242", 5)
    for ann in announcements[:3]:
        print(f"   [{ann['importance']}] {ann['title'][:40]}...")
    
    # 测试个股新闻
    print("\n5. 获取个股新闻...")
    news = tracker.get_stock_news("002242", "九阳", 5)
    for n in news[:3]:
        print(f"   [{n['source']}] {n['title'][:40]}...")
    
    print("\n=== 测试完成 ===")
