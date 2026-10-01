<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'

const items = ref([])
const err = ref('')
const openId = ref(null)
const detail = ref(null)
const detailErr = ref('')

onMounted(async () => {
  try {
    items.value = (await getJSON('/api/runs')).items
  } catch (e) {
    err.value = String(e.message || e)
  }
})

async function toggle(r) {
  detailErr.value = ''
  if (openId.value === r.id) {
    openId.value = null
    detail.value = null
    return
  }
  openId.value = r.id
  detail.value = null
  try {
    detail.value = await getJSON(`/api/runs/${r.id}`)
  } catch (e) {
    detailErr.value = String(e.message || e)
  }
}

function names(r) {
  return (r.box_names && r.box_names.length ? r.box_names : []).filter(Boolean).join('、') || '—'
}
</script>

<template>
  <div class="page">
    <h1>用纸档</h1>
    <p class="hint">列表与详情同源同数：分盒全量展开，合计为写入时派生值。</p>
    <p class="lede">每次写入一条：合计由分盒快照求和派生；此后改盒尺寸，本档不重算。</p>
    <p v-if="err" class="bad">{{ err }}</p>
    <p v-else-if="!items.length" class="empty">还没有写入过。先去算纸试一单。</p>
    <ul v-else class="item-list">
      <li v-for="r in items" :key="r.id" class="run-row">
        <div class="run-head" @click="toggle(r)">
          <span class="run-title">
            #{{ r.id }} {{ names(r) }}
            <span class="meta" v-if="(r.box_ids || []).length > 1">（{{ r.box_ids.length }} 盒套盒）</span>
          </span>
          <span class="meta">{{ r.total_paper_m2 ?? r.result?.paper_m2 ?? '—' }} m² 合计 · {{ r.created_at?.slice(0,10) }}</span>
        </div>
        <div v-if="openId === r.id" class="run-detail">
          <p v-if="detailErr" class="bad">{{ detailErr }}</p>
          <table v-if="detail" class="split-table">
            <thead>
              <tr><th>礼盒</th><th>尺寸快照 (m)</th><th>表面积 m²</th><th>用纸 m²</th></tr>
            </thead>
            <tbody>
              <tr v-for="b in (detail.boxes || [])" :key="b.box_id">
                <td>{{ b.name ?? ('#' + b.box_id) }}</td>
                <td class="num">
                  <template v-if="b.snapshot">
                    {{ b.snapshot.length }} × {{ b.snapshot.width }} × {{ b.snapshot.height }}
                  </template>
                  <template v-else>旧单未存快照</template>
                </td>
                <td class="num">{{ b.box_surface }}</td>
                <td class="num">{{ b.paper_m2 }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td>合计（与列表同源）</td><td></td>
                <td class="num">{{ detail.total_box_surface_m2 }}</td>
                <td class="num strong">{{ detail.total_paper_m2 }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.run-row { display: block; }
.run-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: baseline;
  cursor: pointer;
}
.run-title { font-weight: 600; }
.run-detail { padding: 0.25rem 0 0.75rem; }
.split-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}
.split-table th, .split-table td {
  text-align: left;
  padding: 0.45rem 0.5rem;
  border-bottom: 1px solid var(--line);
}
.split-table td.num { text-align: right; font-variant-numeric: tabular-nums; }
.split-table th:nth-child(3), .split-table th:nth-child(4) { text-align: right; }
.split-table tfoot td { font-weight: 600; border-top: 2px solid var(--line); }
.split-table .strong { color: var(--wash-b); }
</style>
