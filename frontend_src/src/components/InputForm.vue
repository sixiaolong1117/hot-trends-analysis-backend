<template>
  <div class="input-form">
    <h2>分析配置</h2>
    
    <div class="form-group">
      <label>Ollama 模型:</label>
      <input 
        v-model="config.ollama_model" 
        type="text" 
        placeholder="qwen2.5:14b"
        :disabled="loading"
      />
    </div>
    
    <div class="form-group">
      <label>每平台话题数:</label>
      <input 
        v-model.number="config.topics_per_platform" 
        type="number" 
        min="1" 
        max="50"
        :disabled="loading"
      />
    </div>
    
    <div class="form-group">
      <div class="platform-header">
        <label>选择平台:</label>
        <div class="platform-actions">
          <button 
            type="button" 
            @click="selectAll" 
            :disabled="loading"
            class="btn-select"
          >
            全选
          </button>
          <button 
            type="button" 
            @click="clearAll" 
            :disabled="loading"
            class="btn-select"
          >
            清空
          </button>
          <span class="platform-count">已选: {{ config.platforms.length }}/{{ availablePlatforms.length }}</span>
        </div>
      </div>
      <div class="platform-checkboxes">
        <label 
          v-for="platform in availablePlatforms" 
          :key="platform"
          :class="{ disabled: loading }"
        >
          <input 
            type="checkbox" 
            :value="platform" 
            v-model="config.platforms"
            :disabled="loading"
          />
          {{ platformNames[platform] }}
        </label>
      </div>
    </div>
    
    <button 
      @click="startAnalysis" 
      :disabled="loading || config.platforms.length === 0"
      class="btn-analyze"
    >
      {{ loading ? '分析中...' : '🚀 开始分析' }}
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const emit = defineEmits(['start-analysis']);

const config = ref({
  ollama_model: 'qwen2.5:14b',
  topics_per_platform: 10,
  platforms: ['weibo', 'zhihu', 'baidu', 'douyin']
});

const availablePlatforms = ref([
  '36kr', '51cto', '52pojie', 'acfun', 'baidu', 'bilibili', 'coolapk', 'csdn',
  'dgtle', 'douban-group', 'douban-movie', 'douyin', 'earthquake', 'gameres',
  'geekpark', 'genshin', 'github', 'guokr', 'hackernews', 'hellogithub',
  'history', 'honkai', 'hostloc', 'hupu', 'huxiu', 'ifanr', 'ithome-xijiayi',
  'ithome', 'jianshu', 'juejin', 'kuaishou', 'linuxdo', 'lol', 'miyoushe',
  'netease-news', 'newsmth', 'ngabbs', 'nodeseek', 'nytimes', 'producthunt',
  'qq-news', 'sina-news', 'sina', 'smzdm', 'sspai', 'starrail', 'thepaper',
  'tieba', 'toutiao', 'v2ex', 'weatheralarm', 'weibo', 'weread', 'yystv',
  'zhihu-daily', 'zhihu'
]);

