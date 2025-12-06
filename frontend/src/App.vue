<template>
  <div class="app-container">
    <!-- CRT Effects -->
    <div class="crt-overlay" :class="{ 'crt-paused': !crtEnabled }"></div>
    <div class="crt-flicker" :class="{ 'crt-paused': !crtEnabled }"></div>

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
      <div class="top-bar-right">
        <!-- Language Toggle -->
        <button class="lang-toggle" @click="toggleLocale" :title="locale === 'zh' ? 'Switch to English' : '切换到中文'">
          {{ locale === 'zh' ? 'EN' : '中文' }}
        </button>
        <!-- CRT Toggle -->
        <button class="crt-toggle" @click="toggleCRT" :title="crtEnabled ? (locale === 'zh' ? '关闭扫描线' : 'Disable Scanlines') : (locale === 'zh' ? '开启扫描线' : 'Enable Scanlines')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
            <line x1="8" y1="21" x2="16" y2="21"></line>
            <line x1="12" y1="17" x2="12" y2="21"></line>
            <line v-if="crtEnabled" x1="6" y1="8" x2="18" y2="8" stroke-dasharray="2,2"></line>
            <line v-if="crtEnabled" x1="6" y1="12" x2="18" y2="12" stroke-dasharray="2,2"></line>
            <line v-if="!crtEnabled" x1="4" y1="1" x2="20" y2="19" stroke="currentColor" stroke-width="2"></line>
          </svg>
        </button>
        <!-- Theme Toggle -->
        <button class="theme-toggle" @click="toggleTheme" :title="isDark ? '切换亮色模式' : '切换深色模式'">
          <!-- Sun Icon -->
          <svg v-if="isDark" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="5"></circle>
            <line x1="12" y1="1" x2="12" y2="3"></line>
            <line x1="12" y1="21" x2="12" y2="23"></line>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
            <line x1="1" y1="12" x2="3" y2="12"></line>
            <line x1="21" y1="12" x2="23" y2="12"></line>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
          </svg>
          <!-- Moon Icon -->
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
          </svg>
        </button>
        <div class="top-bar-info">
          DATE: {{ currentDate }}
        </div>
      </div>
    </header>

    <div class="layout">
      <!-- Drawer Overlay -->
      <div class="drawer-overlay" v-if="isDrawerOpen" @click="closeDrawer"></div>

      <!-- Sidebar -->
      <aside class="sidebar" :class="{ 'mobile-open': isDrawerOpen }">
        <div class="sidebar-section-title">NAVIGATION // {{ locale === 'zh' ? '导航' : 'NAV' }}</div>
        <ul class="nav-menu">
          <li class="nav-item">
            <router-link to="/" class="nav-link" active-class="active" @click="closeDrawer">{{ t('nav_dashboard') }}</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/daily-summary" class="nav-link" active-class="active" @click="closeDrawer">{{ t('nav_daily_summary') }}</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/weekly-summary" class="nav-link" active-class="active" @click="closeDrawer">{{ t('nav_weekly_summary') }}</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/monthly-summary" class="nav-link" active-class="active" @click="closeDrawer">{{ t('nav_monthly_summary') }}</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/watchlist" class="nav-link" active-class="active" @click="closeDrawer">{{ t('nav_watchlist') }}</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/hot-topics" class="nav-link" active-class="active" @click="closeDrawer">{{ t('nav_hot_topics') }}</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/crypto" class="nav-link" active-class="active" @click="closeDrawer">{{ t('nav_crypto') }}</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/history" class="nav-link" active-class="active" @click="closeDrawer">{{ t('nav_history') }}</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/backtest" class="nav-link" active-class="active" @click="closeDrawer">{{ t('nav_backtest') }}</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/overview" class="nav-link" active-class="active" @click="closeDrawer">{{ t('nav_overview') }}</router-link>
          </li>
        </ul>

        <div class="system-config">
          <div class="config-header">SYSTEM STATUS // {{ t('system_status') }}</div>
          <div class="status-row">
            <span>{{ t('connection_status') }}</span>
            <span><span class="status-indicator"></span>ONLINE</span>
          </div>
          <div class="status-row">
            <span>{{ t('last_sync') }}</span>
            <span>{{ lastSyncTime }}</span>
          </div>
          <div class="status-row">
            <span>{{ t('version') }}</span>
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
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useLocale } from './composables/useLocale'

