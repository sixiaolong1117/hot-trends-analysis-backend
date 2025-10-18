<template>
  <div class="result">
    <h2>📊 分析结果</h2>
    <pre>{{ pretty }}</pre>
  </div>
</template>

<script setup>
import { computed } from "vue";
const props = defineProps({ data: Object });
const pretty = computed(() => JSON.stringify(props.data, null, 2));
</script>

<style scoped>
.result {
  margin-top: 2rem;
  background: #f9fafb;
  padding: 1rem;
  border-radius: 10px;
}
pre {
  background: white;
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 0.9rem;
}
</style>
