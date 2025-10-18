<template>
  <div class="container">
    <h1>🔥 网络热搜分析工具</h1>
    <InputForm @result="handleResult" />
    <ResultViewer v-if="result" :data="result" />
  </div>
</template>

<script setup>
import { ref } from "vue";
import InputForm from "./components/InputForm.vue";
import ResultViewer from "./components/ResultViewer.vue";

const result = ref(null);
function handleResult(data) {
  result.value = data;
}
</script>