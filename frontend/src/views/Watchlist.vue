<template>
  <div class="page-container">
    <header class="page-header">
      <div>
        <div class="page-title-wrapper">ASSET TRACKING</div>
        <h1 class="page-title">自选<span>监控</span></h1>
      </div>
      <div class="meta-bar">
        <span>TOTAL ASSETS: {{ watchlist.length }}</span>
        <span>ALERTS: 0</span>
      </div>
    </header>

    <div class="card">
      <div class="card-header">
        <div class="card-title">我的关注列表</div>
        <div class="actions">
          <div class="add-stock-form">
            <input v-model="newStockSymbol" placeholder="输入代码 (e.g. 002242)" class="input-field sm" @keyup.enter="addStock" />
            <button class="btn btn-sm" @click="addStock">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
              添加
            </button>
          </div>
        </div>
      </div>
      <div class="card-body">
        <table class="data-table">
          <thead>
            <tr>
              <th>代码</th>
              <th>名称</th>
              <th>最新价</th>
              <th>涨跌幅</th>
              <th>成交量</th>
              <th>更新时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="7" class="text-center">加载中...</td>
            </tr>
            <tr v-else-if="watchlist.length === 0">
              <td colspan="7" class="text-center">暂无关注股票，请添加。</td>
            </tr>
            <tr v-for="stock in watchlist" :key="stock.symbol" class="stock-row" @click="openDetail(stock)">
              <td><span class="badge badge-gray">{{ stock.symbol }}</span></td>
              <td><strong>{{ stock.name }}</strong></td>
              <td class="font-mono">{{ formatPrice(stock.price) }}</td>
              <td>
                <span :class="getChangeClass(stock.change_percent)">
                  {{ formatChangePercent(stock.change_percent) }}
                </span>
              </td>
              <td class="font-mono">{{ formatVolume(stock.volume) }}</td>
              <td class="font-mono text-sm">{{ stock.timestamp }}</td>
              <td>
                <button class="btn btn-sm btn-ghost" @click.stop="openDetail(stock)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                  </svg>
                  详情
                </button>
                <button class="btn btn-sm btn-ghost btn-del" @click.stop="removeStock(stock.symbol)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                  </svg>
                  删除
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="showDetail" class="modal-overlay" @click.self="closeDetail">
      <div class="modal-card">
        <!-- 头部 -->
        <div class="modal-header">
          <div class="modal-title-row">
            <div class="stock-code-tag">{{ selectedStock?.symbol }}</div>
            <h2 class="stock-title">{{ selectedStock?.name }}</h2>
          </div>
          <button class="close-btn" @click="closeDetail">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <!-- 加载状态 -->
          <div v-if="detailLoading" class="modal-loading">
            <div class="loader-lg"></div>
            <span>正在加载数据...</span>
          </div>

          <template v-else>
          <!-- 行情面板 -->
          <div class="quote-panel" v-if="detailData.quote">
            <div class="quote-main">
              <div class="quote-price-section">
                <div class="label-tag">实时报价</div>
                <div class="big-price" :class="detailData.quote.change >= 0 ? 'price-up' : 'price-down'">
                  {{ formatPrice(detailData.quote.price) }}
                </div>
                <div class="price-delta">
                  <span :class="detailData.quote.change >= 0 ? 'delta-up' : 'delta-down'">
                    {{ detailData.quote.change >= 0 ? '↑' : '↓' }}
                    {{ Math.abs(detailData.quote.change || 0).toFixed(2) }}
                  </span>
                  <span class="pct-badge" :class="detailData.quote.change >= 0 ? 'pct-up' : 'pct-down'">
                    {{ formatChangePercent(detailData.quote.change_pct) }}
                  </span>
                </div>
              </div>
            </div>
            
            <div class="quote-stats-grid">
              <div class="stat-box">
                <div class="stat-name">今开</div>
                <div class="stat-num">{{ formatPrice(detailData.quote.open) }}</div>
              </div>
              <div class="stat-box">
                <div class="stat-name">昨收</div>
                <div class="stat-num">{{ formatPrice(detailData.quote.prev_close) }}</div>
              </div>
              <div class="stat-box">
                <div class="stat-name">最高</div>
                <div class="stat-num price-up">{{ formatPrice(detailData.quote.high) }}</div>
              </div>
              <div class="stat-box">
                <div class="stat-name">最低</div>
                <div class="stat-num price-down">{{ formatPrice(detailData.quote.low) }}</div>
              </div>
              <div class="stat-box">
                <div class="stat-name">成交量</div>
                <div class="stat-num">{{ formatVolume(detailData.quote.volume) }}</div>
              </div>
              <div class="stat-box">
                <div class="stat-name">成交额</div>
                <div class="stat-num">{{ formatAmount(detailData.quote.amount) }}</div>
              </div>
            </div>
          </div>

          <!-- K线图区域 -->
          <div class="chart-panel">
            <div class="panel-header">
              <div class="panel-label">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/></svg>
                K线走势
              </div>
              <div class="period-btns">
                <button 
                  v-for="p in periods" 
                  :key="p.value" 
                  :class="['period-btn', { active: klinePeriod === p.value }]"
                  @click="changeKlinePeriod(p.value)"
                >{{ p.label }}</button>
              </div>
            </div>
            
            <div class="chart-area" ref="klineChartRef">
              <div v-if="klineLoading" class="chart-loading">
                <div class="loader"></div>
                <span>加载中...</span>
              </div>
              <div v-else-if="!detailData.kline || detailData.kline.length === 0" class="chart-empty">
                暂无数据
              </div>
              <canvas v-show="!klineLoading && detailData.kline && detailData.kline.length > 0" ref="klineCanvas"></canvas>
            </div>
          </div>

          <!-- 相关新闻 -->
          <div class="news-panel" v-if="detailData.news && detailData.news.length > 0">
            <div class="panel-header">
              <div class="panel-label">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                相关资讯
              </div>
            </div>
            <div class="news-items">
              <a v-for="(news, idx) in detailData.news.slice(0, 4)" :key="idx" :href="news.url" target="_blank" class="news-row">
                <span class="news-text">{{ news.title }}</span>
                <span class="news-date">{{ news.time }}</span>
              </a>
            </div>
          </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import axios from 'axios'

