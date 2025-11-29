import { ref, computed } from 'vue'

// Global reactive state
const locale = ref(localStorage.getItem('locale') || 'zh')

// Translation dictionary
const translations = {
  // Navigation
  nav_dashboard: { zh: '概览仪表盘', en: 'Dashboard' },
  nav_watchlist: { zh: '自选监控', en: 'Watchlist' },
  nav_hot_topics: { zh: '全网热搜', en: 'Hot Topics' },
  nav_crypto: { zh: '加密货币', en: 'Crypto' },
  nav_history: { zh: '历史报告', en: 'History' },
  nav_overview: { zh: '项目总览', en: 'Overview' },
  
  // System Status
  system_status: { zh: '系统状态', en: 'System Status' },
  connection_status: { zh: '连接状态', en: 'Connection' },
  last_sync: { zh: '上次同步', en: 'Last Sync' },
  version: { zh: '版本', en: 'Version' },
  
  // Home Page - KPIs
  market_sentiment: { zh: '市场情绪', en: 'MARKET SENTIMENT' },
  key_events: { zh: '关键事件', en: 'KEY EVENTS' },
  stock_prediction: { zh: '个股预测', en: 'STOCK PREDICTION' },
  hot_topics: { zh: '热门话题', en: 'HOT TOPICS' },
  market_outlook: { zh: '市场展望', en: 'MARKET OUTLOOK' },
  statistics: { zh: '统计数据', en: 'STATISTICS' },
  total_news: { zh: '已分析新闻', en: 'Total News' },
  market_sentiment_kpi: { zh: '市场情绪', en: 'Sentiment' },
  hot_topics_kpi: { zh: '热门话题', en: 'Hot Topics' },
  updated_at: { zh: '更新时间', en: 'Updated' },
  system_online: { zh: '系统在线', en: 'System Online' },
  loading: { zh: '正在加载数据...', en: 'Loading data...' },
  empty_events: { zh: '暂无重大事件', en: 'No key events found' },
  empty_topics: { zh: '暂无热门话题', en: 'No hot topics found' },
  beijing_time: { zh: '北京时间', en: 'Beijing Time' },
  newyork_time: { zh: '纽约时间', en: 'New York Time' },
  event_count: { zh: '重大事件', en: 'Key Events' },
  stock_signal_count: { zh: '股票信号', en: 'Stock Signals' },
  positive: { zh: '积极', en: 'Positive' },
  neutral: { zh: '中性', en: 'Neutral' },
  negative: { zh: '消极', en: 'Negative' },
  confidence: { zh: '置信度', en: 'Confidence' },
  mentions: { zh: '提及', en: 'Mentions' },
  times: { zh: '次', en: 'times' },
  brand_title: { zh: '金融终端', en: 'FINANCE TERMINAL' },
  brand_subtitle: { zh: 'DeepSeek 智能引擎', en: 'DeepSeek AI ENGINE' },
  market_global: { zh: '全球市场', en: 'Global Market' },
  market_cn: { zh: '中国市场', en: 'China Market' },
  market_us: { zh: '美国市场', en: 'US Market' },
  market_a_share: { zh: 'A股', en: 'A-Share' },
  market_us_stock: { zh: '美股', en: 'US Stock' },
  market_global_short: { zh: '全球', en: 'Global' },
  trend_bullish: { zh: '看涨', en: 'Bullish' },
  trend_bearish: { zh: '看跌', en: 'Bearish' },
  trend_sideways: { zh: '震荡', en: 'Sideways' },
  unit_items: { zh: '条', en: '' },
  unit_count: { zh: '个', en: '' },
  
  // Watchlist
  watchlist_title: { zh: '我的关注列表', en: 'MY WATCHLIST' },
  add_stock: { zh: '添加', en: 'Add' },
  stock_code: { zh: '代码', en: 'Code' },
  stock_name: { zh: '名称', en: 'Name' },
  current_price: { zh: '最新价', en: 'Price' },
  change_pct: { zh: '涨跌幅', en: 'Change' },
  high: { zh: '最高', en: 'High' },
  low: { zh: '最低', en: 'Low' },
  open: { zh: '今开', en: 'Open' },
  prev_close: { zh: '昨收', en: 'Prev Close' },
  volume: { zh: '成交量', en: 'Volume' },
  amount: { zh: '成交额', en: 'Amount' },
  action: { zh: '操作', en: 'Action' },
  delete: { zh: '删除', en: 'Del' },
  view: { zh: '查看', en: 'View' },
  kline_chart: { zh: 'K线走势', en: 'K-Line Chart' },
  related_news: { zh: '相关资讯', en: 'Related News' },
  period_daily: { zh: '日K', en: 'D' },
  period_weekly: { zh: '周K', en: 'W' },
  period_monthly: { zh: '月K', en: 'M' },
  no_data: { zh: '暂无数据', en: 'No Data' },
  loading_chart: { zh: '加载中...', en: 'Loading...' },
  
  // Hot Topics
  hot_topics_title: { zh: '全网热搜', en: 'HOT TOPICS' },
  sources: { zh: '来源', en: 'SOURCES' },
  update: { zh: '更新', en: 'UPDATE' },
  no_data_or_failed: { zh: '暂无数据或采集失败', en: 'No data or fetch failed' },
  
  // Crypto
  crypto_title: { zh: '加密货币', en: 'CRYPTOCURRENCY' },
  market_cap: { zh: '市值', en: 'MARKET CAP' },
  volume_24h: { zh: '24h成交量', en: '24h Volume' },
  price_change_24h: { zh: '24h涨跌', en: '24h Change' },
  
  // History
  history_title: { zh: '历史报告', en: 'HISTORICAL REPORTS' },
  report_list: { zh: '时间轴', en: 'Timeline' },
  report_content: { zh: '报告内容', en: 'Report' },
  select_report: { zh: '请选择一份报告查看', en: 'Select a report to view' },
  
  // Overview
  overview_title: { zh: '项目总览', en: 'PROJECT OVERVIEW' },
  features: { zh: '功能模块', en: 'Features' },
  data_coverage: { zh: '数据覆盖', en: 'Data Coverage' },
  quick_start: { zh: '快速开始', en: 'Quick Start' }
}

export function useLocale() {
  const isZh = computed(() => locale.value === 'zh')
  
  const t = (key) => {
    return translations[key]?.[locale.value] || key
  }
  
  const toggleLocale = () => {
    locale.value = locale.value === 'zh' ? 'en' : 'zh'
    localStorage.setItem('locale', locale.value)
  }
  
  const setLocale = (lang) => {
    locale.value = lang
    localStorage.setItem('locale', lang)
  }
  
  return {
    locale,
    isZh,
    t,
    toggleLocale,
    setLocale
  }
}
