
import os

content = r"""<template>
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
          <span class="brand-title">FINANCE TERMINAL</span>
          <span class="brand-subtitle">DEEPSEEK INTELLIGENCE</span>
        </div>
      </div>
      <div class="header-right">
        <div class="sys-status">
          <span class="status-dot"></span>
          SYSTEM ONLINE
        </div>
        <div class="sys-time">{{ lastUpdateTime }}</div>
      </div>
    </header>

    <!-- KPI Bar -->
    <div class="kpi-bar">
      <div class="kpi-item">
        <div class="kpi-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10 9 9 9 8 9"></polyline>
          </svg>
        </div>
        <div class="kpi-content">
          <div class="kpi-label">PROCESSED NEWS</div>
          <div class="kpi-value">{{ stats.total_news }}</div>
        </div>
      </div>
      
      <div class="kpi-item">
        <div class="kpi-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="22" y1="12" x2="18" y2="12"></line>
            <line x1="6" y1="12" x2="2" y2="12"></line>
            <line x1="12" y1="6" x2="12" y2="2"></line>
            <line x1="12" y1="22" x2="12" y2="18"></line>
          </svg>
        </div>
        <div class="kpi-content">
          <div class="kpi-label">HOT TOPICS</div>
          <div class="kpi-value">{{ hotTopics.length }}</div>
        </div>
      </div>

      <div class="kpi-item">
        <div class="kpi-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
            <polyline points="17 6 23 6 23 12"></polyline>
          </svg>
        </div>
        <div class="kpi-content">
          <div class="kpi-label">POSITIVE EVENTS</div>
          <div class="kpi-value">{{ stats.positive_news }}</div>
        </div>
      </div>

      <div class="kpi-item">
        <div class="kpi-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
          </svg>
        </div>
        <div class="kpi-content">
          <div class="kpi-label">UPTIME</div>
          <div class="kpi-value">{{ runDuration }}</div>
        </div>
      </div>
    </div>

    <!-- Main Grid -->
    <div class="main-grid">
      
      <!-- Left Column: Intelligence & Reports -->
      <div class="col-main">
        
        <!-- Market Intelligence Panel -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">MARKET INTELLIGENCE</div>
            <div class="panel-meta">CONFIDENCE: 0.92</div>
          </div>
          <div class="panel-body sentiment-dashboard">
            <!-- Global Sentiment Bar -->
            <div class="sentiment-row">
              <div class="sent-label">GLOBAL MARKET</div>
              <div class="sent-bar-container">
                <div class="sent-bar" :style="{ width: Math.abs(sentiment.score * 100) + '%', background: getSentimentColor(sentiment.score) }"></div>
                <div class="sent-marker"></div>
              </div>
              <div class="sent-value" :style="{ color: getSentimentColor(sentiment.score) }">
                {{ sentiment.score > 0 ? '+' : '' }}{{ sentiment.score }}
              </div>
            </div>

            <!-- CN Sentiment Bar -->
            <div class="sentiment-row">
              <div class="sent-label">CN MARKET</div>
              <div class="sent-bar-container">
                <div class="sent-bar" :style="{ width: Math.abs(sentiment.breakdown?.cn * 100) + '%', background: getSentimentColor(sentiment.breakdown?.cn) }"></div>
                <div class="sent-marker"></div>
              </div>
              <div class="sent-value" :style="{ color: getSentimentColor(sentiment.breakdown?.cn) }">
                {{ sentiment.breakdown?.cn > 0 ? '+' : '' }}{{ sentiment.breakdown?.cn || '0.00' }}
              </div>
            </div>

            <!-- US Sentiment Bar -->
            <div class="sentiment-row">
              <div class="sent-label">US MARKET</div>
              <div class="sent-bar-container">
                <div class="sent-bar" :style="{ width: Math.abs(sentiment.breakdown?.us * 100) + '%', background: getSentimentColor(sentiment.breakdown?.us) }"></div>
                <div class="sent-marker"></div>
              </div>
              <div class="sent-value" :style="{ color: getSentimentColor(sentiment.breakdown?.us) }">
                {{ sentiment.breakdown?.us > 0 ? '+' : '' }}{{ sentiment.breakdown?.us || '0.00' }}
              </div>
            </div>
          </div>
        </div>

        <!-- Tabbed Reports Panel -->
        <div class="panel report-panel">
          <div class="panel-tabs">
            <button 
              class="tab-btn" 
              :class="{ active: activeTab === 'hourly' }"
              @click="activeTab = 'hourly'"
            >
              HOURLY BRIEFING
            </button>
            <button 
              class="tab-btn" 
              :class="{ active: activeTab === 'daily' }"
              @click="activeTab = 'daily'"
            >
              DAILY SUMMARY
            </button>
            <button 
              class="tab-btn" 
              :class="{ active: activeTab === 'weekly' }"
              @click="activeTab = 'weekly'"
            >
              WEEKLY ANALYSIS
            </button>
            <div class="tab-spacer"></div>
            <button class="refresh-btn" @click="fetchData">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M23 4v6h-6"></path>
                <path d="M1 20v-6h6"></path>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
              </svg>
              REFRESH
            </button>
          </div>
          
          <div class="panel-body report-content">
            <div v-if="loading" class="loading-state">
              <div class="spinner"></div>
              <span>ACQUIRING DATA...</span>
            </div>
            
            <div v-else-if="activeTab === 'hourly'" class="report-text" v-html="formatReport(report)"></div>
            <div v-else-if="activeTab === 'daily'" class="report-text" v-html="formatReport(dailySummary)"></div>
            <div v-else-if="activeTab === 'weekly'" class="report-text">
              <div v-if="weeklyAnalysis && weeklyAnalysis.summary" v-html="formatReport(weeklyAnalysis.summary)"></div>
              <div v-else class="empty-state">NO WEEKLY DATA AVAILABLE</div>
            </div>
          </div>
        </div>

      </div>

      <!-- Right Column: Strategy & Trends -->
      <div class="col-side">
        
        <!-- Strategy Stream -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">STRATEGY STREAM</div>
            <div class="panel-tag">LIVE</div>
          </div>
          <div class="panel-body">
            <div class="market-group">
              <div class="group-label">CN A-SHARES</div>
              <div v-if="recommendations.a_shares.length === 0" class="empty-text">NO SIGNALS</div>
              <div v-else class="stock-list">
                <div v-for="stock in recommendations.a_shares" :key="stock.symbol" class="stock-row">
                  <span class="stock-code">{{ stock.symbol }}</span>
                  <span class="stock-name">{{ stock.name }}</span>
                  <span class="stock-action up">BUY</span>
                </div>
              </div>
            </div>
            
            <div class="market-group">
              <div class="group-label">US MARKETS</div>
              <div v-if="recommendations.us_shares.length === 0" class="empty-text">NO SIGNALS</div>
              <div v-else class="stock-list">
                <div v-for="stock in recommendations.us_shares" :key="stock.symbol" class="stock-row">
                  <span class="stock-code">{{ stock.symbol }}</span>
                  <span class="stock-name">{{ stock.name }}</span>
                  <span class="stock-action up">BUY</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Hot Topics -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">HOT TOPICS</div>
          </div>
          <div class="panel-body">
            <div class="tag-cloud">
              <span v-for="(topic, index) in hotTopics" :key="index" class="tag">
                {{ topic }}
              </span>
            </div>
          </div>
        </div>

        <!-- Predictions -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">PREDICTIONS</div>
          </div>
          <div class="panel-body">
            <div v-for="market in marketPrediction" :key="market.name" class="pred-row">
              <div class="pred-name">{{ market.name }}</div>
              <div class="pred-trend">{{ market.trend }}</div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>


<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const loading = ref(true)
const activeTab = ref('hourly')
const report = ref(null)
const dailySummary = ref(null)
const weeklyAnalysis = ref(null)
const lastUpdateTime = ref('--:--:--')
const runDuration = ref('00:00:00')

const stats = ref({
  total_news: 0,
  positive_news: 0,
  negative_news: 0
})

const sentiment = ref({
  label: 'Neutral',
  score: 0,
  breakdown: { cn: 0, us: 0 }
})

const hotTopics = ref([])
const recommendations = ref({ a_shares: [], us_shares: [] })
const marketPrediction = ref([])

const getSentimentColor = (score) => {
  if (score > 0.1) return '#4CAF50' // Green
  if (score < -0.1) return '#F44336' // Red
  return '#FF9800' // Orange/Neutral
}

const formatReport = (text) => {
  if (!text) return ''
  // Remove markdown-style headers and clean up
  let formatted = text
    .replace(/={3,}/g, '') // Remove separator lines
    .replace(/【(.*?)】/g, '<h4 class="report-section-title">$1</h4>') // Format section headers
  
  return formatted.split('\n').map(line => {
    if (line.trim().startsWith('-') || line.trim().startsWith('•')) {
      return `<div class="report-list-item"><span class="bullet">›</span> ${line.substring(1)}</div>`
    }
    if (line.trim().length === 0) return '<div class="spacer"></div>'
    return `<div class="report-p">${line}</div>`
  }).join('')
}

const fetchData = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/latest')
    if (response.data) {
      report.value = response.data.content
      if (response.data.stats) stats.value = response.data.stats
      if (response.data.sentiment) sentiment.value = response.data.sentiment
      if (response.data.hot_topics) hotTopics.value = response.data.hot_topics
      if (response.data.recommendations) recommendations.value = response.data.recommendations
      if (response.data.market_prediction) marketPrediction.value = response.data.market_prediction
      lastUpdateTime.value = response.data.timestamp || new Date().toLocaleTimeString()
    }

    const dailyRes = await axios.get('/api/daily_summary')
    if (dailyRes.data && dailyRes.data.content) {
      dailySummary.value = dailyRes.data.content
    }

    const weeklyRes = await axios.get('/api/weekly_analysis')
    if (weeklyRes.data) {
      weeklyAnalysis.value = weeklyRes.data
    }

  } catch (error) {
    console.error('Error fetching data:', error)
  } finally {
    loading.value = false
  }
}

let timer
onMounted(() => {
  fetchData()
  timer = setInterval(fetchData, 300000)
})

onUnmounted(() => {
  clearInterval(timer)
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
  border: 1px solid var(--c-grid);
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 2px 2px 0 rgba(0,0,0,0.05);
}

.kpi-icon {
  background: rgba(0,0,0,0.03);
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-ink);
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

/* Main Grid */
.main-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
}

.col-main {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.col-side {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Panels */
.panel {
  background: var(--c-paper);
  border: 2px solid var(--c-ink);
  box-shadow: 4px 4px 0 rgba(0,0,0,0.1);
}

.panel-header {
  background: rgba(0,0,0,0.02);
  border-bottom: 1px solid var(--c-ink);
  padding: 0.75rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 1.1rem;
  letter-spacing: 0.05em;
}

.panel-meta, .panel-tag {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  background: var(--c-ink);
  color: var(--c-bg);
  padding: 0.1rem 0.4rem;
}

.panel-body {
  padding: 1.5rem;
}

/* Sentiment Dashboard */
.sentiment-dashboard {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.sentiment-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.sent-label {
  width: 120px;
  font-size: 0.8rem;
  font-weight: 700;
}

.sent-bar-container {
  flex: 1;
  height: 24px;
  background: rgba(0,0,0,0.05);
  position: relative;
  display: flex;
  align-items: center;
}

.sent-bar {
  height: 100%;
  transition: width 0.5s ease;
}

.sent-marker {
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--c-ink);
  opacity: 0.3;
}

.sent-value {
  width: 60px;
  text-align: right;
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 1.1rem;
}

/* Tabs */
.panel-tabs {
  display: flex;
  border-bottom: 1px solid var(--c-ink);
  background: rgba(0,0,0,0.02);
}

.tab-btn {
  background: none;
  border: none;
  border-right: 1px solid var(--c-ink);
  padding: 1rem 1.5rem;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 0.9rem;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: rgba(0,0,0,0.05);
  color: var(--c-ink);
}

.tab-btn.active {
  background: var(--c-paper);
  color: var(--c-amber);
  border-bottom: 2px solid var(--c-paper); /* Hide bottom border */
  margin-bottom: -1px;
}

.tab-spacer {
  flex: 1;
}

.refresh-btn {
  background: none;
  border: none;
  padding: 0 1.5rem;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #666;
}

.refresh-btn:hover {
  color: var(--c-ink);
}

/* Report Content */
.report-content {
  min-height: 400px;
  max-height: 600px;
  overflow-y: auto;
}

.report-text :deep(.report-section-title) {
  font-family: var(--font-display);
  font-size: 1.1rem;
  margin: 1.5rem 0 1rem 0;
  border-left: 4px solid var(--c-amber);
  padding-left: 0.75rem;
  color: var(--c-ink);
}

.report-text :deep(.report-list-item) {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  line-height: 1.5;
}

.report-text :deep(.bullet) {
  color: var(--c-amber);
  font-weight: 700;
}

.report-text :deep(.report-p) {
  margin-bottom: 0.75rem;
  line-height: 1.6;
}

.report-text :deep(.spacer) {
  height: 1rem;
}

/* Side Panel Items */
.market-group {
  margin-bottom: 2rem;
}

.group-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: #888;
  margin-bottom: 0.75rem;
  border-bottom: 1px dashed var(--c-grid);
  padding-bottom: 0.25rem;
}

.stock-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(0,0,0,0.05);
}

.stock-code {
  font-family: var(--font-mono);
  font-weight: 700;
  background: var(--c-ink);
  color: var(--c-bg);
  padding: 0.1rem 0.3rem;
  font-size: 0.8rem;
}

.stock-name {
  font-size: 0.9rem;
  flex: 1;
  margin-left: 0.75rem;
}

.stock-action {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.1rem 0.4rem;
  border-radius: 2px;
}

.stock-action.up {
  background: rgba(76, 175, 80, 0.1);
  color: #4CAF50;
}

.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag {
  border: 1px solid var(--c-ink);
  padding: 0.2rem 0.6rem;
  font-size: 0.75rem;
  font-weight: 700;
  background: white;
  box-shadow: 2px 2px 0 rgba(0,0,0,0.1);
}

.pred-row {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px dashed var(--c-grid);
}

.pred-name {
  font-weight: 700;
}

.pred-trend {
  font-family: var(--font-mono);
  color: var(--c-amber);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #888;
  gap: 1rem;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(0,0,0,0.1);
  border-top-color: var(--c-amber);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 1200px) {
  .main-grid { grid-template-columns: 1fr; }
  .kpi-bar { grid-template-columns: 1fr 1fr; }
}

@media (max-width: 768px) {
  .kpi-bar { grid-template-columns: 1fr; }
  .dashboard-header { flex-direction: column; align-items: flex-start; gap: 1rem; }
  .header-right { text-align: left; }
}
</style>
"""

with open(r"d:\GitHub\Wide-Research-for-Finance\frontend\src\views\Home.vue", "w", encoding="utf-8") as f:
    f.write(content)
