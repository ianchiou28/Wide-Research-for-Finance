<template>
  <div class="app-container">
    <!-- CRT Effects -->
    <div class="crt-overlay"></div>
    <div class="crt-flicker"></div>

    <!-- Top Bar -->
    <header class="top-bar">
      <div class="top-bar-left">
        <button class="menu-toggle" @click="toggleDrawer">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>
        <div class="top-bar-logo">
          <div class="top-bar-icon"></div>
          <span class="desktop-title">WIDE RESEARCH // FINANCE TERMINAL</span>
          <span class="mobile-title">WIDE RESEARCH</span>
        </div>
      </div>
      <div class="top-bar-info">
        DATE: {{ currentDate }}
      </div>
    </header>

    <div class="layout">
      <!-- Drawer Overlay -->
      <div class="drawer-overlay" v-if="isDrawerOpen" @click="closeDrawer"></div>

      <!-- Sidebar -->
      <aside class="sidebar" :class="{ 'mobile-open': isDrawerOpen }">
        <div class="sidebar-section-title">NAVIGATION // 导航</div>
        <ul class="nav-menu">
          <li class="nav-item">
            <router-link to="/" class="nav-link" active-class="active" @click="closeDrawer">概览仪表盘</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/watchlist" class="nav-link" active-class="active" @click="closeDrawer">自选监控</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/hot-topics" class="nav-link" active-class="active" @click="closeDrawer">全网热搜</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/crypto" class="nav-link" active-class="active" @click="closeDrawer">加密货币</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/history" class="nav-link" active-class="active" @click="closeDrawer">历史报告</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/overview" class="nav-link" active-class="active" @click="closeDrawer">项目总览</router-link>
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
const isDrawerOpen = ref(false)

const toggleDrawer = () => {
  isDrawerOpen.value = !isDrawerOpen.value
}

const closeDrawer = () => {
  isDrawerOpen.value = false
}

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

<!-- Styles -->
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

.top-bar-left {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.menu-toggle {
    display: none;
    background: transparent;
    border: 2px solid var(--c-ink);
    color: var(--c-ink);
    cursor: pointer;
    padding: 4px;
    margin-right: 1rem;
    border-radius: 0;
    transition: all 0.1s;
    width: 40px;
    height: 40px;
    align-items: center;
    justify-content: center;
    box-shadow: 3px 3px 0 var(--c-ink);
}

.menu-toggle:active {
    transform: translate(3px, 3px);
    box-shadow: none;
    background: var(--c-ink);
    color: var(--c-amber);
}

.top-bar-logo {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.mobile-title {
    display: none;
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
    z-index: 90;
    transition: transform 0.3s ease-in-out;
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

/* Drawer Overlay */
.drawer-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.5);
    z-index: 80;
    backdrop-filter: blur(2px);
}

@keyframes blink-status {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* Responsive Design */
@media (max-width: 768px) {
    .top-bar {
        padding: 0 0.75rem;
    }

    .menu-toggle {
        display: flex;
    }

    .sidebar {
        position: fixed;
        top: 48px;
        left: 0;
        bottom: 0;
        width: 280px;
        transform: translateX(-100%);
        box-shadow: 4px 0 10px rgba(0,0,0,0.1);
    }

    .sidebar.mobile-open {
        transform: translateX(0);
    }
    
    .desktop-title {
        display: none;
    }

    .mobile-title {
        display: block;
        font-weight: 800;
        font-size: 1.1rem;
        letter-spacing: 0.05em;
    }

    .top-bar-info {
        display: none;
    }
}
</style>