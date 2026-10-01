<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'

const s = ref({})
const err = ref('')

onMounted(async () => {
  try {
    s.value = await getJSON('/api/settings')
  } catch (e) {
    err.value = String(e.message || e)
  }
})
</script>

<template>
  <div class="page">
    <h1>折边系数</h1>
    <p class="lede">盒体外表面近似面积乘以该系数，得到含重叠余量的用纸面积。</p>
    <p v-if="err" class="bad">{{ err }}</p>
    <div v-else class="result-board">
      <div class="figure">× {{ s.overlap ?? '—' }}</div>
      <p class="stat-line">用纸面积 = 展开表面积 × 折边系数</p>
    </div>
  </div>
</template>
