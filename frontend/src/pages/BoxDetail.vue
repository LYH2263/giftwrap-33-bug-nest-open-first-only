<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
import BoxUnfold from '../components/BoxUnfold.vue'

const props = defineProps({ id: String })
const box = ref(null)
const err = ref('')

onMounted(async () => {
  try {
    box.value = await getJSON(`/api/boxes/${props.id}`)
  } catch (e) {
    err.value = String(e.message || e)
  }
})
</script>

<template>
  <div class="page">
    <p v-if="err" class="bad">{{ err }}</p>
    <template v-else-if="box">
      <h1>{{ box.name }}</h1>
      <p class="lede">
        {{ box.length }} × {{ box.width }} × {{ box.height }} m
        <span class="pill" :class="{ warn: box.data_quality === 'dirty' }">
          {{ box.data_quality === 'dirty' ? '脏数据' : '可用' }}
        </span>
      </p>
      <p v-if="box.data_quality === 'dirty'" class="bad">{{ box.note }}</p>
      <BoxUnfold :l="box.length" :w="box.width" :h="box.height" />
      <div class="row" style="margin-top: 1.25rem">
        <router-link class="btn" to="/bench">用此盒去算纸</router-link>
        <router-link class="btn ghost" to="/boxes">返回清单</router-link>
      </div>
    </template>
  </div>
</template>
