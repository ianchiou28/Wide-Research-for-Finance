import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import urllib.parse
import os

class WebScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # 微博需要Cookie才能获取到实时热搜
        self.weibo_headers = self.headers.copy()
        self.weibo_headers['Cookie'] = os.getenv('WEIBO_COOKIE', '')
    
    def scrape_fed(self) -> List[Dict]:
        """美联储新闻"""
        try:
            r = requests.get('https://www.federalreserve.gov/newsevents.htm', headers=self.headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
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
            soup = BeautifulSoup(r.text, 'html.parser')
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
            soup = BeautifulSoup(r.text, 'html.parser')
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
            soup = BeautifulSoup(r.text, 'html.parser')
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
    
    def scrape_weibo_hot_search(self) -> List[Dict]:
        """微博财经热搜"""
        articles = []
        try:
            # 微博热搜榜的移动端页面相对简单
            r = requests.get('https://m.weibo.cn/api/container/getIndex?containerid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Drealtimehot', headers=self.weibo_headers, timeout=10)
            data = r.json()
            for item in data['data']['cards'][0]['card_group'][:5]: # 取前5条
                title = item['desc']
                articles.append({
                    'title': f"微博热搜: {title}",
                    'content': item.get('desc_extr', title),
                    'source': '微博热搜',
                    'category': 'hot_search',
                    'url': item.get('scheme', ''),
                    'published_at': datetime.now().isoformat()
                })
            return articles
        except Exception as e:
            print(f"  ⚠ 微博热搜: 无法获取，可能需要有效的Cookie. Error: {e}")
            return []

    def scrape_tonghuashun(self) -> List[Dict]:
        """同花顺7x24快讯"""
        articles = []
        try:
            r = requests.get('http://news.10jqka.com.cn/realtimenews.html', headers=self.headers, timeout=10)
            r.encoding = 'gbk'
            soup = BeautifulSoup(r.text, 'html.parser')
            for item in soup.select('.main-fl ul.list-con li')[:5]: # 取前5条
                title_tag = item.select_one('a')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    content = item.select_one('span').get_text(strip=True) if item.select_one('span') else title
                    articles.append({
                        'title': title,
                        'content': content,
                        'source': '同花顺',
                        'category': 'china_news',
                        'url': title_tag['href'],
                        'published_at': datetime.now().isoformat()
                    })
            return articles
        except Exception as e:
            print(f"  ⚠ 同花顺: {str(e)[:30]}")
            return []

    def search_stock_news(self, stock_name: str) -> List[Dict]:
        """根据股票名称搜索新闻（以百度为例）"""
        articles = []
        try:
            query = urllib.parse.quote(f"{stock_name} 股票 新闻")
            url = f"https://www.baidu.com/s?rtt=1&bsst=1&cl=2&tn=news&word={query}"
            r = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            for item in soup.select('.result-op.c-container.new-pmd')[:2]: # 每个股票取2条
                title_tag = item.select_one('h3 a')
                if title_tag:
                    articles.append({
                        'title': f"[{stock_name}] {title_tag.get_text(strip=True)}",
                        'content': item.select_one('.c-summary').get_text(strip=True) if item.select_one('.c-summary') else '',
                        'source': '百度新闻',
                        'category': 'stock_specific',
                        'url': title_tag['href'],
                        'published_at': datetime.now().isoformat()
                    })
            return articles
        except Exception as e:
            print(f"  ⚠ 搜索'{stock_name}'新闻失败: {e}")
            return []

    def scrape_all(self) -> List[Dict]:
        """爬取所有官方网站"""
        all_articles = []
        success_count = 0
        scrapers = [
            ('美联储', self.scrape_fed),
            ('SEC', self.scrape_sec),
            ('央行', self.scrape_pbc),
            ('证监会', self.scrape_csrc),
            ('微博热搜', self.scrape_weibo_hot_search),
            ('同花顺', self.scrape_tonghuashun),
        ]
        
        for name, scraper in scrapers:
            try:
                articles = scraper()
                all_articles.extend(articles)
                if articles:
                    print(f"  ✓ {name}: {len(articles)}条")
                    success_count += 1
                else:
                    print(f"  - {name}: 0条")
            except Exception as e:
                print(f"  ⚠ {name}: {str(e)[:30]}")
        
        print(f"  📊 爬虫统计: {success_count}/{len(scrapers)} 成功, 共 {len(all_articles)} 条")
        return all_articles
