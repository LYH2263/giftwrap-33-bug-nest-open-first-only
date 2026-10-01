<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'

const items = ref([])
const err = ref('')

onMounted(async () => {
  try {
    items.value = (await getJSON('/api/papers')).items
  } catch (e) {
    err.value = String(e.message || e)
  }
})
</script>

<template>
  <div class="page">
    <h1>包装纸</h1>
    <p class="lede">卷宽用于后续裁切对齐；当前面积估算按折边系数走，不强制绑卷宽。</p>
    <p v-if="err" class="bad">{{ err }}</p>
    <div v-else class="paper-grid">
      <div v-for="p in items" :key="p.id" class="paper-tile">
        <strong>{{ p.name }}</strong>
        <span class="meta">卷宽 {{ p.roll_width }} m</span>
      </div>
    </div>
  </div>
</template>
