<template>
  <div class="weekly-summary-page">
    <header class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>
        </div>
        <div class="header-text">
          <span class="page-title">{{ t('weekly_summary_title') }}</span>
          <span class="page-subtitle">WEEKLY STOCK ANALYSIS</span>
        </div>
      </div>
      <div class="header-actions">
        <select v-model="selectedFile" class="file-selector" @change="loadAnalysis">
          <option v-for="file in analysisFiles" :key="file" :value="file">{{ formatFileName(file) }}</option>
        </select>
        <button class="refresh-btn" @click="refreshData" :disabled="loading">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6"></path><path d="M1 20v-6h6"></path>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
          </svg>
        </button>
      </div>
    </header>

    <div v-if="loading" class="loading-overlay"><div class="spinner"></div><span>{{ t('loading') }}</span></div>
    <div v-else-if="error" class="error-container"><p class="error-text">{{ error }}</p><button class="retry-btn" @click="refreshData">{{ t('retry') }}</button></div>

    <div v-else-if="analysisData" class="analysis-content">
      <div class="kpi-bar">
        <div class="kpi-item bullish">
          <div class="kpi-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg></div>
          <div class="kpi-content"><div class="kpi-label">{{ t('bullish_count') }}</div><div class="kpi-value text-green">{{ stats.bullish }}</div></div>
        </div>
        <div class="kpi-item bearish">
          <div class="kpi-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline><polyline points="17 18 23 18 23 12"></polyline></svg></div>
          <div class="kpi-content"><div class="kpi-label">{{ t('bearish_count') }}</div><div class="kpi-value text-red">{{ stats.bearish }}</div></div>
        </div>
        <div class="kpi-item sideways">
          <div class="kpi-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"></line></svg></div>
          <div class="kpi-content"><div class="kpi-label">{{ t('sideways_count') }}</div><div class="kpi-value text-orange">{{ stats.sideways }}</div></div>
        </div>
        <div class="kpi-item">
          <div class="kpi-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg></div>
          <div class="kpi-content"><div class="kpi-label">{{ t('total_stocks') }}</div><div class="kpi-value">{{ stats.total }}</div></div>
        </div>
      </div>

      <div class="main-grid">
        <div class="col-main">
          <div class="panel">
            <div class="panel-header">
              <div class="panel-title"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:8px;vertical-align:text-bottom;"><circle cx="12" cy="12" r="10"></circle><path d="M12 2v20M2 12h20"></path></svg>{{ t('prediction_distribution') }}</div>
            </div>
            <div class="panel-body">
              <div class="distribution-visual">
                <div class="dist-bar"><div class="bar-bullish" :style="{width: bullishPercent+'%'}"></div><div class="bar-bearish" :style="{width: bearishPercent+'%'}"></div><div class="bar-sideways" :style="{width: sidewaysPercent+'%'}"></div></div>
                <div class="distribution-row">
                  <div class="dist-item positive"><div class="dist-value">{{ stats.bullish }}</div><div class="dist-label">{{ t('bullish') }} ({{ bullishPercent }}%)</div></div>
                  <div class="dist-item negative"><div class="dist-value">{{ stats.bearish }}</div><div class="dist-label">{{ t('bearish') }} ({{ bearishPercent }}%)</div></div>
                  <div class="dist-item neutral"><div class="dist-value">{{ stats.sideways }}</div><div class="dist-label">{{ t('sideways') }} ({{ sidewaysPercent }}%)</div></div>
                </div>
              </div>
            </div>
          </div>

          <div class="panel">
            <div class="panel-header">
              <div class="panel-title"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:8px;vertical-align:text-bottom;"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>{{ t('stock_predictions') }}</div>
              <div class="panel-tag">{{ analysisData.stocks?.length || 0 }} {{ t('unit_count') }}</div>
            </div>
            <div class="panel-body">
              <div v-if="!analysisData.stocks?.length" class="empty-state">{{ t('no_stock_data') }}</div>
              <div v-else class="stock-table-wrap">
                <table class="stock-table">
                  <thead><tr><th>{{ t('symbol') }}</th><th>{{ t('stock_name') }}</th><th>{{ t('prediction') }}</th><th>{{ t('confidence') }}</th><th>{{ t('reason') }}</th></tr></thead>
                  <tbody>
                    <tr v-for="stock in analysisData.stocks" :key="stock.symbol">
                      <td class="symbol-cell">{{ stock.symbol }}</td>
                      <td>{{ stock.name }}</td>
                      <td><span class="pred-tag" :class="getPredClass(stock.prediction)">{{ translatePred(stock.prediction) }}</span></td>
                      <td><span class="conf-tag" :class="getConfClass(stock.confidence)">{{ translateConf(stock.confidence) }}</span></td>
                      <td class="reason-cell">{{ stock.reason }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <div class="col-side">
          <div class="panel">
            <div class="panel-header bullish-header"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:8px;"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline></svg>{{ t('top_bullish') }}</div>
            <div class="panel-body">
              <div v-if="topBullish.length===0" class="empty-state">{{ t('no_bullish_stocks') }}</div>
              <div v-else class="recommend-list">
                <div v-for="s in topBullish" :key="s.symbol" class="recommend-item bullish">
                  <span class="rec-symbol">{{ s.symbol }}</span><span class="rec-name">{{ s.name }}</span><span class="rec-conf">{{ translateConf(s.confidence) }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="panel">
            <div class="panel-header bearish-header"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:8px;"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline></svg>{{ t('top_bearish') }}</div>
            <div class="panel-body">
              <div v-if="topBearish.length===0" class="empty-state">{{ t('no_bearish_stocks') }}</div>
              <div v-else class="recommend-list">
                <div v-for="s in topBearish" :key="s.symbol" class="recommend-item bearish">
                  <span class="rec-symbol">{{ s.symbol }}</span><span class="rec-name">{{ s.name }}</span><span class="rec-conf">{{ translateConf(s.confidence) }}</span>
                </div>
              </div>
            </div>
          </div>
          <div v-if="analysisData.summary" class="panel">
            <div class="panel-header"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:8px;vertical-align:text-bottom;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>{{ t('market_summary') }}</div>
            <div class="panel-body"><p class="summary-text">{{ analysisData.summary }}</p><div class="summary-meta">{{ t('generated_at') }}: {{ analysisData.generated_at }}</div></div>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="empty-container"><p>{{ t('no_analysis_data') }}</p></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useLocale } from '../composables/useLocale'
const { t, locale } = useLocale()

const loading = ref(false), error = ref(null), analysisFiles = ref([]), selectedFile = ref(''), analysisData = ref(null)

const stats = computed(() => {
  if (!analysisData.value?.stocks) return { bullish: 0, bearish: 0, sideways: 0, total: 0 }
  const s = analysisData.value.stocks
  return { bullish: s.filter(x => x.prediction === '上涨').length, bearish: s.filter(x => x.prediction === '下跌').length, sideways: s.filter(x => x.prediction === '震荡').length, total: s.length }
})

const bullishPercent = computed(() => stats.value.total ? Math.round(stats.value.bullish / stats.value.total * 100) : 0)
const bearishPercent = computed(() => stats.value.total ? Math.round(stats.value.bearish / stats.value.total * 100) : 0)
const sidewaysPercent = computed(() => stats.value.total ? Math.round(stats.value.sideways / stats.value.total * 100) : 0)

const topBullish = computed(() => (analysisData.value?.stocks || []).filter(s => s.prediction === '上涨' && s.confidence !== '低').slice(0, 5))
const topBearish = computed(() => (analysisData.value?.stocks || []).filter(s => s.prediction === '下跌' && s.confidence !== '低').slice(0, 5))

const formatFileName = (f) => { const m = f.match(/analysis_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})/); return m ? `${m[1]}-${m[2]}-${m[3]} ${m[4]}:${m[5]}` : f }
const translatePred = (p) => locale.value === 'en' ? ({ '上涨': 'Bullish', '下跌': 'Bearish', '震荡': 'Sideways' }[p] || p) : p
const translateConf = (c) => locale.value === 'en' ? ({ '高': 'High', '中': 'Medium', '低': 'Low' }[c] || c) : c
const getPredClass = (p) => ({ '上涨': 'bullish', '下跌': 'bearish', '震荡': 'sideways' }[p] || '')
const getConfClass = (c) => ({ '高': 'high', '中': 'medium', '低': 'low' }[c] || '')

