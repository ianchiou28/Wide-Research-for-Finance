<template>
  <div class="dashboard-container">
    <!-- Header -->
    <header class="dashboard-header">
      <div class="header-left">
        <div class="brand-logo">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </div>
        <div class="brand-text">
          <span class="brand-title">{{ t('brand_title') }}</span>
          <span class="brand-subtitle">{{ t('brand_subtitle') }}</span>
        </div>
      </div>
      <div class="header-right">
        <div class="sys-status">
          <span class="status-dot"></span>
          {{ t('system_online') }}
        </div>
        <div class="sys-time">{{ currentTime }}</div>
      </div>
    </header>

    <!-- KPI Bar -->
    <div class="kpi-bar">
      <div class="kpi-item">
        <div class="kpi-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10 9 9 9 8 9"></polyline>
          </svg>
        </div>
        <div class="kpi-content">
          <div class="kpi-label">{{ t('total_news') }}</div>
          <div class="kpi-value">{{ reportData.meta?.total_news || 0 }}</div>
        </div>
      </div>
      
      <div class="kpi-item">
        <div class="kpi-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>
        </div>
        <div class="kpi-content">
          <div class="kpi-label">{{ t('market_sentiment_kpi') }}</div>
          <div class="kpi-value" :class="getSentimentClass(reportData.sentiment?.overall?.score)">
            {{ getSentimentLabel(reportData.sentiment?.overall?.score) }}
          </div>
        </div>
      </div>

      <div class="kpi-item">
        <div class="kpi-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="4" y1="9" x2="20" y2="9"></line>
            <line x1="4" y1="15" x2="20" y2="15"></line>
            <line x1="10" y1="3" x2="8" y2="21"></line>
            <line x1="16" y1="3" x2="14" y2="21"></line>
          </svg>
        </div>
        <div class="kpi-content">
          <div class="kpi-label">{{ t('hot_topics_kpi') }}</div>
          <div class="kpi-value">{{ reportData.entities?.length || 0 }}</div>
        </div>
      </div>

      <div class="kpi-item">
        <div class="kpi-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
        </div>
        <div class="kpi-content">
          <div class="kpi-label">{{ t('updated_at') }}</div>
          <div class="kpi-value">{{ formatTime(reportData.meta?.generated_at) }}</div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <span>{{ t('loading') }}</span>
    </div>

    <!-- Main Grid -->
    <div v-else class="main-grid">
      
      <!-- Left Column -->
      <div class="col-main">
        
        <!-- Sentiment Dashboard -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px; vertical-align: text-bottom;">
                <line x1="18" y1="20" x2="18" y2="10"></line>
                <line x1="12" y1="20" x2="12" y2="4"></line>
                <line x1="6" y1="20" x2="6" y2="14"></line>
              </svg>
              {{ t('market_sentiment') }}
            </div>
            <button class="refresh-btn" @click="fetchData">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M23 4v6h-6"></path>
                <path d="M1 20v-6h6"></path>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
              </svg>
            </button>
          </div>
          <div class="panel-body">
            <!-- Sentiment Bars -->
            <div class="sentiment-grid">
              <div class="sentiment-card" v-for="market in sentimentMarkets" :key="market.key">
                <div class="sent-header">
                  <span class="sent-name">{{ market.name }}</span>
                </div>
                <div class="sent-score" :class="getSentimentClass(market.score)">
                  {{ market.score > 0 ? '+' : '' }}{{ market.score?.toFixed(2) || '0.00' }}
                </div>
                <div class="sent-label">{{ market.label }}</div>
                <div class="sent-bar-container">
                  <div class="sent-bar" :style="getBarStyle(market.score)"></div>
                  <div class="sent-marker"></div>
                </div>
              </div>
            </div>
            
            <!-- Distribution -->
            <div class="distribution-row">
              <div class="dist-item positive">
                <div class="dist-value">{{ reportData.sentiment?.distribution?.positive || 0 }}</div>
                <div class="dist-label">{{ t('positive') }}</div>
              </div>
              <div class="dist-item neutral">
                <div class="dist-value">{{ reportData.sentiment?.distribution?.neutral || 0 }}</div>
                <div class="dist-label">{{ t('neutral') }}</div>
              </div>
              <div class="dist-item negative">
                <div class="dist-value">{{ reportData.sentiment?.distribution?.negative || 0 }}</div>
                <div class="dist-label">{{ t('negative') }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- High Impact Events -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px; vertical-align: text-bottom;">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
              </svg>
              {{ t('key_events') }}
            </div>
            <div class="panel-tag">{{ reportData.events?.high_impact?.length || 0 }} {{ t('unit_items') }}</div>
          </div>
          <div class="panel-body">
            <div v-if="!reportData.events?.high_impact?.length" class="empty-state">
              {{ t('empty_events') }}
            </div>
            <div v-else class="event-list">
              <div v-for="event in reportData.events.high_impact" :key="event.ref_id" class="event-card">
                <div class="event-meta">
                  <span class="event-source">{{ event.source }}</span>
                  <span class="event-type">{{ event.event_type }}</span>
                </div>
                <div class="event-title">{{ event.title }}</div>
                <div class="event-summary">{{ event.summary }}</div>
                <div class="event-stocks" v-if="event.stock_impact?.length">
                  <span v-for="stock in event.stock_impact" :key="stock.symbol" 
                        class="stock-tag" :class="getDirectionClass(stock.direction)">
                    {{ stock.symbol }} {{ getDirectionIcon(stock.direction) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Stock Impacts -->
        <div class="panel" v-if="reportData.stock_impacts?.length">
          <div class="panel-header">
            <div class="panel-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px; vertical-align: text-bottom;">
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
                <polyline points="17 6 23 6 23 12"></polyline>
              </svg>
              {{ t('stock_prediction') }}
            </div>
          </div>
          <div class="panel-body">
            <div class="stock-grid">
              <div v-for="stock in reportData.stock_impacts" :key="stock.symbol" class="stock-card">
                <div class="stock-header">
                  <span class="stock-symbol">{{ stock.symbol }}</span>
                  <span class="stock-prediction" :class="getPredictionClass(stock.prediction)">
                    {{ getPredictionIcon(stock.prediction) }} {{ stock.prediction }}
                  </span>
                </div>
                <div class="stock-name">{{ stock.name }}</div>
                <div class="confidence-bar">
                  <div class="confidence-label">{{ t('confidence') }} {{ Math.round(stock.confidence * 100) }}%</div>
                  <div class="confidence-track">
                    <div class="confidence-fill" :style="{ width: (stock.confidence * 100) + '%' }" 
                         :class="getPredictionClass(stock.prediction)"></div>
                  </div>
                </div>
                <div class="stock-stats">
                  {{ t('mentions') }} {{ stock.total_mentions }} {{ t('times') }} | 
                  <span class="text-green">↑{{ stock.up_count }}</span> 
                  <span class="text-red">↓{{ stock.down_count }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- Right Column -->
      <div class="col-side">
        
        <!-- Hot Entities -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px; vertical-align: text-bottom;">
                <line x1="8" y1="6" x2="21" y2="6"></line>
                <line x1="8" y1="12" x2="21" y2="12"></line>
                <line x1="8" y1="18" x2="21" y2="18"></line>
                <line x1="3" y1="6" x2="3.01" y2="6"></line>
                <line x1="3" y1="12" x2="3.01" y2="12"></line>
                <line x1="3" y1="18" x2="3.01" y2="18"></line>
              </svg>
              {{ t('hot_topics') }}
            </div>
          </div>
          <div class="panel-body">
            <div v-if="!reportData.entities?.length" class="empty-state">{{ t('empty_topics') }}</div>
            <div v-else class="entity-list">
              <div v-for="(entity, index) in reportData.entities" :key="entity.name" class="entity-item">
                <span class="entity-rank" :class="{ 'top-3': index < 3 }">{{ index + 1 }}</span>
                <span class="entity-name">{{ entity.name }}</span>
                <span class="entity-count">×{{ entity.count }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Market Prediction -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px; vertical-align: text-bottom;">
                <circle cx="12" cy="12" r="10"></circle>
                <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon>
              </svg>
              {{ t('market_outlook') }}
            </div>
          </div>
          <div class="panel-body">
            <div v-for="market in marketPredictions" :key="market.name" class="pred-row">
              <span class="pred-name">{{ market.name }}</span>
              <span class="pred-trend" :class="getTrendClass(market.trendType)">
                {{ market.trendIcon }} {{ market.trend }}
              </span>
            </div>
          </div>
        </div>

        <!-- Quick Stats -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px; vertical-align: text-bottom;">
                <line x1="4" y1="21" x2="4" y2="14"></line>
                <line x1="4" y1="10" x2="4" y2="3"></line>
                <line x1="12" y1="21" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12" y2="3"></line>
                <line x1="20" y1="21" x2="20" y2="16"></line>
                <line x1="20" y1="12" x2="20" y2="3"></line>
                <line x1="1" y1="14" x2="7" y2="14"></line>
                <line x1="9" y1="8" x2="15" y2="8"></line>
                <line x1="17" y1="16" x2="23" y2="16"></line>
              </svg>
              {{ t('statistics') }}
            </div>
          </div>
          <div class="panel-body">
            <div class="stat-row">
              <span class="stat-label">{{ t('beijing_time') }}</span>
              <span class="stat-value">{{ reportData.meta?.beijing_time || '--:--' }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">{{ t('newyork_time') }}</span>
              <span class="stat-value">{{ reportData.meta?.newyork_time || '--:--' }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">{{ t('event_count') }}</span>
              <span class="stat-value">{{ reportData.events?.high_impact?.length || 0 }} {{ t('unit_items') }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">{{ t('stock_signal_count') }}</span>
              <span class="stat-value">{{ reportData.stock_impacts?.length || 0 }} {{ t('unit_count') }}</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>


<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useLocale } from '../composables/useLocale'

const { locale, t } = useLocale()

const loading = ref(true)
const currentTime = ref('00:00:00')

const reportData = ref({
  meta: {},
  sentiment: {},
  entities: [],
  events: {},
  stock_impacts: []
})

// Helper for sentiment label
const getSentimentLabel = (score) => {
  if (score > 0.1) return t('positive')
  if (score < -0.1) return t('negative')
  return t('neutral')
}

// Computed: Sentiment Markets
const sentimentMarkets = computed(() => {
  const s = reportData.value.sentiment || {}
  return [
    { key: 'overall', name: t('market_global'), score: s.overall?.score || 0, label: getSentimentLabel(s.overall?.score || 0) },
    { key: 'cn', name: t('market_cn'), score: s.cn?.score || 0, label: getSentimentLabel(s.cn?.score || 0) },
    { key: 'us', name: t('market_us'), score: s.us?.score || 0, label: getSentimentLabel(s.us?.score || 0) }
  ]
})

// Computed: Market Predictions
const marketPredictions = computed(() => {
  const s = reportData.value.sentiment || {}
  
  const getPrediction = (score) => {
    if (score > 0.3) return { trend: t('trend_bullish'), trendType: 'bullish', trendIcon: '↑' }
    if (score < -0.3) return { trend: t('trend_bearish'), trendType: 'bearish', trendIcon: '↓' }
    return { trend: t('trend_sideways'), trendType: 'sideways', trendIcon: '→' }
  }
  
  return [
    { name: t('market_a_share'), ...getPrediction(s.cn?.score || 0) },
    { name: t('market_us_stock'), ...getPrediction(s.us?.score || 0) },
    { name: t('market_global_short'), ...getPrediction(s.overall?.score || 0) }
  ]
})

// Helper Functions
const getSentimentClass = (score) => {
  if (score > 0.1) return 'positive'
  if (score < -0.1) return 'negative'
  return 'neutral'
}

const getBarStyle = (score) => {
  const val = score || 0
  const width = Math.min(Math.abs(val) * 50, 50)
  const color = val > 0.1 ? '#4CAF50' : val < -0.1 ? '#F44336' : '#FF9800'
  return {
    width: `${width}%`,
    background: color,
    [val >= 0 ? 'left' : 'right']: '50%'
  }
}

const getDirectionClass = (direction) => {
  if (direction === '上涨') return 'up'
  if (direction === '下跌') return 'down'
  return 'flat'
}

const getDirectionIcon = (direction) => {
  if (direction === '上涨') return '↑'
  if (direction === '下跌') return '↓'
  return '→'
}

const getPredictionClass = (prediction) => {
  if (prediction === '看涨') return 'positive'
  if (prediction === '看跌') return 'negative'
  return 'neutral'
}

const getPredictionIcon = (prediction) => {
  if (prediction === '看涨') return '↑'
  if (prediction === '看跌') return '↓'
  return '→'
}

const getTrendClass = (trendType) => {
  if (trendType === 'bullish') return 'positive'
  if (trendType === 'bearish') return 'negative'
  return 'neutral'
}

const formatTime = (isoString) => {
  if (!isoString) return '--:--'
  try {
    const date = new Date(isoString)
    const loc = locale.value === 'zh' ? 'zh-CN' : 'en-US'
    return date.toLocaleTimeString(loc, { hour: '2-digit', minute: '2-digit' })
  } catch {
    return '--:--'
  }
}

// Fetch Data
const fetchData = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/report/structured')
    if (res.data) {
      reportData.value = res.data
    }
  } catch (error) {
    console.error('Error fetching data:', error)
  } finally {
    loading.value = false
  }
}

// Clock
let clockTimer
const updateClock = () => {
  currentTime.value = new Date().toLocaleTimeString('en-GB', { hour12: false })
}

onMounted(() => {
  fetchData()
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
})

onUnmounted(() => {
  clearInterval(clockTimer)
})
</script>

<style scoped>
.dashboard-container {
  max-width: 1800px;
  margin: 0 auto;
  padding: 1rem 2rem;
}

/* Header */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  border-bottom: 2px solid var(--c-ink);
  padding-bottom: 1rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.brand-logo {
  background: var(--c-ink);
  color: var(--c-bg);
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-text {
  display: flex;
  flex-direction: column;
}

.brand-title {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1;
}

.brand-subtitle {
  font-size: 0.7rem;
  letter-spacing: 0.2em;
  color: var(--c-amber);
  font-weight: 700;
}

.header-right {
  text-align: right;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.sys-status {
  font-size: 0.7rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
  color: #4CAF50;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #4CAF50;
  border-radius: 50%;
  box-shadow: 0 0 5px #4CAF50;
}

.sys-time {
  font-family: var(--font-mono);
  font-size: 1.2rem;
  font-weight: 700;
}

/* KPI Bar */
.kpi-bar {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.kpi-item {
  background: var(--c-paper);
  border: 2px solid var(--c-ink);
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 4px 4px 0 rgba(0,0,0,0.1);
}

.kpi-icon {
  font-size: 2rem;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.kpi-content {
  flex: 1;
}

.kpi-label {
  font-size: 0.7rem;
  font-weight: 700;
  color: #888;
  letter-spacing: 0.05em;
}

.kpi-value {
  font-family: var(--font-mono);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--c-ink);
}

.kpi-value.positive { color: #4CAF50; }
.kpi-value.negative { color: #F44336; }
.kpi-value.neutral { color: #FF9800; }

/* Loading */
.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  gap: 1rem;
  color: var(--c-muted);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--c-grid);
  border-top-color: var(--c-amber);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Main Grid */
.main-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
}

.col-main, .col-side {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Panel */
.panel {
  background: var(--c-paper);
  border: 2px solid var(--c-border);
  box-shadow: 4px 4px 0 var(--c-shadow);
}

.panel-header {
  background: var(--c-hover);
  border-bottom: 1px solid var(--c-border);
  padding: 0.75rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 1rem;
}

.panel-tag {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  background: var(--c-ink);
  color: var(--c-bg);
  padding: 0.2rem 0.5rem;
}

.panel-body {
  padding: 1.5rem;
}

.refresh-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--c-muted);
  padding: 0.25rem;
}

.refresh-btn:hover {
  color: var(--c-ink);
}

/* Sentiment Grid */
.sentiment-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.sentiment-card {
  background: var(--c-hover);
  padding: 1rem;
  text-align: center;
  border: 1px solid var(--c-grid);
}

.sent-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.sent-icon {
  font-size: 1.2rem;
}

.sent-name {
  font-size: 0.85rem;
  font-weight: 600;
}

.sent-score {
  font-family: var(--font-mono);
  font-size: 2rem;
  font-weight: 700;
}

.sent-score.positive { color: #4CAF50; }
.sent-score.negative { color: #F44336; }
.sent-score.neutral { color: #FF9800; }

.sent-label {
  font-size: 0.75rem;
  color: var(--c-muted);
  margin-bottom: 0.75rem;
}

.sent-bar-container {
  height: 8px;
  background: var(--c-grid);
  position: relative;
  border-radius: 4px;
  overflow: hidden;
}

.sent-bar {
  position: absolute;
  height: 100%;
  transition: width 0.5s ease;
}

.sent-marker {
  position: absolute;
  left: 50%;
  top: 0;
  width: 2px;
  height: 100%;
  background: var(--c-ink);
  opacity: 0.3;
}

/* Distribution */
.distribution-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  background: var(--c-hover);
  padding: 1rem;
  border-radius: 4px;
  border: 1px solid var(--c-grid);
}

.dist-item {
  text-align: center;
}

.dist-value {
  font-family: var(--font-mono);
  font-size: 1.5rem;
  font-weight: 700;
}

.dist-item.positive .dist-value { color: #4CAF50; }
.dist-item.negative .dist-value { color: #F44336; }
.dist-item.neutral .dist-value { color: #FF9800; }

.dist-label {
  font-size: 0.75rem;
  color: var(--c-muted);
}

/* Event List */
.event-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.event-card {
  padding: 1rem;
  border: 1px solid var(--c-grid);
  background: var(--c-hover);
}

.event-meta {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.event-source {
  background: var(--c-ink);
  color: var(--c-bg);
  padding: 0.1rem 0.4rem;
  font-size: 0.7rem;
  font-weight: 700;
}

.event-type {
  background: var(--c-amber);
  color: var(--c-bg);
  padding: 0.1rem 0.4rem;
  font-size: 0.7rem;
  font-weight: 700;
}

.event-title {
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.event-summary {
  font-size: 0.9rem;
  color: var(--c-muted);
  line-height: 1.5;
}

.event-stocks {
  margin-top: 0.75rem;
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.stock-tag {
  padding: 0.2rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 700;
  border-radius: 2px;
}

.stock-tag.up { background: rgba(76, 175, 80, 0.15); color: #4CAF50; }
.stock-tag.down { background: rgba(244, 67, 54, 0.15); color: #F44336; }
.stock-tag.flat { background: var(--c-hover); color: var(--c-muted); }

/* Stock Grid */
.stock-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.stock-card {
  background: var(--c-hover);
  padding: 1rem;
  border-radius: 4px;
  border: 1px solid var(--c-grid);
}

.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stock-symbol {
  font-family: var(--font-mono);
  font-weight: 700;
}

.stock-prediction {
  font-size: 0.85rem;
  font-weight: 700;
}

.stock-prediction.positive { color: #4CAF50; }
.stock-prediction.negative { color: #F44336; }
.stock-prediction.neutral { color: #FF9800; }

.stock-name {
  font-size: 0.8rem;
  color: var(--c-muted);
  margin: 0.25rem 0 0.75rem;
}

.confidence-bar {
  margin-bottom: 0.5rem;
}

.confidence-label {
  font-size: 0.7rem;
  color: var(--c-muted);
  margin-bottom: 0.25rem;
}

.confidence-track {
  height: 4px;
  background: var(--c-grid);
  border-radius: 2px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  border-radius: 2px;
}

.confidence-fill.positive { background: #4CAF50; }
.confidence-fill.negative { background: #F44336; }
.confidence-fill.neutral { background: #FF9800; }

.stock-stats {
  font-size: 0.75rem;
  color: var(--c-muted);
}

.text-green { color: #4CAF50; }
.text-red { color: #F44336; }

/* Entity List */
.entity-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.entity-item {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  background: var(--c-hover);
  border: 1px solid var(--c-grid);
}

.entity-rank {
  width: 24px;
  font-family: var(--font-display);
  font-weight: 700;
  color: var(--c-grid);
  font-style: italic;
}

.entity-rank.top-3 { color: var(--c-amber); }

.entity-name {
  flex: 1;
  font-weight: 500;
}

.entity-count {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: var(--c-muted);
}

/* Prediction Row */
.pred-row {
  display: flex;
  align-items: center;
  padding: 0.75rem 0;
  border-bottom: 1px dashed var(--c-grid);
}

.pred-icon {
  font-size: 1.2rem;
  margin-right: 0.75rem;
}

.pred-name {
  flex: 1;
  font-weight: 600;
}

.pred-trend {
  font-family: var(--font-mono);
  font-weight: 700;
}

.pred-trend.positive { color: #4CAF50; }
.pred-trend.negative { color: #F44336; }
.pred-trend.neutral { color: #FF9800; }

/* Stat Row */
.stat-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--c-grid);
}

.stat-label {
  color: var(--c-muted);
  font-size: 0.85rem;
}

.stat-value {
  font-family: var(--font-mono);
  font-weight: 700;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--c-muted);
}

/* Responsive */
@media (max-width: 1200px) {
  .main-grid { grid-template-columns: 1fr; }
  .kpi-bar { grid-template-columns: repeat(2, 1fr); }
  .sentiment-grid { grid-template-columns: 1fr; }
  .stock-grid { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 0;
  }

  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .header-right {
    width: 100%;
    justify-content: space-between;
  }

  .sys-time {
    font-size: 1rem;
  }

  .kpi-bar { grid-template-columns: 1fr; }
  .distribution-row { grid-template-columns: 1fr; }
}
</style>