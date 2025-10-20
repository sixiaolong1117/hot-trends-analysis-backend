<template>
  <div class="container">
    <h1>🔥 网络热搜分析工具</h1>
    <InputForm @start-analysis="handleStartAnalysis" />
    
    <!-- 日志查看器 -->
    <div v-if="showLogs" class="log-section">
      <LogViewer 
        ref="logViewer"
        api-url="/api/analyze-stream"
        :request-data="analysisConfig"
        @complete="handleResult"
        @error="handleError"
      />
    </div>
    
    <!-- 结果展示 -->
    <!-- <ResultViewer v-if="result" :data="result" /> -->
  </div>
</template>

<script setup>
import { ref } from "vue";
import InputForm from "./components/InputForm.vue";
import ResultViewer from "./components/ResultViewer.vue";
import LogViewer from "./components/LogViewer.vue";

const result = ref(null);
const showLogs = ref(false);
const analysisConfig = ref(null);
const logViewer = ref(null);

function handleStartAnalysis(config) {
  // 清除之前的结果
  result.value = null;
  
  // 保存配置并显示日志窗口
  analysisConfig.value = config;
  showLogs.value = true;
  
  // 等待 DOM 更新后启动分析
  setTimeout(() => {
    if (logViewer.value) {
      logViewer.value.startAnalysis();
    }
  }, 100);
}

function handleResult(data) {
  result.value = data;
}

function handleError(error) {
  console.error('分析失败:', error);
}
</script>

<style scoped>
.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
  font-size: 32px;
}

.log-section {
  margin: 30px 0;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  height: 500px;
  overflow: hidden;
}
</style>