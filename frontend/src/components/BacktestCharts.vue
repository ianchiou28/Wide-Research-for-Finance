<template>
  <div class="charts-section" v-if="hasData">
    <!-- 可视化面板标题 -->
    <div class="panel charts-panel">
      <div class="panel-header" @click="showCharts = !showCharts">
        <div class="panel-title-wrap">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
            <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
            <line x1="12" y1="22.08" x2="12" y2="12"></line>
          </svg>
          <span class="panel-title">数据可视化</span>
          <span class="chart-count">{{ chartCount }} 张图表</span>
        </div>
        <span class="toggle-icon" :class="{ open: showCharts }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </span>
      </div>
      <div v-show="showCharts" class="panel-body">
        <div class="charts-grid">
          
          <!-- 图1: 方向偏差对比 -->
          <div class="chart-card" v-if="charts.direction_bias">
            <div class="chart-title">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M12 2a10 10 0 0 1 0 20"></path>
              </svg>
              预测 vs 实际方向分布
            </div>
            <v-chart :option="directionBiasOption" class="chart" autoresize />
          </div>

          <!-- 图2: 混淆矩阵热力图 -->
          <div class="chart-card" v-if="charts.direction_bias?.confusion">
            <div class="chart-title">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="7" height="7"></rect>
                <rect x="14" y="3" width="7" height="7"></rect>
                <rect x="14" y="14" width="7" height="7"></rect>
                <rect x="3" y="14" width="7" height="7"></rect>
              </svg>
              预测混淆矩阵
            </div>
            <v-chart :option="confusionOption" class="chart" autoresize />
          </div>

          <!-- 图3: 涨跌幅分布直方图 -->
          <div class="chart-card wide" v-if="charts.return_distribution?.bins?.length">
            <div class="chart-title">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 20V10"></path><path d="M18 20V4"></path><path d="M6 20v-4"></path>
              </svg>
              涨跌幅分布 (正确 vs 错误)
            </div>
            <v-chart :option="returnDistOption" class="chart" autoresize />
          </div>

          <!-- 图4: 个股胜率排名 -->
          <div class="chart-card tall" v-if="charts.symbol_win_rate?.top?.length">
            <div class="chart-title">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="20" x2="18" y2="10"></line>
                <line x1="12" y1="20" x2="12" y2="4"></line>
                <line x1="6" y1="20" x2="6" y2="14"></line>
              </svg>
              个股胜率排名 TOP
            </div>
            <v-chart :option="symbolRankOption" class="chart chart-tall" autoresize />
          </div>

          <!-- 图5: 置信度分层效果 -->
          <div class="chart-card" v-if="charts.confidence_strat">
            <div class="chart-title">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
              </svg>
              置信度 vs 准确率
            </div>
            <v-chart :option="confidenceOption" class="chart" autoresize />
          </div>

          <!-- 图6: 模拟资金曲线 -->
          <div class="chart-card wide" v-if="charts.equity_curve?.length > 1">
            <div class="chart-title">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
              </svg>
              模拟交易资金曲线
            </div>
            <v-chart :option="equityCurveOption" class="chart" autoresize />
          </div>

          <!-- 图7: 准确率趋势 -->
          <div class="chart-card wide" v-if="charts.accuracy_trend?.length > 1">
            <div class="chart-title">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
                <polyline points="17 6 23 6 23 12"></polyline>
              </svg>
              各期准确率趋势
            </div>
            <v-chart :option="accuracyTrendOption" class="chart" autoresize />
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart, LineChart, HeatmapChart, ScatterChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  VisualMapComponent,
  MarkLineComponent,
  DataZoomComponent,
} from 'echarts/components'

use([
  CanvasRenderer,
  PieChart, BarChart, LineChart, HeatmapChart, ScatterChart,
  TitleComponent, TooltipComponent, LegendComponent, GridComponent,
  VisualMapComponent, MarkLineComponent, DataZoomComponent,
])

const props = defineProps({
  charts: {
    type: Object,
    default: () => ({})
  }
})

const showCharts = ref(true)

const hasData = computed(() => {
  return props.charts && Object.keys(props.charts).length > 0
})

const chartCount = computed(() => {
  let count = 0
  if (props.charts.direction_bias) count += 2  // pie + confusion
  if (props.charts.return_distribution?.bins?.length) count++
  if (props.charts.symbol_win_rate?.top?.length) count++
  if (props.charts.confidence_strat) count++
  if (props.charts.equity_curve?.length > 1) count++
  if (props.charts.accuracy_trend?.length > 1) count++
  return count
})

