<template>
  <div class="overview-view">
    <div class="page-header">
      <div>
        <div class="page-title-wrapper">项目总览</div>
        <h1 class="page-title">SYSTEM: <span>架构与指标</span></h1>
      </div>
      <div class="meta-bar">
        <span>STATUS: ACTIVE</span>
      </div>
    </div>

    <div class="content-grid">
      <!-- Left Column -->
      <div class="main-column">
        <article class="card">
          <div class="card-header">
            <span class="card-title">核心指标 // KPI</span>
            <span class="card-tag">METRICS</span>
          </div>
          <div class="card-body">
            <div class="metric-row">
              <span class="metric-label">采集范围</span>
              <span class="metric-value">全球 4 大洲</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">AI 处理流程</span>
              <span class="metric-value">2 阶段 (筛选+分析)</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">热点识别速度</span>
              <span class="metric-value">&lt; 15 秒</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">运营成本</span>
              <span class="metric-value">$0.003 / 小时</span>
            </div>
          </div>
        </article>

        <article class="card">
          <div class="card-header">
            <span class="card-title">处理链路 // WORKFLOW</span>
            <span class="card-tag">PIPELINE</span>
          </div>
          <div class="card-body">
            <div style="margin-bottom: 1.5rem;">
              <h4 style="font-family: var(--font-display); margin-bottom: 0.5rem;">01 数据采集</h4>
              <p style="font-size: 0.9rem; color: #666;">feedparser + requests 轮询 17 个 RSS / 官方站点，自动去重与合并。</p>
            </div>
            <div style="margin-bottom: 1.5rem;">
              <h4 style="font-family: var(--font-display); margin-bottom: 0.5rem;">02 智能筛选</h4>
              <p style="font-size: 0.9rem; color: #666;">DeepSeek 先基于标题做低成本筛查，保留最高价值 20%-30% 的事件。</p>
            </div>
            <div style="margin-bottom: 1.5rem;">
              <h4 style="font-family: var(--font-display); margin-bottom: 0.5rem;">03 深度分析</h4>
              <p style="font-size: 0.9rem; color: #666;">对保留样本获取全文，抽取实体、估算影响等级，并生成结构化 JSON。</p>
            </div>
            <div>
              <h4 style="font-family: var(--font-display); margin-bottom: 0.5rem;">04 报告输出</h4>
              <p style="font-size: 0.9rem; color: #666;">生成小时/日/周三层报告，支持本地存储、邮箱推送和 Web 展示。</p>
            </div>
          </div>
        </article>
      </div>

      <!-- Right Column -->
      <div class="side-column">
        <article class="card">
          <div class="card-header">
            <span class="card-title">数据覆盖 // COVERAGE</span>
            <span class="card-tag">SOURCES</span>
          </div>
          <div class="card-body">
            <div style="margin-bottom: 1rem;">
              <strong style="display:block; margin-bottom:0.25rem;">🌎 国际财经</strong>
              <span style="font-size:0.8rem; color:#666;">Bloomberg, WSJ, CNBC, MarketWatch, Forbes, FT, Yahoo Finance, Investing.com, Reuters</span>
            </div>
            <div style="margin-bottom: 1rem;">
              <strong style="display:block; margin-bottom:0.25rem;">📊 机构分析</strong>
              <span style="font-size:0.8rem; color:#666;">Seeking Alpha, 雪球, Benzinga, The Motley Fool</span>
            </div>
            <div style="margin-bottom: 1rem;">
              <strong style="display:block; margin-bottom:0.25rem;">🚀 科技/加密</strong>
              <span style="font-size:0.8rem; color:#666;">CoinDesk, TechCrunch, VentureBeat</span>
            </div>
            <div>
              <strong style="display:block; margin-bottom:0.25rem;">🏛️ 官方机构</strong>
              <span style="font-size:0.8rem; color:#666;">美联储, SEC, 央行, 证监会</span>
            </div>
          </div>
        </article>

        <article class="card">
          <div class="card-header">
            <span class="card-title">快速开始 // START</span>
            <span class="card-tag">ACTION</span>
          </div>
          <div class="card-body">
            <div style="margin-bottom: 1rem;">
              <strong style="display:block; margin-bottom:0.25rem;">启动仪表盘</strong>
              <code style="background:#eee; padding:0.2rem 0.4rem; font-size:0.8rem;">python web_app.py</code>
            </div>
            <div>
              <strong style="display:block; margin-bottom:0.25rem;">自动调度</strong>
              <code style="background:#eee; padding:0.2rem 0.4rem; font-size:0.8rem;">python main.py</code>
            </div>
          </div>
        </article>
      </div>
    </div>
  </div>
</template>

<style scoped>
.content-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
}

@media (max-width: 1024px) {
    .content-grid { grid-template-columns: 1fr; }
}
</style>