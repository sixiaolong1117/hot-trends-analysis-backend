<template>
  <form @submit.prevent="submitForm" class="input-form">
    <!-- 模型选择 -->
    <div class="form-group">
      <label for="model">模型</label>
      <input id="model" v-model="form.ollama_model" />
    </div>

    <!-- 平台选择 -->
    <div class="form-group">
      <label>平台</label>
      <div class="platforms">
        <label v-for="p in availablePlatforms" :key="p">
          <input type="checkbox" :value="p" v-model="form.platforms" /> {{ p }}
        </label>
      </div>
    </div>

    <!-- 每个平台的条目数量 -->
    <div class="form-group">
      <label for="topics">每个平台分析条目数</label>
      <input
        id="topics"
        type="number"
        v-model.number="form.topics_per_platform"
        min="1"
      />
    </div>

    <!-- 显示 API 地址（只读） -->
    <div class="form-group readonly">
      <label>Ollama API</label>
      <span>{{ config.ollama_api || "加载中..." }}</span>
    </div>
    <div class="form-group readonly">
      <label>热搜 API</label>
      <span>{{ config.hot_search_api || "加载中..." }}</span>
    </div>

    <!-- 提交按钮，保留 loading 状态 -->
    <button type="submit" :disabled="loading">
      {{ loading ? "分析中..." : "开始分析" }}
    </button>
  </form>
</template>

<script setup>
import { ref, onMounted } from "vue";

const config = ref({
  ollama_api: "",
  hot_search_api: "",
  default_platforms: ""
});

const form = ref({
  ollama_model: "qwen2.5:14b",
  topics_per_platform: 10,
  platforms: []
});

// 所有可用平台列表
const availablePlatforms = [
  "36kr","51cto","52pojie","acfun","baidu","bilibili","coolapk","csdn","dgtle",
  "douban-group","douban-movie","douyin","earthquake","gameres","geekpark",
  "genshin","github","guokr","hackernews","hellogithub","history","honkai",
  "hostloc","hupu","huxiu","ifanr","ithome-xijiayi","ithome","jianshu","juejin",
  "kuaishou","linuxdo","lol","miyoushe","netease-news","newsmth","ngabbs",
  "nodeseek","nytimes","producthunt","qq-news","sina-news","sina","smzdm","sspai",
  "starrail","thepaper","tieba","toutiao","v2ex","weatheralarm","weibo","weread",
  "yystv","zhihu-daily","zhihu"

];

const loading = ref(false);

const emit = defineEmits(["result"]);

onMounted(async () => {
  try {
    const res = await fetch("/api/config");
    const data = await res.json();
    config.value = data;

    // 将后端返回的 DEFAULT_PLATFORMS 字符串解析成数组
    const envDefault = (data.default_platforms || "").split(",")
                      .map(p => p.trim())
                      .filter(p => p);

    form.value.platforms = envDefault;
  } catch (err) {
    console.error("获取配置失败:", err);
    // 失败默认平台
    form.value.platforms = [
      "weibo", "zhihu", "baidu", "douyin", "toutiao"
    ];
  }
});

async function submitForm() {
  loading.value = true;
  try {
    const payload = {
      ollama_model: form.value.ollama_model,
      topics_per_platform: form.value.topics_per_platform,
      platforms: form.value.platforms
    };

    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    emit("result", data);
  } catch (err) {
    console.error("分析请求失败:", err);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.input-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group.readonly span {
  padding: 8px;
  background: #f5f5f5;
  border-radius: 6px;
  font-family: monospace;
}

.platforms label {
  margin-right: 10px;
}

button {
  padding: 10px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
