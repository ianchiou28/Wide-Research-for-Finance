import feedparser
import hashlib
import yaml
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from logger import setup_logger

logger = setup_logger('collector')

# 尝试导入统一配置
try:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config'))
    from settings import Config
except ImportError:
    Config = None

import os
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
        
        # 采集参数（优先从 Config 读取）
        self._fetch_timeout = Config.FETCH_TIMEOUT if Config else 15
        self._max_per_source = Config.MAX_PER_SOURCE if Config else 15
        
        # 去重缓存（线程安全）
        self._seen_hashes = set()
        self._dedup_lock = threading.Lock()
        self._load_recent_hashes()
    
    def _url_hash(self, url: str) -> str:
        """URL 去重 hash"""
        return hashlib.md5(url.encode()).hexdigest() if url else ''
    
    def _load_recent_hashes(self):
        """从数据库加载最近24h的URL hash，用于去重"""
        try:
            from database import get_recent_news_hashes
            self._seen_hashes = set(get_recent_news_hashes(hours=24))
            logger.debug(f"加载了 {len(self._seen_hashes)} 个历史URL hash")
        except Exception:
            self._seen_hashes = set()
    
    def _is_duplicate(self, url: str) -> bool:
        """检查URL是否已采集过"""
        if not url:
            return False
        return self._url_hash(url) in self._seen_hashes
    
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
            logger.warning(f"超时: {url[:60]}...")
            return feedparser.FeedParserDict()
        except requests.RequestException as e:
            logger.warning(f"请求失败: {str(e)[:60]}")
            return feedparser.FeedParserDict()
    
    def _fetch_single_source(self, source: Dict, cutoff_time: datetime, max_per_source: int) -> Dict:
        """采集单个 RSS 源（线程安全），返回 {articles, duplicates_skipped}"""
        articles = []
        duplicates_skipped = 0
        
        try:
            feed = self._fetch_feed_with_timeout(source['url'], timeout=self._fetch_timeout)
            count = 0
            
            for entry in feed.entries[:max_per_source*2]:
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
                
                # 线程安全的去重检查
                with self._dedup_lock:
                    if self._is_duplicate(url):
                        duplicates_skipped += 1
                        continue
                    if url:
                        self._seen_hashes.add(self._url_hash(url))

                articles.append({
                    'title': title,
                    'content': summary_value[:1000],
                    'source': source['name'],
                    'category': source.get('category', 'general'),
                    'url': url,
                    'published_at': pub_date.isoformat()
                })
                count += 1
                
        except Exception as e:
            logger.warning(f"{source['name']}: {str(e)[:60]}")
        
        return {'articles': articles, 'duplicates_skipped': duplicates_skipped}

    def fetch_latest(self, hours=24, max_per_source=15) -> List[Dict]:
        """并发获取最近N小时的新闻（ThreadPoolExecutor）"""
        articles = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        success_count = 0
        duplicates_skipped = 0
        
        sources = self.config.get('rss_sources', [])
        max_workers = min(8, len(sources))  # 最多8个并发线程
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_source = {
                executor.submit(self._fetch_single_source, source, cutoff_time, max_per_source): source['name']
                for source in sources
            }
            
            for future in as_completed(future_to_source, timeout=90):
                source_name = future_to_source[future]
                try:
                    result = future.result(timeout=30)
                    if result['articles']:
                        articles.extend(result['articles'])
                        success_count += 1
                    duplicates_skipped += result['duplicates_skipped']
                except Exception as e:
                    logger.warning(f"{source_name} 并发采集异常: {str(e)[:60]}")
        
        logger.info(f"并发采集完成: {len(articles)} 条新闻 (来自 {success_count}/{len(sources)} 个源, 去重跳过 {duplicates_skipped} 条)")
        return articles

    def fetch_stock_specific_news(self) -> List[Dict]:
        """并发获取用户自选股相关新闻"""
        my_stocks = self.user_config.get('my_stocks', [])
        if not my_stocks:
            return []
        
        logger.info(f"并发采集自选股新闻 ({len(my_stocks)}只)...")
        stock_articles = []
        scraper = WebScraper()
        max_workers = min(4, len(my_stocks))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_stock = {
                executor.submit(scraper.search_stock_news, stock['name']): stock['name']
                for stock in my_stocks
            }
            for future in as_completed(future_to_stock, timeout=60):
                stock_name = future_to_stock[future]
                try:
                    news = future.result(timeout=15)
                    stock_articles.extend(news)
                except Exception as e:
                    logger.warning(f"自选股'{stock_name}'采集异常: {e}")
        
        logger.info(f"自选股新闻采集完成: {len(stock_articles)} 条")
        return stock_articles
