<template>
  <div class="daily-summary-page">
    <!-- Header -->
    <header class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
        </div>
        <div class="header-text">
          <span class="page-title">{{ t('daily_summary_title') }}</span>
          <span class="page-subtitle">DAILY MARKET RECAP</span>
        </div>
      </div>
      <div class="header-actions">
        <select v-model="selectedFile" class="file-selector" @change="loadSummary">
          <option v-for="file in summaryFiles" :key="file" :value="file">
            {{ formatFileName(file) }}
          </option>
        </select>
        <button class="refresh-btn" @click="refreshData" :disabled="loading">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6"></path>
            <path d="M1 20v-6h6"></path>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
          </svg>
        </button>
      </div>
    </header>

    <!-- Loading State -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <span>{{ t('loading') }}</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <p class="error-text">{{ error }}</p>
      <button class="retry-btn" @click="refreshData">{{ t('retry') }}</button>
    </div>

    <!-- Content -->
    <div v-else-if="summaryData" class="summary-content">
      <!-- KPI Bar -->
      <div class="kpi-bar">
        <div class="kpi-item">
          <div class="kpi-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
            </svg>
          </div>
          <div class="kpi-content">
            <div class="kpi-label">{{ t('report_count') }}</div>
            <div class="kpi-value">{{ summaryData.reportCount }}</div>
          </div>
        </div>
        <div class="kpi-item">
          <div class="kpi-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
            </svg>
          </div>
          <div class="kpi-content">
            <div class="kpi-label">{{ t('major_events') }}</div>
            <div class="kpi-value">{{ summaryData.majorEvents }}</div>
          </div>
        </div>
        <div class="kpi-item positive">
          <div class="kpi-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
              <polyline points="17 6 23 6 23 12"></polyline>
            </svg>
          </div>
          <div class="kpi-content">
            <div class="kpi-label">{{ t('positive_events') }}</div>
            <div class="kpi-value text-green">{{ summaryData.positiveCount }}</div>
          </div>
        </div>
        <div class="kpi-item negative">
          <div class="kpi-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline>
              <polyline points="17 18 23 18 23 12"></polyline>
            </svg>
          </div>
          <div class="kpi-content">
            <div class="kpi-label">{{ t('negative_events') }}</div>
            <div class="kpi-value text-red">{{ summaryData.negativeCount }}</div>
          </div>
        </div>
      </div>

      <!-- Main Grid -->
      <div class="main-grid">
        <!-- Left Column -->
        <div class="col-main">
          <!-- Sentiment Distribution -->
          <div class="panel">
            <div class="panel-header">
              <div class="panel-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 8px; vertical-align: text-bottom;">
                  <line x1="18" y1="20" x2="18" y2="10"></line>
                  <line x1="12" y1="20" x2="12" y2="4"></line>
                  <line x1="6" y1="20" x2="6" y2="14"></line>
                </svg>
                {{ t('sentiment_distribution') }}
              </div>
            </div>
            <div class="panel-body">
              <div class="sentiment-bar-wrapper">
                <div class="sentiment-bar">
                  <div class="bar-positive" :style="{ width: positivePercent + '%' }"></div>
                  <div class="bar-neutral" :style="{ width: neutralPercent + '%' }"></div>
                  <div class="bar-negative" :style="{ width: negativePercent + '%' }"></div>
                </div>
              </div>
              <div class="distribution-row">
                <div class="dist-item positive">
                  <div class="dist-value">{{ summaryData.positiveCount }}</div>
                  <div class="dist-label">{{ t('positive') }}</div>
                </div>
                <div class="dist-item neutral">
                  <div class="dist-value">{{ summaryData.neutralCount }}</div>
                  <div class="dist-label">{{ t('neutral') }}</div>
                </div>
                <div class="dist-item negative">
                  <div class="dist-value">{{ summaryData.negativeCount }}</div>
                  <div class="dist-label">{{ t('negative') }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Events List -->
          <div class="panel">
            <div class="panel-header">
              <div class="panel-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 8px; vertical-align: text-bottom;">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                </svg>
                {{ t('key_events_list') }}
              </div>
              <div class="panel-tag">{{ summaryData.events.length }} {{ t('unit_items') }}</div>
            </div>
            <div class="panel-body">
              <div v-if="summaryData.events.length === 0" class="empty-state">
                {{ t('no_events') }}
              </div>
              <div v-else class="event-list">
                <div v-for="(event, index) in summaryData.events" :key="index" class="event-card">
                  <div class="event-rank">#{{ index + 1 }}</div>
                  <div class="event-content">
                    <div class="event-meta">
                      <span class="event-source">{{ event.source }}</span>
                      <span class="event-type" :class="event.sentiment">{{ t(event.sentiment) }}</span>
                    </div>
                    <div class="event-title">{{ event.title }}</div>
                    <div class="event-summary">{{ event.summary }}</div>
                    <div class="event-impacts" v-if="event.chinaImpact || event.usImpact">
                      <span v-if="event.chinaImpact" class="impact-tag cn">CN {{ event.chinaImpact }}</span>
                      <span v-if="event.usImpact" class="impact-tag us">US {{ event.usImpact }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Suggestions -->
          <div v-if="summaryData.suggestions" class="panel">
            <div class="panel-header">
              <div class="panel-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 8px; vertical-align: text-bottom;">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="16" x2="12" y2="12"></line>
                  <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
                {{ t('operation_suggestions') }}
              </div>
            </div>
            <div class="panel-body">
              <pre class="suggestions-content">{{ summaryData.suggestions }}</pre>
            </div>
          </div>
        </div>

        <!-- Right Column -->
        <div class="col-side">
          <!-- Market Divergence -->
          <div class="panel">
            <div class="panel-header">
              <div class="panel-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 8px; vertical-align: text-bottom;">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="2" y1="12" x2="22" y2="12"></line>
                  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                </svg>
                {{ t('market_divergence') }}
              </div>
            </div>
            <div class="panel-body">
              <div class="market-item">
                <div class="market-header">
                  <span class="market-flag">CN</span>
                  <span class="market-name">{{ t('china_market') }}</span>
                </div>
                <div class="market-stats">
                  <span class="stat-positive">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                      <polyline points="18 15 12 9 6 15"></polyline>
                    </svg>
                    {{ summaryData.chinaPositive }}
                  </span>
                  <span class="stat-negative">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                      <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                    {{ summaryData.chinaNegative }}
                  </span>
                </div>
              </div>
              <div class="market-item">
                <div class="market-header">
                  <span class="market-flag us">US</span>
                  <span class="market-name">{{ t('us_market') }}</span>
                </div>
                <div class="market-stats">
                  <span class="stat-positive">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                      <polyline points="18 15 12 9 6 15"></polyline>
                    </svg>
                    {{ summaryData.usPositive }}
                  </span>
                  <span class="stat-negative">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                      <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                    {{ summaryData.usNegative }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Raw Report (Collapsible) -->
          <div class="panel">
            <div class="panel-header collapsible" @click="toggleRawReport">
              <div class="panel-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 8px; vertical-align: text-bottom;">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                </svg>
                {{ t('raw_report') }}
              </div>
              <svg :class="{ 'rotated': showRawReport }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </div>
            <div v-if="showRawReport" class="panel-body">
              <pre class="raw-content">{{ rawContent }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-container">
      <p>{{ t('no_summary_data') }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useLocale } from '../composables/useLocale'

const { t } = useLocale()

const loading = ref(false)
const error = ref(null)
const summaryFiles = ref([])
const selectedFile = ref('')
const rawContent = ref('')
const showRawReport = ref(false)
const summaryData = ref(null)

// Computed percentages for sentiment bar
const totalSentiment = computed(() => {
  if (!summaryData.value) return 1
  return summaryData.value.positiveCount + summaryData.value.neutralCount + summaryData.value.negativeCount || 1
})

const positivePercent = computed(() => {
  return (summaryData.value?.positiveCount / totalSentiment.value * 100) || 0
})

const neutralPercent = computed(() => {
  return (summaryData.value?.neutralCount / totalSentiment.value * 100) || 0
})

const negativePercent = computed(() => {
  return (summaryData.value?.negativeCount / totalSentiment.value * 100) || 0
})

// Format file name for display
const formatFileName = (filename) => {
  const match = filename.match(/summary_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})/)
  if (match) {
    return `${match[1]}-${match[2]}-${match[3]} ${match[4]}:${match[5]}`
  }
  return filename
}

// Parse the summary text content
const parseSummary = (text) => {
  const data = {
    reportCount: 0,
    majorEvents: 0,
    positiveCount: 0,
    neutralCount: 0,
    negativeCount: 0,
    chinaPositive: 0,
    chinaNegative: 0,
    usPositive: 0,
    usNegative: 0,
    events: [],
    suggestions: ''
  }

  // Parse report count
  const reportMatch = text.match(/报告数量:\s*(\d+)/)
  if (reportMatch) data.reportCount = parseInt(reportMatch[1])

  // Parse major events
  const majorMatch = text.match(/重大事件:\s*(\d+)/)
  if (majorMatch) data.majorEvents = parseInt(majorMatch[1])

  // Parse sentiment counts
  const positiveMatch = text.match(/积极事件:\s*(\d+)/)
  if (positiveMatch) data.positiveCount = parseInt(positiveMatch[1])

  const neutralMatch = text.match(/中性事件:\s*(\d+)/)
  if (neutralMatch) data.neutralCount = parseInt(neutralMatch[1])

  const negativeMatch = text.match(/消极事件:\s*(\d+)/)
  if (negativeMatch) data.negativeCount = parseInt(negativeMatch[1])

  // Parse market divergence
  const chinaMatch = text.match(/中国市场:\s*积极\s*(\d+)\s*\|\s*消极\s*(\d+)/)
  if (chinaMatch) {
    data.chinaPositive = parseInt(chinaMatch[1])
    data.chinaNegative = parseInt(chinaMatch[2])
  }

  const usMatch = text.match(/美国市场:\s*积极\s*(\d+)\s*\|\s*消极\s*(\d+)/)
  if (usMatch) {
    data.usPositive = parseInt(usMatch[1])
    data.usNegative = parseInt(usMatch[2])
  }

  // Parse events
  const eventsSection = text.match(/【重点事件】[\s\S]*?(?=【|============|$)/)?.[0] || ''
  const eventRegex = /(\d+)\.\s*\[([^\]]+)\]\s*\n\s*([^\n]+)\s*\n\s*([^\n]+)\s*\n\s*情绪:\s*(\S+)/g
  let eventMatch
  while ((eventMatch = eventRegex.exec(eventsSection)) !== null) {
    const sentiment = eventMatch[5].includes('积极') ? 'positive' : 
                     eventMatch[5].includes('消极') ? 'negative' : 'neutral'
    data.events.push({
      source: eventMatch[2],
      title: eventMatch[3],
      summary: eventMatch[4],
      sentiment: sentiment,
      chinaImpact: '',
      usImpact: ''
    })
  }

  // Parse suggestions
  const suggestionsMatch = text.match(/【操作建议】([\s\S]*?)(?====|$)/)
  if (suggestionsMatch) {
    data.suggestions = suggestionsMatch[1].trim().replace(/\n+/g, '\n')
  }

  return data
}

// Load summary file list
const loadSummaryFiles = async () => {
  try {
    const response = await fetch('/api/daily_summary')
    if (response.ok) {
      const data = await response.json()
      if (data.files && data.files.length > 0) {
        summaryFiles.value = data.files
        selectedFile.value = data.files[0]
      }
    }
  } catch (err) {
    console.error('Failed to load summary files:', err)
  }
}

// Load selected summary
const loadSummary = async () => {
  if (!selectedFile.value) return
  
  loading.value = true
  error.value = null
  
  try {
    const response = await fetch(`/api/daily_summary?file=${selectedFile.value}`)
    if (response.ok) {
      const data = await response.json()
      rawContent.value = data.content || ''
      summaryData.value = parseSummary(rawContent.value)
    } else {
      throw new Error('Failed to load summary')
    }
  } catch (err) {
    error.value = err.message
    console.error('Failed to load summary:', err)
  } finally {
    loading.value = false
  }
}

// Refresh data
const refreshData = async () => {
  await loadSummaryFiles()
  if (selectedFile.value) {
    await loadSummary()
  }
}

// Toggle raw report visibility
const toggleRawReport = () => {
  showRawReport.value = !showRawReport.value
}

onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.daily-summary-page {
  max-width: 1800px;
  margin: 0 auto;
  padding: 1rem 2rem;
}

/* Header */
.page-header {
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

.header-icon {
  background: var(--c-ink);
  color: var(--c-bg);
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-text {
  display: flex;
  flex-direction: column;
}

.page-title {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1;
}

.page-subtitle {
  font-size: 0.7rem;
  letter-spacing: 0.2em;
  color: var(--c-amber);
  font-weight: 700;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.file-selector {
  padding: 0.5rem 1rem;
  border: 2px solid var(--c-border);
  background: var(--c-paper);
  font-family: var(--font-mono);
  font-size: 0.85rem;
  cursor: pointer;
}

.refresh-btn {
  background: var(--c-ink);
  border: 2px solid var(--c-ink);
  color: var(--c-bg);
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  box-shadow: 3px 3px 0 var(--c-shadow);
}

.refresh-btn:hover:not(:disabled) {
  transform: translate(-1px, -1px);
  box-shadow: 4px 4px 0 var(--c-shadow);
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Loading & Error States */
.loading-overlay,
.error-container,
.empty-container {
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

.error-text {
  color: #F44336;
  margin-bottom: 1rem;
}

.retry-btn {
  padding: 0.5rem 1rem;
  border: 2px solid var(--c-ink);
  background: transparent;
  cursor: pointer;
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

.kpi-item.positive { border-color: #4CAF50; }
.kpi-item.negative { border-color: #F44336; }

.kpi-icon {
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

.text-green { color: #4CAF50; }
.text-red { color: #F44336; }

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

.panel-header.collapsible {
  cursor: pointer;
}

.panel-header.collapsible svg {
  transition: transform 0.2s;
}

.panel-header.collapsible svg.rotated {
  transform: rotate(180deg);
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

/* Sentiment Bar */
.sentiment-bar-wrapper {
  margin-bottom: 1.5rem;
}

.sentiment-bar {
  height: 24px;
  display: flex;
  border: 1px solid var(--c-border);
  overflow: hidden;
}

.bar-positive { background: #4CAF50; }
.bar-neutral { background: #FF9800; }
.bar-negative { background: #F44336; }

/* Distribution */
.distribution-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  background: var(--c-hover);
  padding: 1rem;
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
.dist-item.neutral .dist-value { color: #FF9800; }
.dist-item.negative .dist-value { color: #F44336; }

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
  display: flex;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid var(--c-grid);
  background: var(--c-hover);
}

.event-rank {
  font-family: var(--font-display);
  font-weight: 800;
  font-size: 1.25rem;
  color: var(--c-amber);
  min-width: 40px;
}

.event-content {
  flex: 1;
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
  padding: 0.1rem 0.4rem;
  font-size: 0.7rem;
  font-weight: 700;
}

.event-type.positive { background: #4CAF50; color: #fff; }
.event-type.neutral { background: #FF9800; color: #fff; }
.event-type.negative { background: #F44336; color: #fff; }

.event-title {
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.event-summary {
  font-size: 0.9rem;
  color: var(--c-muted);
  line-height: 1.5;
}

.event-impacts {
  margin-top: 0.75rem;
  display: flex;
  gap: 0.5rem;
}

.impact-tag {
  padding: 0.2rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 700;
  background: var(--c-hover);
  border: 1px solid var(--c-border);
}

.impact-tag.cn { border-left: 3px solid #F44336; }
.impact-tag.us { border-left: 3px solid #2196F3; }

/* Market Divergence */
.market-item {
  padding: 1rem;
  background: var(--c-hover);
  border: 1px solid var(--c-grid);
  margin-bottom: 1rem;
}

.market-item:last-child {
  margin-bottom: 0;
}

.market-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.market-flag {
  background: #F44336;
  color: #fff;
  padding: 0.2rem 0.5rem;
  font-size: 0.7rem;
  font-weight: 700;
}

.market-flag.us {
  background: #2196F3;
}

.market-name {
  font-weight: 600;
}

.market-stats {
  display: flex;
  gap: 1.5rem;
}

.stat-positive, .stat-negative {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-family: var(--font-mono);
  font-weight: 700;
}

.stat-positive { color: #4CAF50; }
.stat-negative { color: #F44336; }

/* Suggestions */
.suggestions-content {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  line-height: 1.6;
  white-space: pre-wrap;
  margin: 0;
}

/* Raw Report */
.raw-content {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  background: var(--c-hover);
  padding: 1rem;
  border: 1px solid var(--c-grid);
  max-height: 400px;
  overflow-y: auto;
  margin: 0;
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
}

@media (max-width: 768px) {
  .daily-summary-page {
    padding: 0;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .header-actions {
    width: 100%;
  }
  
  .file-selector {
    flex: 1;
  }

  .kpi-bar { grid-template-columns: 1fr; }
  .distribution-row { grid-template-columns: 1fr; }
}
</style>
