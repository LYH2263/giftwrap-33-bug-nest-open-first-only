<script setup>
defineProps({
  l: { type: Number, default: 0 },
  w: { type: Number, default: 0 },
  h: { type: Number, default: 0 },
  paperM2: { type: Number, default: null },
})
</script>

<template>
  <div class="unfold">
    <p class="unfold-title">盒体展开示意</p>
    <svg class="unfold-svg" viewBox="0 0 280 180" aria-hidden="true">
      <rect class="panel" x="95" y="18" width="90" height="42" rx="2" />
      <rect class="panel top" x="95" y="68" width="90" height="52" rx="2" />
      <rect class="panel" x="20" y="68" width="68" height="52" rx="2" />
      <rect class="panel" x="192" y="68" width="68" height="52" rx="2" />
      <rect class="panel" x="95" y="128" width="90" height="38" rx="2" />
      <text x="140" y="44" text-anchor="middle">顶 {{ Number(l).toFixed(2) }}×{{ Number(w).toFixed(2) }}</text>
      <text x="140" y="98" text-anchor="middle">正面</text>
      <text x="54" y="98" text-anchor="middle">侧</text>
      <text x="226" y="98" text-anchor="middle">侧</text>
      <text x="140" y="152" text-anchor="middle">h≈{{ Number(h).toFixed(2) }}</text>
    </svg>
    <p v-if="paperM2 != null" class="stat-line">
      估算用纸 <strong>{{ Number(paperM2).toFixed(4) }}</strong> m²（含折边系数）
    </p>
    <p v-else class="stat-line">
      外形 {{ Number(l).toFixed(2) }} × {{ Number(w).toFixed(2) }} × {{ Number(h).toFixed(2) }} m
    </p>
  </div>
</template>
