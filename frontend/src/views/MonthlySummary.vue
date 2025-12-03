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
            <div v-if="msg.role === 'assistant'" class="msg-content markdown-body" v-html="renderMarkdown(msg.content)"></div>
            <div v-else class="msg-content">{{ msg.content }}</div>
          </div>
          <!-- 加载提示 -->
          <div v-if="chatLoading" class="chat-msg assistant loading-msg">
            <div class="msg-content">
              <span class="typing-indicator">
                <span></span><span></span><span></span>
              </span>
              正在生成回复...
            </div>
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

// 简易 Markdown 渲染
const renderMarkdown = (text) => {
  if (!text) return ''
  return text
    // 代码块
    .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    // 行内代码
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // 粗体
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    // 斜体
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    // 标题
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    // 列表
    .replace(/^[\-\*] (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
    // 数字列表
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    // 换行
    .replace(/\n/g, '<br>')
}

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
  
  // 处理特殊格式如 "2025-12-16至17日"
  if (dateStr.includes('至') || dateStr.includes('日')) {
    // 提取月和日: 2025-12-16至17日 -> 12/16-17
    const match = dateStr.match(/(\d{4})-(\d{1,2})-(\d{1,2})(.*)/)
    if (match) {
      const month = match[2]
      const day = match[3]
      const rest = match[4] // 如 "至17日"
      if (rest) {
        const extraDay = rest.match(/(\d{1,2})/)
        if (extraDay) {
          return `${month}/${day}-${extraDay[1]}`
        }
      }
      return `${month}/${day}`
    }
    return dateStr
  }
  
  // 标准 ISO 格式日期 2025-12-05
  const match = dateStr.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/)
  if (match) {
    return `${match[2]}/${match[3]}`
  }
  
  // 尝试 Date 解析
  const d = new Date(dateStr)
  if (!isNaN(d.getTime())) {
    return `${d.getMonth() + 1}/${d.getDate()}`
  }
  
  // 无法解析，返回原字符串
  return dateStr
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

.summary-card { 
  background: rgba(255, 85, 0, 0.05); 
  color: var(--c-ink); 
  padding: 1.5rem; 
  margin-bottom: 1.5rem; 
  border: 1px solid var(--c-amber); 
  border-left: 6px solid var(--c-amber);
  box-shadow: 4px 4px 0 var(--c-shadow);
  position: relative;
}
.summary-card::after {
  content: none;
}
.summary-header { display: flex; align-items: center; gap: 0.75rem; font-weight: 700; margin-bottom: 1rem; border-bottom: 1px solid rgba(255, 85, 0, 0.2); padding-bottom: 0.75rem; color: var(--c-amber); }
.summary-text { line-height: 1.8; font-weight: 500; font-size: 1.05rem; }

.panel { background: var(--c-paper); border: 2px solid var(--c-border); margin-bottom: 1.5rem; box-shadow: 4px 4px 0 var(--c-shadow); }
.panel-header { background: var(--c-hover); border-bottom: 2px solid var(--c-border); padding: 0.75rem 1rem; display: flex; align-items: center; gap: 0.75rem; font-weight: 700; }
.panel-header.bullish-header { background: rgba(76,175,80,0.1); color: #2E7D32; border-bottom-color: #4CAF50; }
.panel-header.bearish-header { background: rgba(244,67,54,0.1); color: #C62828; border-bottom-color: #F44336; }
.panel-body { padding: 1.25rem; }

.event-timeline { display: flex; flex-direction: column; gap: 1rem; }
.timeline-item { display: flex; gap: 1.25rem; padding: 1rem; background: var(--c-bg); border: 1px solid var(--c-border); box-shadow: 2px 2px 0 var(--c-grid); }
.timeline-item.high { border-left: 4px solid #F44336; }
.timeline-item.medium { border-left: 4px solid #FF9800; }
.timeline-date { font-family: var(--font-mono); font-weight: 700; min-width: 60px; color: var(--c-ink); font-size: 1.1rem; display: flex; align-items: center; }
.timeline-content { flex: 1; }
.event-name { font-weight: 700; margin-bottom: 0.25rem; font-size: 1rem; }
.event-action { font-size: 0.9rem; color: var(--c-muted); line-height: 1.4; }

.recommendations-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.stock-rec-item { padding: 1rem; background: var(--c-bg); border: 1px solid var(--c-border); margin-bottom: 0.75rem; box-shadow: 2px 2px 0 var(--c-grid); transition: transform 0.2s; }
.stock-rec-item:hover { transform: translate(-2px, -2px); box-shadow: 4px 4px 0 var(--c-grid); }
.stock-rec-item.buy { border-left: 4px solid #4CAF50; }
.stock-rec-item.sell { border-left: 4px solid #F44336; }
.stock-header { display: flex; gap: 0.75rem; align-items: baseline; margin-bottom: 0.5rem; border-bottom: 1px dashed var(--c-grid); padding-bottom: 0.5rem; }
.stock-symbol { font-family: var(--font-mono); font-weight: 700; font-size: 1.1rem; }
.stock-name { font-size: 0.9rem; color: var(--c-muted); font-weight: 600; }
.stock-detail { font-size: 0.9rem; line-height: 1.5; margin-bottom: 0.5rem; }
.stock-meta { font-size: 0.8rem; color: var(--c-muted); display: flex; gap: 1rem; font-family: var(--font-mono); background: var(--c-hover); padding: 0.25rem 0.5rem; display: inline-flex; }

.sectors-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.sector-col { padding: 1rem; background: var(--c-bg); border: 1px solid var(--c-border); }
.sector-col.overweight { border-top: 4px solid #4CAF50; }
.sector-col.underweight { border-top: 4px solid #F44336; }
.sector-title { font-weight: 700; margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 0.05em; font-size: 0.9rem; color: var(--c-muted); border-bottom: 2px solid var(--c-border); padding-bottom: 0.5rem; }
.sector-item { padding: 0.75rem 0; border-bottom: 1px dashed var(--c-grid); }
.sector-item:last-child { border-bottom: none; }
.sector-name { font-weight: 700; margin-bottom: 0.25rem; }
.sector-reason { font-size: 0.85rem; color: var(--c-muted); line-height: 1.4; }

.risk-panel .panel-header { background: rgba(244,67,54,0.05); color: #D32F2F; border-bottom-color: #F44336; }
.risk-position { font-weight: 700; margin-bottom: 1rem; padding: 0.75rem; background: rgba(244,67,54,0.1); border-left: 4px solid #F44336; }
.risk-list { margin: 0; padding-left: 1.25rem; }
.risk-list li { margin-bottom: 0.5rem; line-height: 1.5; }

.chat-section { background: var(--c-paper); border: 2px solid var(--c-border); margin-top: 2rem; box-shadow: 4px 4px 0 var(--c-shadow); }
.chat-header { background: var(--c-ink); color: var(--c-bg); padding: 0.75rem 1rem; display: flex; align-items: center; gap: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
.chat-messages { min-height: 300px; max-height: 500px; overflow-y: auto; padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; background: var(--c-bg); }
.chat-msg { max-width: 85%; padding: 1rem; border-radius: 0; border: 1px solid var(--c-border); box-shadow: 2px 2px 0 var(--c-grid); }
.chat-msg.user { align-self: flex-end; background: var(--c-amber); color: var(--c-ink); border-color: var(--c-ink); }
.chat-msg.assistant { align-self: flex-start; background: var(--c-paper); }
.chat-input-wrap { display: flex; border-top: 2px solid var(--c-border); padding: 0.5rem; background: var(--c-paper); }
.chat-input-wrap input { flex: 1; padding: 0.75rem; border: 1px solid var(--c-border); background: var(--c-bg); font-size: 1rem; font-family: var(--font-body); margin-right: 0.5rem; }
.chat-input-wrap input:focus { outline: 2px solid var(--c-amber); border-color: var(--c-amber); }
.chat-input-wrap button { padding: 0 1.5rem; background: var(--c-ink); color: var(--c-bg); border: none; cursor: pointer; font-weight: 700; transition: all 0.2s; }
.chat-input-wrap button:hover:not(:disabled) { background: var(--c-amber); color: var(--c-ink); }
.chat-input-wrap button:disabled { opacity: 0.5; cursor: not-allowed; }

/* Markdown 样式 */
.markdown-body { line-height: 1.6; }
.markdown-body h2, .markdown-body h3, .markdown-body h4 { margin: 0.5em 0 0.25em; font-weight: 700; }
.markdown-body h2 { font-size: 1.2em; }
.markdown-body h3 { font-size: 1.1em; }
.markdown-body h4 { font-size: 1em; }
.markdown-body strong { font-weight: 700; color: var(--c-ink); }
.markdown-body em { font-style: italic; }
.markdown-body code { background: rgba(0,0,0,0.1); padding: 0.1em 0.3em; border-radius: 3px; font-family: var(--font-mono); font-size: 0.9em; }
.markdown-body pre { background: rgba(0,0,0,0.08); padding: 0.75rem; border-radius: 4px; overflow-x: auto; margin: 0.5em 0; }
.markdown-body pre code { background: none; padding: 0; }
.markdown-body ul, .markdown-body ol { margin: 0.5em 0; padding-left: 1.5em; }
.markdown-body li { margin: 0.25em 0; }
.markdown-body br { display: block; margin: 0.25em 0; content: ''; }

/* 加载动画 */
.loading-msg { opacity: 0.8; }
.typing-indicator { display: inline-flex; gap: 4px; margin-right: 8px; }
.typing-indicator span { width: 6px; height: 6px; background: var(--c-amber); border-radius: 50%; animation: typing 1.4s infinite ease-in-out both; }
.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
@keyframes typing { 0%, 80%, 100% { transform: scale(0.6); opacity: 0.6; } 40% { transform: scale(1); opacity: 1; } }

.empty { text-align: center; color: var(--c-muted); padding: 1rem; }

@media (max-width: 768px) {
  .monthly-page { padding: 0.5rem; }
  .recommendations-grid, .sectors-grid { grid-template-columns: 1fr; }
  .page-header { flex-direction: column; align-items: flex-start; }
  .header-actions { width: 100%; }
  .month-selector { flex: 1; }
}
</style>
