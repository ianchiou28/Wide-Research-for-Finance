"""
虚拟货币数据采集模块
支持主流加密货币的行情、新闻和链上数据
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class CryptoCollector:
    """加密货币数据采集器"""
    
    def __init__(self, coingecko_api_key: str = None):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        self.coingecko_api_key = coingecko_api_key
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 主流币种映射
        self.symbol_to_id = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'XRP': 'ripple',
            'SOL': 'solana',
            'ADA': 'cardano',
            'DOGE': 'dogecoin',
            'TRX': 'tron',
            'DOT': 'polkadot',
            'MATIC': 'matic-network',
            'LTC': 'litecoin',
            'SHIB': 'shiba-inu',
            'AVAX': 'avalanche-2',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
        }
    
    def get_market_data(self, symbols: List[str] = None, vs_currency: str = 'usd') -> List[Dict]:
        """获取加密货币市场数据，国内源优先，减少等待"""
        if symbols is None:
            symbols = list(self.symbol_to_id.keys())[:10]

        # 先走国内可访问源，避免长时间等待
        domestic_results = self._get_market_data_domestic(symbols)
        if domestic_results:
            return domestic_results

        # 再尝试币安（若可直连）
        binance_results = self._get_market_data_backup(symbols)
        if binance_results:
            return binance_results

        # 最后尝试 CoinGecko（多数国内会超时）
        ids = [self.symbol_to_id.get(s.upper(), s.lower()) for s in symbols]
        ids_str = ','.join(ids)

        try:
            url = (
                "https://api.coingecko.com/api/v3/coins/markets"
                f"?vs_currency={vs_currency}&ids={ids_str}&order=market_cap_desc&sparkline=false"
                "&price_change_percentage=24h,7d"
            )

            if self.coingecko_api_key:
                url += f"&x_cg_demo_api_key={self.coingecko_api_key}"

            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = []
                for coin in data:
                    results.append({
                        'id': coin.get('id', ''),
                        'symbol': coin.get('symbol', '').upper(),
                        'name': coin.get('name', ''),
                        'image': coin.get('image', ''),
                        'price_usd': coin.get('current_price', 0),
                        'market_cap': coin.get('market_cap', 0),
                        'market_cap_rank': coin.get('market_cap_rank', 0),
                        'volume_24h': coin.get('total_volume', 0),
                        'change_24h': coin.get('price_change_percentage_24h', 0),
                        'change_7d': coin.get('price_change_percentage_7d_in_currency', 0),
                        'high_24h': coin.get('high_24h', 0),
                        'low_24h': coin.get('low_24h', 0),
                        'circulating_supply': coin.get('circulating_supply', 0),
                        'total_supply': coin.get('total_supply', 0),
                        'ath': coin.get('ath', 0),
                        'ath_change_percentage': coin.get('ath_change_percentage', 0),
                        'timestamp': datetime.now().isoformat()
                    })
                if results:
                    return results
            elif response.status_code == 429:
                print("CoinGecko API限流，使用备用方案...")
        except Exception as e:
            print(f"CoinGecko API请求失败: {e}")

        return []
    
    def _get_market_data_backup(self, symbols: List[str]) -> List[Dict]:
        """备用数据源 - 币安API"""
        results = []
        try:
            # 使用币安现货API
            url = "https://api.binance.com/api/v3/ticker/24hr"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                symbol_set = set(s.upper() for s in symbols)
                
                for item in data:
                    # 币安的交易对格式是 BTCUSDT
                    if item['symbol'].endswith('USDT'):
                        base_symbol = item['symbol'][:-4]
                        if base_symbol in symbol_set:
                            results.append({
                                'symbol': base_symbol,
                                'name': base_symbol,
                                'price_usd': float(item.get('lastPrice', 0)),
                                'volume_24h': float(item.get('quoteVolume', 0)),
                                'change_24h': float(item.get('priceChangePercent', 0)),
                                'high_24h': float(item.get('highPrice', 0)),
                                'low_24h': float(item.get('lowPrice', 0)),
                                'timestamp': datetime.now().isoformat()
                            })
        except Exception as e:
            print(f"币安API请求失败: {e}")
        
        return results

    def _get_market_data_domestic(self, symbols: List[str]) -> List[Dict]:
        """国内可访问的数据源，按“更易直连、短超时”顺序依次尝试"""
        wanted = set(s.upper() for s in symbols)

        # 1) 币安国际的国内域名（可能可直连，精确 symbols 以减小返回体积）
        try:
            pairs = [f"{s.upper()}USDT" for s in wanted]
            url = "https://api.binance.me/api/v3/ticker/24hr?symbols=" + json.dumps(pairs)
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                results = []
                # Binance在symbols参数下返回对象或数组，统一处理为列表
                items = data if isinstance(data, list) else [data]
                for item in items:
                    base = item.get('symbol', '')[:-4].upper()
                    if base and base in wanted:
                        results.append({
                            'id': base.lower(),
                            'symbol': base,
                            'name': base,
                            'image': '',
                            'price_usd': float(item.get('lastPrice', 0) or 0),
                            'market_cap': None,
                            'market_cap_rank': None,
                            'volume_24h': float(item.get('quoteVolume', 0) or 0),
                            'change_24h': float(item.get('priceChangePercent', 0) or 0),
                            'change_7d': None,
                            'high_24h': float(item.get('highPrice', 0) or 0),
                            'low_24h': float(item.get('lowPrice', 0) or 0),
                            'circulating_supply': None,
                            'total_supply': None,
                            'ath': None,
                            'ath_change_percentage': None,
                            'timestamp': datetime.now().isoformat()
                        })
                if results:
                    return results
        except Exception as e:
            print(f"国内市场数据源失败(Binance.me): {e}")

        # 2) Gate.io（通常国内可直连）
        try:
            url = "https://api.gateio.ws/api/v4/spot/tickers"
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for item in data:
                    pair = item.get('currency_pair', '').upper()
                    if pair.endswith('_USDT'):
                        base = pair[:-5]
                        if base in wanted:
                            results.append({
                                'id': base.lower(),
                                'symbol': base,
                                'name': base,
                                'image': '',
                                'price_usd': float(item.get('last', 0) or 0),
                                'market_cap': None,
                                'market_cap_rank': None,
                                'volume_24h': float(item.get('quote_volume', 0) or 0),
                                'change_24h': float(item.get('change_percentage', 0) or 0),
                                'change_7d': None,
                                'high_24h': float(item.get('high_24h', 0) or 0),
                                'low_24h': float(item.get('low_24h', 0) or 0),
                                'circulating_supply': None,
                                'total_supply': None,
                                'ath': None,
                                'ath_change_percentage': None,
                                'timestamp': datetime.now().isoformat()
                            })
                if results:
                    return results
        except Exception as e:
            print(f"国内市场数据源失败(Gate): {e}")

        # 3) OKX 行情
        try:
            url = "https://www.okx.com/api/v5/market/tickers?instType=SPOT"
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                data = resp.json().get('data', [])
                results = []
                for item in data:
                    inst = item.get('instId', '').upper()  # e.g., BTC-USDT
                    if inst.endswith('-USDT'):
                        base = inst.split('-')[0]
                        if base in wanted:
                            results.append({
                                'id': base.lower(),
                                'symbol': base,
                                'name': base,
                                'image': '',
                                'price_usd': float(item.get('last', 0) or 0),
                                'market_cap': None,
                                'market_cap_rank': None,
                                'volume_24h': float(item.get('volCcy24h', 0) or 0),
                                # OKX未直接提供百分比，使用昨收开盘价近似计算
                                'change_24h': float(item.get('last', 0) or 0) - float(item.get('sodUtc0', 0) or 0),
                                'change_7d': None,
                                'high_24h': float(item.get('high24h', 0) or 0),
                                'low_24h': float(item.get('low24h', 0) or 0),
                                'circulating_supply': None,
                                'total_supply': None,
                                'ath': None,
                                'ath_change_percentage': None,
                                'timestamp': datetime.now().isoformat()
                            })
                if results:
                    return results
        except Exception as e:
            print(f"国内市场数据源失败(OKX): {e}")

        # 4) Coinlore tickers（轻量，通常可直连）
        try:
            url = "https://api.coinlore.net/api/tickers/?start=0&limit=200"
            resp = requests.get(url, timeout=4)
            if resp.status_code == 200:
                data = resp.json().get('data', [])
                results = []
                for item in data:
                    sym = item.get('symbol', '').upper()
                    if sym in wanted:
                        results.append({
                            'id': item.get('id', ''),
                            'symbol': sym,
                            'name': item.get('name', ''),
                            'image': '',
                            'price_usd': float(item.get('price_usd', 0) or 0),
                            'market_cap': float(item.get('market_cap_usd', 0) or 0),
                            'market_cap_rank': int(item.get('rank', 0) or 0),
                            'volume_24h': float(item.get('volume24', 0) or 0),
                            'change_24h': float(item.get('percent_change_24h', 0) or 0),
                            'change_7d': float(item.get('percent_change_7d', 0) or 0),
                            'high_24h': None,
                            'low_24h': None,
                            'circulating_supply': float(item.get('csupply', 0) or 0),
                            'total_supply': float(item.get('tsupply', 0) or 0),
                            'ath': None,
                            'ath_change_percentage': None,
                            'timestamp': datetime.now().isoformat()
                        })
                if results:
                    return results
        except Exception as e:
            print(f"国内市场数据源失败(Coinlore tickers): {e}")

        # 5) 非小号公共API（可能偶尔慢）
        try:
            url = "https://fxhapi.feixiaohao.com/public/v1/ticker?limit=200"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for item in data:
                    sym = item.get('symbol', '').upper()
                    if sym in wanted:
                        results.append({
                            'id': item.get('id', ''),
                            'symbol': sym,
                            'name': item.get('name', ''),
                            'image': '',
                            'price_usd': float(item.get('price_usd', 0) or 0),
                            'market_cap': float(item.get('market_cap_usd', 0) or 0),
                            'market_cap_rank': int(item.get('rank', 0) or 0),
                            'volume_24h': float(item.get('24h_volume_usd', 0) or 0),
                            'change_24h': float(item.get('percent_change_24h', 0) or 0),
                            'change_7d': float(item.get('percent_change_7d', 0) or 0),
                            'high_24h': None,
                            'low_24h': None,
                            'circulating_supply': float(item.get('available_supply', 0) or 0),
                            'total_supply': float(item.get('total_supply', 0) or 0),
                            'ath': None,
                            'ath_change_percentage': None,
                            'timestamp': datetime.now().isoformat()
                        })
                if results:
                    return results
        except Exception as e:
            print(f"国内市场数据源失败(非小号): {e}")

        # 6) 火币（超时降到 5s）
        try:
            url = "https://api.huobi.pro/market/tickers"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json().get('data', [])
                results = []
                for item in data:
                    sym = item.get('symbol', '').upper()
                    if sym.endswith('USDT'):
                        base = sym[:-4]
                        if base in wanted:
                            results.append({
                                'id': base.lower(),
                                'symbol': base,
                                'name': base,
                                'image': '',
                                'price_usd': float(item.get('close', 0) or 0),
                                'market_cap': None,
                                'market_cap_rank': None,
                                'volume_24h': float(item.get('vol', 0) or 0),
                                'change_24h': float(item.get('pricePercent', 0) or 0),
                                'change_7d': None,
                                'high_24h': float(item.get('high', 0) or 0),
                                'low_24h': float(item.get('low', 0) or 0),
                                'circulating_supply': None,
                                'total_supply': None,
                                'ath': None,
                                'ath_change_percentage': None,
                                'timestamp': datetime.now().isoformat()
                            })
                if results:
                    return results
        except Exception as e:
            print(f"国内市场数据源失败(火币): {e}")

        return []
    
    def get_coin_details(self, coin_id: str) -> Optional[Dict]:
        """获取单个币种详细信息"""
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=true&developer_data=false"
            
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                market_data = data.get('market_data', {})
                
                return {
                    'id': data.get('id', ''),
                    'symbol': data.get('symbol', '').upper(),
                    'name': data.get('name', ''),
                    'description': data.get('description', {}).get('en', '')[:500],
                    'image': data.get('image', {}).get('large', ''),
                    'price_usd': market_data.get('current_price', {}).get('usd', 0),
                    'price_cny': market_data.get('current_price', {}).get('cny', 0),
                    'market_cap': market_data.get('market_cap', {}).get('usd', 0),
                    'market_cap_rank': data.get('market_cap_rank', 0),
                    'volume_24h': market_data.get('total_volume', {}).get('usd', 0),
                    'change_24h': market_data.get('price_change_percentage_24h', 0),
                    'change_7d': market_data.get('price_change_percentage_7d', 0),
                    'change_30d': market_data.get('price_change_percentage_30d', 0),
                    'ath': market_data.get('ath', {}).get('usd', 0),
                    'ath_date': market_data.get('ath_date', {}).get('usd', ''),
                    'atl': market_data.get('atl', {}).get('usd', 0),
                    'circulating_supply': market_data.get('circulating_supply', 0),
                    'total_supply': market_data.get('total_supply', 0),
                    'max_supply': market_data.get('max_supply', 0),
                    'sentiment_votes_up_percentage': data.get('sentiment_votes_up_percentage', 0),
                    'sentiment_votes_down_percentage': data.get('sentiment_votes_down_percentage', 0),
                    'categories': data.get('categories', []),
                    'links': {
                        'homepage': data.get('links', {}).get('homepage', [None])[0],
                        'blockchain_site': data.get('links', {}).get('blockchain_site', [None])[0],
                        'twitter': data.get('links', {}).get('twitter_screen_name', ''),
                        'telegram': data.get('links', {}).get('telegram_channel_identifier', ''),
                    },
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"获取币种详情失败: {e}")
        
        return None
    
    def get_trending(self) -> List[Dict]:
        """获取热门币种"""
        try:
            url = "https://api.coingecko.com/api/v3/search/trending"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                coins = data.get('coins', [])
                
                return [{
                    'id': c['item']['id'],
                    'symbol': c['item']['symbol'].upper(),
                    'name': c['item']['name'],
                    'market_cap_rank': c['item'].get('market_cap_rank', 0),
                    'score': c['item'].get('score', 0),
                    'image': c['item'].get('large', ''),
                } for c in coins[:10]]
        except Exception as e:
            print(f"获取热门币种失败: {e}")
        
        return []
    
    def get_global_data(self) -> Dict:
        """获取全局数据，国内源优先"""
        domestic = self._get_global_data_domestic()
        if domestic:
            return domestic

        try:
            url = "https://api.coingecko.com/api/v3/global"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                return {
                    'total_market_cap': data.get('total_market_cap', {}).get('usd', 0),
                    'total_volume': data.get('total_volume', {}).get('usd', 0),
                    'market_cap_change_24h': data.get('market_cap_change_percentage_24h_usd', 0),
                    'btc_dominance': data.get('market_cap_percentage', {}).get('btc', 0),
                    'eth_dominance': data.get('market_cap_percentage', {}).get('eth', 0),
                    'active_cryptocurrencies': data.get('active_cryptocurrencies', 0),
                    'markets': data.get('markets', 0),
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"获取全局数据失败: {e}")

        return {}

    def _get_global_data_domestic(self) -> Dict:
        """国内可访问的全局数据源"""
        # 1) Coinlore（轻量，先试，超时短）
        try:
            url = "https://api.coinlore.net/api/global/"
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                arr = resp.json()
                data = arr[0] if isinstance(arr, list) and arr else {}
                return {
                    'total_market_cap': float(data.get('total_mcap', 0) or 0),
                    'total_volume': float(data.get('total_volume', 0) or 0),
                    'market_cap_change_24h': float(data.get('mcap_change', 0) or 0),
                    'btc_dominance': float(data.get('btc_d', 0) or 0),
                    'eth_dominance': float(data.get('eth_d', 0) or 0),
                    'active_cryptocurrencies': None,
                    'markets': None,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"国内全局数据源失败(Coinlore): {e}")

        # 2) 非小号全局（次优，超时缩短）
        try:
            url = "https://fxhapi.feixiaohao.com/public/v1/global"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    'total_market_cap': float(data.get('total_market_cap_usd', 0) or 0),
                    'total_volume': float(data.get('total_24h_volume_usd', 0) or 0),
                    'market_cap_change_24h': float(data.get('market_cap_change_percentage_24h_usd', 0) or 0),
                    'btc_dominance': float(data.get('bitcoin_percentage_of_market_cap', 0) or 0),
                    'eth_dominance': None,
                    'active_cryptocurrencies': int(data.get('active_cryptocurrencies', 0) or 0),
                    'markets': int(data.get('markets', 0) or 0),
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"国内全局数据源失败(非小号): {e}")

        return {}
    
    def get_price_history(self, coin_id: str, days: int = 30, vs_currency: str = 'usd') -> List[Dict]:
        """获取价格历史数据"""
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency={vs_currency}&days={days}"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                prices = data.get('prices', [])
                volumes = data.get('total_volumes', [])
                
                history = []
                for i, (timestamp, price) in enumerate(prices):
                    volume = volumes[i][1] if i < len(volumes) else 0
                    history.append({
                        'timestamp': datetime.fromtimestamp(timestamp/1000).isoformat(),
                        'price': price,
                        'volume': volume
                    })
                return history
        except Exception as e:
            print(f"获取价格历史失败: {e}")
        
        return []
    
    def get_crypto_news(self) -> List[Dict]:
        """获取加密货币相关新闻"""
        news_list = []
        
        # 从CoinDesk RSS获取
        try:
            import feedparser
            feed = feedparser.parse('https://www.coindesk.com/arc/outboundfeeds/rss/')
            
            for entry in feed.entries[:20]:
                news_list.append({
                    'title': entry.get('title', ''),
                    'content': entry.get('summary', '')[:500],
                    'source': 'CoinDesk',
                    'url': entry.get('link', ''),
                    'published_at': entry.get('published', datetime.now().isoformat()),
                    'category': 'crypto'
                })
        except Exception as e:
            print(f"CoinDesk新闻获取失败: {e}")
        
        # 从CoinTelegraph获取
        try:
            import feedparser
            feed = feedparser.parse('https://cointelegraph.com/rss')
            
            for entry in feed.entries[:20]:
                news_list.append({
                    'title': entry.get('title', ''),
                    'content': entry.get('summary', '')[:500],
                    'source': 'CoinTelegraph',
                    'url': entry.get('link', ''),
                    'published_at': entry.get('published', datetime.now().isoformat()),
                    'category': 'crypto'
                })
        except Exception as e:
            print(f"CoinTelegraph新闻获取失败: {e}")
        
        return news_list
    
    def get_fear_greed_index(self) -> Dict:
        """获取加密货币恐惧贪婪指数"""
        try:
            url = "https://api.alternative.me/fng/?limit=10"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json().get('data', [])
                if data:
                    latest = data[0]
                    return {
                        'value': int(latest.get('value', 50)),
                        'classification': latest.get('value_classification', 'Neutral'),
                        'timestamp': datetime.fromtimestamp(int(latest.get('timestamp', 0))).isoformat(),
                        'history': [{
                            'value': int(d.get('value', 50)),
                            'classification': d.get('value_classification', ''),
                            'timestamp': datetime.fromtimestamp(int(d.get('timestamp', 0))).isoformat()
                        } for d in data]
                    }
        except Exception as e:
            print(f"获取恐惧贪婪指数失败: {e}")
        
        return {'value': 50, 'classification': 'Neutral'}
    
    def search_coins(self, query: str) -> List[Dict]:
        """搜索加密货币"""
        try:
            url = f"https://api.coingecko.com/api/v3/search?query={query}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                coins = data.get('coins', [])
                
                return [{
                    'id': c.get('id', ''),
                    'symbol': c.get('symbol', '').upper(),
                    'name': c.get('name', ''),
                    'market_cap_rank': c.get('market_cap_rank', 0),
                    'image': c.get('large', ''),
                } for c in coins[:10]]
        except Exception as e:
            print(f"搜索币种失败: {e}")
        
        return []


# 测试
if __name__ == '__main__':
    print("=== 虚拟货币模块测试 ===\n")
    
    collector = CryptoCollector()
    
    # 测试市场数据
    print("1. 获取主流币种行情...")
    market_data = collector.get_market_data(['BTC', 'ETH', 'SOL', 'DOGE'])
    for coin in market_data:
        print(f"   {coin['symbol']}: ${coin['price_usd']:,.2f} ({coin['change_24h']:+.2f}%)")
    
    # 测试全局数据
    print("\n2. 获取全球市场数据...")
    global_data = collector.get_global_data()
    if global_data:
        print(f"   总市值: ${global_data['total_market_cap']/1e12:.2f}T")
        print(f"   BTC占比: {global_data['btc_dominance']:.1f}%")
        print(f"   24h变化: {global_data['market_cap_change_24h']:+.2f}%")
    
    # 测试热门币种
    print("\n3. 获取热门币种...")
    trending = collector.get_trending()
    for coin in trending[:5]:
        print(f"   {coin['symbol']}: {coin['name']}")
    
    # 测试恐惧贪婪指数
    print("\n4. 获取恐惧贪婪指数...")
    fgi = collector.get_fear_greed_index()
    print(f"   当前指数: {fgi['value']} ({fgi['classification']})")
    
    # 测试新闻
    print("\n5. 获取加密货币新闻...")
    news = collector.get_crypto_news()
    for n in news[:3]:
        print(f"   [{n['source']}] {n['title'][:50]}...")
    
    print("\n=== 测试完成 ===")
