import os
import glob
from datetime import datetime, timedelta
from typing import List, Dict
from collections import Counter

class DailySummary:
    def __init__(self):
        self.reports_dir = "data/reports"
        
    def generate_12h_summary(self) -> str:
        """生成过去12小时的摘要报告"""
        # 获取过去12小时的报告文件
        reports = self._get_recent_reports(hours=12)
        
        if not reports:
            return "过去12小时无报告数据"
        
        # 解析所有报告
        all_news = []
        for report_path in reports:
            news_items = self._parse_report(report_path)
            all_news.extend(news_items)
        
        # 生成摘要
        summary = self._create_summary(all_news, len(reports))
        return summary
    
    def _get_recent_reports(self, hours: int) -> List[str]:
        """获取最近N小时的报告文件"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        reports = glob.glob(os.path.join(self.reports_dir, "report_*.txt"))
        
        recent_reports = []
        for report in reports:
            filename = os.path.basename(report)
            try:
                time_str = filename.replace('report_', '').replace('.txt', '')
                report_time = datetime.strptime(time_str, '%Y%m%d_%H%M%S')
                if report_time >= cutoff_time:
                    recent_reports.append(report)
            except:
                continue
        
        return sorted(recent_reports)
    
    def _parse_report(self, report_path: str) -> List[Dict]:
        """解析单个报告文件"""
        news_items = []
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取重大事件部分
            if '【重大事件提醒】' in content:
                events_section = content.split('【重大事件提醒】')[1].split('【其他新闻')[0]
                
                # 简单解析事件
                lines = events_section.strip().split('\n')
                current_event = {}
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('[') and ']' in line:
                        if current_event:
                            news_items.append(current_event)
                        current_event = {'source': line.split(']')[0][1:]}
                    elif line.startswith('标题:'):
                        current_event['title'] = line.replace('标题:', '').strip()
                    elif line.startswith('摘要:'):
                        current_event['summary'] = line.replace('摘要:', '').strip()
                    elif line.startswith('情绪:'):
                        sentiment_line = line.replace('情绪:', '').strip()
                        parts = sentiment_line.split('|')
                        current_event['sentiment'] = parts[0].strip()
                        if len(parts) >= 2:
                            current_event['sentiment_cn'] = parts[1].replace('中国:', '').strip()
                        if len(parts) >= 3:
                            current_event['sentiment_us'] = parts[2].replace('美国:', '').strip()
                
                if current_event:
                    news_items.append(current_event)
        
        except Exception as e:
            print(f"解析报告失败 {report_path}: {e}")
        
        return news_items
    
    def _create_summary(self, news_items: List[Dict], report_count: int) -> str:
        """创建摘要报告"""
        now = datetime.now()
        period = "早间" if now.hour == 8 else "晚间"
        
        # 统计情绪
        sentiments = [item.get('sentiment', '中性') for item in news_items]
        sentiment_counts = Counter(sentiments)
        
        # 提取关键词
        all_titles = ' '.join([item.get('title', '') for item in news_items])
        
        # 分类统计
        cn_positive = sum(1 for item in news_items if item.get('sentiment_cn') == '积极')
        cn_negative = sum(1 for item in news_items if item.get('sentiment_cn') == '消极')
        us_positive = sum(1 for item in news_items if item.get('sentiment_us') == '积极')
        us_negative = sum(1 for item in news_items if item.get('sentiment_us') == '消极')
        
        summary = f"""
{'='*60}
{period}财经摘要 - {now.strftime('%Y年%m月%d日 %H时')}
过去12小时重点回顾
{'='*60}

【数据概览】
- 时间范围: {(now - timedelta(hours=12)).strftime('%m月%d日 %H时')} - {now.strftime('%m月%d日 %H时')}
- 报告数量: {report_count} 份
- 重大事件: {len(news_items)} 条

【市场情绪】
- 积极事件: {sentiment_counts.get('积极', 0)} 条
- 中性事件: {sentiment_counts.get('中性', 0)} 条
- 消极事件: {sentiment_counts.get('消极', 0)} 条

【市场分化】
中国市场: 积极 {cn_positive} | 消极 {cn_negative}
美国市场: 积极 {us_positive} | 消极 {us_negative}

【重点事件】（按时间倒序）
"""
        
        # 列出最重要的事件（最近的10条）
        for i, item in enumerate(news_items[-10:][::-1], 1):
            sentiment_info = item.get('sentiment', '中性')
            if 'sentiment_cn' in item and 'sentiment_us' in item:
                sentiment_info += f" | 🇨🇳{item['sentiment_cn']} 🇺🇸{item['sentiment_us']}"
            
            summary += f"""
{i}. [{item.get('source', '未知')}]
   {item.get('title', '无标题')}
   {item.get('summary', '无摘要')}
   情绪: {sentiment_info}
"""
        
        summary += f"""
{'='*60}
【操作建议】
"""
        
        # 根据情绪给出建议
        if sentiment_counts.get('消极', 0) > sentiment_counts.get('积极', 0):
            summary += """
⚠️ 市场情绪偏消极，建议：
- 关注风险控制，适当降低仓位
- 重点关注避险资产（黄金、国债）
- 警惕市场波动加剧
"""
        elif sentiment_counts.get('积极', 0) > sentiment_counts.get('消极', 0) * 1.5:
            summary += """
✅ 市场情绪积极，建议：
- 可适当增加风险资产配置
- 关注热点板块机会
- 注意获利回吐风险
"""
        else:
            summary += """
➡️ 市场情绪中性，建议：
- 保持现有仓位，观望为主
- 关注重大政策和数据发布
- 等待明确方向信号
"""
        
        # 市场分化建议
        if cn_negative > cn_positive and us_positive > us_negative:
            summary += """
🌏 市场分化明显：
- 中国市场承压，美国市场相对强势
- 建议关注全球配置平衡
"""
        elif cn_positive > cn_negative and us_negative > us_positive:
            summary += """
🌏 市场分化明显：
- 中国市场表现较好，美国市场承压
- 可关注A股机会，美股谨慎
"""
        
        summary += f"""
{'='*60}
报告生成时间: {now.strftime('%Y-%m-%d %H:%M:%S')}
下次摘要时间: {(now + timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')}
{'='*60}
"""
        
        return summary
    
    def save_summary(self, summary: str):
        """保存摘要报告"""
        os.makedirs('data/summaries', exist_ok=True)
        filename = f"data/summaries/summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"✅ 摘要已保存: {filename}")
        return filename