const watchlist = ref([])
const loading = ref(false)
const newStockSymbol = ref('')

// 详情弹窗相关
const showDetail = ref(false)
const selectedStock = ref(null)
const detailData = ref({ quote: null, kline: [], news: [] })
const detailLoading = ref(false)
const klineLoading = ref(false)
const klinePeriod = ref('daily')
const klineCanvas = ref(null)
const klineChartRef = ref(null)

const periods = [
  { label: '日K', value: 'daily' },
  { label: '周K', value: 'weekly' },
  { label: '月K', value: 'monthly' }
]

const getChangeClass = (change) => {
  if (change > 0) return 'badge badge-green'
  if (change < 0) return 'badge badge-red'
  return 'badge badge-gray'
}

const formatPrice = (price) => {
  if (price === '-' || price === null || price === undefined) return '-'
  return typeof price === 'number' ? price.toFixed(2) : price
}

const formatChangePercent = (change) => {
  if (change === null || change === undefined || change === 0) return '0%'
  const prefix = change > 0 ? '+' : ''
  return `${prefix}${change.toFixed(2)}%`
}

const formatVolume = (vol) => {
  if (!vol) return '-'
  if (vol > 100000000) return (vol / 100000000).toFixed(2) + '亿'
  if (vol > 10000) return (vol / 10000).toFixed(2) + '万'
  return vol
}

const formatAmount = (amt) => {
  if (!amt) return '-'
  if (amt > 100000000) return (amt / 100000000).toFixed(2) + '亿'
  if (amt > 10000) return (amt / 10000).toFixed(2) + '万'
  return amt.toFixed(0)
}

const fetchWatchlist = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/watchlist')
    watchlist.value = res.data.data.map(item => {
      const quote = item.quote || {}
      return {
        symbol: item.symbol,
        name: quote.name || item.name || item.symbol,
        price: quote.price ?? '-',
        change_percent: quote.change_pct ?? 0,
        volume: quote.volume ?? 0,
        timestamp: quote.timestamp ? formatTimestamp(quote.timestamp) : '-'
      }
    })
  } catch (e) {
    console.error(e)
    watchlist.value = []
  } finally {
    loading.value = false
  }
}

