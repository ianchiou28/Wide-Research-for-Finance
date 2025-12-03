<template>
  <div class="monthly-page">
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
          <span class="page-title">{{ t('monthly_title') }}</span>
          <span class="page-subtitle">MONTHLY DEEP ANALYSIS</span>
        </div>
      </div>
      <div class="header-actions">
        <select v-model="selectedMonth" class="month-selector" @change="loadAnalysis">
          <option v-for="m in monthOptions" :key="m.value" :value="m.value">{{ m.label }}</option>
        </select>
        <button class="refresh-btn" @click="regenerate" :disabled="loading">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6"></path><path d="M1 20v-6h6"></path>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
          </svg>
        </button>
      </div>
    </header>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>{{ t('generating_analysis') }}</span>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadAnalysis">{{ t('retry') }}</button>
    </div>

    <div v-else-if="analysis" class="analysis-content">
      <!-- 月度总结 -->
      <div class="summary-card">
        <div class="summary-header">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="16" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12.01" y2="8"></line>
          </svg>
          <span>{{ analysis.month }} {{ t('summary') }}</span>
        </div>
        <p class="summary-text">{{ analysis.summary }}</p>
      </div>

      <!-- 事件日历 -->
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">{{ t('key_dates') }}</span>
        </div>
        <div class="panel-body">
          <div class="event-timeline">
            <div v-for="(event, idx) in analysis.key_dates" :key="idx" class="timeline-item" :class="event.priority">
              <div class="timeline-date">{{ formatDate(event.date) }}</div>
              <div class="timeline-content">
                <div class="event-name">{{ event.event }}</div>
                <div class="event-action">{{ event.action }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 加减仓建议 -->
      <div class="recommendations-grid">
        <div class="panel buy-panel">
          <div class="panel-header bullish-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
            </svg>
            <span>{{ t('buy_recommendations') }}</span>
          </div>
          <div class="panel-body">
            <div v-for="s in (analysis.stock_recommendations?.buy || [])" :key="s.symbol" class="stock-rec-item buy">
              <div class="stock-header">
                <span class="stock-symbol">{{ s.symbol }}</span>
                <span class="stock-name">{{ s.name }}</span>
              </div>
              <div class="stock-detail">{{ s.reason }}</div>
              <div class="stock-meta">
                <span v-if="s.target_price">目标: {{ s.target_price }}</span>
                <span v-if="s.stop_loss">止损: {{ s.stop_loss }}</span>
              </div>
            </div>
            <div v-if="!analysis.stock_recommendations?.buy?.length" class="empty">{{ t('no_data') }}</div>
          </div>
        </div>

        <div class="panel sell-panel">
          <div class="panel-header bearish-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline>
            </svg>
            <span>{{ t('sell_recommendations') }}</span>
          </div>
          <div class="panel-body">
            <div v-for="s in (analysis.stock_recommendations?.sell || [])" :key="s.symbol" class="stock-rec-item sell">
              <div class="stock-header">
                <span class="stock-symbol">{{ s.symbol }}</span>
                <span class="stock-name">{{ s.name }}</span>
              </div>
              <div class="stock-detail">{{ s.reason }}</div>
            </div>
            <div v-if="!analysis.stock_recommendations?.sell?.length" class="empty">{{ t('no_data') }}</div>
          </div>
        </div>
      </div>

      <!-- 行业轮动 -->
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">{{ t('sector_rotation') }}</span>
        </div>
        <div class="panel-body sectors-grid">
          <div class="sector-col overweight">
            <div class="sector-title">{{ t('overweight') }}</div>
            <div v-for="s in (analysis.sector_rotation?.overweight || [])" :key="s.sector" class="sector-item">
              <div class="sector-name">{{ s.sector }}</div>
              <div class="sector-reason">{{ s.reason }}</div>
            </div>
          </div>
          <div class="sector-col underweight">
            <div class="sector-title">{{ t('underweight') }}</div>
            <div v-for="s in (analysis.sector_rotation?.underweight || [])" :key="s.sector" class="sector-item">
              <div class="sector-name">{{ s.sector }}</div>
              <div class="sector-reason">{{ s.reason }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 风险提示 -->
      <div class="panel risk-panel">
        <div class="panel-header">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
            <line x1="12" y1="9" x2="12" y2="13"></line>
            <line x1="12" y1="17" x2="12.01" y2="17"></line>
          </svg>
          <span>{{ t('risk_warnings') }}</span>
        </div>
        <div class="panel-body">
          <div class="risk-position">{{ analysis.risk_warnings?.position_management }}</div>
          <ul class="risk-list">
            <li v-for="(r, i) in (analysis.risk_warnings?.main_uncertainties || [])" :key="i">{{ r }}</li>
          </ul>
        </div>
      </div>

      <!-- 对话追问 -->
      <div class="chat-section">
        <div class="chat-header">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          <span>{{ t('ask_analyst') }}</span>
        </div>
        <div class="chat-messages" ref="chatBox">
          <div v-for="(msg, i) in chatHistory" :key="i" class="chat-msg" :class="msg.role">
            <div class="msg-content">{{ msg.content }}</div>
          </div>
        </div>
        <div class="chat-input-wrap">
          <input v-model="chatInput" @keyup.enter="sendChat" :placeholder="t('ask_placeholder')" :disabled="chatLoading" />
          <button @click="sendChat" :disabled="chatLoading || !chatInput.trim()">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <p>{{ t('no_analysis') }}</p>
      <button @click="loadAnalysis">{{ t('generate_now') }}</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useLocale } from '../composables/useLocale'

const { t } = useLocale()

const loading = ref(false)
const error = ref(null)
const analysis = ref(null)
const selectedMonth = ref('')
const chatInput = ref('')
const chatLoading = ref(false)
const chatHistory = ref([])
const chatBox = ref(null)

const monthOptions = computed(() => {
  const opts = []
  const now = new Date()
  for (let i = 0; i < 6; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    opts.push({
      value: `${d.getFullYear()}-${d.getMonth() + 1}`,
      label: `${d.getFullYear()}年${d.getMonth() + 1}月`
    })
  }
  return opts
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

const loadAnalysis = async (regen = false) => {
  loading.value = true
  error.value = null
  try {
    const [year, month] = selectedMonth.value.split('-')
    const url = `/api/monthly/analysis?year=${year}&month=${month}${regen ? '&regenerate=true' : ''}`
    const res = await fetch(url)
    if (!res.ok) throw new Error('Failed')
    analysis.value = await res.json()
    if (analysis.value.error) {
      error.value = analysis.value.message || 'Error'
      analysis.value = null
    }
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

const regenerate = () => loadAnalysis(true)

const sendChat = async () => {
  if (!chatInput.value.trim() || chatLoading.value) return
  const msg = chatInput.value.trim()
  chatHistory.value.push({ role: 'user', content: msg })
  chatInput.value = ''
  chatLoading.value = true
  await nextTick()
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight

  try {
    const res = await fetch('/api/monthly/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    })
    const data = await res.json()
    chatHistory.value.push({ role: 'assistant', content: data.reply || data.error || 'Error' })
  } catch (e) {
    chatHistory.value.push({ role: 'assistant', content: '请求失败' })
  } finally {
    chatLoading.value = false
    await nextTick()
    if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
  }
}

onMounted(() => {
  const now = new Date()
  selectedMonth.value = `${now.getFullYear()}-${now.getMonth() + 1}`
  loadAnalysis()
})
</script>

<style scoped>
.monthly-page { max-width: 1400px; margin: 0 auto; padding: 1rem; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; border-bottom: 2px solid var(--c-ink); padding-bottom: 1rem; flex-wrap: wrap; gap: 1rem; }
.header-left { display: flex; align-items: center; gap: 1rem; }
.header-icon { background: var(--c-ink); color: var(--c-bg); width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; }
.header-text { display: flex; flex-direction: column; }
.page-title { font-family: var(--font-display); font-size: 1.5rem; font-weight: 700; }
.page-subtitle { font-size: 0.7rem; letter-spacing: 0.15em; color: var(--c-amber); font-weight: 700; }
.header-actions { display: flex; gap: 0.5rem; }
.month-selector { padding: 0.5rem; border: 2px solid var(--c-border); background: var(--c-paper); font-family: var(--font-mono); }
.refresh-btn { background: var(--c-ink); border: 2px solid var(--c-ink); color: var(--c-bg); padding: 0.5rem; cursor: pointer; }
.refresh-btn:disabled { opacity: 0.5; }

.loading-state, .error-state, .empty-state { text-align: center; padding: 4rem 1rem; }
.spinner { width: 40px; height: 40px; border: 4px solid var(--c-grid); border-top-color: var(--c-amber); border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 1rem; }
@keyframes spin { to { transform: rotate(360deg); } }

.summary-card { background: linear-gradient(135deg, var(--c-amber) 0%, #e67e22 100%); color: #fff; padding: 1.5rem; margin-bottom: 1.5rem; border: 2px solid var(--c-ink); }
.summary-header { display: flex; align-items: center; gap: 0.5rem; font-weight: 700; margin-bottom: 0.75rem; }
.summary-text { line-height: 1.6; }

.panel { background: var(--c-paper); border: 2px solid var(--c-border); margin-bottom: 1.5rem; box-shadow: 4px 4px 0 var(--c-shadow); }
.panel-header { background: var(--c-hover); border-bottom: 1px solid var(--c-border); padding: 0.75rem 1rem; display: flex; align-items: center; gap: 0.5rem; font-weight: 700; }
.panel-header.bullish-header { background: rgba(76,175,80,0.15); color: #4CAF50; }
.panel-header.bearish-header { background: rgba(244,67,54,0.15); color: #F44336; }
.panel-body { padding: 1rem; }

.event-timeline { display: flex; flex-direction: column; gap: 0.75rem; }
.timeline-item { display: flex; gap: 1rem; padding: 0.75rem; background: var(--c-hover); border-left: 3px solid var(--c-border); }
.timeline-item.high { border-left-color: #F44336; }
.timeline-item.medium { border-left-color: #FF9800; }
.timeline-date { font-family: var(--font-mono); font-weight: 700; min-width: 50px; }
.event-name { font-weight: 600; }
.event-action { font-size: 0.85rem; color: var(--c-muted); }

.recommendations-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.stock-rec-item { padding: 0.75rem; border: 1px solid var(--c-grid); margin-bottom: 0.5rem; }
.stock-rec-item.buy { border-left: 3px solid #4CAF50; }
.stock-rec-item.sell { border-left: 3px solid #F44336; }
.stock-header { display: flex; gap: 0.5rem; align-items: baseline; margin-bottom: 0.25rem; }
.stock-symbol { font-family: var(--font-mono); font-weight: 700; }
.stock-name { font-size: 0.85rem; color: var(--c-muted); }
.stock-detail { font-size: 0.85rem; line-height: 1.4; }
.stock-meta { font-size: 0.75rem; color: var(--c-muted); margin-top: 0.25rem; display: flex; gap: 1rem; }

.sectors-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.sector-col { padding: 0.75rem; }
.sector-col.overweight { background: rgba(76,175,80,0.1); }
.sector-col.underweight { background: rgba(244,67,54,0.1); }
.sector-title { font-weight: 700; margin-bottom: 0.5rem; }
.sector-item { padding: 0.5rem 0; border-bottom: 1px solid var(--c-grid); }
.sector-name { font-weight: 600; }
.sector-reason { font-size: 0.85rem; color: var(--c-muted); }

.risk-panel .panel-header { background: rgba(244,67,54,0.1); color: #F44336; }
.risk-position { font-weight: 600; margin-bottom: 0.5rem; }
.risk-list { margin: 0; padding-left: 1.25rem; }
.risk-list li { margin-bottom: 0.25rem; }

.chat-section { background: var(--c-paper); border: 2px solid var(--c-border); margin-top: 1.5rem; }
.chat-header { background: var(--c-ink); color: var(--c-bg); padding: 0.75rem 1rem; display: flex; align-items: center; gap: 0.5rem; font-weight: 700; }
.chat-messages { height: 200px; overflow-y: auto; padding: 1rem; display: flex; flex-direction: column; gap: 0.75rem; }
.chat-msg { max-width: 80%; padding: 0.5rem 0.75rem; border-radius: 4px; }
.chat-msg.user { align-self: flex-end; background: var(--c-amber); color: #fff; }
.chat-msg.assistant { align-self: flex-start; background: var(--c-hover); }
.chat-input-wrap { display: flex; border-top: 1px solid var(--c-border); }
.chat-input-wrap input { flex: 1; padding: 0.75rem; border: none; background: transparent; font-size: 1rem; }
.chat-input-wrap button { padding: 0.75rem 1rem; background: var(--c-ink); color: var(--c-bg); border: none; cursor: pointer; }
.chat-input-wrap button:disabled { opacity: 0.5; }

.empty { text-align: center; color: var(--c-muted); padding: 1rem; }

@media (max-width: 768px) {
  .monthly-page { padding: 0.5rem; }
  .recommendations-grid, .sectors-grid { grid-template-columns: 1fr; }
  .page-header { flex-direction: column; align-items: flex-start; }
  .header-actions { width: 100%; }
  .month-selector { flex: 1; }
}
</style>