// ============ 主题色 ============
const colors = {
  up: '#4CAF50',
  down: '#F44336',
  neutral: '#9E9E9E',
  amber: '#FF9800',
  blue: '#2196F3',
  purple: '#9C27B0',
  bg: 'transparent',
  text: '#e0e0e0',
  subtext: '#888',
  grid: 'rgba(255,255,255,0.08)',
  axis: 'rgba(255,255,255,0.2)',
}

// ============ 图1: 方向偏差环形图 ============
const directionBiasOption = computed(() => {
  const db = props.charts.direction_bias
  if (!db) return {}
  const dmap = { '上涨': colors.up, '下跌': colors.down, '震荡': colors.neutral }
  return {
    tooltip: { trigger: 'item', backgroundColor: '#1a1a2e', borderColor: '#333', textStyle: { color: '#e0e0e0' } },
    legend: { bottom: 0, textStyle: { color: colors.subtext, fontSize: 11 } },
    series: [
      {
        name: '预测分布',
        type: 'pie',
        radius: ['30%', '55%'],
        center: ['30%', '45%'],
        label: {
          show: true,
          formatter: '{b}\n{d}%',
          color: colors.text,
          fontSize: 11,
        },
        data: ['上涨', '下跌', '震荡'].map(d => ({
          name: d,
          value: db.predicted[d] || 0,
          itemStyle: { color: dmap[d] }
        })).filter(d => d.value > 0),
        emphasis: { label: { fontSize: 14, fontWeight: 'bold' } },
      },
      {
        name: '实际分布',
        type: 'pie',
        radius: ['30%', '55%'],
        center: ['72%', '45%'],
        label: {
          show: true,
          formatter: '{b}\n{d}%',
          color: colors.text,
          fontSize: 11,
        },
        data: ['上涨', '下跌', '震荡'].map(d => ({
          name: d,
          value: db.actual[d] || 0,
          itemStyle: { color: dmap[d] }
        })).filter(d => d.value > 0),
        emphasis: { label: { fontSize: 14, fontWeight: 'bold' } },
      },
    ],
    graphic: [
      { type: 'text', left: '22%', top: '12%', style: { text: '预测方向', fill: colors.amber, fontSize: 13, fontWeight: 'bold' } },
      { type: 'text', left: '64%', top: '12%', style: { text: '实际方向', fill: colors.blue, fontSize: 13, fontWeight: 'bold' } },
    ],
  }
})

// ============ 图2: 混淆矩阵热力图 ============
const confusionOption = computed(() => {
  const db = props.charts.direction_bias
  if (!db?.confusion) return {}

  const labels = ['上涨', '下跌', '震荡']
  const data = []
  let maxVal = 0

  for (let pi = 0; pi < labels.length; pi++) {
    for (let ai = 0; ai < labels.length; ai++) {
      const val = (db.confusion[labels[pi]] || {})[labels[ai]] || 0
      data.push([ai, pi, val])
      if (val > maxVal) maxVal = val
    }
  }

  return {
    tooltip: {
      backgroundColor: '#1a1a2e', borderColor: '#333', textStyle: { color: '#e0e0e0' },
      formatter: (p) => `预测: ${labels[p.value[1]]}<br/>实际: ${labels[p.value[0]]}<br/>数量: <b>${p.value[2]}</b>`
    },
    grid: { top: 30, bottom: 40, left: 70, right: 30 },
    xAxis: { type: 'category', data: labels, name: '实际方向', nameLocation: 'middle', nameGap: 25, axisLabel: { color: colors.text }, nameTextStyle: { color: colors.subtext }, splitArea: { show: false } },
    yAxis: { type: 'category', data: labels, name: '预测方向', nameLocation: 'middle', nameGap: 50, axisLabel: { color: colors.text }, nameTextStyle: { color: colors.subtext }, splitArea: { show: false } },
    visualMap: {
      min: 0, max: maxVal || 1,
      calculable: false, show: false,
      inRange: { color: ['#1a1a2e', '#2196F3', '#FF9800', '#F44336'] }
    },
    series: [{
      type: 'heatmap',
      data: data,
      label: { show: true, color: '#fff', fontSize: 14, fontWeight: 'bold' },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' } },
      itemStyle: { borderColor: '#111', borderWidth: 2, borderRadius: 4 },
    }],
  }
})