const { locale, t, toggleLocale } = useLocale()

const currentDate = computed(() => {
  const now = new Date()
  if (locale.value === 'zh') {
    return now.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }).replace(/\//g, '-')
  }
  return now.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
})
const lastSyncTime = ref(new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }))
const isDrawerOpen = ref(false)
const isDark = ref(false)
const crtEnabled = ref(true)

const toggleDrawer = () => {
  isDrawerOpen.value = !isDrawerOpen.value
}

const closeDrawer = () => {
  isDrawerOpen.value = false
}

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

const toggleCRT = () => {
  crtEnabled.value = !crtEnabled.value
  localStorage.setItem('crtEnabled', crtEnabled.value ? 'true' : 'false')
}

const initTheme = () => {
  // Check localStorage first
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme) {
    isDark.value = savedTheme === 'dark'
  } else {
    // Check system preference
    isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
  }
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  
  // Init CRT setting
  const savedCRT = localStorage.getItem('crtEnabled')
  if (savedCRT !== null) {
    crtEnabled.value = savedCRT === 'true'
  }
}

let timer
onMounted(() => {
  initTheme()
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

.top-bar-right {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.lang-toggle {
    background: transparent;
    border: 2px solid var(--c-ink);
    color: var(--c-ink);
    cursor: pointer;
    padding: 4px 10px;
    font-family: var(--font-mono);
    font-size: 0.75rem;
    font-weight: 700;
    transition: all 0.15s;
    box-shadow: 2px 2px 0 var(--c-ink);
}

.lang-toggle:hover {
    background: var(--c-ink);
    color: var(--c-amber);
    transform: translate(-1px, -1px);
    box-shadow: 3px 3px 0 var(--c-ink);
}

.lang-toggle:active {
    transform: translate(1px, 1px);
    box-shadow: 1px 1px 0 var(--c-ink);
}

.theme-toggle {
    background: transparent;
    border: 2px solid var(--c-ink);
    color: var(--c-ink);
    cursor: pointer;
    padding: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;
    box-shadow: 2px 2px 0 var(--c-ink);
}

.theme-toggle:hover {
    background: var(--c-ink);
    color: var(--c-amber);
}

.theme-toggle:active {
    transform: translate(2px, 2px);
    box-shadow: none;
}

.crt-toggle {
    background: transparent;
    border: 2px solid var(--c-ink);
    color: var(--c-ink);
    cursor: pointer;
    padding: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;
    box-shadow: 2px 2px 0 var(--c-ink);
}

.crt-toggle:hover {
    background: var(--c-ink);
    color: var(--c-amber);
}

.crt-toggle:active {
    transform: translate(2px, 2px);
    box-shadow: none;
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
    border-right: 2px solid var(--c-border);
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
    color: var(--c-muted);
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
    border: 2px solid var(--c-border);
    background: var(--c-paper);
    font-weight: 700;
    font-family: var(--font-body);
    transition: all 0.1s;
    box-shadow: 4px 4px 0 var(--c-shadow);
    position: relative;
}

.nav-link:hover, .nav-link.active {
    transform: translate(2px, 2px);
    box-shadow: 2px 2px 0 var(--c-shadow);
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
    border: 2px solid var(--c-border);
    background: var(--c-paper);
    padding: 1rem;
}

.config-header {
    font-size: 0.65rem;
    font-weight: 700;
    margin-bottom: 0.75rem;
    text-transform: uppercase;
    border-bottom: 1px solid var(--c-border);
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
        box-shadow: 4px 0 10px var(--c-shadow);
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