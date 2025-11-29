<template>
  <div class="page-container">
    <header class="page-header">
      <div>
        <div class="page-title-wrapper">SYSTEM OVERVIEW</div>
        <h1 class="page-title">系统<span>架构</span></h1>
      </div>
      <div class="meta-bar">
        <a href="https://github.com/ianchiou28/Wide-Research-for-Finance" target="_blank" class="github-link">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
          </svg>
          GITHUB REPO
        </a>
        <span>VERSION: v2.4.0</span>
        <span>STATUS: ONLINE</span>
      </div>
    </header>

    <div class="content-grid">
      <!-- Left: Architecture & Workflow -->
      <div class="main-column">
        <!-- Tech Stack -->
        <div class="card mb-2">
          <div class="card-header">
            <span class="card-title">技术栈 // TECH STACK</span>
          </div>
          <div class="card-body tech-stack">
            <span class="badge badge-ink">Python 3.11</span>
            <span class="badge badge-ink">Vue.js 3</span>
            <span class="badge badge-ink">Vite</span>
            <span class="badge badge-amber">DeepSeek V3</span>
            <span class="badge badge-gray">SQLite</span>
            <span class="badge badge-gray">APScheduler</span>
          </div>
        </div>

        <!-- Workflow -->
        <div class="card mb-2">
          <div class="card-header">
            <span class="card-title">处理链路 // PIPELINE</span>
          </div>
          <div class="card-body">
            <div class="pipeline-steps">
              <div class="step">
                <div class="step-num">01</div>
                <div class="step-content">
                  <div class="step-title">多源采集</div>
                  <div class="step-desc">RSS/API 轮询 17+ 国际财经源</div>
                </div>
              </div>
              <div class="step-line"></div>
              <div class="step">
                <div class="step-num">02</div>
                <div class="step-content">
                  <div class="step-title">智能清洗</div>
                  <div class="step-desc">DeepSeek 初筛，去重与价值评估</div>
                </div>
              </div>
              <div class="step-line"></div>
              <div class="step">
                <div class="step-num">03</div>
                <div class="step-content">
                  <div class="step-title">深度分析</div>
                  <div class="step-desc">全文提取，实体识别，情感打分</div>
                </div>
              </div>
              <div class="step-line"></div>
              <div class="step">
                <div class="step-num">04</div>
                <div class="step-content">
                  <div class="step-title">终端呈现</div>
                  <div class="step-desc">Web 仪表盘，实时推送，历史归档</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Data Coverage (Restored) -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">数据覆盖 // COVERAGE</span>
          </div>
          <div class="card-body">
            <div class="coverage-list">
              <div class="cov-item">
                <div class="cov-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="2" y1="12" x2="22" y2="12"></line>
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                  </svg>
                </div>
                <div class="cov-content">
                  <strong>国际财经</strong>
                  <span>Bloomberg, WSJ, CNBC, MarketWatch, Forbes, FT, Reuters</span>
                </div>
              </div>
              <div class="cov-item">
                <div class="cov-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="20" x2="18" y2="10"></line>
                    <line x1="12" y1="20" x2="12" y2="4"></line>
                    <line x1="6" y1="20" x2="6" y2="14"></line>
                  </svg>
                </div>
                <div class="cov-content">
                  <strong>机构分析</strong>
                  <span>Seeking Alpha, 雪球, Benzinga, The Motley Fool</span>
                </div>
              </div>
              <div class="cov-item">
                <div class="cov-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                  </svg>
                </div>
                <div class="cov-content">
                  <strong>科技/加密</strong>
                  <span>CoinDesk, TechCrunch, VentureBeat</span>
                </div>
              </div>
              <div class="cov-item">
                <div class="cov-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 21h18M5 21V7l8-4 8 4v14M8 21V11M16 21V11"></path>
                  </svg>
                </div>
                <div class="cov-content">
                  <strong>官方机构</strong>
                  <span>美联储, SEC, 央行, 证监会</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Modules & Stats -->
      <div class="side-column">
        <!-- Core Metrics -->
        <div class="card mb-2">
          <div class="card-header">
            <span class="card-title">核心指标 // METRICS</span>
          </div>
          <div class="card-body">
            <div class="metric-grid">
              <div class="metric-box">
                <div class="m-label">响应速度</div>
                <div class="m-value">&lt;15s</div>
              </div>
              <div class="metric-box">
                <div class="m-label">覆盖源</div>
                <div class="m-value">17+</div>
              </div>
              <div class="metric-box">
                <div class="m-label">AI 模型</div>
                <div class="m-value">DeepSeek</div>
              </div>
              <div class="metric-box">
                <div class="m-label">运行成本</div>
                <div class="m-value">Low</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Module Map -->
        <div class="card mb-2">
          <div class="card-header">
            <span class="card-title">功能模块 // MODULES</span>
          </div>
          <div class="card-body module-list">
            <div class="module-item">
              <span class="mod-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                  <line x1="3" y1="9" x2="21" y2="9"></line>
                  <line x1="9" y1="21" x2="9" y2="9"></line>
                </svg>
              </span>
              <div class="mod-info">
                <div class="mod-name">概览仪表盘</div>
                <div class="mod-desc">实时市场情绪与关键事件</div>
              </div>
            </div>
            <div class="module-item">
              <span class="mod-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
                  <polyline points="17 6 23 6 23 12"></polyline>
                </svg>
              </span>
              <div class="mod-info">
                <div class="mod-name">自选监控</div>
                <div class="mod-desc">个股 K 线与实时报价</div>
              </div>
            </div>
            <div class="module-item">
              <span class="mod-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 2a10 10 0 1 0 10 10H12V2z"></path>
                  <path d="M12 2a10 10 0 0 1 10 10"></path>
                  <path d="M12 12 2.1 12"></path>
                </svg>
              </span>
              <div class="mod-info">
                <div class="mod-name">全网热搜</div>
                <div class="mod-desc">微博/抖音/百度热点聚合</div>
              </div>
            </div>
            <div class="module-item">
              <span class="mod-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"></path>
                  <line x1="12" y1="18" x2="12" y2="22"></line>
                  <line x1="12" y1="2" x2="12" y2="6"></line>
                </svg>
              </span>
              <div class="mod-info">
                <div class="mod-name">加密货币</div>
                <div class="mod-desc">主流币种行情与市值</div>
              </div>
            </div>
            <div class="module-item">
              <span class="mod-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                  <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
              </span>
              <div class="mod-info">
                <div class="mod-name">历史报告</div>
                <div class="mod-desc">每日/每周深度分析归档</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Start (Restored) -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">快速开始 // START</span>
          </div>
          <div class="card-body">
            <div class="start-item">
              <strong class="start-label">启动仪表盘</strong>
              <code class="start-code">python web_app.py</code>
            </div>
            <div class="start-item">
              <strong class="start-label">自动调度</strong>
              <code class="start-code">python main.py</code>
            </div>
          </div>
        </div>
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