const formatTimestamp = (ts) => {
  if (!ts) return '-'
  try {
    const date = new Date(ts)
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return '-'
  }
}

const addStock = async () => {
  if (!newStockSymbol.value) return
  try {
    await axios.post('/api/watchlist', { symbol: newStockSymbol.value })
    newStockSymbol.value = ''
    fetchWatchlist()
  } catch (e) {
    alert('添加失败: ' + (e.response?.data?.error || e.message))
  }
}

const removeStock = async (symbol) => {
  if (!confirm('确定删除?')) return
  try {
    await axios.delete(`/api/watchlist/${symbol}`)
    fetchWatchlist()
  } catch (e) {
    alert('删除失败')
  }
}

// 打开详情弹窗
const openDetail = async (stock) => {
  selectedStock.value = stock
  showDetail.value = true
  detailLoading.value = true
  klinePeriod.value = 'daily'
  
  try {
    // 并行获取详情和K线数据
    const [detailRes, klineRes] = await Promise.all([
      axios.get(`/api/stocks/${stock.symbol}/detail`),
      axios.get(`/api/stocks/${stock.symbol}/kline`, { params: { period: 'daily', limit: 60 } })
    ])
    detailData.value = {
      ...detailRes.data,
      kline: klineRes.data.data || detailRes.data.kline || []
    }
  } catch (e) {
    console.error('获取详情失败:', e)
    detailData.value = { quote: null, kline: [], news: [] }
  } finally {
    detailLoading.value = false
    // 等待DOM更新后再绘制K线图
    await nextTick()
    setTimeout(() => {
      drawKlineChart(detailData.value.kline)
    }, 50)
  }
}

// 关闭详情弹窗
const closeDetail = () => {
  showDetail.value = false
  selectedStock.value = null
  detailData.value = { quote: null, kline: [], news: [] }
}

// 切换K线周期
const changeKlinePeriod = async (period) => {
  if (klinePeriod.value === period || !selectedStock.value) return
  klinePeriod.value = period
  klineLoading.value = true
  
  try {
    const res = await axios.get(`/api/stocks/${selectedStock.value.symbol}/kline`, {
      params: { period, limit: 60 }
    })
    detailData.value.kline = res.data.data || []
  } catch (e) {
    console.error('获取K线失败:', e)
    detailData.value.kline = []
  } finally {
    klineLoading.value = false
    // 等待 DOM 更新后再绘制
    await nextTick()
    setTimeout(() => {
      drawKlineChart(detailData.value.kline)
    }, 50)
  }
}

