<template>
  <div class="backtest-page">
    <header class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 20V10"></path>
            <path d="M18 20V4"></path>
            <path d="M6 20v-4"></path>
          </svg>
        </div>
        <div class="header-text">
          <span class="page-title">预测回测</span>
          <span class="page-subtitle">PREDICTION BACKTEST</span>
        </div>
      </div>
      <div class="header-actions">
        <button class="refresh-btn" @click="loadData" :disabled="loading">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6"></path><path d="M1 20v-6h6"></path>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
          </svg>
        </button>
        <button class="run-btn" @click="runBacktest" :disabled="running">
          {{ running ? '运行中...' : '运行回测' }}
        </button>
      </div>
    </header>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>

    <div v-else-if="!summary || summary.error" class="empty-state">
      <div class="empty-icon">📊</div>
      <p>{{ summary?.message || '暂无回测数据' }}</p>
      <button @click="runBacktest" :disabled="running">{{ running ? '运行中...' : '立即运行回测' }}</button>
    </div>

    <div v-else class="backtest-content">
      <!-- 汇总卡片 -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="card-label">回测日期</div>
          <div class="card-value">{{ summary.date }}</div>
        </div>
        <div class="summary-card" :class="getAccuracyClass(weeklyAccuracy)">
          <div class="card-label">周报准确率</div>
          <div class="card-value">{{ weeklyAccuracy.toFixed(1) }}%</div>
          <div class="card-sub">{{ summary.weekly?.total_predictions || 0 }} 条预测</div>
        </div>
        <div class="summary-card" :class="getAccuracyClass(monthlyStockAccuracy)">
          <div class="card-label">月报股票准确率</div>
          <div class="card-value">{{ monthlyStockAccuracy.toFixed(1) }}%</div>
          <div class="card-sub">{{ summary.monthly?.stock_predictions?.total || 0 }} 条预测</div>
        </div>
        <div class="summary-card" :class="getAccuracyClass(monthlyEventAccuracy)">
          <div class="card-label">月报事件准确率</div>
          <div class="card-value">{{ monthlyEventAccuracy.toFixed(1) }}%</div>
          <div class="card-sub">{{ summary.monthly?.event_predictions?.total || 0 }} 条预测</div>
        </div>
      </div>

      <!-- 周报详情 -->
      <div class="panel">
        <div class="panel-header" @click="toggleWeekly">
          <span class="panel-title">📈 周报预测回测</span>
          <span class="toggle-icon">{{ showWeekly ? '▼' : '▶' }}</span>
        </div>
        <div v-show="showWeekly" class="panel-body">
          <!-- 按方向统计 -->
          <div v-if="summary.weekly?.by_direction" class="direction-stats">
            <div v-for="(stat, dir) in summary.weekly.by_direction" :key="dir" class="stat-item">
              <span class="stat-label" :class="dir">{{ dir }}</span>
              <div class="stat-bar-wrap">
                <div class="stat-bar" :style="{ width: stat.accuracy + '%' }" :class="getAccuracyClass(stat.accuracy)"></div>
              </div>
              <span class="stat-value">{{ stat.correct }}/{{ stat.total }} ({{ stat.accuracy }}%)</span>
            </div>
          </div>
          
          <!-- 详细预测列表 -->
          <div v-if="weeklyDetails?.verified?.length" class="predictions-table">
            <div class="table-header">
              <span>日期</span>
              <span>股票</span>
              <span>预测</span>
              <span>实际</span>
              <span>涨跌幅</span>
              <span>结果</span>
            </div>
            <div v-for="(pred, idx) in weeklyDetails.verified.slice(0, showAllWeekly ? 100 : 10)" :key="idx" class="table-row" :class="{ correct: pred.is_correct, wrong: !pred.is_correct }">
              <span>{{ pred.analysis_date }}</span>
              <span class="symbol">{{ pred.symbol }}</span>
              <span :class="pred.predicted_direction">{{ pred.predicted_direction }}</span>
              <span :class="pred.actual_direction">{{ pred.actual_direction }}</span>
              <span :class="pred.actual_change_pct > 0 ? '上涨' : '下跌'">{{ pred.actual_change_pct?.toFixed(2) }}%</span>
              <span class="result-icon">{{ pred.is_correct ? '✓' : '✗' }}</span>
            </div>
            <button v-if="weeklyDetails.verified.length > 10" class="show-more" @click="showAllWeekly = !showAllWeekly">
              {{ showAllWeekly ? '收起' : `查看全部 ${weeklyDetails.verified.length} 条` }}
            </button>
          </div>
          <div v-else class="empty">暂无详细数据</div>
        </div>
      </div>

      <!-- 月报详情 -->
      <div class="panel">
        <div class="panel-header" @click="toggleMonthly">
          <span class="panel-title">📅 月报预测回测</span>
          <span class="toggle-icon">{{ showMonthly ? '▼' : '▶' }}</span>
        </div>
        <div v-show="showMonthly" class="panel-body">
          <!-- 股票预测 -->
          <h4>股票预测</h4>
          <div v-if="monthlyDetails?.verified_stocks?.length" class="predictions-table">
            <div class="table-header">
              <span>日期</span>
              <span>股票</span>
              <span>预测</span>
              <span>实际</span>
              <span>涨跌幅</span>
              <span>结果</span>
            </div>
            <div v-for="(pred, idx) in monthlyDetails.verified_stocks.slice(0, 20)" :key="'s'+idx" class="table-row" :class="{ correct: pred.is_correct, wrong: !pred.is_correct }">
              <span>{{ pred.analysis_date }}</span>
              <span class="symbol">{{ pred.symbol }}</span>
              <span :class="pred.predicted_direction">{{ pred.predicted_direction }}</span>
              <span :class="pred.actual_direction">{{ pred.actual_direction }}</span>
              <span :class="pred.actual_change_pct > 0 ? '上涨' : '下跌'">{{ pred.actual_change_pct?.toFixed(2) }}%</span>
              <span class="result-icon">{{ pred.is_correct ? '✓' : '✗' }}</span>
            </div>
          </div>
          <div v-else class="empty">暂无股票预测数据</div>

          <!-- 事件预测 -->
          <h4 style="margin-top: 1.5rem;">事件预测</h4>
          <div v-if="monthlyDetails?.verified_events?.length" class="predictions-table events">
            <div class="table-header">
              <span>事件</span>
              <span>日期</span>
              <span>预测影响</span>
              <span>实际影响</span>
              <span>结果</span>
            </div>
            <div v-for="(pred, idx) in monthlyDetails.verified_events.slice(0, 20)" :key="'e'+idx" class="table-row" :class="{ correct: pred.is_correct, wrong: !pred.is_correct }">
              <span class="event-name">{{ pred.event_name }}</span>
              <span>{{ pred.event_date }}</span>
              <span :class="pred.predicted_direction">{{ pred.predicted_direction }}</span>
              <span :class="pred.actual_impact">{{ pred.actual_impact }}</span>
              <span class="result-icon">{{ pred.is_correct ? '✓' : '✗' }}</span>
            </div>
          </div>
          <div v-else class="empty">暂无事件预测数据</div>
        </div>
      </div>

      <!-- 优化状态 -->
      <div class="panel optimization-panel">
        <div class="panel-header" @click="toggleOptimization">
          <span class="panel-title">🔧 自动优化状态</span>
          <span class="toggle-icon">{{ showOptimization ? '▼' : '▶' }}</span>
        </div>
        <div v-show="showOptimization" class="panel-body">
          <div v-if="optimization?.config" class="opt-content">
            <div class="opt-section">
              <h5>当前配置 (v{{ optimization.config.version }})</h5>
              <div class="opt-grid">
                <div class="opt-item">
                  <span class="opt-label">判定阈值</span>
                  <span class="opt-value">±{{ optimization.config.thresholds?.bullish || 1 }}%</span>
                </div>
                <div class="opt-item">
                  <span class="opt-label">验证天数</span>
                  <span class="opt-value">{{ optimization.config.thresholds?.verify_days || 5 }}天</span>
                </div>
                <div class="opt-item">
                  <span class="opt-label">最低置信度</span>
                  <span class="opt-value">{{ ((optimization.config.min_confidence || 0.3) * 100).toFixed(0) }}%</span>
                </div>
                <div class="opt-item">
                  <span class="opt-label">优化次数</span>
                  <span class="opt-value">{{ optimization.history?.total_count || 0 }}次</span>
                </div>
              </div>
            </div>
            
            <div class="opt-section" v-if="optimization.config.signal_weights">
              <h5>信号权重</h5>
              <div class="weight-bars">
                <div v-for="(weight, dir) in optimization.config.signal_weights" :key="dir" class="weight-item">
                  <span class="weight-label" :class="dir">{{ dir }}</span>
                  <div class="weight-bar-wrap">
                    <div class="weight-bar" :style="{ width: (weight * 50) + '%' }" :class="weight > 1 ? 'boost' : weight < 1 ? 'reduce' : ''"></div>
                  </div>
                  <span class="weight-value">{{ weight.toFixed(2) }}x</span>
                </div>
              </div>
            </div>
            
            <div class="opt-section" v-if="optimization.latest_report?.analysis?.recommendations?.length">
              <h5>最新优化建议</h5>
              <ul class="recommendations">
                <li v-for="(rec, i) in optimization.latest_report.analysis.recommendations" :key="i">{{ rec }}</li>
              </ul>
            </div>
            
            <div class="opt-section" v-if="optimization.history?.optimizations?.length">
              <h5>优化历史</h5>
              <div class="opt-history">
                <div v-for="(opt, i) in optimization.history.optimizations.slice(-5).reverse()" :key="i" class="history-item">
                  <span class="history-date">{{ opt.timestamp?.slice(0, 10) }}</span>
                  <span class="history-changes">{{ opt.changes?.length || 0 }} 项调整</span>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="empty">暂无优化数据，运行回测后将自动优化</div>
        </div>
      </div>

      <!-- 说明 -->
      <div class="info-panel">
        <h4>📌 回测说明</h4>
        <ul>
          <li><strong>周报回测</strong>：验证周度分析中的股票预测，观察期 5 天</li>
          <li><strong>月报回测</strong>：验证月度分析中的股票和事件预测，观察期 10 天</li>
          <li><strong>判定标准</strong>：涨幅 >1% 为上涨，跌幅 >1% 为下跌，其余为震荡</li>
          <li><strong>自动优化</strong>：每次回测后自动分析结果并调整预测参数</li>
          <li><strong>运行时间</strong>：每日 21:00 自动运行回测+优化</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const loading = ref(false)
