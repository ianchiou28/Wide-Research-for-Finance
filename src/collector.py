import feedparser
import yaml
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from web_scraper import WebScraper # 引入WebScraper

class DataCollector:
    def __init__(self, config_path='config/sources.yaml', user_config_path='src/user_config.yaml'):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        try:
            with open(user_config_path, 'r', encoding='utf-8') as f:
                self.user_config = yaml.safe_load(f)
        except FileNotFoundError:
            self.user_config = {}
    
    def _fetch_feed_with_timeout(self, url: str, timeout: int = 15) -> dict:
        """使用 requests 获取 RSS，带超时控制"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()
            return feedparser.parse(response.content)
        except requests.Timeout:
            print(f"    超时: {url[:50]}...")
            return feedparser.FeedParserDict()
        except requests.RequestException as e:
            print(f"    请求失败: {str(e)[:50]}")
            return feedparser.FeedParserDict()
    
    def fetch_latest(self, hours=24, max_per_source=15) -> List[Dict]:
        """获取最近N小时的新闻"""
        articles = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        success_count = 0
        
        for source in self.config.get('rss_sources', []):
            try:
                feed = self._fetch_feed_with_timeout(source['url'], timeout=15)
                count = 0
                
                for entry in feed.entries[:max_per_source*2]:  # 多取一些以防过滤
                    if count >= max_per_source:
                        break
                    
                    try:
                        published_parsed = None
                        if hasattr(entry, 'published_parsed'):
                            published_parsed = entry.published_parsed
                        elif isinstance(entry, dict) and 'published_parsed' in entry:
                            published_parsed = entry['published_parsed']
                        if published_parsed:
                            safe_defaults = (1970, 1, 1, 0, 0, 0)
                            date_parts = []
                            for value, fallback in zip(published_parsed[:6], safe_defaults):
                                if isinstance(value, (int, float, str)):
                                    try:
                                        date_parts.append(int(value))
                                    except (TypeError, ValueError):
                                        date_parts.append(fallback)
                                else:
                                    date_parts.append(fallback)
                            pub_date = datetime(*date_parts)
                        else:
                            pub_date = datetime.now()
                    except Exception:
                        pub_date = datetime.now()
                    
                    if pub_date < cutoff_time:
                        continue
                    
                    # Normalize entry fields to avoid AttributeError/TypeError when values are missing
                    title = getattr(entry, 'title', None)
                    if not title:
                        title = entry.get('title', 'Untitled')

                    summary_value = (
                        entry.get('summary')
                        or getattr(entry, 'summary', None)
                        or entry.get('description')
                        or getattr(entry, 'description', None)
                        or ''
                    )
                    if not isinstance(summary_value, str):
                        summary_value = str(summary_value)

                    url = getattr(entry, 'link', None) or entry.get('link', '')

                    articles.append({
                        'title': title,
                        'content': summary_value[:1000],
                        'source': source['name'],
                        'category': source.get('category', 'general'),
                        'url': url,
                        'published_at': pub_date.isoformat()
                    })
                    count += 1
                
                if count > 0:
                    success_count += 1
                    
            except Exception as e:
                print(f"  ⚠ {source['name']}: {str(e)[:50]}")
        
        print(f"  ✓ 成功采集 {len(articles)} 条新闻 (来自 {success_count} 个源)")
        return articles

    def fetch_stock_specific_news(self) -> List[Dict]:
        """获取用户自选股相关新闻"""
        my_stocks = self.user_config.get('my_stocks', [])
        if not my_stocks:
            return []
        
        print(f"\n2a. 采集自选股新闻 ({len(my_stocks)}只)...")
        stock_articles = []
        scraper = WebScraper()
        for stock in my_stocks:
            news = scraper.search_stock_news(stock['name'])
            stock_articles.extend(news)
        return stock_articles