.mb-2 { margin-bottom: 2rem; }

/* Header Link */
.github-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--c-ink);
  text-decoration: none;
  font-size: 0.8rem;
  font-weight: 700;
  border-bottom: 1px solid transparent;
  transition: all 0.2s;
}

.github-link:hover {
  color: var(--c-amber);
  border-bottom-color: var(--c-amber);
}

/* Tech Stack */
.tech-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.badge-ink { background: var(--c-ink); color: var(--c-bg); }
.badge-amber { background: var(--c-amber); color: var(--c-ink); }

/* Pipeline */
.pipeline-steps {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.step {
  display: flex;
  gap: 1rem;
  padding: 1rem 0;
}

.step-num {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--c-amber);
  line-height: 1;
}

.step-title {
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.step-desc {
  font-size: 0.85rem;
  color: var(--c-muted);
}

.step-line {
  width: 2px;
  height: 20px;
  background: var(--c-grid);
  margin-left: 1rem; /* Align with num center approx */
}

/* Metrics */
.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.metric-box {
  background: var(--c-hover);
  padding: 1rem;
  border: 1px solid var(--c-grid);
}

.m-label {
  font-size: 0.75rem;
  color: var(--c-muted);
  margin-bottom: 0.5rem;
}

.m-value {
  font-family: var(--font-mono);
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--c-ink);
}

/* Modules */
.module-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.module-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.module-item:hover {
  background: var(--c-hover);
  border-color: var(--c-grid);
  transform: translateX(5px);
}

.mod-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-ink);
}

.mod-name {
  font-weight: 700;
  font-size: 0.9rem;
}

.mod-desc {
  font-size: 0.8rem;
  color: var(--c-muted);
}

/* Coverage */
.coverage-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.cov-item {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.cov-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--c-hover);
  border-radius: 4px;
  color: var(--c-ink);
}

.cov-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.cov-content strong {
  font-size: 0.9rem;
  margin-bottom: 0.25rem;
}

.cov-content span {
  font-size: 0.8rem;
  color: var(--c-muted);
  line-height: 1.4;
}

/* Quick Start */
.start-item {
  margin-bottom: 1rem;
}

.start-item:last-child {
  margin-bottom: 0;
}

.start-label {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
}

.start-code {
  display: block;
  background: var(--c-hover);
  padding: 0.5rem;
  font-family: var(--font-mono);
  font-size: 0.85rem;
  border-left: 3px solid var(--c-amber);
}

@media (max-width: 1024px) {
  .content-grid { grid-template-columns: 1fr; }
}
</style>