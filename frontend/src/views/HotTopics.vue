<template>
  <div class="page-container">
    <header class="page-header">
      <div>
        <div class="page-title-wrapper">MARKET SENTIMENT</div>
        <h1 class="page-title">全网<span>热搜</span></h1>
      </div>
      <div class="meta-bar">
        <span>SOURCES: {{ Object.keys(hotSearches).length }}</span>
        <span>UPDATE: {{ lastUpdate }}</span>
      </div>
    </header>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>正在获取各平台热搜数据...</span>
    </div>

    <div v-else class="grid-3">
      <div class="card" v-for="(items, platformName) in hotSearches" :key="platformName">
        <div class="card-header">
          <div class="card-title">{{ platformName.toUpperCase() }}</div>
          <div class="card-tag">HOT</div>
        </div>
        <div class="card-body p-0">
          <div v-if="!items || items.length === 0" class="empty-state">
            暂无数据或采集失败
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

const hotSearches = ref({})
const lastUpdate = ref('--:--')
const loading = ref(true)

const formatHeat = (val) => {
  if (!val) return '-'
  if (val >= 10000000) return (val / 10000000).toFixed(1) + '千万'
  if (val >= 10000) return (val / 10000).toFixed(1) + '万'
  if (val >= 1000) return (val / 1000).toFixed(1) + 'k'
  return val
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
  color: #888;
  background: #eee;
  padding: 0.1rem 0.3rem;
  border-radius: 2px;
  white-space: nowrap;
}
</style>
