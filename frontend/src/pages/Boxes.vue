<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'

const items = ref([])
const err = ref('')

onMounted(async () => {
  try {
    items.value = (await getJSON('/api/boxes')).items
  } catch (e) {
    err.value = String(e.message || e)
  }
})
</script>

<template>
  <div class="page">
    <h1>礼盒清单</h1>
    <p class="lede">可进详情看展开外形；脏数据会标出，不算入试算候选。</p>
    <p v-if="err" class="bad">{{ err }}</p>
    <ul v-else class="item-list">
      <li v-for="b in items" :key="b.id">
        <router-link :to="`/boxes/${b.id}`">{{ b.name }}</router-link>
        <span class="meta">
          {{ b.length }}×{{ b.width }}×{{ b.height }} m
          <span class="pill" :class="{ warn: b.data_quality === 'dirty' }">
            {{ b.data_quality === 'dirty' ? '脏数据' : '可用' }}
          </span>
        </span>
      </li>
    </ul>
  </div>
</template>
