<template>
  <div class="page-container">
    <header class="page-header">
      <div>
        <div class="page-title-wrapper">MARKET SENTIMENT</div>
        <h1 class="page-title">{{ locale === 'zh' ? '全网' : 'HOT' }}<span>{{ locale === 'zh' ? '热搜' : 'TOPICS' }}</span></h1>
      </div>
      <div class="meta-bar">
        <span>{{ t('sources') }}: {{ Object.keys(hotSearches).length }}</span>
        <span>{{ t('update') }}: {{ lastUpdate }}</span>
      </div>
    </header>

    <!-- 英文模式提示 -->
    <div v-if="locale === 'en'" class="locale-notice">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="16" x2="12" y2="12"></line>
        <line x1="12" y1="8" x2="12.01" y2="8"></line>
      </svg>
      <span>Trending topics from Chinese platforms (Baidu, Douyin, Toutiao, Weibo, Zhihu) - Content shown in original language</span>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>{{ t('loading') }}</span>
    </div>

    <div v-else class="grid-3">
      <div class="card" v-for="(items, platformName) in hotSearches" :key="platformName">
        <div class="card-header">
          <div class="card-title">{{ platformName.toUpperCase() }}</div>
          <div class="card-tag">HOT</div>
        </div>
        <div class="card-body p-0">
          <div v-if="!items || items.length === 0" class="empty-state">
            {{ t('no_data_or_failed') }}
          </div>
          <div v-else class="topic-list">
            <div v-for="(item, index) in items.slice(0, 10)" :key="index" class="topic-item">
              <div class="topic-rank" :class="{ 'top-3': index < 3 }">{{ index + 1 }}</div>
              <div class="topic-content">
                <a :href="item.url" target="_blank" class="topic-title">{{ item.title }}</a>
                <div class="topic-heat">{{ formatHeat(item.hot_value) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useLocale } from '../composables/useLocale'

const { locale, t } = useLocale()

const hotSearches = ref({})
const lastUpdate = ref('--:--')
const loading = ref(true)

const formatHeat = (val) => {
  if (!val) return '-'
  
  if (locale.value === 'zh') {
    // 中文：用万、千万
    if (val >= 10000000) return (val / 10000000).toFixed(1) + '千万'
    if (val >= 10000) return (val / 10000).toFixed(1) + '万'
    if (val >= 1000) return (val / 1000).toFixed(1) + 'k'
    return val
  } else {
    // 英文：用 K (千), M (百万)
    if (val >= 1000000) return (val / 1000000).toFixed(1) + 'M'
    if (val >= 1000) return (val / 1000).toFixed(1) + 'K'
    return val
  }
}

const fetchHotSearches = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/hot-searches/all')
    // API returns { "weibo": [...], "toutiao": [...], ... }
    hotSearches.value = res.data || {}
    lastUpdate.value = new Date().toLocaleTimeString()
  } catch (e) {
    console.error(e)
    hotSearches.value = {}
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchHotSearches()
})
</script>

<style scoped>
.p-0 { padding: 0; }

.locale-notice {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--c-hover);
  border: 1px solid var(--c-grid);
  margin-bottom: 1.5rem;
  font-size: 0.85rem;
  color: var(--c-muted);
}

.locale-notice svg {
  flex-shrink: 0;
  color: var(--c-amber);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  color: #888;
  gap: 1rem;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(0,0,0,0.1);
  border-top-color: var(--c-amber);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #888;
  font-size: 0.9rem;
}

.topic-list {
  display: flex;
  flex-direction: column;
}

.topic-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  transition: background 0.2s;
}

.topic-item:hover {
  background: rgba(0,0,0,0.02);
}

.topic-rank {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 1.2rem;
  width: 30px;
  color: #ccc;
  font-style: italic;
}

.topic-rank.top-3 {
  color: var(--c-amber);
}

.topic-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}

.topic-title {
  font-weight: 500;
  font-size: 0.9rem;
  color: var(--c-ink);
  text-decoration: none;
  flex: 1;
}

.topic-title:hover {
  color: var(--c-amber);
}

.topic-heat {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--c-ink);
  background: var(--c-grid);
  padding: 0.1rem 0.3rem;
  border-radius: 2px;
  white-space: nowrap;
  border: 1px solid var(--c-border);
}
</style>
