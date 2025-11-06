import feedparser
import yaml
from datetime import datetime, timedelta
from typing import List, Dict

class DataCollector:
    def __init__(self, config_path='config/sources.yaml'):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
    def fetch_latest(self, hours=24, max_per_source=15) -> List[Dict]:
        """获取最近N小时的新闻"""
        articles = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for source in self.config.get('rss_sources', []):
            try:
                feed = feedparser.parse(source['url'])
                count = 0
                
                for entry in feed.entries[:max_per_source*2]:  # 多取一些以防过滤
                    if count >= max_per_source:
                        break
                    
                    try:
                        pub_date = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                    except:
                        pub_date = datetime.now()
                    
                    if pub_date < cutoff_time:
                        continue
                    
                    articles.append({
                        'title': entry.title,
                        'content': entry.get('summary', entry.get('description', ''))[:1000],
                        'source': source['name'],
                        'category': source.get('category', 'general'),
                        'url': entry.link,
                        'published_at': pub_date.isoformat()
                    })
                    count += 1
                    
            except Exception as e:
                print(f"  ⚠ {source['name']}: {str(e)[:50]}")
        
        print(f"  ✓ 成功采集 {len(articles)} 条新闻")
        return articles
