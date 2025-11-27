"""
实时数据采集器
解决新闻延迟问题，接入多个实时数据源
"""

import requests
import json
import re
import time
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

class RealtimeCollector:
    """实时财经信息采集器"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def fetch_all_realtime(self) -> List[Dict]:
        """获取所有实时数据源"""
        all_news = []
        
        # 同花顺7x24
        ths_news = self.fetch_ths_7x24()
        all_news.extend(ths_news)
        
        # 东方财富快讯
        eastmoney_news = self.fetch_eastmoney_kuaixun()
        all_news.extend(eastmoney_news)
        
        # 新浪财经实时
        sina_news = self.fetch_sina_realtime()
        all_news.extend(sina_news)
        
        # 金十数据快讯
        jin10_news = self.fetch_jin10_flash()
        all_news.extend(jin10_news)
        
        print(f"  ✓ 实时采集完成，共 {len(all_news)} 条")
        return all_news
    
    def fetch_ths_7x24(self) -> List[Dict]:
        """同花顺7x24快讯 - 超级实时"""
        news_list = []
        try:
            # 同花顺7x24快讯API
            url = "https://news.10jqka.com.cn/tapp/news/push/stock/?page=1&tag=&track=website&pagesize=50"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get('data', {}).get('list', [])
                
                for item in items[:30]:
                    news_list.append({
                        'title': item.get('title', ''),
                        'content': item.get('digest', '') or item.get('title', ''),
                        'source': '同花顺7x24',
                        'category': 'realtime',
                        'url': item.get('url', ''),
                        'published_at': datetime.now().isoformat(),
                        'is_realtime': True
                    })
                print(f"    ✓ 同花顺7x24: {len(news_list)} 条")
        except Exception as e:
            print(f"    ⚠ 同花顺7x24采集失败: {str(e)[:50]}")
        
        return news_list
    
    def fetch_eastmoney_kuaixun(self) -> List[Dict]:
        """东方财富快讯"""
        news_list = []
        try:
            # 东方财富7x24快讯
            url = "https://np-listapi.eastmoney.com/comm/wap/getListInfo?cb=callback&client=wap&type=5&mession=&pageSize=50&pageIndex=0&callback="
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                text = response.text
                # 处理JSONP
                if text.startswith('callback('):
                    text = text[9:-1]
                data = json.loads(text)
                items = data.get('data', {}).get('list', [])
                
                for item in items[:30]:
                    title = item.get('title', '') or item.get('digest', '')
                    # 清理HTML标签
                    title = re.sub(r'<[^>]+>', '', title)
                    
                    news_list.append({
                        'title': title,
                        'content': item.get('content', '') or title,
                        'source': '东方财富快讯',
                        'category': 'realtime',
                        'url': f"https://finance.eastmoney.com/a/{item.get('id', '')}.html",
                        'published_at': item.get('showtime', datetime.now().isoformat()),
                        'is_realtime': True
                    })
                print(f"    ✓ 东方财富快讯: {len(news_list)} 条")
        except Exception as e:
            print(f"    ⚠ 东方财富快讯采集失败: {str(e)[:50]}")
        
        return news_list
    
    def fetch_sina_realtime(self) -> List[Dict]:
        """新浪财经实时新闻"""
        news_list = []
        try:
            # 新浪财经7x24
            url = "https://zhibo.sina.com.cn/api/zhibo/feed?id=152&page=1&page_size=30&zhession="
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get('result', {}).get('data', {}).get('feed', {}).get('list', [])
                
                for item in items[:30]:
                    rich_text = item.get('rich_text', '')
                    # 清理HTML
                    clean_text = re.sub(r'<[^>]+>', '', rich_text)
                    
                    news_list.append({
                        'title': clean_text[:100] if clean_text else '',
                        'content': clean_text,
                        'source': '新浪财经7x24',
                        'category': 'realtime',
                        'url': item.get('docurl', ''),
                        'published_at': item.get('create_time', datetime.now().isoformat()),
                        'is_realtime': True
                    })
                print(f"    ✓ 新浪财经7x24: {len(news_list)} 条")
        except Exception as e:
            print(f"    ⚠ 新浪财经7x24采集失败: {str(e)[:50]}")
        
        return news_list
    
    def fetch_jin10_flash(self) -> List[Dict]:
        """金十数据快讯"""
        news_list = []
        try:
            # 金十数据7x24
            url = "https://flash-api.jin10.com/get_flash_list?max_time=&channel=-8200"
            
            headers = self.headers.copy()
            headers['x-app-id'] = 'bVBF4FyRTn5NJF5n'
            headers['x-version'] = '1.0.0'
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get('data', [])
                
                for item in items[:30]:
                    content = item.get('data', {})
                    title = content.get('title', '') or content.get('content', '')
                    # 清理HTML
                    title = re.sub(r'<[^>]+>', '', title)
                    
                    if title:
                        news_list.append({
                            'title': title[:100],
                            'content': title,
                            'source': '金十数据',
                            'category': 'realtime',
                            'url': '',
                            'published_at': item.get('time', datetime.now().isoformat()),
                            'is_realtime': True,
                            'importance': item.get('important', 0)
                        })
                print(f"    ✓ 金十数据: {len(news_list)} 条")
        except Exception as e:
            print(f"    ⚠ 金十数据采集失败: {str(e)[:50]}")
        
        return news_list
    
    def fetch_company_announcements(self, stock_code: str) -> List[Dict]:
        """获取公司公告 - 捕捉新产品发布等一手信息"""
        news_list = []
        try:
            # 东方财富公司公告
            url = f"https://np-anotice-stock.eastmoney.com/api/security/ann?page_index=1&page_size=20&ann_type=all&cb=&stock_list={stock_code}"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get('data', {}).get('list', [])
                
                for item in items[:10]:
                    news_list.append({
                        'title': item.get('title', ''),
                        'content': item.get('title', ''),
                        'source': '公司公告',
                        'category': 'announcement',
                        'url': item.get('url', ''),
                        'published_at': item.get('notice_date', datetime.now().isoformat()),
                        'stock_code': stock_code,
                        'is_official': True
                    })
        except Exception as e:
            print(f"    ⚠ 公司公告采集失败: {str(e)[:50]}")
        
        return news_list
    
    def fetch_stock_news(self, stock_code: str, stock_name: str = '') -> List[Dict]:
        """获取个股相关新闻"""
        news_list = []
        
        # 东方财富个股新闻
        try:
            url = f"https://np-listapi.eastmoney.com/comm/wap/getListInfo?cb=&type=1&mession=&pageSize=30&pageIndex=0&callback=&code={stock_code}"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                text = response.text
                if text.startswith('('):
                    text = text[1:-1]
                data = json.loads(text) if text else {}
                items = data.get('data', {}).get('list', [])
                
                for item in items[:20]:
                    title = item.get('title', '')
                    title = re.sub(r'<[^>]+>', '', title)
                    
                    news_list.append({
                        'title': title,
                        'content': item.get('content', '') or title,
                        'source': '东方财富个股',
                        'category': 'stock_specific',
                        'url': item.get('url', ''),
                        'published_at': item.get('showtime', datetime.now().isoformat()),
                        'stock_code': stock_code,
                        'stock_name': stock_name
                    })
        except Exception as e:
            print(f"    ⚠ 个股新闻采集失败: {str(e)[:50]}")
        
        # 公司公告
        announcements = self.fetch_company_announcements(stock_code)
        news_list.extend(announcements)
        
        return news_list


class SocialMediaCollector:
    """社交媒体信息采集器"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def fetch_xueqiu_hot(self) -> List[Dict]:
        """雪球热门讨论"""
        news_list = []
        try:
            # 雪球热帖
            url = "https://xueqiu.com/statuses/hot/listV2.json?since_id=-1&max_id=-1&size=30"
            
            headers = self.headers.copy()
            headers['Cookie'] = 'xq_a_token=your_token'  # 可能需要token
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get('data', {}).get('items', [])
                
                for item in items[:20]:
                    original = item.get('original_status', {})
                    text = original.get('text', '') or original.get('description', '')
                    text = re.sub(r'<[^>]+>', '', text)
                    
                    news_list.append({
                        'title': text[:100] if text else '',
                        'content': text,
                        'source': '雪球热帖',
                        'category': 'social',
                        'url': f"https://xueqiu.com{original.get('target', '')}",
                        'published_at': datetime.now().isoformat(),
                        'engagement': original.get('reply_count', 0) + original.get('retweet_count', 0)
                    })
                print(f"    ✓ 雪球热帖: {len(news_list)} 条")
        except Exception as e:
            print(f"    ⚠ 雪球热帖采集失败: {str(e)[:50]}")
        
        return news_list
    
    def fetch_eastmoney_guba_hot(self, stock_code: str = None) -> List[Dict]:
        """东方财富股吧热帖"""
        news_list = []
        try:
            if stock_code:
                url = f"https://guba.eastmoney.com/interface/GetData.aspx?path=newtopic/api/Topic/TopicList&ps=30&p=1&type=0&code={stock_code}"
            else:
                url = "https://guba.eastmoney.com/interface/GetData.aspx?path=newtopic/api/Topic/HotList&ps=30&p=1"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get('re', [])
                
                for item in items[:20]:
                    news_list.append({
                        'title': item.get('post_title', ''),
                        'content': item.get('post_content', '') or item.get('post_title', ''),
                        'source': '股吧热帖',
                        'category': 'social',
                        'url': item.get('post_url', ''),
                        'published_at': item.get('post_publish_time', datetime.now().isoformat()),
                        'engagement': item.get('post_click_count', 0),
                        'stock_code': stock_code
                    })
                print(f"    ✓ 股吧热帖: {len(news_list)} 条")
        except Exception as e:
            print(f"    ⚠ 股吧热帖采集失败: {str(e)[:50]}")
        
        return news_list


# 测试
if __name__ == '__main__':
    print("=== 实时数据采集测试 ===\n")
    
    collector = RealtimeCollector()
    
    print("1. 测试同花顺7x24...")
    ths = collector.fetch_ths_7x24()
    if ths:
        print(f"   示例: {ths[0]['title'][:50]}...")
    
    print("\n2. 测试东方财富快讯...")
    em = collector.fetch_eastmoney_kuaixun()
    if em:
        print(f"   示例: {em[0]['title'][:50]}...")
    
    print("\n3. 测试新浪财经7x24...")
    sina = collector.fetch_sina_realtime()
    if sina:
        print(f"   示例: {sina[0]['title'][:50]}...")
    
    print("\n4. 测试金十数据...")
    jin10 = collector.fetch_jin10_flash()
    if jin10:
        print(f"   示例: {jin10[0]['title'][:50]}...")
    
    print("\n=== 测试完成 ===")
