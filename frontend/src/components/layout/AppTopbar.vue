<script setup lang="ts">
import BreadcrumbTrail from './BreadcrumbTrail.vue'
defineProps<{ title: string; drawerOpen: boolean }>()
defineEmits<{ 'open-menu': [] }>()
</script>

<template>
  <header class="topbar">
    <button class="icon-button menu-trigger" type="button" aria-label="Open navigation menu" aria-haspopup="dialog" :aria-expanded="drawerOpen" @click="$emit('open-menu')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" /></svg>
    </button>
    <div class="topbar-heading">
      <BreadcrumbTrail />
      <h1>{{ title }}</h1>
    </div>
    <div class="topbar-context"><span class="context-mark">M</span><span>MyHarf team</span></div>
  </header>
</template>
