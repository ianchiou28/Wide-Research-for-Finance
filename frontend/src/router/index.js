import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Overview from '../views/Overview.vue'
import Watchlist from '../views/Watchlist.vue'
import HotTopics from '../views/HotTopics.vue'
import Crypto from '../views/Crypto.vue'
import History from '../views/History.vue'
import DailySummary from '../views/DailySummary.vue'
import WeeklySummary from '../views/WeeklySummary.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home
    },
    {
      path: '/overview',
      name: 'overview',
      component: Overview
    },
    {
      path: '/watchlist',
      name: 'watchlist',
      component: Watchlist
    },
    {
      path: '/hot-topics',
      name: 'hot-topics',
      component: HotTopics
    },
    {
      path: '/crypto',
      name: 'crypto',
      component: Crypto
    },
    {
      path: '/history',
      name: 'history',
      component: History
    },
    {
      path: '/daily-summary',
      name: 'daily-summary',
      component: DailySummary
    },
    {
      path: '/weekly-summary',
      name: 'weekly-summary',
      component: WeeklySummary
    }
  ]
})

export default router