const loadAnalysisFiles = async () => { try { const r = await fetch('/api/weekly_analysis'); if (r.ok) { const d = await r.json(); if (d.files?.length) { analysisFiles.value = d.files; selectedFile.value = d.files[0] } } } catch (e) { console.error(e) } }
const loadAnalysis = async () => { if (!selectedFile.value) return; loading.value = true; error.value = null; try { const r = await fetch(`/api/weekly_analysis?file=${selectedFile.value}`); if (r.ok) analysisData.value = await r.json(); else throw new Error('Failed') } catch (e) { error.value = e.message } finally { loading.value = false } }
const refreshData = async () => { await loadAnalysisFiles(); if (selectedFile.value) await loadAnalysis() }
onMounted(() => refreshData())
</script>

<style scoped>
.weekly-summary-page { max-width: 1800px; margin: 0 auto; padding: 1rem 2rem; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 2px solid var(--c-ink); padding-bottom: 1rem; }
.header-left { display: flex; align-items: center; gap: 1rem; }
.header-icon { background: var(--c-ink); color: var(--c-bg); width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; }
.header-text { display: flex; flex-direction: column; }
.page-title { font-family: var(--font-display); font-size: 1.5rem; font-weight: 700; line-height: 1; }
.page-subtitle { font-size: 0.7rem; letter-spacing: 0.2em; color: var(--c-amber); font-weight: 700; }
.header-actions { display: flex; gap: 0.75rem; align-items: center; }
.file-selector { padding: 0.5rem 1rem; border: 2px solid var(--c-border); background: var(--c-paper); font-family: var(--font-mono); font-size: 0.85rem; cursor: pointer; }
.refresh-btn { background: var(--c-ink); border: 2px solid var(--c-ink); color: var(--c-bg); cursor: pointer; padding: 0.5rem; display: flex; align-items: center; justify-content: center; transition: all 0.15s; box-shadow: 3px 3px 0 var(--c-shadow); }
.refresh-btn:hover:not(:disabled) { transform: translate(-1px, -1px); box-shadow: 4px 4px 0 var(--c-shadow); }
.refresh-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.loading-overlay, .error-container, .empty-container { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4rem; gap: 1rem; color: var(--c-muted); }
.spinner { width: 40px; height: 40px; border: 4px solid var(--c-grid); border-top-color: var(--c-amber); border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.error-text { color: #F44336; margin-bottom: 1rem; }
.retry-btn { padding: 0.5rem 1rem; border: 2px solid var(--c-ink); background: transparent; cursor: pointer; }
.kpi-bar { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; margin-bottom: 2rem; }
.kpi-item { background: var(--c-paper); border: 2px solid var(--c-ink); padding: 1rem; display: flex; align-items: center; gap: 1rem; box-shadow: 4px 4px 0 rgba(0,0,0,0.1); }
.kpi-item.bullish { border-color: #4CAF50; }
.kpi-item.bearish { border-color: #F44336; }
.kpi-item.sideways { border-color: #FF9800; }
.kpi-icon { width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; }
.kpi-content { flex: 1; }
.kpi-label { font-size: 0.7rem; font-weight: 700; color: #888; letter-spacing: 0.05em; }
.kpi-value { font-family: var(--font-mono); font-size: 1.5rem; font-weight: 700; color: var(--c-ink); }
.text-green { color: #4CAF50; }
.text-red { color: #F44336; }
.text-orange { color: #FF9800; }
.main-grid { display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1fr); gap: 2rem; }
.col-main, .col-side { display: flex; flex-direction: column; gap: 2rem; min-width: 0; }
.panel { background: var(--c-paper); border: 2px solid var(--c-border); box-shadow: 4px 4px 0 var(--c-shadow); }
.panel-header { background: var(--c-hover); border-bottom: 1px solid var(--c-border); padding: 0.75rem 1rem; display: flex; justify-content: space-between; align-items: center; }
.panel-header.bullish-header { background: rgba(76, 175, 80, 0.15); color: #4CAF50; }
.panel-header.bearish-header { background: rgba(244, 67, 54, 0.15); color: #F44336; }
.panel-title { font-family: var(--font-display); font-weight: 700; font-size: 1rem; }
.panel-tag { font-family: var(--font-mono); font-size: 0.7rem; background: var(--c-ink); color: var(--c-bg); padding: 0.2rem 0.5rem; }
.panel-body { padding: 1.5rem; }
.distribution-visual { }
.dist-bar { height: 24px; display: flex; border: 1px solid var(--c-border); overflow: hidden; margin-bottom: 1rem; }
.bar-bullish { background: #4CAF50; }
.bar-bearish { background: #F44336; }
.bar-sideways { background: #FF9800; }
.distribution-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; background: var(--c-hover); padding: 1rem; border: 1px solid var(--c-grid); }
.dist-item { text-align: center; }
.dist-value { font-family: var(--font-mono); font-size: 1.5rem; font-weight: 700; }
.dist-item.positive .dist-value { color: #4CAF50; }
.dist-item.negative .dist-value { color: #F44336; }
.dist-item.neutral .dist-value { color: #FF9800; }
.dist-label { font-size: 0.75rem; color: var(--c-muted); }
.stock-table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; width: 100%; }
.stock-table { width: 100%; border-collapse: collapse; min-width: 600px; }
.stock-table th, .stock-table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid var(--c-grid); vertical-align: top; }
.stock-table th { font-family: var(--font-display); font-weight: 700; text-transform: uppercase; font-size: 0.75rem; background: var(--c-hover); white-space: nowrap; }
.symbol-cell { font-family: var(--font-mono); font-weight: 700; white-space: nowrap; }
.reason-cell { font-size: 0.85rem; color: var(--c-muted); min-width: 200px; word-break: break-word; white-space: normal; }
.pred-tag { padding: 0.2rem 0.5rem; font-size: 0.75rem; font-weight: 700; white-space: nowrap; display: inline-block; }
.pred-tag.bullish { background: rgba(76,175,80,0.15); color: #4CAF50; }
.pred-tag.bearish { background: rgba(244,67,54,0.15); color: #F44336; }
.pred-tag.sideways { background: rgba(255,152,0,0.15); color: #FF9800; }
.conf-tag { padding: 0.2rem 0.5rem; font-size: 0.75rem; font-weight: 700; white-space: nowrap; display: inline-block; }
.conf-tag.high { background: rgba(76,175,80,0.15); color: #4CAF50; }
.conf-tag.medium { background: rgba(255,152,0,0.15); color: #FF9800; }
.conf-tag.low { background: var(--c-hover); color: var(--c-muted); }
.recommend-list { display: flex; flex-direction: column; gap: 0.5rem; }
.recommend-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem; background: var(--c-hover); border: 1px solid var(--c-grid); }
.recommend-item.bullish { border-left: 3px solid #4CAF50; }
.recommend-item.bearish { border-left: 3px solid #F44336; }
.rec-symbol { font-family: var(--font-mono); font-weight: 700; min-width: 70px; }
.rec-name { flex: 1; }
.rec-conf { font-size: 0.75rem; padding: 0.2rem 0.5rem; background: var(--c-paper); border: 1px solid var(--c-border); }
.summary-text { line-height: 1.6; margin-bottom: 1rem; }
.summary-meta { font-size: 0.75rem; color: var(--c-muted); font-family: var(--font-mono); }
.empty-state { text-align: center; padding: 2rem; color: var(--c-muted); }
@media (max-width: 1200px) { .main-grid { grid-template-columns: minmax(0, 1fr); } .kpi-bar { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 768px) { .weekly-summary-page { padding: 0; overflow-x: hidden; } .page-header { flex-direction: column; align-items: flex-start; gap: 1rem; padding: 1rem; } .header-actions { width: 100%; } .file-selector { flex: 1; } .kpi-bar { grid-template-columns: 1fr; padding: 0 1rem; } .distribution-row { grid-template-columns: 1fr; } .panel { border-left: none; border-right: none; box-shadow: none; border-radius: 0; } .panel-body { padding: 1rem; } }
</style>
