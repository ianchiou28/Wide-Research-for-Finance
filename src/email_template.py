"""
HTML邮件模板生成器
生成美观的可视化邮件报告
"""

from datetime import datetime
from typing import Dict, Any


class EmailTemplateGenerator:
    """HTML邮件模板生成器"""
    
    # 颜色配置
    COLORS = {
        'primary': '#FF5500',
        'positive': '#4CAF50',
        'negative': '#F44336',
        'neutral': '#FF9800',
        'bg': '#F2F2E9',
        'card': '#FFFFFF',
        'text': '#111111',
        'muted': '#666666',
        'border': '#E0E0D8'
    }
    
    # SVG图标路径
    ICONS = {
        'up': '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>',
        'down': '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline><polyline points="17 18 23 18 23 12"></polyline></svg>',
        'flat': '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><line x1="5" y1="12" x2="19" y2="12"></line></svg>'
    }
    
    def generate_email_html(self, report_data: Dict[str, Any]) -> str:
        """生成完整的HTML邮件"""
        meta = report_data.get('meta', {})
        sentiment = report_data.get('sentiment', {})
        entities = report_data.get('entities', [])
        events = report_data.get('events', {})
        stock_impacts = report_data.get('stock_impacts', [])
        
        return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>财经新闻简报</title>
</head>
<body style="margin: 0; padding: 0; background-color: {self.COLORS['bg']}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 700px; margin: 0 auto; background-color: {self.COLORS['bg']};">
        <!-- Header -->
        <tr>
            <td style="padding: 30px 20px; background-color: {self.COLORS['primary']};">
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                        <td>
                            <h1 style="margin: 0; color: white; font-size: 24px; font-weight: 700; letter-spacing: 1px;">
                                财经新闻简报
                            </h1>
                            <p style="margin: 8px 0 0 0; color: rgba(255,255,255,0.9); font-size: 14px;">
                                {meta.get('generated_at', '')[:10]} | 北京 {meta.get('beijing_time', '')} | 纽约 {meta.get('newyork_time', '')}
                            </p>
                        </td>
                        <td style="text-align: right; color: white;">
                            <div style="font-size: 36px; font-weight: 700;">{meta.get('total_news', 0)}</div>
                            <div style="font-size: 12px; opacity: 0.9;">条新闻分析</div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        
        <!-- Sentiment Section -->
        <tr>
            <td style="padding: 20px;">
                <table width="100%" cellpadding="0" cellspacing="0" style="background: {self.COLORS['card']}; border: 1px solid {self.COLORS['border']};">
                    <tr>
                        <td style="padding: 20px; border-bottom: 1px solid {self.COLORS['border']};">
                            <h2 style="margin: 0; font-size: 16px; color: {self.COLORS['text']}; text-transform: uppercase; letter-spacing: 0.5px;">
                                <span style="display: inline-block; width: 8px; height: 8px; background-color: {self.COLORS['primary']}; margin-right: 8px; vertical-align: middle;"></span>
                                MARKET SENTIMENT
                            </h2>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 20px;">
                            {self._render_sentiment_bars(sentiment)}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0 20px 20px;">
                            {self._render_sentiment_distribution(sentiment.get('distribution', {}))}
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        
        <!-- High Impact Events -->
        {self._render_events_section(events.get('high_impact', []), 'KEY EVENTS', 'high')}
        
        <!-- Stock Impacts -->
        {self._render_stock_impacts_section(stock_impacts)}
        
        <!-- Hot Entities -->
        {self._render_entities_section(entities)}
        
        <!-- Footer -->
        <tr>
            <td style="padding: 30px 20px; text-align: center;">
                <p style="margin: 0; color: {self.COLORS['muted']}; font-size: 12px;">
                    本报告由 AI 自动生成，仅供参考，不构成投资建议
                </p>
                <p style="margin: 8px 0 0 0; color: {self.COLORS['muted']}; font-size: 12px;">
                    Wide Research Finance Terminal | DeepSeek 智能引擎
                </p>
            </td>
        </tr>
    </table>
