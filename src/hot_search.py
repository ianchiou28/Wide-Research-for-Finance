"""
热搜采集模块
聚合微博、头条、知乎、百度等平台的财经相关热搜
"""

import requests
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

class HotSearchCollector:
    """热搜采集器"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 财经相关关键词，用于筛选
        self.finance_keywords = [
            '股', '基金', '债', '金融', '银行', '证券', '保险', '理财',
            '涨', '跌', '牛市', '熊市', 'A股', '美股', '港股', '创业板',
            '科创板', 'IPO', '融资', '上市', '退市', '收购', '并购',
            '央行', '利率', '汇率', '美联储', 'GDP', 'CPI', 'PMI',
            '房价', '楼市', '地产', '经济', '贸易', '关税',
            '比特币', '以太坊', '加密货币', '数字货币', '区块链',
            '特斯拉', '苹果', '英伟达', '茅台', '宁德', '比亚迪',
            '芯片', '半导体', '新能源', '光伏', '锂电', '人工智能', 'AI'
        ]
    
    def is_finance_related(self, text: str) -> bool:
        """判断是否与财经相关"""
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in self.finance_keywords)
    
    def fetch_all_hot_searches(self, finance_only: bool = True) -> Dict[str, List[Dict]]:
        """获取所有平台热搜"""
        results = {
            'weibo': [],
            'toutiao': [],
            'zhihu': [],
            'baidu': [],
            'douyin': []
        }
        
        # 微博热搜
        results['weibo'] = self.fetch_weibo_hot(finance_only)
        
        # 今日头条
        results['toutiao'] = self.fetch_toutiao_hot(finance_only)
        
        # 知乎热榜
        results['zhihu'] = self.fetch_zhihu_hot(finance_only)
        
        # 百度热搜
        results['baidu'] = self.fetch_baidu_hot(finance_only)
        
        # 抖音热点
        results['douyin'] = self.fetch_douyin_hot(finance_only)
        
        # 统计
        total = sum(len(v) for v in results.values())
        print(f"  ✓ 热搜采集完成，共 {total} 条")
        
        return results
    
    def fetch_weibo_hot(self, finance_only: bool = True) -> List[Dict]:
        """微博热搜"""
        hot_list = []
        try:
            # 使用第三方API（更稳定）
            url = "https://weibo.com/ajax/side/hotSearch"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get('data', {}).get('realtime', [])
                
                for i, item in enumerate(items[:50]):
                    title = item.get('word', '') or item.get('note', '')
                    
                    # 筛选财经相关
                    if finance_only and not self.is_finance_related(title):
                        continue
                    
                    hot_list.append({
                        'rank': i + 1,
                        'title': title,
                        'url': f"https://s.weibo.com/weibo?q={title}",
                        'hot_value': item.get('num', 0),
                        'category': item.get('category', ''),
                        'is_hot': item.get('is_hot', 0) == 1,
                        'is_new': item.get('is_new', 0) == 1,
                        'platform': 'weibo',
                        'collected_at': datetime.now().isoformat()
                    })
                
                print(f"    ✓ 微博热搜: {len(hot_list)} 条" + (" (财经相关)" if finance_only else ""))
        except Exception as e:
            print(f"    ⚠ 微博热搜采集失败: {str(e)[:50]}")
            
            # 备用方案：使用第三方API
            try:
                backup_url = "https://tenapi.cn/v2/weibohot"
                response = requests.get(backup_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('data', [])
                    for i, item in enumerate(items[:30]):
                        title = item.get('name', '')
                        if finance_only and not self.is_finance_related(title):
                            continue
                        hot_list.append({
                            'rank': i + 1,
                            'title': title,
                            'url': item.get('url', ''),
                            'hot_value': item.get('hot', 0),
                            'platform': 'weibo',
                            'collected_at': datetime.now().isoformat()
                        })
                    print(f"    ✓ 微博热搜(备用): {len(hot_list)} 条")
            except:
                pass
        
        return hot_list
    
    def fetch_toutiao_hot(self, finance_only: bool = True) -> List[Dict]:
        """今日头条热榜"""
        hot_list = []
        try:
            url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
            
            headers = self.headers.copy()
            headers['Referer'] = 'https://www.toutiao.com/'
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get('data', [])
                
                for i, item in enumerate(items[:50]):
                    title = item.get('Title', '')
                    
                    if finance_only and not self.is_finance_related(title):
                        continue
                    
                    hot_list.append({
                        'rank': i + 1,
                        'title': title,
                        'url': item.get('Url', ''),
                        'hot_value': item.get('HotValue', 0),
                        'image': item.get('Image', {}).get('url', ''),
                        'platform': 'toutiao',
                        'collected_at': datetime.now().isoformat()
                    })
                
                print(f"    ✓ 头条热榜: {len(hot_list)} 条" + (" (财经相关)" if finance_only else ""))
        except Exception as e:
            print(f"    ⚠ 头条热榜采集失败: {str(e)[:50]}")
        
        return hot_list
    
    def fetch_zhihu_hot(self, finance_only: bool = True) -> List[Dict]:
        """知乎热榜"""
        hot_list = []
        try:
            url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50"
            
            headers = self.headers.copy()
            headers['Referer'] = 'https://www.zhihu.com/hot'
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get('data', [])
                
                for i, item in enumerate(items):
                    target = item.get('target', {})
                    title = target.get('title', '')
                    
                    if finance_only and not self.is_finance_related(title):
                        continue
                    
                    hot_list.append({
                        'rank': i + 1,
                        'title': title,
                        'url': f"https://www.zhihu.com/question/{target.get('id', '')}",
                        'hot_value': int(item.get('detail_text', '0').replace('万热度', '0000').replace('热度', '')),
                        'excerpt': target.get('excerpt', ''),
                        'answer_count': target.get('answer_count', 0),
                        'platform': 'zhihu',
                        'collected_at': datetime.now().isoformat()
                    })
                
                print(f"    ✓ 知乎热榜: {len(hot_list)} 条" + (" (财经相关)" if finance_only else ""))
        except Exception as e:
            print(f"    ⚠ 知乎热榜采集失败: {str(e)[:50]}")
        
        return hot_list
    
    def fetch_baidu_hot(self, finance_only: bool = True) -> List[Dict]:
        """百度热搜"""
        hot_list = []
        try:
            url = "https://top.baidu.com/api/board?platform=wise&tab=realtime"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get('data', {}).get('cards', [{}])[0].get('content', [])
                
                for i, item in enumerate(items[:50]):
                    title = item.get('word', '') or item.get('query', '')
                    
                    if finance_only and not self.is_finance_related(title):
                        continue
                    
                    hot_list.append({
                        'rank': i + 1,
                        'title': title,
                        'url': item.get('url', f"https://www.baidu.com/s?wd={title}"),
                        'hot_value': item.get('hotScore', 0),
                        'description': item.get('desc', ''),
                        'image': item.get('img', ''),
                        'platform': 'baidu',
                        'collected_at': datetime.now().isoformat()
                    })
                
                print(f"    ✓ 百度热搜: {len(hot_list)} 条" + (" (财经相关)" if finance_only else ""))
        except Exception as e:
            print(f"    ⚠ 百度热搜采集失败: {str(e)[:50]}")
        
        return hot_list
    
    def fetch_douyin_hot(self, finance_only: bool = True) -> List[Dict]:
        """抖音热点"""
        hot_list = []
        try:
            url = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
            
            headers = self.headers.copy()
            headers['Referer'] = 'https://www.douyin.com/'
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get('data', {}).get('word_list', [])
                
                for i, item in enumerate(items[:50]):
                    title = item.get('word', '')
                    
                    if finance_only and not self.is_finance_related(title):
                        continue
                    
                    hot_list.append({
                        'rank': i + 1,
                        'title': title,
                        'url': f"https://www.douyin.com/search/{title}",
                        'hot_value': item.get('hot_value', 0),
                        'platform': 'douyin',
                        'collected_at': datetime.now().isoformat()
                    })
                
                print(f"    ✓ 抖音热点: {len(hot_list)} 条" + (" (财经相关)" if finance_only else ""))
        except Exception as e:
            print(f"    ⚠ 抖音热点采集失败: {str(e)[:50]}")
        
        return hot_list
    
    def get_aggregated_finance_hot(self, top_n: int = 20) -> List[Dict]:
        """获取聚合的财经热搜榜"""
        all_results = self.fetch_all_hot_searches(finance_only=True)
        
        # 合并所有平台
        aggregated = []
        for platform, items in all_results.items():
            for item in items:
                item['platform'] = platform
                aggregated.append(item)
        
        # 按热度排序
        aggregated.sort(key=lambda x: x.get('hot_value', 0), reverse=True)
        
        # 去重（相似标题）
        seen_titles = set()
        unique_results = []
        for item in aggregated:
            title_key = item['title'][:10]  # 取前10字符作为去重key
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_results.append(item)
        
        return unique_results[:top_n]


# 测试
if __name__ == '__main__':
    print("=== 热搜采集测试 ===\n")
    
    collector = HotSearchCollector()
    
    print("1. 获取各平台热搜（财经相关）...")
    results = collector.fetch_all_hot_searches(finance_only=True)
    
    for platform, items in results.items():
        if items:
            print(f"\n{platform.upper()} Top 3:")
            for item in items[:3]:
                print(f"   {item['rank']}. {item['title']}")
    
    print("\n\n2. 获取聚合财经热搜榜...")
    top_finance = collector.get_aggregated_finance_hot(10)
    print("\n财经热搜 TOP 10:")
    for i, item in enumerate(top_finance, 1):
        print(f"   {i}. [{item['platform']}] {item['title']}")
    
    print("\n=== 测试完成 ===")