// 绘制K线图
const drawKlineChart = (klineData) => {
  const canvas = klineCanvas.value
  const container = klineChartRef.value
  if (!canvas || !container || !klineData || klineData.length === 0) return
  
  // 动态设置canvas尺寸
  const rect = container.getBoundingClientRect()
  canvas.width = rect.width
  canvas.height = rect.height
  
  const ctx = canvas.getContext('2d')
  const width = canvas.width
  const height = canvas.height
  const padding = { top: 20, right: 60, bottom: 30, left: 10 }
  const chartWidth = width - padding.left - padding.right
  const chartHeight = height - padding.top - padding.bottom
  
  // 清空画布 - 浅色背景
  ctx.fillStyle = '#fafaf5'
  ctx.fillRect(0, 0, width, height)
  
  // 计算价格范围
  let minPrice = Infinity, maxPrice = -Infinity
  klineData.forEach(d => {
    minPrice = Math.min(minPrice, d.low)
    maxPrice = Math.max(maxPrice, d.high)
  })
  
  // 扩展范围
  const priceRange = maxPrice - minPrice
  minPrice -= priceRange * 0.05
  maxPrice += priceRange * 0.05
  
  const barWidth = Math.max(2, (chartWidth / klineData.length) * 0.7)
  const barGap = chartWidth / klineData.length
  
  // 绘制网格线和价格刻度
  ctx.strokeStyle = 'rgba(0,0,0,0.08)'
  ctx.lineWidth = 1
  ctx.fillStyle = '#666'
  ctx.font = '10px monospace'
  ctx.textAlign = 'right'
  
  for (let i = 0; i <= 4; i++) {
    const y = padding.top + (chartHeight / 4) * i
    const price = maxPrice - ((maxPrice - minPrice) / 4) * i
    
    ctx.beginPath()
    ctx.moveTo(padding.left, y)
    ctx.lineTo(width - padding.right, y)
    ctx.stroke()
    
    ctx.fillText(price.toFixed(2), width - 5, y + 3)
  }
  
  // 绘制K线
  klineData.forEach((d, i) => {
    const x = padding.left + i * barGap + barGap / 2
    const isUp = d.close >= d.open
    const color = isUp ? '#22a06b' : '#de350b'
    
    // 计算位置
    const openY = padding.top + ((maxPrice - d.open) / (maxPrice - minPrice)) * chartHeight
    const closeY = padding.top + ((maxPrice - d.close) / (maxPrice - minPrice)) * chartHeight
    const highY = padding.top + ((maxPrice - d.high) / (maxPrice - minPrice)) * chartHeight
    const lowY = padding.top + ((maxPrice - d.low) / (maxPrice - minPrice)) * chartHeight
    
    // 绘制影线
    ctx.strokeStyle = color
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(x, highY)
    ctx.lineTo(x, lowY)
    ctx.stroke()
    
    // 绘制实体
    ctx.fillStyle = color
    const bodyTop = Math.min(openY, closeY)
    const bodyHeight = Math.max(1, Math.abs(closeY - openY))
    ctx.fillRect(x - barWidth / 2, bodyTop, barWidth, bodyHeight)
  })
  
  // 绘制日期标签 (显示5个)
  ctx.fillStyle = '#666'
  ctx.font = '9px monospace'
  ctx.textAlign = 'center'
  const step = Math.floor(klineData.length / 5)
  for (let i = 0; i < klineData.length; i += step) {
    if (klineData[i]?.date) {
      const x = padding.left + i * barGap + barGap / 2
      ctx.fillText(klineData[i].date.slice(5), x, height - 10)
    }
  }
}

onMounted(() => {
  fetchWatchlist()
})
</script>