// ============ 图3: 涨跌幅分布 ============
const returnDistOption = computed(() => {
  const rd = props.charts.return_distribution
  if (!rd?.bins?.length) return {}

  return {
    tooltip: {
      trigger: 'axis', backgroundColor: '#1a1a2e', borderColor: '#333', textStyle: { color: '#e0e0e0' },
      axisPointer: { type: 'shadow' }
    },
    legend: { data: ['预测正确', '预测错误'], textStyle: { color: colors.subtext, fontSize: 11 }, top: 5, right: 10 },
    grid: { top: 40, bottom: 30, left: 50, right: 20 },
    xAxis: {
      type: 'category', data: rd.bins,
      axisLabel: { color: colors.text, fontSize: 10, rotate: 30 },
      axisLine: { lineStyle: { color: colors.axis } },
    },
    yAxis: {
      type: 'value', name: '次数',
      nameTextStyle: { color: colors.subtext },
      axisLabel: { color: colors.text },
      splitLine: { lineStyle: { color: colors.grid } },
      axisLine: { lineStyle: { color: colors.axis } },
    },
    series: [
      {
        name: '预测正确', type: 'bar', stack: 'total',
        data: rd.correct,
        itemStyle: { color: colors.up, borderRadius: [2, 2, 0, 0] },
      },
      {
        name: '预测错误', type: 'bar', stack: 'total',
        data: rd.wrong,
        itemStyle: { color: colors.down, borderRadius: [2, 2, 0, 0] },
      },
    ],
  }
})

// ============ 图4: 个股胜率排名 ============
const symbolRankOption = computed(() => {
  const sr = props.charts.symbol_win_rate
  if (!sr?.top?.length) return {}

  const items = sr.top.slice(0, 15)
  const symbols = items.map(s => `${s.symbol} (${s.total})`).reverse()
  const rates = items.map(s => s.win_rate).reverse()

  return {
    tooltip: {
      trigger: 'axis', backgroundColor: '#1a1a2e', borderColor: '#333', textStyle: { color: '#e0e0e0' },
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const idx = items.length - 1 - params[0].dataIndex
        const item = items[idx]
        return `<b>${item.symbol}</b> ${item.name}<br/>胜率: ${item.win_rate}%<br/>正确/总数: ${item.correct}/${item.total}`
      }
    },
    grid: { top: 10, bottom: 30, left: 100, right: 40 },
    xAxis: {
      type: 'value', max: 100, name: '胜率 %',
      nameTextStyle: { color: colors.subtext },
      axisLabel: { color: colors.text, formatter: '{value}%' },
      splitLine: { lineStyle: { color: colors.grid } },
      axisLine: { lineStyle: { color: colors.axis } },
    },
    yAxis: {
      type: 'category', data: symbols,
      axisLabel: { color: colors.text, fontSize: 11 },
      axisLine: { lineStyle: { color: colors.axis } },
    },
    series: [{
      type: 'bar',
      data: rates.map(r => ({
        value: r,
        itemStyle: {
          color: r >= 60 ? colors.up : r >= 40 ? colors.amber : colors.down,
          borderRadius: [0, 4, 4, 0],
        }
      })),
      barWidth: '60%',
      label: { show: true, position: 'right', color: colors.text, formatter: '{c}%', fontSize: 11 },
      markLine: {
        silent: true,
        data: [{ xAxis: 50, label: { show: true, formatter: '50%', color: colors.subtext, position: 'end' }, lineStyle: { color: '#666', type: 'dashed' } }]
      },
    }],
  }
})

