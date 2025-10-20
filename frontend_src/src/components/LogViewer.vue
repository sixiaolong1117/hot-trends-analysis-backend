<template>
  <div class="log-viewer">
    <div class="log-header">
      <h3>执行日志</h3>
      <div class="log-actions">
        <button @click="clearLogs" class="btn-clear">清空日志</button>
        <button @click="toggleAutoScroll" :class="['btn-scroll', { active: autoScroll }]">
          {{ autoScroll ? '自动滚动: 开' : '自动滚动: 关' }}
        </button>
      </div>
    </div>
    
    <div ref="logContainer" class="log-container" @scroll="handleScroll">
      <div v-if="logs.length === 0" class="log-empty">
        等待日志输出...
      </div>
      <div v-for="(log, index) in logs" :key="index" :class="['log-line', `log-${log.type}`]">
        <span class="log-time">{{ log.time }}</span>
        <span class="log-message">{{ log.message }}</span>
      </div>
    </div>
    
    <div v-if="status" class="log-status" :class="`status-${status}`">
      {{ statusMessage }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'LogViewer',
  props: {
    apiUrl: {
      type: String,
      required: true
    },
    requestData: {
      type: Object,
      required: true
    },
    autoStart: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      logs: [],
      autoScroll: true,
      status: null, // 'running', 'complete', 'error'
      statusMessage: '',
      eventSource: null
    }
  },
  mounted() {
    if (this.autoStart) {
      this.startAnalysis()
    }
  },
  beforeUnmount() {
    this.closeEventSource()
  },
  methods: {
    startAnalysis() {
      this.clearLogs()
      this.status = 'running'
      this.statusMessage = '正在执行分析...'
      
      // 构建 URL 查询参数
      const params = new URLSearchParams()
      for (const [key, value] of Object.entries(this.requestData)) {
        if (Array.isArray(value)) {
          value.forEach(v => params.append(key, v))
        } else {
          params.append(key, value)
        }
      }
      
      // 使用 fetch 进行 POST 请求获取 SSE 流
      this.connectSSE()
    },
    
    async connectSSE() {
      try {
        const response = await fetch(this.apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(this.requestData)
        })
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''  // 用于存储不完整的数据
        
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          
          // 将新数据追加到缓冲区
          buffer += decoder.decode(value, { stream: true })
          
          // 按行分割，处理完整的行
          const lines = buffer.split('\n')
          
          // 保留最后一个可能不完整的行
          buffer = lines.pop() || ''
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const jsonStr = line.slice(6).trim()
                if (jsonStr) {
                  const data = JSON.parse(jsonStr)
                  this.handleMessage(data)
                }
              } catch (parseError) {
                console.error('JSON 解析错误:', parseError, '原始数据:', line)
                // 继续处理其他行，不中断整个流
              }
            }
          }
        }
        
        // 处理缓冲区中剩余的数据
        if (buffer.trim() && buffer.startsWith('data: ')) {
          try {
            const jsonStr = buffer.slice(6).trim()
            if (jsonStr) {
              const data = JSON.parse(jsonStr)
              this.handleMessage(data)
            }
          } catch (parseError) {
            console.error('最终缓冲区 JSON 解析错误:', parseError)
          }
        }
      } catch (error) {
        this.addLog('error', `连接错误: ${error.message}`)
        this.status = 'error'
        this.statusMessage = '执行失败'
      }
    },
    
    handleMessage(data) {
      switch (data.type) {
        case 'log':
          this.addLog('info', data.message)
          break
        case 'error':
          this.addLog('error', data.message)
          this.status = 'error'
          this.statusMessage = '执行失败'
          this.$emit('error', data.message)
          break
        case 'complete':
          this.addLog('success', '分析完成！')
          this.status = 'complete'
          this.statusMessage = '执行完成'
          this.$emit('complete', data.result)
          break
      }
    },
    
    addLog(type, message) {
      const now = new Date()
      const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
      
      this.logs.push({
        type,
        message,
        time
      })
      
      if (this.autoScroll) {
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      }
    },
    
    clearLogs() {
      this.logs = []
      this.status = null
      this.statusMessage = ''
    },
    
    toggleAutoScroll() {
      this.autoScroll = !this.autoScroll
      if (this.autoScroll) {
        this.scrollToBottom()
      }
    },
    
    scrollToBottom() {
      const container = this.$refs.logContainer
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    },
    
    handleScroll() {
      const container = this.$refs.logContainer
      if (container) {
        const isAtBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 10
        if (!isAtBottom && this.autoScroll) {
          this.autoScroll = false
        }
      }
    },
    
    closeEventSource() {
      if (this.eventSource) {
        this.eventSource.close()
        this.eventSource = null
      }
    }
  }
}
</script>

<style scoped>
.log-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f5f5;
  border-bottom: 1px solid #ddd;
}

.log-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.log-actions {
  display: flex;
  gap: 8px;
}

.log-actions button {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.log-actions button:hover {
  background: #f0f0f0;
}

.btn-scroll.active {
  background: #4CAF50;
  color: white;
  border-color: #4CAF50;
}

.log-container {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  background: #1e1e1e;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.log-empty {
  color: #888;
  text-align: center;
  padding: 20px;
  font-style: italic;
}

.log-line {
  margin-bottom: 4px;
  word-wrap: break-word;
}

.log-time {
  color: #888;
  margin-right: 8px;
}

.log-message {
  color: #ddd;
}

.log-info .log-message {
  color: #ddd;
}

.log-success .log-message {
  color: #4CAF50;
  font-weight: 500;
}

.log-error .log-message {
  color: #f44336;
  font-weight: 500;
}

.log-status {
  padding: 10px 16px;
  font-size: 14px;
  font-weight: 500;
  text-align: center;
  border-top: 1px solid #ddd;
}

.status-running {
  background: #2196F3;
  color: white;
}

.status-complete {
  background: #4CAF50;
  color: white;
}

.status-error {
  background: #f44336;
  color: white;
}

/* 滚动条样式 */
.log-container::-webkit-scrollbar {
  width: 8px;
}

.log-container::-webkit-scrollbar-track {
  background: #2d2d2d;
}

.log-container::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.log-container::-webkit-scrollbar-thumb:hover {
  background: #666;
}
</style>