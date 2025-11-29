<template>
  <div class="page-container">
    <header class="page-header">
      <div>
        <div class="page-title-wrapper">ARCHIVE</div>
        <h1 class="page-title">{{ locale === 'zh' ? '历史' : 'HISTORY' }}<span>{{ locale === 'zh' ? '报告' : 'REPORTS' }}</span></h1>
      </div>
    </header>

    <div class="layout-split">
      <!-- Timeline Sidebar -->
      <div class="timeline-list card">
        <div class="card-header">
          <div class="card-title">{{ t('report_list') }}</div>
        </div>
        <div class="list-body">
          <div 
            v-for="item in history" 
            :key="item.id" 
            class="timeline-item"
            :class="{ active: selectedReport?.id === item.id }"
            @click="selectReport(item)"
          >
            <div class="item-date">{{ formatDate(item.timestamp) }}</div>
            <div class="item-title">{{ item.type === 'daily' ? (locale === 'zh' ? '每日总结' : 'Daily Summary') : (locale === 'zh' ? '深度报告' : 'Deep Report') }}</div>
          </div>
        </div>
      </div>

      <!-- Report Viewer -->
      <div class="report-viewer card">
        <div class="card-header">
          <div class="card-title">{{ selectedReport ? formatDate(selectedReport.timestamp) : t('report_content') }}</div>
          <div class="actions" v-if="selectedReport">
            <button 
              class="btn btn-sm btn-outline" 
              @click="exportPDF"
              :disabled="exporting || !selectedReportContent"
            >
              <span v-if="exporting">{{ locale === 'zh' ? '导出中...' : 'Exporting...' }}</span>
              <span v-else>{{ locale === 'zh' ? '导出 PDF' : 'Export PDF' }}</span>
            </button>
          </div>
        </div>
        <div class="card-body report-content-area">
          <div v-if="loading" class="loading">{{ t('loading') }}</div>
          <div v-else-if="selectedReportContent" class="markdown-body" v-html="formatContent(selectedReportContent)"></div>
          <div v-else class="empty-state">{{ t('select_report') }}</div>
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

const history = ref([])
const selectedReport = ref(null)
const selectedReportContent = ref('')
const loading = ref(false)
const exporting = ref(false)

const formatDate = (ts) => {
  if (!ts) return ''
  return new Date(ts).toLocaleString()
}

