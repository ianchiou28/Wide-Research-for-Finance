import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict

class WebScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_fed(self) -> List[Dict]:
        """美联储新闻"""
        try:
            r = requests.get('https://www.federalreserve.gov/newsevents.htm', headers=self.headers, timeout=10)
            soup = BeautifulSoup(r.content, 'html.parser')
            articles = []
            for item in soup.select('.row.eventlist__event')[:3]:
                title = item.select_one('.eventlist__event__title')
                if title:
                    articles.append({
                        'title': title.get_text(strip=True),
                        'content': item.get_text(strip=True)[:500],
                        'source': '美联储',
                        'category': 'us_official',
                        'url': 'https://www.federalreserve.gov' + title.find('a')['href'] if title.find('a') else '',
                        'published_at': datetime.now().isoformat()
                    })
            return articles
        except:
            return []
    
    def scrape_sec(self) -> List[Dict]:
        """SEC公告"""
        try:
            r = requests.get('https://www.sec.gov/news/pressreleases', headers=self.headers, timeout=10)
            soup = BeautifulSoup(r.content, 'html.parser')
            articles = []
            for item in soup.select('.views-row')[:3]:
                title = item.select_one('.views-field-title a')
                if title:
                    articles.append({
                        'title': title.get_text(strip=True),
                        'content': item.get_text(strip=True)[:500],
                        'source': 'SEC公告',
                        'category': 'us_official',
                        'url': 'https://www.sec.gov' + title['href'],
                        'published_at': datetime.now().isoformat()
                    })
            return articles
        except:
            return []
    
    def scrape_pbc(self) -> List[Dict]:
        """中国人民银行"""
        try:
            r = requests.get('http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html', timeout=10)
            r.encoding = 'utf-8'
            soup = BeautifulSoup(r.content, 'html.parser')
            articles = []
            for item in soup.select('ul.list li')[:3]:
                link = item.find('a')
                if link:
                    articles.append({
                        'title': link.get_text(strip=True),
                        'content': link.get_text(strip=True),
                        'source': '中国人民银行',
                        'category': 'china_official',
                        'url': 'http://www.pbc.gov.cn' + link['href'],
                        'published_at': datetime.now().isoformat()
                    })
            return articles
        except:
            return []
    
    def scrape_csrc(self) -> List[Dict]:
        """证监会"""
        try:
            r = requests.get('https://www.csrc.gov.cn/csrc/c100028/common_list.shtml', timeout=10)
            r.encoding = 'utf-8'
            soup = BeautifulSoup(r.content, 'html.parser')
            articles = []
            for item in soup.select('.fl_list li')[:3]:
                link = item.find('a')
                if link:
                    articles.append({
                        'title': link.get_text(strip=True),
                        'content': link.get_text(strip=True),
                        'source': '证监会',
                        'category': 'china_official',
                        'url': 'https://www.csrc.gov.cn' + link.get('href', ''),
                        'published_at': datetime.now().isoformat()
                    })
            return articles
        except:
            return []
    
    def scrape_all(self) -> List[Dict]:
        """爬取所有官方网站"""
        all_articles = []
        scrapers = [
            ('美联储', self.scrape_fed),
            ('SEC', self.scrape_sec),
            ('央行', self.scrape_pbc),
            ('证监会', self.scrape_csrc),
        ]
        
        for name, scraper in scrapers:
            try:
                articles = scraper()
                all_articles.extend(articles)
                if articles:
                    print(f"  ✓ {name}: {len(articles)}条")
            except Exception as e:
                print(f"  ⚠ {name}: {str(e)[:30]}")
        
        return all_articles