</body>
</html>
'''
    
    def _render_sentiment_bars(self, sentiment: Dict) -> str:
        """渲染情绪条"""
        markets = [
            ('GLOBAL', sentiment.get('overall', {})),
            ('CHINA', sentiment.get('cn', {})),
            ('USA', sentiment.get('us', {}))
        ]
        
        html = '<table width="100%" cellpadding="0" cellspacing="0">'
        
        for name, data in markets:
            score = data.get('score', 0)
            label = data.get('label', '中性')
            color = self._get_sentiment_color(score)
            
            # 计算条的位置和宽度
            bar_width = min(abs(score) * 50, 50)
            bar_position = 'left: 50%;' if score >= 0 else f'right: 50%;'
            
            html += f'''
            <tr>
                <td style="padding: 10px 0;">
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                            <td width="80" style="font-size: 12px; font-weight: 700; color: {self.COLORS['text']};">{name}</td>
                            <td style="padding: 0 15px;">
                                <div style="position: relative; height: 24px; background: #eee; border-radius: 2px;">
                                    <div style="position: absolute; top: 0; {bar_position} width: {bar_width}%; height: 100%; background: {color};"></div>
                                    <div style="position: absolute; left: 50%; top: 0; width: 2px; height: 100%; background: {self.COLORS['text']}; opacity: 0.2;"></div>
                                </div>
                            </td>
                            <td width="80" style="text-align: right;">
                                <span style="font-weight: 700; color: {color}; font-size: 16px;">
                                    {'+' if score > 0 else ''}{score:.2f}
                                </span>
                                <span style="font-size: 12px; color: {self.COLORS['muted']}; display: block;">{label}</span>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            '''
        
        html += '</table>'
        return html
    
    def _render_sentiment_distribution(self, distribution: Dict) -> str:
        """渲染情绪分布"""
        positive = distribution.get('positive', 0)
        neutral = distribution.get('neutral', 0)
        negative = distribution.get('negative', 0)
        total = positive + neutral + negative or 1
        
        return f'''
        <table width="100%" cellpadding="0" cellspacing="0" style="background: #f5f5f5; border-radius: 4px;">
            <tr>
                <td style="padding: 15px;">
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                            <td style="text-align: center; width: 33%;">
                                <div style="font-size: 24px; font-weight: 700; color: {self.COLORS['positive']};">{positive}</div>
                                <div style="font-size: 12px; color: {self.COLORS['muted']};">积极 ({positive*100//total}%)</div>
                            </td>
                            <td style="text-align: center; width: 33%;">
                                <div style="font-size: 24px; font-weight: 700; color: {self.COLORS['neutral']};">{neutral}</div>
                                <div style="font-size: 12px; color: {self.COLORS['muted']};">中性 ({neutral*100//total}%)</div>
                            </td>
                            <td style="text-align: center; width: 33%;">
                                <div style="font-size: 24px; font-weight: 700; color: {self.COLORS['negative']};">{negative}</div>
                                <div style="font-size: 12px; color: {self.COLORS['muted']};">消极 ({negative*100//total}%)</div>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        '''
    
    def _render_events_section(self, events: list, title: str, event_type: str) -> str:
        """渲染事件列表"""
        if not events:
            return ''
        
        events_html = ''
        for event in events[:5]:
            sentiment_score = event.get('sentiment', {}).get('overall', 0) if isinstance(event.get('sentiment'), dict) else 0
            sentiment_color = self._get_sentiment_color(sentiment_score)
            
            # 股票影响标签
            stock_tags = ''
            stock_impact = event.get('stock_impact', [])
            if isinstance(stock_impact, list):
                for stock in stock_impact[:3]:
                    # 处理字符串或字典两种格式
                    if isinstance(stock, str):
                        stock_tags += f'''
                        <span style="display: inline-block; padding: 2px 8px; margin-right: 5px; background: {self.COLORS['neutral']}20; color: {self.COLORS['neutral']}; font-size: 11px; border-radius: 2px;">
                            {stock}
                        </span>
                        '''
                    elif isinstance(stock, dict):
                        direction = stock.get('direction', '')
                        icon = self.ICONS['up'] if direction == '上涨' else self.ICONS['down'] if direction == '下跌' else self.ICONS['flat']
                        tag_color = self.COLORS['positive'] if direction == '上涨' else self.COLORS['negative'] if direction == '下跌' else self.COLORS['neutral']
                        stock_tags += f'''
                        <span style="display: inline-block; padding: 2px 8px; margin-right: 5px; background: {tag_color}20; color: {tag_color}; font-size: 11px; border-radius: 2px;">
                            {stock.get('symbol', '')} {icon}
                        </span>
                        '''
            
            events_html += f'''
            <tr>
                <td style="padding: 15px; border-bottom: 1px solid {self.COLORS['border']};">
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                            <td>
                                <span style="display: inline-block; padding: 2px 8px; background: {self.COLORS['text']}; color: white; font-size: 11px; margin-right: 8px;">
                                    {event.get('source', '')}
                                </span>
                                <span style="display: inline-block; padding: 2px 8px; background: {sentiment_color}20; color: {sentiment_color}; font-size: 11px;">
                                    {event.get('event_type', '')}
                                </span>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding-top: 10px;">
                                <a href="{event.get('url', '#')}" style="color: {self.COLORS['text']}; text-decoration: none; font-weight: 600; font-size: 15px;">
                                    {event.get('title', '')}
                                </a>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding-top: 8px; color: {self.COLORS['muted']}; font-size: 13px; line-height: 1.5;">
                                {event.get('summary', '')}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding-top: 10px;">
                                {stock_tags}
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            '''
        
        return f'''
        <tr>
            <td style="padding: 20px;">
                <table width="100%" cellpadding="0" cellspacing="0" style="background: {self.COLORS['card']}; border: 1px solid {self.COLORS['border']};">
                    <tr>
                        <td style="padding: 20px; border-bottom: 1px solid {self.COLORS['border']};">
                            <h2 style="margin: 0; font-size: 16px; color: {self.COLORS['text']};">{title}</h2>
                        </td>
                    </tr>
                    {events_html}
                </table>
            </td>
        </tr>
        '''
    
    def _render_stock_impacts_section(self, stocks: list) -> str:
        """渲染股票影响"""
        if not stocks:
            return ''
        
        stocks_html = ''
        for stock in stocks[:6]:
            prediction = stock.get('prediction', '中性')
            confidence = stock.get('confidence', 0.5)
            
            if prediction == '看涨':
                pred_color = self.COLORS['positive']
                pred_icon = self.ICONS['up']
            elif prediction == '看跌':
                pred_color = self.COLORS['negative']
                pred_icon = self.ICONS['down']
            else:
                pred_color = self.COLORS['neutral']
                pred_icon = self.ICONS['flat']
            
            # 置信度条
            conf_width = int(confidence * 100)
            
            stocks_html += f'''
            <td style="width: 50%; padding: 10px; vertical-align: top;">
                <div style="background: #f9f9f9; padding: 15px; border-radius: 4px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 700; color: {self.COLORS['text']};">{stock.get('symbol', '')}</span>
                        <span style="color: {pred_color}; font-weight: 700; display: flex; align-items: center;">{pred_icon} <span style="margin-left: 4px;">{prediction}</span></span>
                    </div>
                    <div style="font-size: 12px; color: {self.COLORS['muted']}; margin-top: 5px;">{stock.get('name', '')}</div>
                    <div style="margin-top: 10px;">
                        <div style="font-size: 11px; color: {self.COLORS['muted']}; margin-bottom: 3px;">置信度 {conf_width}%</div>
                        <div style="height: 4px; background: #eee; border-radius: 2px;">
                            <div style="width: {conf_width}%; height: 100%; background: {pred_color}; border-radius: 2px;"></div>
                        </div>
                    </div>
                    <div style="font-size: 11px; color: {self.COLORS['muted']}; margin-top: 8px;">
                        提及 {stock.get('total_mentions', 0)} 次 | 看涨 {stock.get('up_count', 0)} | 看跌 {stock.get('down_count', 0)}
                    </div>
                </div>
            </td>
            '''
        
        # 每行两个股票
        rows_html = ''
        for i in range(0, len(stocks[:6]), 2):
            row_stocks = stocks[i:i+2]
            row_html = '<tr>'
            for j, stock in enumerate(row_stocks):
                prediction = stock.get('prediction', '中性')
                confidence = stock.get('confidence', 0.5)
                
                if prediction == '看涨':
                    pred_color = self.COLORS['positive']
                    pred_icon = self.ICONS['up']
                elif prediction == '看跌':
                    pred_color = self.COLORS['negative']
                    pred_icon = self.ICONS['down']
                else:
                    pred_color = self.COLORS['neutral']
                    pred_icon = self.ICONS['flat']
                
                conf_width = int(confidence * 100)
                
                row_html += f'''
                <td style="width: 50%; padding: 10px; vertical-align: top;">
                    <div style="background: #f9f9f9; padding: 15px; border-radius: 4px;">
                        <table width="100%" cellpadding="0" cellspacing="0">
                            <tr>
                                <td style="font-weight: 700; color: {self.COLORS['text']};">{stock.get('symbol', '')}</td>
                                <td style="text-align: right; color: {pred_color}; font-weight: 700;">
                                    <span style="display: inline-flex; align-items: center;">
                                        {pred_icon} <span style="margin-left: 4px;">{prediction}</span>
                                    </span>
                                </td>
                            </tr>
                        </table>
                        <div style="font-size: 12px; color: {self.COLORS['muted']}; margin-top: 5px;">{stock.get('name', '')}</div>
                        <div style="margin-top: 10px;">
                            <div style="font-size: 11px; color: {self.COLORS['muted']}; margin-bottom: 3px;">置信度 {conf_width}%</div>
                            <div style="height: 4px; background: #eee; border-radius: 2px;">
                                <div style="width: {conf_width}%; height: 100%; background: {pred_color}; border-radius: 2px;"></div>
                            </div>
                        </div>
                        <div style="font-size: 11px; color: {self.COLORS['muted']}; margin-top: 8px;">
                            提及 {stock.get('total_mentions', 0)} 次
                        </div>
                    </div>
                </td>
                '''
            
            if len(row_stocks) == 1:
                row_html += '<td style="width: 50%;"></td>'
            
            row_html += '</tr>'
            rows_html += row_html
        
        return f'''
        <tr>
            <td style="padding: 20px;">
                <table width="100%" cellpadding="0" cellspacing="0" style="background: {self.COLORS['card']}; border: 1px solid {self.COLORS['border']};">
                    <tr>
                        <td style="padding: 20px; border-bottom: 1px solid {self.COLORS['border']};">
                            <h2 style="margin: 0; font-size: 16px; color: {self.COLORS['text']}; text-transform: uppercase; letter-spacing: 0.5px;">STOCK IMPACT PREDICTION</h2>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px;">
                            <table width="100%" cellpadding="0" cellspacing="0">
                                {rows_html}
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        '''
    
    def _render_entities_section(self, entities: list) -> str:
        """渲染热门实体"""
        if not entities:
            return ''
        
        tags_html = ''
        for entity in entities[:12]:
            sentiment = entity.get('avg_sentiment', 0)
            color = self._get_sentiment_color(sentiment)
            
            tags_html += f'''
            <span style="display: inline-block; padding: 6px 12px; margin: 4px; background: white; border: 1px solid {self.COLORS['border']}; font-size: 13px; border-radius: 2px;">
                <span style="color: {self.COLORS['text']};">{entity.get('name', '')}</span>
                <span style="color: {self.COLORS['muted']}; font-size: 11px; margin-left: 5px;">×{entity.get('count', 0)}</span>
            </span>
            '''
        
        return f'''
        <tr>
            <td style="padding: 20px;">
                <table width="100%" cellpadding="0" cellspacing="0" style="background: {self.COLORS['card']}; border: 1px solid {self.COLORS['border']};">
                    <tr>
                        <td style="padding: 20px; border-bottom: 1px solid {self.COLORS['border']};">
                            <h2 style="margin: 0; font-size: 16px; color: {self.COLORS['text']}; text-transform: uppercase; letter-spacing: 0.5px;">HOT TOPICS</h2>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 15px;">
                            {tags_html}
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        '''
    
    def _get_sentiment_color(self, score: float) -> str:
        """根据情绪分数获取颜色"""
        if score > 0.1:
            return self.COLORS['positive']
        if score < -0.1:
            return self.COLORS['negative']
        return self.COLORS['neutral']


# 测试
if __name__ == '__main__':
    generator = EmailTemplateGenerator()
    
    test_report = {
        'meta': {
            'generated_at': '2025-11-27T14:00:00',
            'beijing_time': '14:00',
            'newyork_time': '01:00',
            'total_news': 42,
            'report_type': 'hourly'
        },
        'sentiment': {
            'overall': {'score': 0.35, 'label': '积极'},
            'cn': {'score': 0.28, 'label': '中性'},
            'us': {'score': 0.52, 'label': '积极'},
            'distribution': {'positive': 18, 'neutral': 16, 'negative': 8}
        },
        'entities': [
            {'name': '英伟达', 'count': 12, 'avg_sentiment': 0.6},
            {'name': 'AI', 'count': 10, 'avg_sentiment': 0.4},
            {'name': '央行', 'count': 8, 'avg_sentiment': 0.2},
        ],
        'events': {
            'high_impact': [
                {
                    'title': '英伟达Q3财报超预期，AI芯片需求强劲',
                    'summary': '英伟达第三季度营收达到350亿美元，同比增长94%，超出分析师预期。',
                    'source': 'Reuters',
                    'url': 'https://example.com',
                    'event_type': '财报',
                    'sentiment': {'overall': 0.8},
                    'stock_impact': [
                        {'symbol': 'NVDA', 'name': '英伟达', 'direction': '上涨'},
                        {'symbol': 'AMD', 'name': 'AMD', 'direction': '上涨'}
                    ]
                }
            ]
        },
        'stock_impacts': [
            {'symbol': 'NVDA', 'name': '英伟达', 'prediction': '看涨', 'confidence': 0.85, 'total_mentions': 12, 'up_count': 10, 'down_count': 1, 'neutral_count': 1},
            {'symbol': 'TSLA', 'name': '特斯拉', 'prediction': '中性', 'confidence': 0.55, 'total_mentions': 8, 'up_count': 3, 'down_count': 3, 'neutral_count': 2},
        ]
    }
    
    html = generator.generate_email_html(test_report)
    
    with open('test_email.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("HTML邮件已生成: test_email.html")
