<template>
  <div class="page-container">
    <header class="page-header">
      <div>
        <div class="page-title-wrapper">DIGITAL ASSETS</div>
        <h1 class="page-title">{{ locale === 'zh' ? '加密' : 'CRYPTO' }}<span>{{ locale === 'zh' ? '货币' : 'CURRENCY' }}</span></h1>
      </div>
      <div class="meta-bar">
        <span>{{ t('market_cap') }}: ${{ formatMarketCap(globalData.total_market_cap) }}</span>
        <span>BTC DOM: {{ globalData.btc_dominance?.toFixed(1) || '52' }}%</span>
      </div>
    </header>

    <!-- Top Coins Cards -->
    <div class="grid-4 mb-2">
      <div class="card highlight-card" v-for="coin in topCoins" :key="coin.symbol">
        <div class="card-body">
          <div class="coin-header">
            <span class="coin-symbol">{{ coin.symbol }}</span>
            <span class="coin-rank">#{{ coin.market_cap_rank || '-' }}</span>
          </div>
          <div class="coin-price">${{ formatPrice(coin.price_usd) }}</div>
          <div class="coin-change" :class="getChangeClass(coin.change_24h)">
            {{ coin.change_24h?.toFixed(2) || '0.00' }}%
          </div>
        </div>
      </div>
    </div>

    <!-- Main Table -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">{{ locale === 'zh' ? '市场概览' : 'Market Overview' }}</div>
        <button class="btn btn-sm btn-outline" @click="fetchCrypto">{{ locale === 'zh' ? '刷新' : 'Refresh' }}</button>
      </div>
      <div class="card-body">
        <div v-if="loading" class="text-center">{{ t('loading') }}</div>
        <div v-else class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>{{ locale === 'zh' ? '排名' : 'Rank' }}</th>
                <th>{{ locale === 'zh' ? '名称' : 'Name' }}</th>
                <th>{{ locale === 'zh' ? '价格 (USD)' : 'Price (USD)' }}</th>
                <th>{{ t('price_change_24h') }}</th>
                <th class="hide-mobile">24h {{ t('high') }}/{{ t('low') }}</th>
                <th class="hide-mobile">{{ t('volume_24h') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(coin, index) in marketData" :key="coin.symbol">
                <td>{{ coin.market_cap_rank || index + 1 }}</td>
                <td>
                  <div class="coin-name-cell">
                    <img v-if="coin.image" :src="coin.image" class="coin-icon" />
                    <span class="coin-icon-placeholder" v-else>{{ coin.symbol?.charAt(0) }}</span>
                    <span>{{ coin.name || coin.symbol }}</span>
                    <span class="text-gray">{{ coin.symbol }}</span>
                  </div>
                </td>
                <td class="font-mono">${{ formatPrice(coin.price_usd) }}</td>
                <td>
                  <span :class="getChangeClass(coin.change_24h)">
                    {{ coin.change_24h >= 0 ? '+' : '' }}{{ coin.change_24h?.toFixed(2) || '0.00' }}%
                  </span>
                </td>
                <td class="font-mono text-sm hide-mobile">
                  <span class="text-green">${{ formatPrice(coin.high_24h) }}</span> /
                  <span class="text-red">${{ formatPrice(coin.low_24h) }}</span>
                </td>
                <td class="font-mono hide-mobile">${{ formatVolume(coin.volume_24h) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useLocale } from '../composables/useLocale'

const { locale, t } = useLocale()

const marketData = ref([])
const globalData = ref({})
const loading = ref(true)
const topCoins = computed(() => marketData.value.slice(0, 4))

const getChangeClass = (change) => {
  if (change > 0) return 'text-green'
  if (change < 0) return 'text-red'
  return 'text-gray'
}

const formatPrice = (price) => {
  if (!price) return '0.00'
  if (price >= 1000) return price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  if (price >= 1) return price.toFixed(2)
  return price.toFixed(4)
}

const formatVolume = (vol) => {
  if (!vol) return '0'
  if (vol >= 1e9) return (vol / 1e9).toFixed(2) + 'B'
  if (vol >= 1e6) return (vol / 1e6).toFixed(2) + 'M'
  if (vol >= 1e3) return (vol / 1e3).toFixed(2) + 'K'
  return vol.toFixed(2)
}

const formatMarketCap = (cap) => {
  if (!cap) return '2.4T'
  if (cap >= 1e12) return (cap / 1e12).toFixed(2) + 'T'
  if (cap >= 1e9) return (cap / 1e9).toFixed(2) + 'B'
  return cap.toLocaleString()
}

const fetchCrypto = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/crypto/market')
    // API returns array directly now
    marketData.value = Array.isArray(res.data) ? res.data : (res.data.data || [])
    
    // Also fetch global data
    try {
      const globalRes = await axios.get('/api/crypto/global')
      globalData.value = globalRes.data || {}
    } catch (e) {
      console.error('Global data fetch failed:', e)
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchCrypto()
})
</script>

<style scoped>
.mb-2 { margin-bottom: 2rem; }

.highlight-card {
  background: var(--c-ink);
  color: var(--c-bg);
  border: none;
}

.highlight-card .coin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.highlight-card .coin-symbol {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--c-amber);
}

.highlight-card .coin-rank {
  font-size: 0.8rem;
  opacity: 0.6;
}

.highlight-card .coin-price {
  font-family: var(--font-mono);
  font-size: 2rem;
  font-weight: 700;
  margin: 0.5rem 0;
}

.highlight-card .coin-change {
  font-family: var(--font-mono);
  font-weight: 700;
}

.text-green { color: #4CAF50; }
.text-red { color: #F44336; }
.text-gray { color: var(--c-muted); }
.text-center { text-align: center; padding: 2rem; color: var(--c-muted); }
.text-sm { font-size: 0.8rem; }

.coin-name-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.coin-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
}

.coin-icon-placeholder {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--c-amber);
  color: var(--c-ink);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.8rem;
}
</style>