const running = ref(false)
const summary = ref(null)
const weeklyDetails = ref(null)
const monthlyDetails = ref(null)
const optimization = ref(null)
const showWeekly = ref(true)
const showMonthly = ref(false)
const showOptimization = ref(true)
const showAllWeekly = ref(false)

const weeklyAccuracy = computed(() => summary.value?.weekly?.accuracy || 0)
const monthlyStockAccuracy = computed(() => summary.value?.monthly?.stock_predictions?.accuracy || 0)
const monthlyEventAccuracy = computed(() => summary.value?.monthly?.event_predictions?.accuracy || 0)

const getAccuracyClass = (acc) => {
  if (acc >= 60) return 'good'
  if (acc >= 40) return 'medium'
  return 'poor'
}

const toggleWeekly = () => { showWeekly.value = !showWeekly.value }
const toggleMonthly = () => { showMonthly.value = !showMonthly.value }
const toggleOptimization = () => { showOptimization.value = !showOptimization.value }

const loadData = async () => {
  loading.value = true
  try {
    // 加载汇总
    const summaryRes = await fetch('/api/backtest/summary')
    summary.value = await summaryRes.json()

    // 加载详情和优化状态
    const [weeklyRes, monthlyRes, optRes] = await Promise.all([
      fetch('/api/backtest/weekly'),
      fetch('/api/backtest/monthly'),
      fetch('/api/backtest/optimization')
    ])
    weeklyDetails.value = await weeklyRes.json()
    monthlyDetails.value = await monthlyRes.json()
    optimization.value = await optRes.json()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const runBacktest = async () => {
  running.value = true
  try {
    const res = await fetch('/api/backtest/run', { method: 'POST' })
    const data = await res.json()
    if (data.success) {
      await loadData()
    } else {
      alert(data.error || '回测失败')
    }
  } catch (e) {
    alert('回测请求失败: ' + e.message)
  } finally {
    running.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.backtest-page { max-width: 1400px; margin: 0 auto; padding: 1rem; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; border-bottom: 2px solid var(--c-ink); padding-bottom: 1rem; flex-wrap: wrap; gap: 1rem; }
.header-left { display: flex; align-items: center; gap: 1rem; }
.header-icon { background: var(--c-ink); color: var(--c-bg); width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; }
.header-text { display: flex; flex-direction: column; }
.page-title { font-family: var(--font-display); font-size: 1.5rem; font-weight: 700; }
.page-subtitle { font-size: 0.7rem; letter-spacing: 0.15em; color: var(--c-amber); font-weight: 700; }
.header-actions { display: flex; gap: 0.5rem; }
.refresh-btn, .run-btn { padding: 0.5rem 1rem; border: 2px solid var(--c-ink); background: var(--c-paper); cursor: pointer; font-weight: 600; }
.run-btn { background: var(--c-ink); color: var(--c-bg); }
.run-btn:disabled, .refresh-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.loading-state, .empty-state { text-align: center; padding: 4rem 1rem; }
.spinner { width: 40px; height: 40px; border: 4px solid var(--c-grid); border-top-color: var(--c-amber); border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 1rem; }
@keyframes spin { to { transform: rotate(360deg); } }
.empty-icon { font-size: 4rem; margin-bottom: 1rem; }
.empty-state button { margin-top: 1rem; padding: 0.75rem 1.5rem; background: var(--c-ink); color: var(--c-bg); border: none; cursor: pointer; font-weight: 600; }

.summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
.summary-card { background: var(--c-paper); border: 2px solid var(--c-border); padding: 1.25rem; text-align: center; box-shadow: 4px 4px 0 var(--c-shadow); }
.card-label { font-size: 0.85rem; color: var(--c-muted); margin-bottom: 0.5rem; }
.card-value { font-family: var(--font-mono); font-size: 2rem; font-weight: 700; }
.card-sub { font-size: 0.75rem; color: var(--c-muted); margin-top: 0.25rem; }
.summary-card.good .card-value { color: #4CAF50; }
.summary-card.medium .card-value { color: #FF9800; }
.summary-card.poor .card-value { color: #F44336; }

.panel { background: var(--c-paper); border: 2px solid var(--c-border); margin-bottom: 1.5rem; box-shadow: 4px 4px 0 var(--c-shadow); }
.panel-header { background: var(--c-hover); border-bottom: 1px solid var(--c-border); padding: 0.75rem 1rem; display: flex; justify-content: space-between; align-items: center; font-weight: 700; cursor: pointer; }
.panel-header:hover { background: var(--c-grid); }
.toggle-icon { font-size: 0.8rem; }
.panel-body { padding: 1rem; }

.direction-stats { display: flex; flex-direction: column; gap: 0.75rem; margin-bottom: 1.5rem; }
.stat-item { display: flex; align-items: center; gap: 1rem; }
.stat-label { min-width: 50px; font-weight: 600; padding: 0.25rem 0.5rem; border-radius: 3px; font-size: 0.85rem; }
.stat-label.上涨 { background: rgba(76,175,80,0.2); color: #4CAF50; }
.stat-label.下跌 { background: rgba(244,67,54,0.2); color: #F44336; }
.stat-label.震荡 { background: rgba(158,158,158,0.2); color: #666; }
.stat-bar-wrap { flex: 1; height: 20px; background: var(--c-grid); border-radius: 3px; overflow: hidden; }
.stat-bar { height: 100%; transition: width 0.3s; }
.stat-bar.good { background: #4CAF50; }
.stat-bar.medium { background: #FF9800; }
.stat-bar.poor { background: #F44336; }
.stat-value { font-family: var(--font-mono); font-size: 0.85rem; min-width: 120px; text-align: right; }

.predictions-table { border: 1px solid var(--c-grid); }
.table-header, .table-row { display: grid; grid-template-columns: 100px 80px 60px 60px 80px 50px; gap: 0.5rem; padding: 0.5rem 0.75rem; align-items: center; font-size: 0.85rem; }
.predictions-table.events .table-header, .predictions-table.events .table-row { grid-template-columns: 1fr 100px 80px 80px 50px; }
.table-header { background: var(--c-hover); font-weight: 700; border-bottom: 1px solid var(--c-grid); }
.table-row { border-bottom: 1px solid var(--c-grid); }
.table-row:last-child { border-bottom: none; }
.table-row.correct { background: rgba(76,175,80,0.08); }
.table-row.wrong { background: rgba(244,67,54,0.08); }
.symbol { font-family: var(--font-mono); font-weight: 600; }
.event-name { font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.上涨, .利多 { color: #4CAF50; }
.下跌, .利空 { color: #F44336; }
.震荡, .中性 { color: #666; }
.result-icon { font-size: 1.1rem; text-align: center; }
.table-row.correct .result-icon { color: #4CAF50; }
.table-row.wrong .result-icon { color: #F44336; }

.show-more { width: 100%; padding: 0.5rem; background: var(--c-hover); border: none; cursor: pointer; font-size: 0.85rem; }
.show-more:hover { background: var(--c-grid); }

/* 优化面板样式 */
.optimization-panel .panel-header { background: linear-gradient(135deg, rgba(103,58,183,0.15), rgba(156,39,176,0.15)); }
.opt-content { display: flex; flex-direction: column; gap: 1.5rem; }
.opt-section h5 { margin: 0 0 0.75rem; font-size: 0.9rem; color: var(--c-muted); border-bottom: 1px solid var(--c-grid); padding-bottom: 0.5rem; }
.opt-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.75rem; }
.opt-item { background: var(--c-hover); padding: 0.75rem; border-radius: 4px; }
.opt-label { display: block; font-size: 0.75rem; color: var(--c-muted); margin-bottom: 0.25rem; }
.opt-value { font-family: var(--font-mono); font-size: 1.1rem; font-weight: 700; }

.weight-bars { display: flex; flex-direction: column; gap: 0.5rem; }
.weight-item { display: flex; align-items: center; gap: 0.75rem; }
.weight-label { min-width: 50px; font-size: 0.85rem; font-weight: 600; }
.weight-label.上涨 { color: #4CAF50; }
.weight-label.下跌 { color: #F44336; }
.weight-label.震荡 { color: #9E9E9E; }
.weight-bar-wrap { flex: 1; height: 16px; background: var(--c-grid); border-radius: 3px; overflow: hidden; }
.weight-bar { height: 100%; background: #9C27B0; transition: width 0.3s; }
.weight-bar.boost { background: #4CAF50; }
.weight-bar.reduce { background: #F44336; }
.weight-value { font-family: var(--font-mono); font-size: 0.85rem; min-width: 50px; }

.recommendations { margin: 0; padding-left: 1.25rem; font-size: 0.85rem; }
.recommendations li { margin-bottom: 0.5rem; line-height: 1.4; }

.opt-history { display: flex; flex-direction: column; gap: 0.5rem; }
.history-item { display: flex; justify-content: space-between; padding: 0.5rem 0.75rem; background: var(--c-hover); border-radius: 3px; font-size: 0.85rem; }
.history-date { font-family: var(--font-mono); }
.history-changes { color: var(--c-muted); }

.info-panel { background: var(--c-hover); border: 1px solid var(--c-border); padding: 1rem 1.25rem; margin-top: 1rem; }
.info-panel h4 { margin: 0 0 0.75rem; }
.info-panel ul { margin: 0; padding-left: 1.25rem; }
.info-panel li { margin-bottom: 0.35rem; font-size: 0.9rem; }

.empty { text-align: center; color: var(--c-muted); padding: 2rem 1rem; }

@media (max-width: 768px) {
  .table-header, .table-row { grid-template-columns: 80px 60px 50px 50px 60px 40px; font-size: 0.75rem; }
  .summary-cards { grid-template-columns: 1fr 1fr; }
  .opt-grid { grid-template-columns: 1fr 1fr; }
}
</style>
