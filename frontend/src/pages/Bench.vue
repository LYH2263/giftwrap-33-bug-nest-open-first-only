<script setup>
import { computed, onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
import BoxUnfold from '../components/BoxUnfold.vue'

const boxes = ref([])
const selected = ref([])
const out = ref(null)
const err = ref('')
const busy = ref(false)
const savedId = ref(null)

const multi = computed(() => selected.value.length > 1)
const single = computed(() => selected.value.length === 1 ? boxes.value.find((b) => b.id === selected.value[0]) : null)

onMounted(async () => {
  try {
    const all = (await getJSON('/api/boxes')).items.filter((b) => b.data_quality === 'clean')
    boxes.value = all
    if (all.length) selected.value = [all[0].id]
  } catch (e) {
    err.value = String(e.message || e)
  }
})

function toggle(id, on) {
  selected.value = on ? [...selected.value, id] : selected.value.filter((x) => x !== id)
  out.value = null
  savedId.value = null
  err.value = ''
}

async function go(save) {
  if (!selected.value.length) {
    err.value = '请至少勾选一个礼盒'
    return
  }
  err.value = ''
  busy.value = true
  savedId.value = null
  try {
    if (multi.value) {
      // 多盒：统一 box_ids 合并通道（试算 GET / 写入 POST）
      out.value = save
        ? await postJSON('/api/estimate', { box_ids: selected.value, save: true })
        : await getJSON(`/api/estimate?box_ids=${selected.value.join(',')}`)
    } else {
      // 单盒：走单盒通道，保留展开图与丝带；合计与该盒单独测算相等
      out.value = save
        ? await postJSON('/api/estimate', { box_id: selected.value[0], save: true })
        : await getJSON(`/api/estimate?box_id=${selected.value[0]}`)
    }
    if (save) savedId.value = out.value.run_id
  } catch (e) {
    out.value = null
    err.value = String(e.message || e)
  } finally {
    busy.value = false
  }
}

function dims(b) {
  const s = b.snapshot || {}
  return [s.length ?? '—', s.width ?? '—', s.height ?? '—']
}
</script>

<template>
  <div class="page">
    <h1>算纸</h1>
    <p class="lede">勾选一个或多个 clean 礼盒：分盒面积各自落地，合计派生汇总成一条用纸档。</p>
    <ul class="box-pick">
      <li v-for="b in boxes" :key="b.id">
        <label>
          <input type="checkbox" :checked="selected.includes(b.id)"
                 @change="toggle(b.id, $event.target.checked)" />
          <span>{{ b.name }}</span>
          <span class="meta">{{ b.length }} × {{ b.width }} × {{ b.height }} m</span>
        </label>
      </li>
    </ul>
    <div class="row">
      <span class="meta">已选 {{ selected.length }} 盒</span>
      <button :disabled="busy" @click="go(false)">试算</button>
      <button class="ribbon" :disabled="busy" @click="go(true)">写入用纸档</button>
    </div>
    <p v-if="err" class="bad">{{ err }}</p>
    <p v-if="savedId" class="ok-pill">已写入用纸档 #{{ savedId }}，合计见 <router-link to="/history">用纸档</router-link>。</p>

    <div v-if="out" class="result-board">
      <div class="figure">{{ out.total_paper_m2 ?? out.paper_m2 }}<span>m² 合计用纸</span></div>
      <p class="stat-line" v-if="out.ribbon">
        十字丝带约 {{ out.ribbon.ribbon_m ?? out.ribbon }} m
      </p>

      <table class="split-table">
        <thead>
          <tr><th>礼盒</th><th>尺寸快照 (m)</th><th>表面积 m²</th><th>用纸 m²</th></tr>
        </thead>
        <tbody>
          <tr v-for="b in (out.boxes || [])" :key="b.box_id">
            <td>{{ b.name ?? ('#' + b.box_id) }}</td>
            <td class="num">{{ dims(b).join(' × ') }}</td>
            <td class="num">{{ b.box_surface }}</td>
            <td class="num">{{ b.paper_m2 }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td>合计（分盒求和派生）</td><td></td>
            <td class="num">{{ out.total_box_surface_m2 ?? out.box_surface }}</td>
            <td class="num strong">{{ out.total_paper_m2 ?? out.paper_m2 }}</td>
          </tr>
        </tfoot>
      </table>

      <BoxUnfold
        v-if="single && out.box"
        :l="out.box.length"
        :w="out.box.width"
        :h="out.box.height"
        :paper-m2="out.paper_m2"
      />
    </div>
  </div>
</template>

<style scoped>
.box-pick {
  list-style: none;
  margin: 0 0 0.75rem;
  padding: 0;
  border-top: 1px solid var(--line);
}
.box-pick li { border-bottom: 1px solid var(--line); }
.box-pick label {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.55rem 0.15rem;
  cursor: pointer;
}
.box-pick label:hover { background: rgba(255,255,255,0.45); }
.box-pick .meta { margin-left: auto; }
.split-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
  font-size: 0.92rem;
}
.split-table th, .split-table td {
  text-align: left;
  padding: 0.5rem 0.55rem;
  border-bottom: 1px solid var(--line);
}
.split-table td.num, .split-table th:nth-child(n+3) { text-align: right; font-variant-numeric: tabular-nums; }
.split-table tfoot td { font-weight: 600; border-top: 2px solid var(--line); }
.split-table .strong { color: var(--wash-b); }
.ok-pill { color: var(--wash-b); font-weight: 600; }
</style>
