<template>
  <div class="gw-shell">
    <aside class="gw-rail">
      <div class="gw-brand">
        <span class="mark">Giftwrap</span>
        <span class="sub">礼品包装纸</span>
      </div>
      <nav>
        <router-link to="/">盒型</router-link>
        <router-link to="/boxes">清单</router-link>
        <router-link to="/papers">纸张</router-link>
        <router-link to="/bench">算纸</router-link>
        <router-link to="/ribbon">丝带</router-link>
        <router-link to="/overlap">折边系数</router-link>
        <router-link to="/history">用纸档</router-link>
        <router-link to="/settings">设置</router-link>
      </nav>
      <div class="gw-rail-foot">BOX → PAPER → UNFOLD</div>
    </aside>
    <main class="gw-main">
      <router-view />
    </main>
  </div>
</template>
