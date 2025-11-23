<template>
  <div class="app-container">
    <!-- CRT Effects -->
    <div class="crt-overlay"></div>
    <div class="crt-flicker"></div>

    <!-- Top Bar -->
    <header class="top-bar">
      <div class="top-bar-logo">
        <div class="top-bar-icon"></div>
        <span>WIDE RESEARCH // FINANCE TERMINAL</span>
      </div>
      <div class="top-bar-info">
        DATE: {{ currentDate }}
      </div>
    </header>

    <div class="layout">
      <!-- Sidebar -->
      <aside class="sidebar">
        <div class="sidebar-section-title">NAVIGATION // 导航</div>
        <ul class="nav-menu">
          <li class="nav-item">
            <router-link to="/" class="nav-link" active-class="active">概览仪表盘</router-link>
          </li>
          <li class="nav-item">
            <a href="#" class="nav-link">深度分析</a>
          </li>
          <li class="nav-item">
            <a href="#" class="nav-link">系统设置</a>
          </li>
          <li class="nav-item">
            <router-link to="/overview" class="nav-link" active-class="active">项目总览</router-link>
          </li>
        </ul>

        <div class="system-config">
          <div class="config-header">SYSTEM STATUS // 系统状态</div>
          <div class="status-row">
            <span>连接状态</span>
            <span><span class="status-indicator"></span>ONLINE</span>
          </div>
          <div class="status-row">
            <span>上次同步</span>
            <span>{{ lastSyncTime }}</span>
          </div>
          <div class="status-row">
            <span>版本</span>
            <span>v2.4.0</span>
          </div>
        </div>
      </aside>

      <!-- Main Content -->
      <main class="main-content">
        <router-view></router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const currentDate = ref(new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }).replace(/\//g, '-'))
const lastSyncTime = ref(new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }))

let timer
onMounted(() => {
  timer = setInterval(() => {
    lastSyncTime.value = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' })
  }, 60000)
})

onUnmounted(() => {
  clearInterval(timer)
})
</script>

<style scoped>
/* Top Bar */
.top-bar {
    background: var(--c-amber);
    color: var(--c-ink);
    height: 48px;
    display: flex;
    align-items: center;
    padding: 0 2rem;
    border-bottom: 2px solid var(--c-ink);
    position: sticky;
    top: 0;
    z-index: 100;
    font-family: var(--font-display);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    justify-content: space-between;
}

.top-bar-logo {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.top-bar-icon {
    width: 24px;
    height: 24px;
    border: 2px solid var(--c-ink);
    border-radius: 50%;
    position: relative;
}
.top-bar-icon::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 8px;
    height: 8px;
    background: var(--c-ink);
    border-radius: 50%;
}

/* Sidebar */
.sidebar {
    background: var(--c-bg);
    border-right: 2px solid var(--c-ink);
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    height: calc(100vh - 48px);
    position: sticky;
    top: 48px;
}

.sidebar-section-title {
    font-family: var(--font-display);
    font-size: 0.75rem;
    font-weight: 700;
    margin-bottom: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #666;
}

.nav-menu {
    list-style: none;
    margin-bottom: 2rem;
}

.nav-item {
    margin-bottom: 0.75rem;
}

.nav-link {
    display: flex;
    align-items: center;
    padding: 0.75rem 1rem;
    text-decoration: none;
    color: var(--c-ink);
    border: 2px solid var(--c-ink);
    background: var(--c-paper);
    font-weight: 700;
    font-family: var(--font-body);
    transition: all 0.1s;
    box-shadow: 4px 4px 0 rgba(0,0,0,0.1);
    position: relative;
}

.nav-link:hover, .nav-link.active {
    transform: translate(2px, 2px);
    box-shadow: 2px 2px 0 rgba(0,0,0,0.1);
    background: var(--c-ink);
    color: var(--c-bg);
}

.nav-link.active::before {
    content: '>';
    position: absolute;
    left: 0.5rem;
    color: var(--c-amber);
}

/* System Config Panel */
.system-config {
    margin-top: auto;
    border: 2px solid var(--c-ink);
    background: var(--c-paper);
    padding: 1rem;
}

.config-header {
    font-size: 0.65rem;
    font-weight: 700;
    margin-bottom: 0.75rem;
    text-transform: uppercase;
    border-bottom: 1px solid var(--c-ink);
    padding-bottom: 0.25rem;
}

.status-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
    font-size: 0.75rem;
    font-family: var(--font-mono);
}

.status-indicator {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #4CAF50;
    border-radius: 50%;
    margin-right: 0.5rem;
    animation: blink-status 2s infinite;
}

@keyframes blink-status {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}
</style>