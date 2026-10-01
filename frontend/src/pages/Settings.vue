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
    <h1>设置</h1>
    <p class="lede">当前全局参数只读展示；改系数请走「折边系数」页对照算法说明。</p>
    <p v-if="err" class="bad">{{ err }}</p>
    <ul v-else class="item-list">
      <li>
        <span>折边系数 overlap</span>
        <span class="meta">{{ s.overlap }}</span>
      </li>
    </ul>
  </div>
</template>