const formatContent = (text) => {
  if (!text) return ''
  // Simple markdown-ish formatter
  return text
    .replace(/【(.*?)】/g, '<h3 class="section-title">$1</h3>')
    .replace(/\n/g, '<br>')
    .replace(/#{1,3}\s(.*?)<br>/g, '<h3>$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}

const fetchHistory = async () => {
  try {
    const res = await axios.get('/api/reports/history')
    history.value = res.data.data || []
  } catch (e) {
    console.error(e)
  }
}

const selectReport = async (item) => {
  selectedReport.value = item
  loading.value = true
  try {
    const res = await axios.get(`/api/reports/${item.id}?type=${item.type}`)
    selectedReportContent.value = res.data.content || JSON.stringify(res.data, null, 2)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

// 导出 PDF 功能
const exportPDF = () => {
  if (!selectedReport.value || !selectedReportContent.value) return
  
  exporting.value = true
  
  // 创建打印专用的 iframe
  const printFrame = document.createElement('iframe')
  printFrame.style.position = 'absolute'
  printFrame.style.top = '-10000px'
  printFrame.style.left = '-10000px'
  document.body.appendChild(printFrame)
  
  const reportDate = formatDate(selectedReport.value.timestamp)
  const reportType = selectedReport.value.type === 'daily' 
    ? (locale.value === 'zh' ? '每日总结' : 'Daily Summary')
    : (locale.value === 'zh' ? '深度报告' : 'Deep Report')
  
  // 构建打印内容
  const printContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>${reportType} - ${reportDate}</title>
      <style>
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }
        body {
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Microsoft YaHei", sans-serif;
          font-size: 12px;
          line-height: 1.8;
          color: #1a1a1a;
          padding: 40px;
          background: white;
        }
        .header {
          text-align: center;
          margin-bottom: 30px;
          padding-bottom: 20px;
          border-bottom: 2px solid #e85a1b;
        }
        .header h1 {
          font-size: 24px;
          margin-bottom: 10px;
          color: #1a1a1a;
        }
        .header .meta {
          color: #666;
          font-size: 14px;
        }
        .content {
          max-width: 100%;
        }
        .section-title {
          margin-top: 24px;
          margin-bottom: 12px;
          font-size: 16px;
          font-weight: 700;
          color: #1a1a1a;
          border-bottom: 2px solid #e85a1b;
          display: inline-block;
          padding-bottom: 4px;
        }
        h3 {
          margin-top: 20px;
          margin-bottom: 10px;
          font-size: 14px;
          font-weight: 700;
        }
        strong {
          font-weight: 700;
        }
        .footer {
          margin-top: 40px;
          padding-top: 20px;
          border-top: 1px solid #ddd;
          text-align: center;
          color: #999;
          font-size: 10px;
        }
        @media print {
          body { padding: 20px; }
          @page { margin: 1cm; }
        }
      </style>
    </head>
    <body>
      <div class="header">
        <h1>WIDE RESEARCH // ${locale.value === 'zh' ? '财经研究终端' : 'FINANCE TERMINAL'}</h1>
        <div class="meta">${reportType} | ${reportDate}</div>
      </div>
      <div class="content">
        ${formatContent(selectedReportContent.value)}
      </div>
      <div class="footer">
        Generated by Wide Research Finance Terminal | ${new Date().toLocaleString()}
      </div>
    </body>
    </html>
  `
  
  // 写入 iframe 并触发打印
  const frameDoc = printFrame.contentWindow || printFrame.contentDocument
  const doc = frameDoc.document || frameDoc
  
  doc.open()
  doc.write(printContent)
  doc.close()
  
  // 等待内容加载完成后打印
  setTimeout(() => {
    printFrame.contentWindow.focus()
    printFrame.contentWindow.print()
    
    // 打印对话框关闭后移除 iframe
    setTimeout(() => {
      if (document.body.contains(printFrame)) {
        document.body.removeChild(printFrame)
      }
      exporting.value = false
    }, 500)
  }, 300)
}

onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
.page-container {
  height: calc(100vh - 48px - 6rem);
  display: flex;
  flex-direction: column;
}

.layout-split {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 2rem;
  flex: 1;
  min-height: 0;
}

.timeline-list {
  height: 100%;
  margin-bottom: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.list-body {
  padding: 0;
  flex: 1;
  overflow-y: auto;
}

.timeline-item {
  padding: 1rem;
  border-bottom: 1px solid var(--c-grid);
  cursor: pointer;
  transition: all 0.2s;
  border-left: 4px solid transparent;
}

.timeline-item:hover {
  background: var(--c-hover);
}

.timeline-item.active {
  background: var(--c-ink);
  color: var(--c-bg);
  border-left-color: var(--c-amber);
}

.item-date {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  margin-bottom: 0.25rem;
  opacity: 0.8;
}

.item-title {
  font-weight: 700;
}

.report-viewer {
  height: 100%;
  margin-bottom: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.report-content-area {
  flex: 1;
  overflow-y: auto;
  font-family: var(--font-body);
  line-height: 1.8;
  padding: 2rem;
  background: var(--c-paper);
}

.markdown-body {
  max-width: 800px;
  margin: 0 auto;
}

/* Deep selector for v-html content */
.report-content-area :deep(.section-title) {
  margin-top: 2rem;
  margin-bottom: 1rem;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--c-ink);
  border-bottom: 2px solid var(--c-amber);
  display: inline-block;
  padding-bottom: 0.2rem;
}

.report-content-area :deep(h3) {
  margin-top: 1.5rem;
  font-size: 1.1rem;
  font-weight: 700;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--c-muted);
  font-weight: 700;
}

@media (max-width: 768px) {
  .page-container {
    height: auto;
    display: block;
  }

  .layout-split {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .timeline-list {
    height: 300px; /* Fixed height for list on mobile */
    margin-bottom: 1rem;
  }

  .report-viewer {
    height: 600px; /* Fixed height for viewer on mobile */
  }
}
</style>