<style scoped>
.add-stock-form {
  display: flex;
  gap: 0.5rem;
}
.input-field.sm {
  padding: 0.4rem 0.8rem;
  width: 200px;
}
.text-center { text-align: center; color: #888; }
.text-sm { font-size: 0.8rem; color: #666; }
.font-mono { font-family: var(--font-mono); }

.stock-row {
  cursor: pointer;
  transition: background 0.2s;
}
.stock-row:hover {
  background: rgba(255, 85, 0, 0.05);
}

/* 列表操作按钮 */
.btn-ghost {
  background: transparent;
  border: 2px solid var(--c-ink, #111);
  color: var(--c-ink, #111);
}
.btn-ghost:hover {
  background: var(--c-ink, #111);
  color: var(--c-bg, #F2F2E9);
}
.btn-del:hover {
  background: #de350b;
  border-color: #de350b;
  color: #fff;
}
.btn-sm.btn-ghost {
  margin-right: 0.4rem;
}

/* ==================== 报刊风格弹窗 ==================== */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 2rem;
}

.modal-card {
  background: var(--c-paper, #fff);
  border: 3px solid var(--c-ink, #111);
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 12px 12px 0 rgba(0, 0, 0, 0.2);
  position: relative;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 3px solid var(--c-ink, #111);
  background: rgba(0, 0, 0, 0.02);
}

.modal-title-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stock-code-tag {
  background: var(--c-ink, #111);
  color: var(--c-bg, #F2F2E9);
  padding: 0.3rem 0.8rem;
  font-family: var(--font-mono);
  font-size: 0.85rem;
  font-weight: 700;
}

.stock-title {
  margin: 0;
  font-family: var(--font-display, 'Oswald', sans-serif);
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--c-ink, #111);
  text-transform: uppercase;
}

.close-btn {
  background: transparent;
  border: 2px solid var(--c-ink, #111);
  color: var(--c-ink, #111);
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--c-ink, #111);
  color: var(--c-paper, #fff);
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0 var(--c-amber, #FF5500);
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  background-image: 
    linear-gradient(var(--c-grid, #E0E0D8) 1px, transparent 1px),
    linear-gradient(90deg, var(--c-grid, #E0E0D8) 1px, transparent 1px);
  background-size: 20px 20px;
}

/* 行情面板 */
.quote-panel {
  background: var(--c-paper, #fff);
  border: 2px solid var(--c-ink, #111);
  padding: 1.5rem;
  box-shadow: 6px 6px 0 rgba(0, 0, 0, 0.1);
}

.quote-main {
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px dashed var(--c-ink, #111);
}

.label-tag {
  display: inline-block;
  background: var(--c-ink, #111);
  color: var(--c-bg, #F2F2E9);
  padding: 0.2rem 0.6rem;
  font-size: 0.7rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
}

.big-price {
  font-family: var(--font-mono);
  font-size: 3rem;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 0.5rem;
}

.price-up { color: #4CAF50; }
.price-down { color: #F44336; }

.price-delta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.delta-up { color: #4CAF50; font-family: var(--font-mono); font-weight: 700; }
.delta-down { color: #F44336; font-family: var(--font-mono); font-weight: 700; }

.pct-badge {
  padding: 0.2rem 0.5rem;
  font-family: var(--font-mono);
  font-size: 0.85rem;
  font-weight: 700;
}
.pct-up { background: rgba(76, 175, 80, 0.15); color: #4CAF50; }
.pct-down { background: rgba(244, 67, 54, 0.15); color: #F44336; }

.quote-stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.stat-box {
  padding: 0.75rem;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: rgba(0, 0, 0, 0.02);
}

.stat-name {
  font-size: 0.7rem;
  color: #666;
  text-transform: uppercase;
  font-weight: 700;
  margin-bottom: 0.3rem;
}

.stat-num {
  font-family: var(--font-mono);
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--c-ink, #111);
}

/* 图表面板 */
.chart-panel, .news-panel {
  background: var(--c-paper, #fff);
  border: 2px solid var(--c-ink, #111);
  box-shadow: 6px 6px 0 rgba(0, 0, 0, 0.1);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 2px solid var(--c-ink, #111);
  background: rgba(0, 0, 0, 0.02);
}

.panel-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-family: var(--font-display, 'Oswald', sans-serif);
  font-size: 1rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--c-ink, #111);
}

.panel-label svg {
  color: var(--c-amber, #FF5500);
}

.period-btns {
  display: flex;
  gap: 0;
}

.period-btn {
  background: var(--c-paper, #fff);
  border: 2px solid var(--c-ink, #111);
  border-left-width: 0;
  color: var(--c-ink, #111);
  padding: 0.3rem 0.8rem;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s;
}

.period-btn:first-child {
  border-left-width: 2px;
}

.period-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}

.period-btn.active {
  background: var(--c-amber, #FF5500);
  border-color: var(--c-amber, #FF5500);
  color: #fff;
}

.chart-area {
  height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafaf5;
  border-top: none;
  position: relative;
}

.chart-area canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.chart-loading, .chart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  color: #888;
  font-family: var(--font-mono);
  font-size: 0.85rem;
}

.loader {
  width: 28px;
  height: 28px;
  border: 3px solid #ddd;
  border-top-color: var(--c-amber, #FF5500);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* 弹窗加载状态 */
.modal-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 4rem 2rem;
  color: #666;
  font-family: var(--font-mono);
  font-size: 0.9rem;
}

.loader-lg {
  width: 48px;
  height: 48px;
  border: 4px solid #e0e0e0;
  border-top-color: var(--c-amber, #FF5500);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 新闻区域 */
.news-items {
  padding: 0;
}

.news-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.9rem 1rem;
  border-bottom: 1px dashed rgba(0, 0, 0, 0.15);
  text-decoration: none;
  color: var(--c-ink, #111);
  transition: all 0.15s;
}

.news-row:last-child {
  border-bottom: none;
}

.news-row:hover {
  background: rgba(255, 85, 0, 0.05);
  padding-left: 1.5rem;
}

.news-text {
  flex: 1;
  font-size: 0.9rem;
  line-height: 1.4;
}

.news-row:hover .news-text {
  color: var(--c-amber, #FF5500);
}

.news-date {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: #888;
  white-space: nowrap;
}
</style>