// ============ 图5: 置信度分层效果 ============
const confidenceOption = computed(() => {
  const cs = props.charts.confidence_strat
  if (!cs) return {}

  const labels = ['高置信度\n(>60%)', '中置信度\n(30-60%)', '低置信度\n(<30%)']
  const keys = ['high', 'medium', 'low']
  const accuracies = keys.map(k => cs[k]?.accuracy || 0)
  const totals = keys.map(k => cs[k]?.total || 0)
  const corrects = keys.map(k => cs[k]?.correct || 0)

  return {
    tooltip: {
      trigger: 'axis', backgroundColor: '#1a1a2e', borderColor: '#333', textStyle: { color: '#e0e0e0' },
      formatter: (params) => {
        const idx = params[0].dataIndex
        return `${['高', '中', '低'][idx]}置信度<br/>准确率: <b>${accuracies[idx]}%</b><br/>正确/总数: ${corrects[idx]}/${totals[idx]}`
      }
    },
    grid: { top: 30, bottom: 40, left: 50, right: 30 },
    xAxis: {
      type: 'category', data: labels,
      axisLabel: { color: colors.text, fontSize: 11 },
      axisLine: { lineStyle: { color: colors.axis } },
    },
    yAxis: {
      type: 'value', max: 100, name: '准确率 %',
      nameTextStyle: { color: colors.subtext },
      axisLabel: { color: colors.text },
      splitLine: { lineStyle: { color: colors.grid } },
      axisLine: { lineStyle: { color: colors.axis } },
    },
    series: [
      {
        type: 'bar',
        data: accuracies.map((a, i) => ({
          value: a,
          itemStyle: {
            color: i === 0 ? colors.blue : i === 1 ? colors.amber : colors.neutral,
            borderRadius: [4, 4, 0, 0],
          }
        })),
        barWidth: '50%',
        label: {
          show: true, position: 'top', color: colors.text, fontSize: 13, fontWeight: 'bold',
          formatter: (p) => `${p.value}%\n(${totals[p.dataIndex]}条)`
        },
        markLine: {
          silent: true,
          data: [{ yAxis: 50, label: { show: true, formatter: '随机基准 50%', color: colors.subtext, position: 'end' }, lineStyle: { color: '#666', type: 'dashed' } }]
        },
      },
    ],
  }
})

// ============ 图6: 资金曲线 ============
const equityCurveOption = computed(() => {
  const ec = props.charts.equity_curve
  if (!ec?.length) return {}

  const dates = ec.map(e => e.date)
  const capitals = ec.map(e => e.capital)
  const initial = ec[0]?.capital || 100000
  const final = ec[ec.length - 1]?.capital || initial
  const returnPct = ((final - initial) / initial * 100).toFixed(2)

  return {
    tooltip: {
      trigger: 'axis', backgroundColor: '#1a1a2e', borderColor: '#333', textStyle: { color: '#e0e0e0' },
      formatter: (params) => {
        const idx = params[0].dataIndex
        const item = ec[idx]
        const pnl = ((item.capital - initial) / initial * 100).toFixed(2)
        return `${item.date}<br/>资金: ¥${item.capital.toLocaleString()}<br/>累计收益: ${pnl}%${item.trade ? '<br/>' + item.trade : ''}`
      }
    },
    grid: { top: 40, bottom: 50, left: 70, right: 30 },
    xAxis: {
      type: 'category', data: dates, boundaryGap: false,
      axisLabel: { color: colors.text, fontSize: 10, rotate: 30, interval: Math.max(0, Math.floor(dates.length / 8)) },
      axisLine: { lineStyle: { color: colors.axis } },
    },
    yAxis: {
      type: 'value', name: '资金 (¥)',
      nameTextStyle: { color: colors.subtext },
      axisLabel: { color: colors.text, formatter: val => (val / 1000).toFixed(0) + 'K' },
      splitLine: { lineStyle: { color: colors.grid } },
      axisLine: { lineStyle: { color: colors.axis } },
    },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
    ],
    series: [{
      type: 'line',
      data: capitals,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 2, color: final >= initial ? colors.up : colors.down },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: final >= initial ? 'rgba(76,175,80,0.35)' : 'rgba(244,67,54,0.35)' },
            { offset: 1, color: 'rgba(0,0,0,0)' },
          ]
        }
      },
      markLine: {
        silent: true,
        data: [{ yAxis: initial, label: { show: true, formatter: '初始资金', color: colors.subtext, position: 'end' }, lineStyle: { color: '#666', type: 'dashed' } }]
      },
    }],
    graphic: [{
      type: 'text', right: 20, top: 10,
      style: {
        text: `累计收益: ${returnPct}%`,
        fill: final >= initial ? colors.up : colors.down,
        fontSize: 15, fontWeight: 'bold',
      }
    }],
  }
})