const platformNames = {
  '36kr': '36氪',
  '51cto': '51CTO',
  '52pojie': '吾爱破解',
  'acfun': 'AcFun',
  'baidu': '百度',
  'bilibili': '哔哩哔哩',
  'coolapk': '酷安',
  'csdn': 'CSDN',
  'dgtle': '数字尾巴',
  'douban-group': '豆瓣小组',
  'douban-movie': '豆瓣电影',
  'douyin': '抖音',
  'earthquake': '地震速报',
  'gameres': '游资网',
  'geekpark': '极客公园',
  'genshin': '原神',
  'github': 'GitHub',
  'guokr': '果壳',
  'hackernews': 'Hacker News',
  'hellogithub': 'HelloGitHub',
  'history': '历史上的今天',
  'honkai': '崩坏3',
  'hostloc': 'HostLoc',
  'hupu': '虎扑',
  'huxiu': '虎嗅',
  'ifanr': '爱范儿',
  'ithome-xijiayi': 'IT之家(西街一))',
  'ithome': 'IT之家',
  'jianshu': '简书',
  'juejin': '稀土掘金',
  'kuaishou': '快手',
  'linuxdo': 'LinuxDo',
  'lol': '英雄联盟',
  'miyoushe': '米游社',
  'netease-news': '网易新闻',
  'newsmth': '水木社区',
  'ngabbs': 'NGA',
  'nodeseek': 'NodeSeek',
  'nytimes': '纽约时报',
  'producthunt': 'Product Hunt',
  'qq-news': '腾讯新闻',
  'sina-news': '新浪新闻',
  'sina': '新浪',
  'smzdm': '什么值得买',
  'sspai': '少数派',
  'starrail': '崩坏:星穹铁道',
  'thepaper': '澎湃新闻',
  'tieba': '百度贴吧',
  'toutiao': '今日头条',
  'v2ex': 'V2EX',
  'weatheralarm': '天气预警',
  'weibo': '微博',
  'weread': '微信读书',
  'yystv': '游研社',
  'zhihu-daily': '知乎日报',
  'zhihu': '知乎'
};

const loading = ref(false);

// 从后端加载配置
onMounted(async () => {
  try {
    const response = await fetch('/api/config');
    if (response.ok) {
      const serverConfig = await response.json();
      
      // 如果有默认平台配置，使用它
      if (serverConfig.default_platforms) {
        config.value.platforms = serverConfig.default_platforms.split(',');
      }
    }
  } catch (error) {
    console.error('加载配置失败:', error);
  }
});

function startAnalysis() {
  if (config.value.platforms.length === 0) {
    alert('请至少选择一个平台');
    return;
  }
  
  loading.value = true;
  
  // 发射事件给父组件，传递配置数据
  emit('start-analysis', { ...config.value });
  
  // 注意：loading 状态会在分析完成或失败后由父组件通过其他方式重置
  // 这里设置一个定时器作为保护措施
  setTimeout(() => {
    loading.value = false;
  }, 2000);
}

function selectAll() {
  config.value.platforms = [...availablePlatforms.value];
}

function clearAll() {
  config.value.platforms = [];
}
</script>

<style scoped>
.input-form {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

h2 {
  font-size: 20px;
  color: #333;
  margin-bottom: 20px;
  margin-top: 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #555;
  font-size: 14px;
}

.platform-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.platform-header label {
  margin-bottom: 0;
}

.platform-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-select {
  padding: 4px 12px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-select:hover:not(:disabled) {
  background: #f0f0f0;
  border-color: #2196F3;
}

.btn-select:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.platform-count {
  font-size: 12px;
  color: #666;
  font-weight: normal;
}

.form-group input[type="text"],
.form-group input[type="number"] {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-group input[type="text"]:focus,
.form-group input[type="number"]:focus {
  outline: none;
  border-color: #2196F3;
}

.form-group input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.platform-checkboxes {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 8px;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 6px;
  max-height: 300px;
  overflow-y: auto;
}

.platform-checkboxes label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-weight: normal;
  font-size: 13px;
  padding: 6px 10px;
  border-radius: 4px;
  transition: background 0.2s;
  background: #fff;
  border: 1px solid #e0e0e0;
}

.platform-checkboxes label:hover:not(.disabled) {
  background: #f5f5f5;
  border-color: #2196F3;
}

.platform-checkboxes label.disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.platform-checkboxes input[type="checkbox"] {
  cursor: pointer;
  width: 16px;
  height: 16px;
}

.platform-checkboxes input[type="checkbox"]:disabled {
  cursor: not-allowed;
}

.platform-checkboxes::-webkit-scrollbar {
  width: 6px;
}

.platform-checkboxes::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.platform-checkboxes::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

.platform-checkboxes::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.btn-analyze {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-analyze:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

.btn-analyze:active:not(:disabled) {
  transform: translateY(0);
}

.btn-analyze:disabled {
  background: linear-gradient(135deg, #ccc 0%, #999 100%);
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}
</style>