// ============ 图7: 准确率趋势 ============
const accuracyTrendOption = computed(() => {
  const at = props.charts.accuracy_trend
  if (!at?.length) return {}

  const dates = at.map(a => a.date)
  const accs = at.map(a => a.accuracy)
  const totals = at.map(a => a.total)

  // 计算移动平均 (3期)
  const ma = accs.map((_, i) => {
    if (i < 2) return null
    const avg = (accs[i] + accs[i - 1] + accs[i - 2]) / 3
    return Math.round(avg * 10) / 10
  })

  return {
    tooltip: {
      trigger: 'axis', backgroundColor: '#1a1a2e', borderColor: '#333', textStyle: { color: '#e0e0e0' },
      formatter: (params) => {
        const idx = params[0]?.dataIndex
        if (idx == null) return ''
        const item = at[idx]
        let text = `${item.date}<br/>准确率: <b>${item.accuracy}%</b><br/>样本: ${item.correct}/${item.total}`
        if (ma[idx] != null) text += `<br/>3期均线: ${ma[idx]}%`
        return text
      }
    },
    legend: { data: ['准确率', '3期均线', '样本数'], textStyle: { color: colors.subtext, fontSize: 11 }, top: 5 },
    grid: { top: 40, bottom: 50, left: 50, right: 50 },
    xAxis: {
      type: 'category', data: dates, boundaryGap: false,
      axisLabel: { color: colors.text, fontSize: 10, rotate: 30, interval: Math.max(0, Math.floor(dates.length / 8)) },
      axisLine: { lineStyle: { color: colors.axis } },
    },
    yAxis: [
      {
        type: 'value', name: '准确率 %', max: 100,
        nameTextStyle: { color: colors.subtext },
        axisLabel: { color: colors.text },
        splitLine: { lineStyle: { color: colors.grid } },
        axisLine: { lineStyle: { color: colors.axis } },
      },
      {
        type: 'value', name: '样本数',
        nameTextStyle: { color: colors.subtext },
        axisLabel: { color: colors.text },
        splitLine: { show: false },
        axisLine: { lineStyle: { color: colors.axis } },
      },
    ],
    dataZoom: [{ type: 'inside', start: 0, end: 100 }],
    series: [
      {
        name: '准确率', type: 'line', yAxisIndex: 0,
        data: accs,
        smooth: false,
        symbolSize: 6,
        lineStyle: { width: 2, color: colors.blue },
        itemStyle: { color: colors.blue },
      },
      {
        name: '3期均线', type: 'line', yAxisIndex: 0,
        data: ma,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color: colors.amber, type: 'dashed' },
      },
      {
        name: '样本数', type: 'bar', yAxisIndex: 1,
        data: totals,
        barWidth: '40%',
        itemStyle: { color: 'rgba(156,39,176,0.3)', borderRadius: [2, 2, 0, 0] },
      },
      // 50%基准线 (via markLine on first series)
    ],
  }
})
</script>

<style scoped>
.charts-section { margin-bottom: 1.5rem; }

.panel { background: var(--c-paper); border: 2px solid var(--c-border); margin-bottom: 1.5rem; box-shadow: 4px 4px 0 var(--c-shadow); }
.panel-header { background: var(--c-hover); border-bottom: 1px solid var(--c-border); padding: 0.75rem 1rem; display: flex; justify-content: space-between; align-items: center; font-weight: 700; cursor: pointer; }
.panel-header:hover { background: var(--c-grid); }
.panel-title-wrap { display: flex; align-items: center; gap: 0.75rem; }
.panel-title { font-family: var(--font-display); }
.chart-count { font-size: 0.7rem; background: var(--c-amber, #FF9800); color: #000; padding: 0.1rem 0.5rem; border-radius: 3px; font-weight: 700; letter-spacing: 0.05em; }
.toggle-icon { display: flex; align-items: center; transition: transform 0.3s; }
.toggle-icon.open { transform: rotate(90deg); }
.panel-body { padding: 1rem; }

.charts-panel .panel-header {
  background: linear-gradient(135deg, rgba(33,150,243,0.15), rgba(156,39,176,0.15));
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.chart-card {
  background: var(--c-hover, #1a1a2e);
  border: 1px solid var(--c-border, #333);
  border-radius: 6px;
  padding: 0.75rem;
  min-height: 300px;
  display: flex;
  flex-direction: column;
}

.chart-card.wide {
  grid-column: span 2;
}

.chart-card.tall {
  min-height: 400px;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--c-muted, #ccc);
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--c-grid, rgba(255,255,255,0.08));
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.chart {
  flex: 1;
  min-height: 250px;
  width: 100%;
}

.chart-tall {
  min-height: 350px;
}

@media (max-width: 900px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
  .chart-card.wide {
    grid-column: span 1;
  }
}
</style>
